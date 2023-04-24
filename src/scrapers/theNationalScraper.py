import datetime as dt

import feedparser
from dateutil.parser import parse
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By

from data.Event import Event
from data.VenueInfo import VenueInfo

theNationalRSSFeedURL = "https://www.thenationalva.com/events/rss"
theNationalVenueInfo = VenueInfo(venue_name="The National", street_address="708 E. Broad Street", city="Richmond", state="Virginia", postal_code=23219)


def get_national_event_urls():
    event_feed = feedparser.parse(theNationalRSSFeedURL)
    return [entry.link for entry in event_feed.entries]


def the_national_details_scraper(driver, event_url):
    try:
        event_detail_container = driver.find_element(By.CLASS_NAME, "event_detail")
        event_date = parse(event_detail_container.find_element(By.CLASS_NAME, "left_column").find_element(By.CLASS_NAME, "date").text.replace("DATE", "")).date()
        event_time = parse(driver.find_element(By.CLASS_NAME, "left_column").find_element(By.CLASS_NAME, "text-large").text.replace("TIME", "")).time()
        event_date_time = dt.datetime.combine(event_date, event_time)
        event_door_open_time = parse(
            event_detail_container.find_element(By.CLASS_NAME, "doors").find_elements(By.TAG_NAME, "label")[1].text).time()  # The first one will just have the text "Doors"
        event_name = event_detail_container.find_element(By.CLASS_NAME, "page_header_left").find_element(By.TAG_NAME, "h1").text
        event_image_url = event_detail_container.find_element(By.CLASS_NAME, "event_image").find_element(By.TAG_NAME, "img").get_attribute("src")
        event_description = ""
        try:
            event_description = event_detail_container.find_element(By.CLASS_NAME, "bio").find_element(By.CLASS_NAME, "collapse-wrapper").text
        except:
            print(f"no bio available for this event {event_name}, {event_url}")
        event = Event(theNationalVenueInfo, event_date_time, event_door_open_time, event_name, event_image_url, event_description, event_url, color_id="2")
        return event
    except NoSuchElementException as e:
        print(f"Problem extracting for {event_url}, {e}")
    except:
        print(f"Problem extracting for {event_url}")
