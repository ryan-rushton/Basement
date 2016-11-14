import requests
import time
import sys
from sqlite3 import IntegrityError
from datetime import datetime
from multiprocessing import Process, Queue
from bs4 import BeautifulSoup
from app.models import Paste
from app import db_worker


def depreciated_get_paste(paste_tup):
    """
    This takes a tuple consisting of href from a paste link and a name that identify a pastebin paste.
    It scrapes the page for the pastes content.

    :param paste_tup: (string, string)
    :return: Paste if successful or False
    """
    href, name = paste_tup

    # Form the url from the href and perform GET request
    paste_url = 'http://pastebin.com' + href
    paste_page = requests.get(paste_url)

    # Collect the paste details from paste page
    if paste_page.status_code == 200:
        text = paste_page.text
        soup = BeautifulSoup(text, 'html.parser')
        # soup.textarea.get_text() return the paste content
        paste = Paste(url="http://www.pastebin.com"+href, name=name, content=soup.textarea.get_text(), datetime=datetime.now())
        return paste

    # Return False if the scrape failed
    return False


class DepreciatedPastebinScraper(Process):
    """
    This Class forms a scraper from the multiprocessing.Process class.
    It uses q (= multiprocessing.Queue) to pass information back to the parent process.
    It scrapes pastebin.com/archives for the latest pastes input, pastebin blocks your
    IP if you scrape too fast so time.sleep() needs to be used to mitigate this.
    """

    def __init__(self, q):
        """
        :param q: multiprocessing.Queue - Used to pass function in and out of the process.
        """
        Process.__init__(self)
        self.daemon = True
        self.q = q
        # old_list is a list of the last 50 processed pastes
        tmp = self.q.get()
        if tmp != 'Stop':
            self.old_list = tmp
        # Used to keep the while loop running, changed to false through q when asked to stop
        self.running = True

    def get_paste_list(self):
        """
        This scrapes the pastebin.com/archive page for new pastes and
        saves them to our database.

        :return: None
        """
        while self.running:
            # final_wait is a incremented counter for a delay
            final_wait = 4
            paste_links = []
            # Get the pastebin.com/archive page
            public_pastes = "http://pastebin.com/archive"
            public_page = requests.get(public_pastes)

            # Scrape the archive page
            if public_page.status_code == 200:

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
                        if 'archive' not in a.get('href'):
                            paste_links.append((a.get('href'), a.get_text()))

            # If there are items in paste_links that are not already processed we scrape
            # the associated link page, create a Paste object and add it to the database
            if len(paste_links) > 0:
                for paste in paste_links:
                    if paste not in self.old_list:
                        paste_obj = depreciated_get_paste(paste)

                        # Try to add to the database
                        try:
                            db_worker.q.put(paste_obj)
                        except IntegrityError:
                            print("Couldn't save" + str(paste_obj) + "to database")
                        except:
                            print("Unexpected error:", sys.exc_info()[0])

                        # Increment final_wait to try and offset the scraping restrictions
                        final_wait += 1
                        time.sleep(3)

                        # Update old_list
                        self.old_list.append(paste)
                        if len(self.old_list) > 50:
                            self.old_list.pop(0)

                    # Look for 'Stop' in q, if found we stop the process
                    if not self.q.empty():
                        if self.q.get() == 'Stop':
                            self.running = False
                            final_wait = 0
                            break

            time.sleep(final_wait)

            # Look for 'Stop' in q, if found we stop the process
            if not self.q.empty():
                if self.q.get() == 'Stop':
                    self.running = False

        # Put old list in q to ensure we don't try and process old pastes
        self.q.put(self.old_list)
        return None

    def run(self):
        self.get_paste_list()


class DepreciatedPastebinHandle:
    """
    A handler for starting and stopping PastebinScraper
    """
    def __init__(self):
        self.q = Queue()
        self.processed = []
        self.q.put(self.processed)
        print("New pastebin handle created")
        self.action = 'Start'
        self.scraper = None

    def start(self):
        print(self.q)
        if self.scraper is not None:
            self.scraper.terminate()
        self.scraper = DepreciatedPastebinScraper(self.q)
        print("Pastebin scraper starting")
        self.scraper.start()
        print("Pastebin scraper started")
        self.action = 'Stop'

    def stop(self):
        # Put 'Stop' in q to stop the scraper
        print("Pastebin scraper stopping")
        self.q.put(self.action)
        print("Pastebin scraper stopped")
        self.action = 'Start'



