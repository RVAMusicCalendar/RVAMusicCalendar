import os
import time
from datetime import datetime

from gcsa.event import Event
from jinja2 import Environment, select_autoescape, FileSystemLoader
from selenium.webdriver.common.by import By

from seleniumDriver import get_selenium_screenshot_driver

OUTPUT_FOLDER = "generatedImages/"


env = Environment(
    # loader=PackageLoader("main"),
    loader=FileSystemLoader(["src/templates/", "/app/templates/"]),
    autoescape=select_autoescape()
)

template = env.get_template("image.jinja")


def render_html_for_day(date: datetime.date, events: list[Event]):
    return template.render(events=events, date=date)


def generate_image_for_day(date: datetime.date, events: list[Event]):
    events.sort(key=lambda x: x.start)  # sort the list so it displays chronologically
    for event in events:
        print(event.start.strftime("%-I:%M"))

    html = render_html_for_day(date, events)
    # Use extendedProperties.private to store data for reuse a bit better, so we don't have to parse again.
    # output_file = f'{OUTPUT_FOLDER}{date.strftime("%m-%d-%Y")}.jpg'
    html_file = f'{OUTPUT_FOLDER}{date.strftime("%m-%d-%Y")}.html'
    with open(html_file, "w") as f:
        f.write(html)
    get_image_from_selenium(date)
    # imgkit.from_string(html, output_file)


def get_image_from_selenium(date: datetime.date):
    driver = get_selenium_screenshot_driver()
    cwd = os.getcwd()
    localHtmlPath = "file://{}/{}{}.html".format(cwd, OUTPUT_FOLDER, date.strftime("%m-%d-%Y"))
    print(localHtmlPath)
    # time.sleep(10)
    driver.get(localHtmlPath)
    driver.save_screenshot(OUTPUT_FOLDER+date.strftime("%m-%d-%Y")+".png")
