import requests
import time
import random
import sys
from datetime import datetime
from logging import getLogger
from bs4 import BeautifulSoup
from app.models import Paste
from app import db_worker
import app
from app.db_worker import DbWorker
from .tor_requests import tor_request

logger = getLogger(__name__)


class PastebinScraper:

    def __init__(self, q, out_q, use_tor=False):
        # Multiprocessing Queues used to pass messages to and from the scraper.
        self.q = q
        self.out_q = out_q

        # old_list is a list of the last 50 processed pastes
        if not self.q.empty():
            self.old_list = self.q.get()

        # Set to True if it is desired to use tor for the scraping
        self.use_tor = use_tor

        # The last http/s response address/code the scraper generated
        self.last_response_address = None
        self.last_response_code = None
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
        logger.info('Request code for %s retrieval: %s', paste_url, paste_page.status_code)
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
                    a_list = tr.find_all('a')
                    for a in a_list:
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

    def check_q(self):
        if not self.q.empty():
            tmp = self.q.get()
            if tmp == 'change_tor':
                self.use_tor = not self.use_tor
            elif tmp == 'request_details':
                self.out_q.put(self.return_details())
        return None

    def return_details(self):
        rtn = {
            'ps_last_response_address': self.last_response_address,
            'ps_last_response_code': self.last_response_code,
            'ps_using_tor': self.use_tor
        }
        return rtn

    def scrape_archive(self):
        """
        This scrapes the pastebin.com/archive page for new pastes and
        saves them to our database.

        :return:
        """
        # This a list of paste objects to process and add to the data base
        try:
            paste_objects = self.get_documents()
        except:
            logger.error('get_documents() function failed')
            paste_objects = []

        # If there are items in paste_objects that are not already processed we add it to the database
        if len(paste_objects) > 0:
            for paste in paste_objects:

                # Try to add to the database
                try:
                    db_worker.q.put(('Add', paste))
                except:
                    logger.error('Unable to put paste in db_worker Queue: %s', paste)
                    if not db_worker.is_alive():
                        db_worker = DbWorker()
                        db_worker.start()

                # Update old_list
                self.old_list.append(paste)
                if len(self.old_list) > 100:
                    self.old_list.pop(0)

        # Put old list in q to ensure we don't try and process old pastes
        self.out_q.put(self.return_details())
        self.q.put(self.old_list)
        logger.info('Scraper stopped')
        return None
