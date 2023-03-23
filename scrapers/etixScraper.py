from dateutil.parser import parse
from selenium.webdriver.common.by import By

from data.Event import Event
from data.VenueInfo import VenueInfo


def etix_event_details_scraper(driver, event_url):
    try:
        performance_info = driver.find_element(By.CLASS_NAME, "performance-info")
        event_image_url = performance_info.find_element(By.CLASS_NAME, "performance-image").find_element(By.TAG_NAME, "img").get_attribute("src")
        location_info_element = performance_info.find_element(By.CLASS_NAME, "location")
        venue_name = location_info_element.find_element(By.XPATH, "//span[@itemprop='name']").text
        address_info_element = performance_info.find_element(By.XPATH, "//span[@itemprop='address']")
        street_address = address_info_element.find_element(By.XPATH, "//meta[@itemprop='streetAddress']").get_attribute("content")
        city = address_info_element.find_element(By.XPATH, "//meta[@itemprop='addressLocality']").get_attribute("content")
        state = address_info_element.find_element(By.XPATH, "//meta[@itemprop='addressRegion']").get_attribute("content")
        postal_code = address_info_element.find_element(By.XPATH, "//meta[@itemprop='postalCode']").get_attribute("content")
        event_name = performance_info.find_element(By.XPATH, "//h1[@itemprop='name']").text
        event_date_time = parse(performance_info.find_element(By.XPATH, "//meta[@itemprop='startDate']").get_attribute('content'))
        event_door_open_time = parse(performance_info.find_element(By.CLASS_NAME, "time").text.split("\n")[-1].replace("Doors Open:", "").strip()).time()
        event_description = performance_info.find_element(By.XPATH, "//div[@itemprop='description']").get_attribute("innerHTML")  # .text
        return Event(VenueInfo(venue_name, street_address, city, state, postal_code), event_date_time, event_door_open_time, event_name, event_image_url, event_description,
                     event_url, color_id="1")
    except:
        print(f"Problem extracting for {event_url}")
