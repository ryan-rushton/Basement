import requests
import time
import random
import sys
from datetime import datetime
from logging import getLogger
from bs4 import BeautifulSoup
from app.models import Paste
from .generic_scraper import GenericScraper, ScraperHandle
from .tor_requests import tor_request

logger = getLogger(__name__)


class FacebookScraper(GenericScraper):
    """
    A class to scrape facebook from the html
    """

    def __init__(self, q, out_q, daemon=True, use_tor=False):
        GenericScraper.__init__(self, q, out_q, daemon=daemon, use_tor=use_tor)
        self.address = None

    def get_documents(self):
        pass


class FacebookHandle(ScraperHandle):
    """
    A class used to start and stop instances of the scraper
    """
    def __init__(self):
        ScraperHandle.__init__(self)
        logger.info('FacebookHandle initialised')

    def start(self):
        """
        Start function for the scraper
        :return:
        """
        self.scraper = FacebookScraper(self.q, self.out_q, use_tor=self.use_tor)
        logger.info('Starting FacebookScraper')
        self.gen_start()


if __name__ == '__main__':
    scraper = FacebookHandle()
    scraper.start()
