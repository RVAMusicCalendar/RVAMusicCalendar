import time

from alive_progress import alive_bar
from selenium.webdriver.common.by import By

broadBerryURL = "https://thebroadberry.com/events/?view=month"


def progressed_wait(wait_time, title=""):
    with alive_bar(wait_time, force_tty=True, monitor=False, stats=False, title=title) as bar:
        for i in range(wait_time):
            time.sleep(1)
            bar()


def get_broadberry_event_urls(driver):
    driver.get(broadBerryURL)
    progressed_wait(10, title="Giving the Broadberry website time to appear")
    events = driver.find_elements(By.LINK_TEXT, "BUY TICKETS")
    event_urls = [*map(lambda event: event.get_attribute("href"), events)]
    return event_urls
