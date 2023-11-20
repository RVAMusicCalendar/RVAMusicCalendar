import datetime
import datetime as dt
import os
from collections import defaultdict

from alive_progress import alive_bar
from gcsa.attachment import Attachment as GCalAttachment
from gcsa.event import Event as GCalEvent
from gcsa.google_calendar import GoogleCalendar
from google.oauth2.service_account import Credentials
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions

from data.Event import Event
from scrapers import getTightScraper
from scrapers.broadberryScraper import get_broadberry_event_urls
from scrapers.etixScraper import etix_event_details_scraper
from scrapers.getTightScraper import get_gettight_events
from scrapers.theCamelScraper import get_camel_event_urls, the_camel_details_scraper
from scrapers.theNationalScraper import get_national_event_urls, the_national_details_scraper
from seleniumDriver import get_selenium_driver

rva_music_calendar_id = "810rm4o2829cdhurresns7a4cc@group.calendar.google.com"


def get_event_details(driver, event_url):
    driver.get(event_url)
    scraped_event: Event | None = None
    if "etix" in event_url:
        scraped_event = etix_event_details_scraper(driver, event_url)
    elif "thenationalva" in event_url:
        scraped_event = the_national_details_scraper(driver, event_url)
    elif "thecamel" in event_url:
        scraped_event = the_camel_details_scraper(driver, event_url)
    elif "dice.fm" in event_url:
        scraped_event = getTightScraper.get_event_details(driver, event_url)
    else:
        print(f"ticketProvider not supported yet {event_url}")
    return scraped_event


def add_gcal_event(calendar_service, event):
    attachment = GCalAttachment(file_url=event.image_url)
    calendar_event = calendar_service.add_event(event=GCalEvent(
        summary=event.event_name,
        location=event.venue_info.full_address,
        start=event.event_datetime,
        end=(event.event_datetime + dt.timedelta(hours=3)),
        description=event.full_description,
        guests_can_see_other_guests=False,
        minutes_before_popup_reminder=15,
        color_id=event.color_id,
        attachments=attachment,
        # visibility="public",
        other={
            "source": event.source_url if event.source_url != "" else event.url
        }
    ))
    return calendar_event


def add_calendar_events(calendar_service, events):
    with alive_bar(total=len(events), dual_line=True, title='Creating Google Events', ctrl_c=False, force_tty=True) as bar:
        for event in events:
            calendar_event = add_gcal_event(calendar_service, event)
            bar.text = f'-> {calendar_event} Created'
            bar()


def get_google_credentials():
    scopes = ['https://www.googleapis.com/auth/calendar']
    secret_file = os.path.join(os.getcwd(), 'service.json')
    credentials = Credentials.from_service_account_file(secret_file, scopes=scopes)
    return credentials


def clear_calendar(calendar_service):
    events = calendar_service.get_events(time_min=datetime.datetime.now())
    with alive_bar(dual_line=True, title='Trying to delete upcoming Google Events', force_tty=True) as bar:
        for event in events:
            if event.creator.email == "calendar-bot@rva-music-calendar.iam.gserviceaccount.com":
                bar.text = f'-> Deleting {event.id} {event.summary}'
                calendar_service.delete_event(event=event)
                bar()
            else:
                bar.text = f'-> Not Deleting manually created event {event.id} {event.summary} created by {event.creator}'
                bar()


def scrape_events(driver, urls):
    events = []
    with alive_bar(len(urls), dual_line=True, title='Scraping events by URL', force_tty=True) as bar:
        for url in urls:
            bar.text = f'-> currently scraping {url}'
            events.append(get_event_details(driver, url))
            bar()
    return events


def get_or_insert_venue(supabase, venue_info):
    data, count = supabase.table('venues').select("id", "street_address").eq('street_address', venue_info.street_address).execute()
    data = data[1]
    if data and len(data) > 0:  # Already in DB
        print("Already have this venue in the db", data[0])
        return data[0]["id"]
    else:  # Add it
        print("Adding venue to the db", venue_info)
        res = supabase.table('venues').insert({
            "name": venue_info.venue_name,
            "street_address": venue_info.street_address,
            "state": venue_info.state,
            "postal_code": venue_info.postal_code,
        }).execute()
        data = res.data
        return data[0]['id']


def insert_event_db(supabase, event, venue_id, calendar_event_id):
    data, count = supabase.table('events').insert({
        "event_name": event.event_name,
        "description": event.description,
        "event_datetime": f"{event.event_datetime}",
        "door_time": f"{event.door_time}",
        "price": event.price,
        "url": event.url,
        "image_url": event.image_url,
        "source_url": event.source_url,
        "googleCalendarEventId": calendar_event_id,
        "venue": venue_id
    }).execute()
    return data[1][0]


def add_event_db(supabase, event, venue_db_id, calendar_id):
    try:
        created = insert_event_db(supabase, event, venue_db_id, calendar_id)
        print(f"Added {created} to the db")
        return created
    except:
        print("Error with the db and venue ", event)
        return None


