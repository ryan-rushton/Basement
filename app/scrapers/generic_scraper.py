import time
from multiprocessing import Process, Queue
from abc import ABCMeta, abstractmethod
from app import db_worker
from logging import getLogger

logger = getLogger(__name__)


class GenericScraper(Process):
    """
    This Class forms a scraper from the multiprocessing.Process class.
    It uses q (= multiprocessing.Queue) to pass information back to the parent process.
    It scrapes pastebin.com/archives for the latest pastes input, pastebin blocks your
    IP if you scrape too fast so time.sleep() needs to be used to mitigate this.
    """

    __metaclass__ = ABCMeta

    def __init__(self, q, out_q, daemon=True, use_tor=False):
        """
        :param q: multiprocessing.Queue - Used to pass messages in and out of the process.
        """
        Process.__init__(self)

        # Make the process a daemon so as to ensure if closes when the app closes
        self.daemon = daemon

        # Multiprocessing Queues used to pass messages to and from the scraper.
        self.q = q
        self.out_q = out_q

        # old_list is a list of the last 50 processed pastes
        if not self.q.empty():
            self.old_list = self.q.get()

        # Used to keep the while loop running, changed to false through q when asked to stop
        self.running = True

        # No idea why I included this
        # self.domain_module = None

        # Set to True if it is desired to use tor for the scraping
        self.use_tor = use_tor

        # The last http/s response address/code the scraper generated
        self.last_response_address = None
        self.last_response_code = None

    @abstractmethod
    def get_documents(self):
        """
        To be overridden.
        :return:
        """
        pass

    def get_documents_list(self, wait_addr=2):
        """
        This scrapes the pastebin.com/archive page for new pastes and
        saves them to our database.

        :return:
        """
        while self.running:
            # final_wait is a incremented counter for a delay
            final_wait = 2

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

                    # Increment final_wait to try and offset the scraping restrictions
                    final_wait += wait_addr

                    # Update old_list
                    self.old_list.append(paste)
                    if len(self.old_list) > 100:
                        self.old_list.pop(0)

                    # Look for 'Stop' in q, if found we stop the process
                    if not self.q.empty():
                        if self.q.get() == 'Stop':
                            logger.info('Stopping scraper')
                            self.running = False
                            final_wait = 0
                            break

            # Look for 'Stop' in q, if found we stop the process
            self.check_q()
            if self.running:
                time.sleep(final_wait)

        # Put old list in q to ensure we don't try and process old pastes
        self.out_q.put(self.return_details())
        self.q.put(self.old_list)
        logger.info('Scraper stopped')
        return None

    def run(self):
        self.get_documents_list()

    def check_q(self):
        if not self.q.empty():
            tmp = self.q.get()
            if tmp == 'Stop':
                self.running = False
            elif tmp == 'change_tor':
                self.use_tor = not self.use_tor
            elif tmp == 'request_details':
                self.out_q.put(self.return_details())
        return None

    def return_details(self):
        rtn = {
            'ps_is_alive': self.running,
            'ps_last_response_address': self.last_response_address,
            'ps_last_response_code': self.last_response_code,
            'ps_using_tor': self.use_tor
        }
        return rtn


class ScraperHandle:
    """
    A handler for starting and stopping PastebinScraper
    """

    def __init__(self):
        self.q = Queue()
        self.out_q = Queue()
        self.processed = []
        self.q.put(self.processed)
        self.action = 'Start'
        self.scraper = None
        self.use_tor = False

    def gen_start(self):
        self.scraper.start()
        self.action = 'Stop'

    def stop(self):
        # Put 'Stop' in q to stop the scraper
        self.q.put(self.action)
        self.action = 'Start'
        logger.info('Sending stop message to scraper')
