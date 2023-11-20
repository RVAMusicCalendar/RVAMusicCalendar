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

from data.db.dbService import insert_dupe_event_db, event_already_exists, get_or_insert_venue, insert_event_db
from scraper import scrape
from seleniumDriver import get_selenium_driver

rva_music_calendar_id = "810rm4o2829cdhurresns7a4cc@group.calendar.google.com"


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


def add_event_db(supabase, event, venue_db_id, calendar_id):
    try:
        created = insert_event_db(supabase, event, venue_db_id, calendar_id)
        print(f"Added {created} to the db")
        return created
    except Exception as e:
        print("error", e)
        print("Error with the db and venue ", event)
        return None


def add_events(calendar_service, supabase, events):
    for event in events:
        venue_db_id = None
        try:
            venue_db_id = get_or_insert_venue(supabase, event.venue_info)
            print(f"venue {venue_db_id}")
        except Exception as e:
            print(e)
            print("Problem getting venue for", event)
        preexisting_event = None
        try:
            preexisting_event = event_already_exists(supabase, event)
        except Exception as e:
            print(e)
            print("Problem checking if event already exists", event)
        if not preexisting_event:
            calendar_event = add_gcal_event(calendar_service, event)
            event = add_event_db(supabase, event, venue_db_id, calendar_event.event_id)
        else:
            print(f"not adding event it already exists as {preexisting_event}", event)
            # lol could check if the pre-existing event isn't on the calendar and add it if it is would keep the db and calendar more in sync
            # Add dupes to a separate table to check later
            insert_dupe_event_db(supabase, event, preexisting_event, venue_db_id)


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
