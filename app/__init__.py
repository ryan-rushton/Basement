from flask import Flask
from subprocess import Popen
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from elasticsearch import Elasticsearch
from stem.process import launch_tor_with_config
import config

# Ports to be used with tor and tors path
CONTROL_PORT = 9051
SOCKS_PORT = 9050
TOR_PATH = '/usr/local/bin/tor'
tor_enabled = False

elasticsearch_path = '/usr/local/bin/elasticsearch'

app = Flask(__name__)
app.config.from_object('config')
meta = MetaData()
db = SQLAlchemy(app, metadata=meta)
meta.bind = db.engine
meta.create_all()

if config.start_app:
    # Start a elasticsearch subprocess
    Popen(elasticsearch_path)

    # Default connection to elasticsearch at localhost:9200
    es = Elasticsearch()

    if tor_enabled:
        # Setup a printer so tor can indicate its startup status in the terminal
        def bootstrap_printer(line):
            if 'Bootstrapped' in line:
                print('Tor:', line)

        # Launch the tor process
        tor_process = launch_tor_with_config(
            tor_cmd=TOR_PATH,
            config={'ControlPort': str(CONTROL_PORT),
                    'SocksPort': str(SOCKS_PORT)},
            take_ownership=True,
            init_msg_handler=bootstrap_printer)

# These imports have to be placed later to stop circular imports

from app.custom_logger import setup_custom_logger

logger = setup_custom_logger(__name__)
logger.info('Logger has been setup')

from app import models

if config.start_app:
    from app.db_worker import DbWorker

    db_worker = DbWorker()
    logger.info('DbWorker initialised')

    from app.scrapers.pastebin_scraper import PastebinHandle

    pastebin_handle = PastebinHandle()
    logger.info('PastebinHandle initialised')

    from app import views

    # Start a database worker subprocess
    db_worker.start()
