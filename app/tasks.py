from app import celery_basement
from app.scrapers.pastebin_task import PastebinScraper
from app import db_worker

@celery_basement.task
def run_pastebin_task():

    scraper = PastebinScraper()
    return None





