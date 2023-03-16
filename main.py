import datetime as dt
import os

from alive_progress import alive_it, alive_bar
from gcsa.attachment import Attachment as GCalAttachment
from gcsa.event import Event as GCalEvent
from gcsa.google_calendar import GoogleCalendar
from google.oauth2.service_account import Credentials
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from scrapers.broadberryScraper import get_broadberry_event_urls
from scrapers.etixScraper import etix_event_details_scraper
from scrapers.theNationalScraper import get_national_event_urls, the_national_details_scraper

rva_music_calendar_id = "810rm4o2829cdhurresns7a4cc@group.calendar.google.com"


def get_event_details(driver, event_url):
    driver.get(event_url)
    scraped_event = None
    if "etix" in event_url:
        scraped_event = etix_event_details_scraper(driver, event_url)
    elif "thenationalva" in event_url:
        scraped_event = the_national_details_scraper(driver, event_url)
    else:
        print(f"ticketProvider not supported yet {event_url}")
    return scraped_event


def addCalendarEvents(calendarService, events):
    with alive_bar(total=len(events), dual_line=True, title='Creating Google Events', ctrl_c=False) as bar:
        for event in events:
            attachment = GCalAttachment(file_url=event.image_url)
            calendar_event = calendarService.add_event(event=GCalEvent(
                summary=event.event_name,
                location=event.venue_info.full_address,
                start=event.event_datetime,
                end=(event.event_datetime + dt.timedelta(hours=3)),
                description=event.full_description,
                guests_can_see_other_guests=False,
                minutes_before_popup_reminder=15,
                attachments=attachment,
                visibility="public",
                other={
                    "source": event.url
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
    events = calendar_service.get_events()

    with alive_bar(dual_line=True, title='Deleting Old Google Events') as bar:
        for event in events:
            bar.text = f'-> Deleting {event.id} {event.summary}'
            calendar_service.delete_event(event=event)
            bar()


def get_selenium_driver(headless=True):
    options = Options()
    # options.add_experimental_option("detach", True)
    options.add_argument("--window-size=1920,1080")

    options.add_argument("--headless") if headless else None
    options.add_argument("--disable-infobars")
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    return driver


def main():
    driver = get_selenium_driver()

    creds = get_google_credentials()
    calendar_service = GoogleCalendar(credentials=creds, default_calendar=rva_music_calendar_id)

    clear_calendar(calendar_service)

    broad_berry_event_urls = get_broadberry_event_urls(driver)
    the_national_event_urls = get_national_event_urls()
    event_urls = broad_berry_event_urls + the_national_event_urls

    events = [*map(lambda event_url: get_event_details(driver, event_url), alive_it(event_urls, title="Scraping events"))]
    print(f"{len(events)} events found")

    events = [event for event in events if event is not None]  # If we get errors in scraping we return None, this strips those out
    print(f"{len(events)} events were valid")

    # for event in events:
    #     print(event.venue_info.city)
    # events = [event for event in events if event.venue_info.city.strip() != "Richmond"]  # Filter out events that aren't in richmond

    # print(f"{len(events)} events were valid AND in Richmond")
    addCalendarEvents(calendar_service, events)
    print(f"All of the events have been created")


if __name__ == '__main__':
    main()
