# logger.py
# Copyright © 2024 Joel A Mussman. All rights reserved.
#
# Initialize the logging environment. In this case that means sending the
# logging to stdout, where it will be picked up by the container logging.
#

from dotenv import load_dotenv
from logging import error, Formatter, getLogger, StreamHandler
import os
import sys

load_dotenv()

# Log levels: DEBUG, INFO, WARNING, ERROR

log_level = os.environ.get('LAMBDA_LOG_LEVEL', 'ERROR')
logger = getLogger()
logger.setLevel(log_level)

handler = StreamHandler(sys.stdout)
handler.setLevel(log_level)

formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)

error(f'log level {log_level}')