import datetime
import datetime as dt
import os

from alive_progress import alive_bar
from gcsa.attachment import Attachment as GCalAttachment
from gcsa.event import Event as GCalEvent
from gcsa.google_calendar import GoogleCalendar
from google.oauth2.service_account import Credentials

from data.Event import Event
from scrapers.broadberryScraper import get_broadberry_event_urls
from scrapers.etixScraper import etix_event_details_scraper
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
    else:
        print(f"ticketProvider not supported yet {event_url}")
    return scraped_event


def add_calendar_events(calendar_service, events):
    with alive_bar(total=len(events), dual_line=True, title='Creating Google Events', ctrl_c=False) as bar:
        for event in events:
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
            bar.text = f'-> {calendar_event} Created'
            bar()


def get_google_credentials():
    scopes = ['https://www.googleapis.com/auth/calendar']
    secret_file = os.path.join(os.getcwd(), 'service.json')
    credentials = Credentials.from_service_account_file(secret_file, scopes=scopes)
    return credentials


def clear_calendar(calendar_service):
    events = calendar_service.get_events(time_min=datetime.datetime.now())
    with alive_bar(dual_line=True, title='Trying to delete upcoming Google Events') as bar:
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
    with alive_bar(len(urls), dual_line=True, title='Scraping events') as bar:
        for url in urls:
            bar.text = f'-> currently scraping {url}'
            events.append(get_event_details(driver, url))
            bar()
    return events


def main():
    driver = get_selenium_driver()

    creds = get_google_credentials()
    calendar_service = GoogleCalendar(credentials=creds, default_calendar=rva_music_calendar_id)
    clear_calendar(calendar_service)
    broad_berry_event_urls = get_broadberry_event_urls(driver)
    the_national_event_urls = get_national_event_urls()
    the_camel_event_urls = get_camel_event_urls(driver)
    event_urls = broad_berry_event_urls + the_national_event_urls + the_camel_event_urls

    events = scrape_events(driver, event_urls)
    print(f"{len(events)} events found")
    events = [event for event in events if event is not None]  # If we get errors in scraping we return None, this strips those out
    print(f"{len(events)} events were valid")
    events = [event for event in events if event.venue_info.city == "Richmond"]  # Filter out events that aren't in richmond
    print(f"{len(events)} events were valid AND in Richmond")

    add_calendar_events(calendar_service, events)

    print(f"All of the {len(events)} events have been created")


if __name__ == '__main__':
    main()
