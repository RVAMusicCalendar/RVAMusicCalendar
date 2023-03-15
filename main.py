import datetime as dt

import time
import feedparser
from dateutil.parser import parse as dateTimeParse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from GoogleCalendarService import getGoogleCalendarService
from data.Event import Event
from data.VenueInfo import VenueInfo

broadBerryURL = "https://thebroadberry.com/events/?view=month"
theNationalRSSFeedURL = "https://www.thenationalva.com/events/rss"
theNationalVenueInfo = VenueInfo("The National", "708 E. Broad Street", "Richmond", "Virginia", 23219)


def get_broadberry_event_urls(driver):
    driver.get(broadBerryURL)
    time.sleep(5)
    events = driver.find_elements(By.LINK_TEXT, "BUY TICKETS")
    event_urls = [*map(lambda event: event.get_attribute("href"), events)]
    return event_urls


def get_national_event_urls():
    event_feed = feedparser.parse(theNationalRSSFeedURL)
    return [entry.link for entry in event_feed.entries]


def the_national_details_scraper(driver, event_url):
    event_detail_container = driver.find_element(By.CLASS_NAME, "event_detail")
    event_date = dateTimeParse(event_detail_container.find_element(By.CLASS_NAME, "left_column").find_element(By.CLASS_NAME, "date").text.replace("DATE", "")).date()
    event_time = dateTimeParse(driver.find_element(By.CLASS_NAME, "left_column").find_element(By.CLASS_NAME, "text-large").text.replace("TIME", "")).time()
    event_date_time = dt.datetime.combine(event_date, event_time)
    event_door_open_time = dateTimeParse(
        event_detail_container.find_element(By.CLASS_NAME, "doors").find_elements(By.TAG_NAME, "label")[1].text).time()  # The first one will just have the text "Doors"
    event_name = event_detail_container.find_element(By.CLASS_NAME, "page_header_left").find_element(By.TAG_NAME, "h1").text
    event_image_url = event_detail_container.find_element(By.CLASS_NAME, "event_image").find_element(By.TAG_NAME, "img").get_attribute("src")
    event_description = ""
    try:
        event_description = event_detail_container.find_element(By.CLASS_NAME, "bio").find_element(By.CLASS_NAME, "collapse-wrapper").text
    except:
        print(f"no bio available for this event {event_name}, {event_url}")
    event = Event(theNationalVenueInfo, event_date_time, event_door_open_time, event_name, event_image_url, event_description, event_url)
    print(event)
    return event


def get_event_details(driver, event_url):
    driver.get(event_url)
    if "etix" in event_url:
        return etix_event_details_scraper(driver, event_url)
    if "thenationalva" in event_url:
        return the_national_details_scraper(driver, event_url)
    else:
        print(f"ticketProvider not supported yet {event_url}")


def etix_event_details_scraper(driver, event_url):
    try:
        performance_info = driver.find_element(By.CLASS_NAME, "performance-info")
        event_image_url = performance_info.find_element(By.CLASS_NAME, "performance-image").find_element(By.TAG_NAME, "img").get_attribute("src")
        location_info_element = performance_info.find_element(By.CLASS_NAME, "location")
        venue_name = location_info_element.find_element(By.XPATH, "//span[@itemprop='name']").text
        address_info_element = performance_info.find_element(By.XPATH, "//span[@itemprop='address']")
        street_address = address_info_element.find_element(By.XPATH, "//meta[@itemprop='streetAddress']").get_attribute("content")
        address_locality = address_info_element.find_element(By.XPATH, "//meta[@itemprop='addressLocality']").get_attribute("content")
        address_region = address_info_element.find_element(By.XPATH, "//meta[@itemprop='addressRegion']").get_attribute("content")
        postal_code = address_info_element.find_element(By.XPATH, "//meta[@itemprop='postalCode']").get_attribute("content")
        event_name = performance_info.find_element(By.XPATH, "//h1[@itemprop='name']").text
        event_date_time = dateTimeParse(performance_info.find_element(By.XPATH, "//meta[@itemprop='startDate']").get_attribute('content'))
        event_door_open_time = dateTimeParse(performance_info.find_element(By.CLASS_NAME, "time").text.split("\n")[-1].replace("Doors Open:", "").strip()).time()
        event_description = performance_info.find_element(By.XPATH, "//div[@itemprop='description']").text
        return Event(VenueInfo(venue_name, street_address, address_locality, address_region, postal_code), event_date_time, event_door_open_time, event_name, event_image_url, event_description,
                     event_url)
    except:
        print(f"Problem extracting for {event_url}")


