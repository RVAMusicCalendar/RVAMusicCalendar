import json
import time
from pprint import pprint

import requests
from dateutil.parser import parse
from selenium.webdriver.common.by import By

from data.Event import Event
from data.VenueInfo import VenueInfo
from seleniumDriver import get_selenium_driver

getTightEventsURL = "https://www.gettightrva.com/events"

getTightVenueInfo = VenueInfo(venue_name="Get Tight Lounge", street_address="1104 W Main St", city="Richmond", state="Virginia", postal_code=23220)


def handle_popup(driver):
    popups = driver.find_elements(By.CLASS_NAME, "sqs-slide-layer")
    pprint(popups)
    if len(popups):
        driver.find_element(By.CLASS_NAME, "sqs-popup-overlay-close").click()


def get_event_urls(driver):
    try:
        driver.get(getTightEventsURL)
        time.sleep(5)
        handle_popup(driver)
        driver.find_element(By.CLASS_NAME, "dice_load-more").click()
        time.sleep(5)
        events = driver.find_elements(By.CLASS_NAME, "dice_event-title")
        event_urls = [*map(lambda event: event.get_attribute("href"), events)]
        return event_urls
    except:
        print("Problem occured while scraping The Get Tight Lounge event urls")
        return []


# noinspection PyTypeChecker
def get_event_details(driver, event_url):
    try:
        dice_artist_id = driver.find_element(By.XPATH, "//meta[@property='product:retailer_item_id']").get_attribute("content")
        response = json.loads(requests.get(url=f'https://api.dice.fm/events/{dice_artist_id}').content)
        event_date_time = parse(response['date'])
        event_ticket_url = event_url
        price = driver.find_element(By.XPATH, "//div[contains(@class, 'EventDetailsCallToAction__Price')]/span").text.replace("$", "")
        event_door_open_time = parse(response['summary_lineup']['doors_open']).time()
        event_name = response['name']
        event_image_url = response['background_image']
        event_description = driver.find_element(By.XPATH, "//div[contains(@class, 'EventDetailsAbout__Text')]").get_attribute("innerHTML")
        event = Event(getTightVenueInfo, event_date_time, event_door_open_time, event_name, event_image_url, event_description, event_ticket_url, source_url=event_url, price=price, color_id="4")
        return event
    except:
        print(f"Problem extracting for {event_url}")


if __name__ == '__main__':
    # selenium_driver = get_selenium_driver(False, True)
    selenium_driver = get_selenium_driver(False)
    # urls = get_event_urls(selenium_driver)
    # print(len(urls))
    # print(urls)

    test_event_url = "https://link.dice.fm/i22ef77bf801?pid=8984aee2"

    selenium_driver.get(test_event_url)
    test_event = get_event_details(selenium_driver, test_event_url)
    pprint(test_event)
