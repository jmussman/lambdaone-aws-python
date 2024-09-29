# test_fixed_key.py
# Copyright © 2024 Joel A. Mussman. All rights reserved.
#

import importlib
import jwt
import logging
from unittest import TestCase
from unittest.mock import mock_open, patch

from lambdaone import fixed_key

class TestFixedKey(TestCase):

    @classmethod
    def setUpClass(cls):

        cls.mock_key = '-----BEGIN PUBLIC KEY-----MIIBIjA...'
        cls.mock_path = "public.pem"
        cls.mock_algorithm = 'RS256'
        cls.mock_token = 'token'
        cls.mock_token_header = { 'alg': 'RS256' }
       
        # "Hoist" the mock of jwt get_unverified_header.

        cls.mod_jwt_get_unverified_header = jwt.get_unverified_header

        cls.mock_jwt_get_unverified_header_context = patch('jwt.get_unverified_header')
        cls.mock_jwt_get_unverified_header_context.start()

        # "Hoist" the mock of logging debug and error. The full description of this pattern is in the test_lambdaone/test_jwt_key.py file.

        cls.mod_logging_debug = logging.debug
        cls.mod_logging_error = logging.error

        cls.mock_logging_debug_context = patch('logging.debug', return_value = None)
        cls.mock_logging_debug_context.start()

        cls.mock_logging_error_context = patch('logging.error', return_value = None)
        cls.mock_logging_error_context.start()

        importlib.reload(fixed_key)

    @classmethod
    def tearDownClass(cls) -> None:

        cls.mock_jwt_get_unverified_header_context.stop()

        jwt.get_unverified_header = cls.mod_jwt_get_unverified_header

        cls.mock_logging_debug_context.stop()
        cls.mock_logging_error_context.stop()

        logging.debug = cls.mock_logging_debug_context
        logging.error = cls.mod_logging_error

        importlib.reload(fixed_key)

        return super().tearDownClass()
    
    def setUp(self):

        TestFixedKey.mock_jwt_get_unverified_header_context.target.get_unverified_header.reset_mock()
        TestFixedKey.mock_jwt_get_unverified_header_context.target.get_unverified_header.return_value = { 'alg': TestFixedKey.mock_algorithm }
        TestFixedKey.mock_jwt_get_unverified_header_context.target.get_unverified_header.side_effect = None

        TestFixedKey.mock_logging_debug_context.target.error.reset_mock()
        TestFixedKey.mock_logging_debug_context.target.error.return_value = None
    
    @patch('builtins.open')
    def test_load_key(self, mock_builtins_open):
    
        mo = mock_open(read_data = TestFixedKey.mock_key)
        mock_builtins_open.side_effect = mo

        result = fixed_key.load(TestFixedKey.mock_path, TestFixedKey.mock_token)

        self.assertEqual(( TestFixedKey.mock_key, TestFixedKey.mock_algorithm ), result)

    @patch('builtins.open')
    def test_None_on_open_error(self, mock_builtins_open):
        
        mock_builtins_open.side_effect = FileNotFoundError

        result = fixed_key.load(TestFixedKey.mock_path, TestFixedKey.mock_token)

        self.assertEqual(( None, None ), result)

    @patch('builtins.open')
    def test_None_on_read_error(self, mock_builtins_open):
                
        mo = mock_open(read_data = TestFixedKey.mock_key)
        mo.side_effect = IOError
        mock_builtins_open.side_effect = mo

        result = fixed_key.load(TestFixedKey.mock_path, TestFixedKey.mock_token)

        self.assertEqual(( None, None), result)

    @patch('builtins.open')
    def test_get_algorithm_with_token(self, mock_builtins_open):

        mo = mock_open(read_data = TestFixedKey.mock_key)
        mock_builtins_open.side_effect = mo
        
        result = fixed_key.load(TestFixedKey.mock_path, TestFixedKey.mock_token)

        TestFixedKey.mock_jwt_get_unverified_header_context.target.get_unverified_header.assert_called_once_with(TestFixedKey.mock_token)

    @patch('builtins.open')
    def test_None_on_get_algorithm_error(self, mock_builtins_open):      

        TestFixedKey.mock_jwt_get_unverified_header_context.target.get_unverified_header.side_effect = Exception
        mo = mock_open(read_data = TestFixedKey.mock_key)
        mock_builtins_open.side_effect = mo
        
        result = fixed_key.load(TestFixedKey.mock_path, TestFixedKey.mock_token)

        self.assertEqual(( None, None ), result)

    @patch('builtins.open')
    def test_logs_error_on_exception(self, mock_builtins_open):      

        TestFixedKey.mock_jwt_get_unverified_header_context.target.get_unverified_header.side_effect = Exception
        mo = mock_open(read_data = TestFixedKey.mock_key)
        mock_builtins_open.side_effect = mo
        
        result = fixed_key.load(TestFixedKey.mock_path, TestFixedKey.mock_token)

        TestFixedKey.mock_logging_error_context.target.error.assert_called_once()

    @patch('builtins.open')
    def test_get_algorithm_no_algorithm(self, mock_builtins_open):

        TestFixedKey.mock_jwt_get_unverified_header_context.target.get_unverified_header.return_value = { }
        mo = mock_open(read_data = TestFixedKey.mock_key)
        mock_builtins_open.side_effect = mo
        
        result = fixed_key.load(TestFixedKey.mock_path, TestFixedKey.mock_token)

        self.assertEqual(( None, None ), result)