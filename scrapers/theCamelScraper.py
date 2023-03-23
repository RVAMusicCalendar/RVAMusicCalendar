import json
from pprint import pprint

from dateutil.parser import parse
from selenium.webdriver.common.by import By

from data.Event import Event
from data.VenueInfo import VenueInfo
from seleniumDriver import get_selenium_driver

theCamelEventsURL = "https://thecamel.org/events/"

theCamelVenueInfo = VenueInfo(venue_name="The Camel", street_address="1621 W. BROAD STREET", city="Richmond", state="Virginia", postal_code=23220)


def get_camel_event_urls(driver):
    driver.get(theCamelEventsURL)
    # progressed_wait(10, title="Giving the Camel website time to appear")
    events = driver.find_elements(By.LINK_TEXT, "More Info")
    event_urls = [*map(lambda event: event.get_attribute("href"), events)]
    return event_urls


def the_camel_details_scraper(driver, event_url):
    try:
        googleInfo = json.loads(driver.find_element(By.XPATH, "//script[@type='application/ld+json']").get_attribute("innerHTML"))
        event_date_time = parse(googleInfo['startDate'])
        event_ticket_url = googleInfo['offers']['url']
        price = googleInfo['offers']['price']
        event_door_open_time = parse(driver.find_element(By.CLASS_NAME, "eventDoorStartDate").text.replace("Doors: ", "").strip()).time()
        event_name = driver.find_element(By.ID, "eventTitle").get_attribute("title")
        event_image_url = driver.find_element(By.XPATH, "//meta[@property='og:image']").get_attribute('content')
        event_description = driver.find_element(By.XPATH, "//meta[@property='og:description']").get_attribute('content')
        event = Event(theCamelVenueInfo, event_date_time, event_door_open_time, event_name, event_image_url, event_description, event_ticket_url, source_url=event_url, price=price, color_id="3")
        return event
    except:
        print(f"Problem extracting for {event_url}")


if __name__ == '__main__':
    selenium_driver = get_selenium_driver()
    # urls = get_camel_event_urls(driver)
    #
    # print(len(urls))
    # print(urls)

    test_event_url = "https://thecamel.org/event/sam-burchfield-the-scoundrels-and-virginia-man/the-camel-2/richmond-virginia/"

    selenium_driver.get(test_event_url)
    test_event = the_camel_details_scraper(selenium_driver, test_event_url)
    pprint(test_event)
