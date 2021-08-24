"""Logging system"""

import logging
import sys

LOGGER = logging.getLogger(__name__)


def setup_logger(logging_config):
    """
    Setup configuration
    :param logging_config: logging specific configuration
    :returns: void (creates logging instance)
    """

    log_format = "[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s"
    date_format = "%Y-%m-%dT%H:%M:%SZ"

    loglevels = {
        "CRITICAL": logging.CRITICAL,
        "ERROR": logging.ERROR,
        "WARNING": logging.WARNING,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
        "NOTSET": logging.NOTSET,
    }

    loglevel = loglevels[logging_config["level"]]

    if "logfile" in logging_config:
        logging.basicConfig(
            level=loglevel,
            datefmt=date_format,
            format=log_format,
            filename=logging_config["logfile"],
        )
    else:
        logging.basicConfig(
            level=loglevel, datefmt=date_format, format=log_format, stream=sys.stdout
        )

    LOGGER.debug("Logging initialized")
    return
