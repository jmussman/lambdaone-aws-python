# logger.py
# Copyright © 2024 Joel A Mussman. All rights reserved.
#

from logging import basicConfig, Formatter, getLogger, StreamHandler
import os
import sys

# Log levels: DEBUG, INFO, WARNING, ERROR

log_level = os.environ.get('LAMBDA_LOG_LEVEL', 'DEBUG')
logger = getLogger()
logger.setLevel(log_level)

handler = StreamHandler(sys.stdout)
handler.setLevel(log_level)

formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)

# If this is DOCKER but not AWS Lambda, route logging to a file. If AWS, logging is controlled by AWS.
# If neither, logging is not configured so goes to STDERR.

# if os.environ.get('DOCKER') is not None:

#     basicConfig(filename = '/var/log/lambda.log',
#                 encoding = 'utf-8',
#                 filemode = 'a',
#                 format = '{asctime} - {levelname} - {message}',
#                 style = '{',
#                 datefmt = '%Y-%m-%d %H:%M')