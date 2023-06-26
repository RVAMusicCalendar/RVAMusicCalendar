import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

SELENIUM_HOST = "http://selenium:4444/wd/hub" if os.environ['ENV'] == "DEV" else "http://localhost:4444/wd/hub"


def get_selenium_driver(headless=True, detach=False):
    options = Options()
    options.add_experimental_option("detach", True) if detach else None
    options.add_argument('--no-sandbox')
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--headless=new") if headless else None
    options.add_argument("--disable-infobars")
    options.add_argument('--disable-gpu')
    options.add_argument("--disable-dev-shm-usage")  # otherwise it uses memory and we would need to add more shared mem.
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    return driver


def get_selenium_screenshot_driver(headless=True, detach=False):
    options = Options()
    options.add_experimental_option("detach", True) if detach else None
    options.add_argument('--no-sandbox')
    options.add_argument("--headless=new") if headless else None
    options.add_argument("--window-size=1080,1080")
    options.add_argument("--disable-infobars")
    options.add_argument('--disable-gpu')
    options.add_argument('--hide-scrollbars')
    options.add_argument("--disable-dev-shm-usage")  # otherwise it uses memory and we would need to add more shared mem.
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    return driver


def get_selenium_options(headless=True, detach=False):
    options = Options()
    options.add_experimental_option("detach", True) if detach else None
    options.add_argument('--no-sandbox')
    options.add_argument("--headless=new") if headless else None
    options.add_argument("--window-size=1080,1080")
    options.add_argument("--disable-infobars")
    options.add_argument('--disable-gpu')
    options.add_argument('--hide-scrollbars')
    # options.add_argument("--disable-dev-shm-usage")  # otherwise it uses memory and we would need to add more shared mem.
    options.add_argument("--start-maximized")
    return options


def get_selenium_driver(headless=True, detach=False):
    options = get_selenium_options(headless, detach)
    driver = webdriver.Remote(
        command_executor=SELENIUM_HOST,
        options=options
    )
    return driver
