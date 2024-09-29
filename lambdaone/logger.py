# logger.py
# Copyright © 2024 Joel A Mussman. All rights reserved.
#
# Initialize the logging environment. In this case that means sending the
# logging to stdout, where it will be picked up by the container logging.
#

import logging
from logging import Formatter, getLogger, StreamHandler
import sys

def initialize(log_level):

    logger = getLogger()

    try:

        # Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL; ask of Python 3.2
        # you can pass the numeric value or a string.

        logger.setLevel(log_level)

    except Exception as e:

        log_level = logging.NOTSET

    handler = StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)