# RETURNS False if event doesn't exist
# RETURNS the id of the event if it does.
def event_already_exists(supabase, event): #TODO: could offload this to a trigger on the db
    # I wonder how bad using an ilike on a possibly large field like description is.
    data, count = supabase.table('events') \
        .select("*") \
        .ilike('event_name', event.event_name) \
        .ilike('description', event.description) \
        .execute()
    # TODO: How can we add in the within same time window check
    data = data[1]
    if data and len(data) > 0:  # Already in DB
        print("Already have this venue in the db", data[0])
        return data[0]["id"]  # I mean I didn't mean for this to return anything more than true or false... but not a bad feature?
    return False


def insert_dupe_event_db(supabase, event, preexisting_event_id, venue_db_id):
    data, count = supabase.table('dupes').insert({
        "event_name": event.event_name,
        "description": event.description,
        "event_datetime": f"{event.event_datetime}",
        "door_time": f"{event.door_time}",
        "price": event.price,
        "url": event.url,
        "image_url": event.image_url,
        "source_url": event.source_url,
        "venue": venue_db_id,
        "event_id": preexisting_event_id,
    }).execute()
    return data[1][0]


def add_events(calendar_service, supabase, events):
    for event in events:
        venue_db_id = get_or_insert_venue(supabase, event.venue_info)
        print(f"venue {venue_db_id}")
        preexisting_event = event_already_exists(supabase, event)
        if not preexisting_event:
            calendar_event = add_gcal_event(calendar_service, event)
            event = add_event_db(supabase, event, venue_db_id, calendar_event.event_id)
        else:
            print(f"not adding event it already exists as {preexisting_event}", event)
            # lol could check if the pre-existing event isn't on the calendar and add it if it is would keep the db and calendar more in sync
            # Add dupes to a separate table to check later
            insert_dupe_event_db(supabase, event, preexisting_event, venue_db_id)


def scrape(driver):
    events = []
    broad_berry_event_urls = get_broadberry_event_urls(driver)
    the_national_event_urls = get_national_event_urls()
    the_camel_event_urls = get_camel_event_urls(driver)
    event_urls = broad_berry_event_urls + the_national_event_urls + the_camel_event_urls

    # TODO: Add a check to the db and don't run it if source_url
    events += scrape_events(driver, event_urls)
    get_tight_events = get_gettight_events(driver)
    if len(get_tight_events) > 0:
        print("problem scraping Get Tight Lounge Events")  # TODO: maybe alert or something
        events += get_tight_events

    return events


def group_all_events_by_day():
    creds = get_google_credentials()
    calendar_service = GoogleCalendar(credentials=creds, default_calendar=rva_music_calendar_id)
    calendar_events = calendar_service.get_events()
    grouped = defaultdict(list)
    for event in calendar_events:
        event_date = event.start.strftime("%m/%d/%Y")
        # event = event.copy()
        grouped[event_date].append(event)
        print(event)

    print(grouped)
    print(grouped["04/25/2023"])


def get_events_for_day(date: datetime.date):
    creds = get_google_credentials()
    calendar_service = GoogleCalendar(credentials=creds, default_calendar=rva_music_calendar_id)
    time_min = datetime.datetime.combine(date, datetime.time.min)
    time_max = datetime.datetime.combine(date, datetime.time.max)
    events_on_date = [*calendar_service.get_events(time_min, time_max)]
    return events_on_date


def main():
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")

    supabase: Client = create_client(url, key,
                                     options=ClientOptions(
                                         postgrest_client_timeout=10,
                                         storage_client_timeout=10
                                     ))
    driver = get_selenium_driver(False, True)
    # driver = get_selenium_driver()

    creds = get_google_credentials()
    calendar_service = GoogleCalendar(credentials=creds, default_calendar=rva_music_calendar_id)
    # clear_calendar(calendar_service)

    events = scrape(driver)

    print(f"{len(events)} events found")
    filteredEvents = [event for event in events if event is not None]  # If we get errors in scraping we return None, this strips those out
    print(f"{len(filteredEvents)} events were valid")
    richmondEvents = [event for event in filteredEvents if event.venue_info.city == "Richmond"]  # Filter out events that aren't in richmond
    print(f"{len(richmondEvents)} events were valid AND in Richmond")
    add_events(calendar_service, supabase, richmondEvents)

    print(f"All of the Richmond {len(richmondEvents)} events have been created in google calendar")
    driver.quit()
    # tomorrow = datetime.date.today() + datetime.timedelta(1)
    # events_on_date = get_events_for_day(tomorrow)
    # generate_image_for_day(tomorrow, events_on_date)


if __name__ == '__main__':
    main()

# getTightVenueInfo = VenueInfo(venue_name="Get Tight Lounge", street_address="1104 W Main St", city="Richmond", state="Virginia", postal_code=23220)
# # get_or_insert_venue(supabase, getTightVenueInfo)
# now = datetime.datetime.now()
# event = Event(venue_info=getTightVenueInfo, event_datetime=now, door_time=now.time(), event_name="asdfasdf", image_url="url", description="asdf", event_url="event_url")
# # print("should add event before", should_add_event(supabase, event))
# # insert_event_db(supabase, event, "25", "asdf")
# # print("should add event after", should_add_event(supabase, event))
# add_events(None, supabase, [event])
#
