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


class PastebinScraper(GenericScraper):

    def __init__(self, q, out_q, daemon=True, use_tor=False):
        GenericScraper.__init__(self, q, out_q, daemon=daemon, use_tor=use_tor)
        self.address = "http://pastebin.com"

    def get_paste(self, href, name):
        """
        Get the individual paste from its associated page.
        :param href: String
        :param name: String
        :return: Paste object if successful False otherwise
        """

        # Form the url from the href and perform GET request
        paste_url = self.address + href
        if self.use_tor:
            logger.info('Attempting to use Tor to get paste: %s', paste_url)
            paste_page = tor_request(paste_url)
        else:
            paste_page = requests.get(paste_url)
        self.last_response_address = paste_url
        self.last_response_code = paste_page.status_code

        # Collect the paste details from paste page
        logger.info('Request code for %s retrieval: %s', paste_url,paste_page.status_code)
        if paste_page.status_code == 200:
            text = paste_page.text
            soup = BeautifulSoup(text, 'html.parser')
            paste = Paste(url="http://www.pastebin.com"+href, name=name, content=soup.textarea.get_text(),
                          datetime=datetime.now())
            logger.info('Returning paste: %s', paste)
            return paste

        # Return False if the scrape failed
        logger.warning('Failed to scrape paste: %s', paste_url)
        return False

    def get_documents(self):
        """
        This scrapes the pastebin.com/archive page for new pastes and
        saves them to our database.

        :return: None
        """
        paste_links = []
        # Get the pastebin.com/archive page
        archive_url = self.address + "/archive"
        if self.use_tor:
            public_page = tor_request(archive_url)
            logger.info('Using Tor to get paste: %s', archive_url)
        else:
            public_page = requests.get(archive_url)
        self.last_response_address = archive_url
        self.last_response_code = public_page.status_code

        # Scrape the archive page
        logger.info('Request code for %s retrieval: %s', archive_url, public_page.status_code)
        if public_page.status_code == 200:

            try:
                # Turn the page text into a tree to be parsed
                text = public_page.text
                soup = BeautifulSoup(text, 'html.parser')

                # Navigate the tree to the table of paste links
                monster_frame = soup.find_all(id='monster_frame')
                content_frame = monster_frame[0].find_all(id='content_frame')
                content_left = content_frame[0].find_all(id='content_left')
                table = content_left[0].find_all('table')

                # Collect the href's and names of the links in paste_links
                tr_list = table[0].find_all('tr')
                for tr in tr_list:
                    if not self.running:
                        break
                    a_list = tr.find_all('a')
                    for a in a_list:
                        if not self.running:
                            break
                        href = a.get('href')
                        if 'archive' not in href and not any(href in x.url for x in self.old_list):
                            paste = self.get_paste(href, a.get_text())
                            time.sleep(random.randrange(40, 50, 1) / 10.0)
                            if paste is not False:
                                paste_links.append(paste)
                        self.check_q()
                    self.check_q()

            except:
                self.check_q()
                error_sleep = 120
                logger.error("Unable to scrape page: %s, %s", archive_url, sys.exc_info())
                logger.info('Scraper sleeping for %s seconds', error_sleep)
                time.sleep(error_sleep)

        return paste_links


class PastebinHandle(ScraperHandle):
    """
    A class used to start and stop instances of the scraper
    """
    def __init__(self):
        ScraperHandle.__init__(self)
        logger.info('PastebinHandle initialised')

    def start(self):
        """
        Start function for the scraper
        :return:
        """
        self.scraper = PastebinScraper(self.q, self.out_q, use_tor=self.use_tor)
        logger.info('Starting PastebinScraper')
        self.gen_start()
