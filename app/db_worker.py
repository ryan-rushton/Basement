from multiprocessing import Process, Queue
from app.es_search import add_to_es, delete_all_es, reindex_es, delete_from_es
from logging import getLogger
from flask_sqlalchemy import SQLAlchemy
import sys
from app import app
from .models import Paste

logger = getLogger(__name__)


def delete_by_date_paste(date):
    """
    Deletes the paste entries older than a certain date. Note that it will delete any document/index type entered into
    it  for elasticsearch, the paste restriction is due to postgreql
    :return: True once
    """
    # Create a connection to the database (seemd to want it in this case)
    db = SQLAlchemy(app)

    # Add the start of the day to ensure anything older gets deleted
    date += " 00:00:00.000000"

    # Make the query to get the pastes to be deleted
    old_pastes = db.session.query(Paste).filter(Paste.datetime < date)

    # Attempt to delete old pastes
    for item in old_pastes:
        try:
            delete_from_es(item)
            db.session.delete(item)
            db.session.commit()
        except:
            logger.error("Did not delete item from one or more databases: %s", item)

    return True


class DbDrone(Process):
    """
    A Process subclass to handle database transactions
    """
    def __init__(self, data, ready_q):
        """
        A subprocess to handle single database transactions
        :param data: (String, Model)
        :param ready_q: Queue to tell DB worker when it can start a new process
        """
        Process.__init__(self)
        # Set to daemon to ensure it closes when app closes
        self.daemon = True
        self.ready_q = ready_q
        self.data = data

    def run(self):
        """
        The necessary run function for a Process
        :return: None
        """
        db = SQLAlchemy(app)
        # The data tuple is split into a keyword, action, and the datum itself
        action, datum = self.data

        # Delete everything in the databases
        if action == 'Delete':
            try:
                num = db.session.query(Paste).delete()
                db.session.commit()
                delete_all_es()
                logger.info('%s entries deleted from db', num)
            except:
                db.session.rollback()
                logger.error("Failed to delete all entries in both databases")

        # Reindex elasticsearch using entries in th postgresql database
        elif action == 'Reindex ES':
            reindex_es()

        # Delete everything older than a given date
        elif action == 'Delete Date':
            delete_by_date_paste(datum)

        # Add an entry to the databases
        elif action == 'Add':
            in_db = False

            # Try to add to postgresql databse
            try:
                db.session.add(datum)
                db.session.commit()
                in_db = True
                logger.info('DB got %s', datum)
            except:
                db.session.rollback()
                logger.error('Could not be added to DB: %s , %s', datum, sys.exc_info())

            # If previous add successful add to elasticsearch
            if in_db:
                try:
                    add_to_es(datum)
                    logger.info('ES got %s', datum)
                except:
                    logger.error('Could not be added to ES, putting back into Queue: %s', datum)

        # Add true to the queue so that the next process can be started
        self.ready_q.put(True)


class DbWorker(Process):
    """
    A persistent Process subclass that listens for inputs and passes them to the DbDrone to handle
    """

    def __init__(self):
        Process.__init__(self)
        # A multiprocessing Queue to pass messages
        self.q = Queue()
        self.child_q = Queue()
        self.next = None
        self.ready = True

    def run(self):
        logger.info('A DbWorker has started')
        while True:
            if self.next is None:
                self.next = self.q.get()
            if self.next is not None and not self.ready:
                self.ready = self.child_q.get()
            if self.next is not None and self.ready:
                tmp = self.next
                self.next = None
                self.ready = False
                DbDrone(tmp, self.child_q).start()
