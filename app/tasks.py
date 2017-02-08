from app import celery_basement
from app.scrapers.pastebin_task import PastebinScraper
from multiprocessing import Queue


# Set up queues for use with the scrapers and database tasks
database_input_queue = Queue()
database_output_queue = Queue()
pastebin_input_queue = Queue()
pastebin_output_queue = Queue()


@celery_basement.task
def run_pastebin_task():

    scraper = PastebinScraper()
    return None





