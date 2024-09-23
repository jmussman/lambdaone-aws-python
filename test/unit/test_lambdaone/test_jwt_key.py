# test_jwt_key.py
# Copyright © 2024 Joel A. Mussman. All rights reserved.
#


import importlib
import sys
import unittest
from unittest import TestCase
from unittest.mock import MagicMock, patch

# Get the patches set up and started for the two instances of the PyJWKClient class: the original is in the
# jwt.jwks_client module, and the second is imported (and exported) from the jwt module. The original is
# most likely not used, unless the code under test goes there. But the patch is set up anyways, just in case.
# Much more likely is pulling it from the jwt module. In that case if jwt.PyJWKClient is used in the code,
# any normal patch on the test class or the test methods will work. But... if the CUT invokes
# "from jwt import PyJWKClient", that must happen AFTER the patches have been established or the module
# will see the real class. This hoists the mocks above the import of the CUT:

from lambdaone import jwt_key

mock_client = MagicMock()

mock_jwt_jwks_client_PyJWKClient_context = patch('jwt.jwks_client.PyJWKClient', return_value = mock_client)
mock_jwt_jwks_client_PyJWKClient_context.start()

mock_jwt_PyJWKClient_context = patch('jwt.PyJWKClient', return_value = mock_client)
mock_jwt_PyJWKClient_context.start()

importlib.reload(jwt_key)

class TestJwtKey(TestCase):

    @classmethod
    def setUpClass(cls):

        # This stuff should only be done once, and the setUpClass method is the better choice
        # instead of doing it outside the TestCase.

        cls.mock_key = '-----BEGIN PUBLIC KEY-----'
        cls.mock_path = 'https://pyrates/jwks'
        cls.mock_token = 'token'

    @classmethod
    def tearDownClass(cls) -> None:

        mock_jwt_jwks_client_PyJWKClient_context.stop()
        mock_jwt_PyJWKClient_context.stop()

        importlib.reload(jwt_key)

        return super().tearDownClass()

    def setUp(self):

        self.mock_algorithm = 'RS256'

        # The "instantiated" object created by PyJWKClient must be reset
        # and the return_value and side_effect reinitalized after each test,
        # because changes could be made in any test.

        mock_client.reset_mock()
        mock_client.get_signing_key_from_jwt.return_value = TestJwtKey.mock_key
        mock_client.get_signing_key_from_jwt.side_effect = None

        # The two Class mocks for PyJWKClient must be reset and the return_value
        # and side_effect reinitialized after each test.

        mock_jwt_jwks_client_PyJWKClient_context.target.PyJWKClient.reset_mock()
        mock_jwt_jwks_client_PyJWKClient_context.target.PyJWKClient.return_value = mock_client
        mock_jwt_jwks_client_PyJWKClient_context.target.PyJWKClient.side_effect = None

        mock_jwt_PyJWKClient_context.target.PyJWKClient.reset_mock()
        mock_jwt_PyJWKClient_context.target.PyJWKClient.return_value = mock_client
        mock_jwt_PyJWKClient_context.target.PyJWKClient.side_effect = None

        # Mock jwt.get_unverified_header; this is a fixed function so it will be OK here.

        self.mock_jwt_get_unverified_header_context = patch('jwt.get_unverified_header')
        self.mock_jwt_get_unverified_header_context.start()
        self.mock_jwt_get_unverified_header_context.target.get_unverified_header.return_value = { 'alg': self.mock_algorithm }
        self.mock_jwt_get_unverified_header_context.target.get_unverified_header.side_effect = None
        self.addCleanup(self.mock_jwt_get_unverified_header_context.stop)

    def test_load_key(self):

        result = jwt_key.load(TestJwtKey.mock_path, TestJwtKey.mock_token)

        self.assertEqual(( TestJwtKey.mock_key, self.mock_algorithm), result)

    def test_client_initialized_with_path(self):

        result = jwt_key.load(TestJwtKey.mock_path, TestJwtKey.mock_token)

        # This is a tricky example: one of two different Class definitions could be used, the one
        # in jwt (more likely) or the one in jwt.jwks_client where it originates. Both must be
        # checked to make sure at least one was called with the correct argument.

        if mock_jwt_jwks_client_PyJWKClient_context.target.PyJWKClient.call_count > 0:

            mock_jwt_jwks_client_PyJWKClient_context.target.PyJWKClient.assert_called_once_with(TestJwtKey.mock_path)

        elif mock_jwt_PyJWKClient_context.target.PyJWKClient.call_count > 0:
            
            mock_jwt_PyJWKClient_context.target.PyJWKClient.assert_called_once_with(TestJwtKey.mock_path)

        else:

            self.assertTrue(False)

    def test_get_signing_key_with_token(self):

        result = jwt_key.load(TestJwtKey.mock_path, TestJwtKey.mock_token)

        mock_client.get_signing_key_from_jwt.assert_called_once_with(TestJwtKey.mock_token)

    def test_get_algorithm_with_token(self):
        
        result = jwt_key.load(TestJwtKey.mock_path, TestJwtKey.mock_token)

        self.mock_jwt_get_unverified_header_context.target.get_unverified_header.assert_called_once_with(TestJwtKey.mock_token)

    def test_None_on_read_error(self):

        mock_client.get_signing_key_from_jwt.side_effect = Exception

        result = jwt_key.load(TestJwtKey.mock_path, TestJwtKey.mock_token)

        self.assertEqual(( None, None ), result)

    def test_None_on_get_algorithm_error(self):
        
        self.mock_jwt_get_unverified_header_context.target.get_unverified_header.side_effect = Exception

        result = jwt_key.load(TestJwtKey.mock_path, TestJwtKey.mock_token)

        self.assertEqual(( None, None ), result)

    def test_None_on_get_algorithm_no_algorithm(self):
        
        self.mock_jwt_get_unverified_header_context.target.get_unverified_header.return_value = { 'xyz': self.mock_algorithm }

        result = jwt_key.load(TestJwtKey.mock_path, TestJwtKey.mock_token)

        self.assertEqual(( None, None ), result)

    # This is a test we would like to have, but impossible to implement given the circumstances.
    # The side_effect in the mocks becomes a list iterator, so reassigning it is a no-op. And
    # because the CUT may not be able to see us change a mock (the "from jwt import PyJWKClient"
    # problem) there just isn't any way to force the exception to happen.

    def test_None_on_open_error(self):

        mock_jwt_PyJWKClient_context.target.PyJWKClient.side_effect = Exception
        mock_jwt_jwks_client_PyJWKClient_context.target.PyJWKClient.side_effect = Exception

        result = jwt_key.load(TestJwtKey.mock_path, TestJwtKey.mock_token)

        # self.assertEqual(( None, None ), result)    # This is what we are looking for.  
        self.assertEqual(( None, None ), result)  # This is what we get.