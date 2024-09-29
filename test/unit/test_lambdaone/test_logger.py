# test_logger.py
# Copyright © 2024 Joel A. Mussman. All rights reserved.
#

import importlib
import jwt
import logging
import sys
import time
from unittest import TestCase
from unittest.mock import MagicMock, patch

from lambdaone import logger

class TestLogger(TestCase):

    @classmethod
    def setUpClass(cls):

        # Hoist the class and functions logger will import from logging.

        cls.mod_Formatter = logging.Formatter
        cls.mod_getLogger = logging.getLogger
        cls.mod_StreamHandler = logging.StreamHandler

        cls.mock_Formatter = MagicMock()
        cls.mock_getLogger = MagicMock()
        cls.mock_StreamHandler = MagicMock()

        cls.mock_Formatter_context = patch('logging.Formatter')
        cls.mock_Formatter_context.start()

        cls.mock_getLogger_context = patch('logging.getLogger')
        cls.mock_getLogger_context.start()

        cls.mock_StreamHandler_context = patch('logging.StreamHandler')
        cls.mock_StreamHandler_context.start()

        importlib.reload(logger)

    @classmethod
    def tearDownClass(cls) -> None:

        cls.mock_StreamHandler_context.stop()
        cls.mock_getLogger_context.stop()
        cls.mock_Formatter_context.stop()

        logging.Formatter = cls.mod_Formatter
        logging.getLogger = cls.mod_getLogger
        logging.StreamHandler = cls.mod_StreamHandler

        importlib.reload(logger)

        return super().tearDownClass()
    
    def setUp(self):

        TestLogger.mock_Formatter_context.target.Formatter.reset_mock()
        TestLogger.mock_Formatter_context.target.Formatter.return_value = TestLogger.mock_Formatter

        TestLogger.mock_getLogger_context.target.getLogger.reset_mock()
        TestLogger.mock_getLogger_context.target.getLogger.return_value = TestLogger.mock_getLogger
        TestLogger.mock_getLogger.setLevel.side_effect = None

        TestLogger.mock_StreamHandler_context.target.StreamHandler.reset_mock()
        TestLogger.mock_StreamHandler_context.target.StreamHandler.return_value = TestLogger.mock_StreamHandler

    def test_getLogger(self):

        logger.initialize(logging.DEBUG)

        TestLogger.mock_getLogger_context.target.getLogger.assert_called_once()

    def test_logger_setLevel(self):

        logger.initialize(logging.DEBUG)

        TestLogger.mock_getLogger.setLevel.assert_called_once_with(logging.DEBUG)

    def test_instantiates_StreamHandler(self):

        logger.initialize(logging.DEBUG)

        TestLogger.mock_StreamHandler_context.target.StreamHandler.assert_called_once_with(sys.stdout)

    def test_stream_handler_setLevel(self):

        logger.initialize(logging.DEBUG)

        TestLogger.mock_StreamHandler.setLevel.assert_called_once_with(logging.DEBUG)

    def test_instantiates_Formatter(self):

        logger.initialize(logging.DEBUG)

        TestLogger.mock_Formatter_context.target.Formatter.assert_called_once()

    def test_stream_handler_setFormatter(self):

        logger.initialize(logging.DEBUG)

        TestLogger.mock_StreamHandler.setFormatter.assert_called_once_with(TestLogger.mock_Formatter)

    def test_logger_addHandler(self):

        logger.initialize(logging.DEBUG)

        TestLogger.mock_getLogger.addHandler.assert_called_once_with(TestLogger.mock_StreamHandler)

    def test_fallback_to_DEBUG_on_bad_level(self):

        TestLogger.mock_getLogger.setLevel.side_effect = ValueError
        logger.initialize('BADLEVEL')

        TestLogger.mock_StreamHandler.setLevel.assert_called_once_with(logging.NOTSET)