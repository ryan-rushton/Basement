from stem import Signal
from stem.control import Controller
import requests
from logging import getLogger
from app import SOCKS_PORT, CONTROL_PORT

logger = getLogger(__name__)


def tor_request(url):
    """
    Make the a http request using the Tor network
    :param url: String
    :return: Response object from the Requests library
    """

    # Fake headers to use in the request, mimics a broser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/52.0.2743.116 Safari/537.36'
    }

    # Open a controller for connection
    with Controller.from_port(port=CONTROL_PORT) as controller:

        controller.authenticate()
        proxies = {
            'http': 'socks5://localhost:' + str(SOCKS_PORT),
            'https': 'socks5://localhost:' + str(SOCKS_PORT)
        }

        # Get a new exit node
        if controller.is_newnym_available():
            controller.signal(Signal.NEWNYM)
            logger.info('Tor circuit changed. Requesting url: %s', url)
        else:
            logger.info('Tor circuit not changed. Requesting url: %s', url)

        # return the Response object
        rtn = requests.get(url, proxies=proxies, headers=headers)
        return rtn

