# test_fixed_key.py
# Copyright © 2024 Joel A. Mussman. All rights reserved.
#

import unittest
from unittest import TestCase
from unittest.mock import mock_open, patch

from lambdaone import fixed_key

class TestFixedKey(TestCase):

    @classmethod
    def setUpClass(cls):

        cls.mock_key = '-----BEGIN PUBLIC KEY-----MIIBIjA...'
        cls.mock_path = "public.pem"

    @patch('builtins.open')
    def test_load_key(self, mock_builtins_open):
    
        mo = mock_open(read_data = TestFixedKey.mock_key)
        mock_builtins_open.side_effect = mo

        result = fixed_key.load(TestFixedKey.mock_path)

        self.assertEqual(TestFixedKey.mock_key, result)

    @patch('builtins.open')
    def test_None_on_open_error(self, mock_builtins_open):
        
        mock_builtins_open.side_effect = FileNotFoundError

        result = fixed_key.load(TestFixedKey.mock_path)

        self.assertIsNone(result)

    @patch('builtins.open')
    def test_None_on_read_error(self, mock_builtins_open):
                
        mo = mock_open(read_data = TestFixedKey.mock_key)
        mo.side_effect = IOError
        mock_builtins_open.side_effect = mo

        result = fixed_key.load(TestFixedKey.mock_path)

        self.assertIsNone(result)

if __name__ == '__main__':

    unittest.main()