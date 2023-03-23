from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def get_selenium_driver(headless=True):
    options = Options()
    # options.add_experimental_option("detach", True)
    options.add_argument("--window-size=1920,1080")

    options.add_argument("--headless") if headless else None
    options.add_argument("--disable-infobars")
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=options)
    return driver
