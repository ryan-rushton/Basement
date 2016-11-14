import logging


def setup_custom_logger(name):
    """
    Custom logger for the application, self explanatory
    :param name: String
    :return: Logger object
    """
    w_logger = logging.getLogger('werkzeug')
    w_logger.setLevel(logging.ERROR)

    fmt = '[%(asctime)s][%(levelname)s][%(module)s][%(threadName)s][%(message)s]'
    formatter = logging.Formatter(fmt=fmt)

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return logger