def getMusicCalendar(calendarService):
    calendar = {
        'summary': 'RVA Music Calendar',
        'timeZone': 'America/New_York'
    }
    created_calendar = calendarService.calendars().insert(body=calendar).execute()
    calendarService.calendarList().insert(body={
        "id": created_calendar['id'],
    }, colorRgbFormat=False)
    # calendarList = calendarService.calendarList().list()
    # print(calendarList.__dict__)
    # print(calendarList.items)
    return created_calendar


def addCalendarEvent(event, calendar, service):
    googleCalendarEvent = {
        "summary": event.eventName,  # Title of the event.
        "start": {  # The (inclusive) start time of the event. For a recurring event, this is the start time of the first instance.
            # "date": "A String",  # The date, in the format "yyyy-mm-dd", if this is an all-day event.
            "dateTime": event.eventDateTime.isoformat(),  # The time, as a combined date-time value (formatted according to RFC3339). A time zone offset is required unless a time zone is explicitly specified in timeZone.
        },
        "source": {
            "url": event.eventUrl
        },
        "location": event.venueInfo.streetAddress,
        "description": event.description,
        "end": {  # The (exclusive) end time of the event. For a recurring event, this is the end time of the first instance.
            "dateTime": (event.eventDateTime + dt.timedelta(hours=3)).isoformat(),  # The time, as a combined date-time value (formatted according to RFC3339). A time zone offset is required unless a time zone is explicitly specified in timeZone.
        },
        "privateCopy": True,
        # "colorId": "A String",  # The color of the event. This is an ID referring to an entry in the event section of the colors definition (see the  colors endpoint). Optional.
        # # "reminders": { # Information about the event's reminders for the authenticated user.
        # #   "overrides": [ # If the event doesn't use the default reminders, this lists the reminders specific to the event, or, if not set, indicates that no reminders are set for this event. The maximum number of override reminders is 5.
        # #     {
        # #       "minutes": 42, # Number of minutes before the start of the event when the reminder should trigger. Valid values are between 0 and 40320 (4 weeks in minutes).
        # #           # Required when adding a reminder.
        # #       "method": "A String", # The method used by this reminder. Possible values are:
        # #           # - "email" - Reminders are sent via email.
        # #           # - "popup" - Reminders are sent via a UI popup.
        # #           # Required when adding a reminder.
        # #     },
        # #   ],
        # #   "useDefault": True or False, # Whether the default reminders of the calendar apply to the event.
        # # },
        "guestsCanSeeOtherGuests": False,  # Whether attendees other than the organizer can see who the event's attendees are. Optional. The default is True.
        "guestsCanInviteOthers": True,  # Whether attendees other than the organizer can invite others to the event. Optional. The default is True.
    }
    print(googleCalendarEvent)
    response = service.events().insert(calendarId=calendar['id'], body=googleCalendarEvent)
    print(response.body)
    calendarEvents = service.events().list(calendarId=calendar['id'])
    print(calendarEvents)

def addCalendarEvents(events, calendar, service):
    for event in events:
        addCalendarEvent(event, calendar, service)


def main():
    options = Options()
    # options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(options=options)
    calendarService = getGoogleCalendarService()
    musicCalendar = getMusicCalendar(calendarService)

    broad_berry_event_urls = []  # get_broadberry_event_urls(driver)
    the_national_event_urls = get_national_event_urls()[:3]
    event_urls = broad_berry_event_urls + the_national_event_urls
    events = [*map(lambda event_url: get_event_details(driver, event_url), event_urls)]
    print([event for event in events])

    print(musicCalendar['id'])

    calendarService.calendars().delete(calendarId=musicCalendar['id'])
    addCalendarEvents(events, musicCalendar, calendarService)


# print(eventURLs)

# details = getBroadBerryEventDetails(driver, 'https://www.etix.com/ticket/p/7898189/girl-god-wwill-sennett-seated-show-richmond-richmond-music-hall?partner_id=240')
# print(details)
# broadBerryEventURLs = broadBerryEventURLs[10:]

# events = [*map(lambda eventUrl: getBroadBerryEventDetails(driver, eventUrl), broadBerryEventURLs)]
# print([event for event in events])

if __name__ == '__main__':
    main()
