# test_fixed_key.py
# Copyright © 2024 Joel A. Mussman. All rights reserved.
#

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

    @patch('builtins.open')
    @patch('jwt.get_unverified_header')
    def test_load_key(self, mock_jwt_get_unverified_header, mock_builtins_open):
    
        mock_jwt_get_unverified_header.return_value = { 'alg': TestFixedKey.mock_algorithm }
        mo = mock_open(read_data = TestFixedKey.mock_key)
        mock_builtins_open.side_effect = mo

        result = fixed_key.load(TestFixedKey.mock_path, TestFixedKey.mock_token)

        self.assertEqual(( TestFixedKey.mock_key, TestFixedKey.mock_algorithm ), result)

    @patch('builtins.open')
    @patch('jwt.get_unverified_header')
    def test_None_on_open_error(self, mock_jwt_get_unverified_header, mock_builtins_open):
        
        mock_jwt_get_unverified_header.return_value = { 'alg': TestFixedKey.mock_algorithm }
        mock_builtins_open.side_effect = FileNotFoundError

        result = fixed_key.load(TestFixedKey.mock_path, TestFixedKey.mock_token)

        self.assertEqual(( None, None ), result)

    @patch('builtins.open')
    @patch('jwt.get_unverified_header')
    def test_None_on_read_error(self, mock_jwt_get_unverified_header, mock_builtins_open):
                
        mock_jwt_get_unverified_header.return_value = { 'alg': TestFixedKey.mock_algorithm }
        mo = mock_open(read_data = TestFixedKey.mock_key)
        mo.side_effect = IOError
        mock_builtins_open.side_effect = mo

        result = fixed_key.load(TestFixedKey.mock_path, TestFixedKey.mock_token)

        self.assertEqual(( None, None), result)

    @patch('builtins.open')
    @patch('jwt.get_unverified_header')
    def test_get_algorithm_with_token(self, mock_jwt_get_unverified_header, mock_builtins_open):

        mock_jwt_get_unverified_header.return_value = { 'alg': TestFixedKey.mock_algorithm }
        mo = mock_open(read_data = TestFixedKey.mock_key)
        mock_builtins_open.side_effect = mo
        
        result = fixed_key.load(TestFixedKey.mock_path, TestFixedKey.mock_token)

        mock_jwt_get_unverified_header.assert_called_once_with(TestFixedKey.mock_token)

    @patch('builtins.open')
    @patch('jwt.get_unverified_header')
    def test_None_on_get_algorithm_error(self, mock_jwt_get_unverified_header, mock_builtins_open):      

        mock_jwt_get_unverified_header.side_effect = Exception
        mo = mock_open(read_data = TestFixedKey.mock_key)
        mock_builtins_open.side_effect = mo
        
        result = fixed_key.load(TestFixedKey.mock_path, TestFixedKey.mock_token)

        self.assertEqual(( None, None ), result)

    @patch('builtins.open')
    @patch('jwt.get_unverified_header')
    def test_get_algorithm_no_algorithm(self, mock_jwt_get_unverified_header, mock_builtins_open):

        mock_jwt_get_unverified_header.return_value = { 'xyz': TestFixedKey.mock_algorithm }
        mo = mock_open(read_data = TestFixedKey.mock_key)
        mock_builtins_open.side_effect = mo
        
        result = fixed_key.load(TestFixedKey.mock_path, TestFixedKey.mock_token)

        self.assertEqual(( None, None ), result)