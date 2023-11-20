from alive_progress import alive_bar

from data.model.Event import Event
from scrapers import getTightScraper
from scrapers.broadberryScraper import get_broadberry_event_urls
from scrapers.etixScraper import etix_event_details_scraper
from scrapers.getTightScraper import get_gettight_events
from scrapers.theCamelScraper import get_camel_event_urls, the_camel_details_scraper
from scrapers.theNationalScraper import get_national_event_urls, the_national_details_scraper


def get_event_details(driver, event_url):
    driver.get(event_url)
    scraped_event: Event | None = None
    if "etix" in event_url:
        scraped_event = etix_event_details_scraper(driver, event_url)
    elif "thenationalva" in event_url:
        scraped_event = the_national_details_scraper(driver, event_url)
    elif "thecamel" in event_url:
        scraped_event = the_camel_details_scraper(driver, event_url)
    elif "dice.fm" in event_url:
        scraped_event = getTightScraper.get_event_details(driver, event_url)
    else:
        print(f"ticketProvider not supported yet {event_url}")
    # TODO: log the failure
    return scraped_event


def scrape_events(driver, urls):
    events = []
    with alive_bar(len(urls), dual_line=True, title='Scraping events by URL', force_tty=True) as bar:
        for url in urls:
            bar.text = f'-> currently scraping {url}'
            events.append(get_event_details(driver, url))
            bar()
    return events


def scrape(driver):
    events = []
    broad_berry_event_urls = get_broadberry_event_urls(driver)
    the_national_event_urls = get_national_event_urls()
    the_camel_event_urls = get_camel_event_urls(driver)
    event_urls = broad_berry_event_urls + the_national_event_urls + the_camel_event_urls

    # TODO: Add a check to the db and don't run it if source_url
    events += scrape_events(driver, event_urls)
    get_tight_events = get_gettight_events(driver)
    if len(get_tight_events) > 0:
        print("problem scraping Get Tight Lounge Events")  # TODO: maybe alert or something
        events += get_tight_events

    return events
