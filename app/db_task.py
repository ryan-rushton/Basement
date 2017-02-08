from app.es_search import add_to_es, delete_all_es, delete_from_es, es_delete_by_date
from logging import getLogger

logger = getLogger(__name__)


def database_handler(data):
    """
    The necessary run function for a Process
    :return: None
    """
    # The data tuple is split into a keyword, action, and the datum itself
    action, datum = data

    # Delete everything in the databases
    if action == 'Delete':
        try:
            delete_all_es()
            logger.info('All entries deleted from elasticsearch')
        except:
            logger.error("Failed to delete all entries in both databases")

    # Delete everything older than a given date
    elif action == 'Delete Date':
        es_delete_by_date(datum)

    # Add an entry to the databases
    elif action == 'Add':
        try:
            add_to_es(datum)
            logger.info('ES got %s', datum)
        except:
            logger.error('Could not be added to ES, putting back into Queue: %s', datum)
