# test_jwt_key.py
# Copyright © 2024 Joel A. Mussman. All rights reserved.
#

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

mock_client = MagicMock()

mock_jwt_jwks_client_PyJWKClient_context = patch('jwt.jwks_client.PyJWKClient', return_value = mock_client)
mock_jwt_jwks_client_PyJWKClient_context.start()

mock_jwt_PyJWKClient_context = patch('jwt.PyJWKClient', return_value = mock_client)
mock_jwt_PyJWKClient_context.start()

from lambdaone import jwt_key

class TestJwtKey(TestCase):

    @classmethod
    def setUpClass(cls):

        # This stuff should only be done once, and the setUpClass method is the better choice
        # instead of doing it outside the TestCase.

        cls.mock_key = '-----BEGIN PUBLIC KEY-----'
        cls.mock_path = 'https://pyrates/jwks'
        cls.mock_token = 'token'

    def setUp(self):

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

    def test_load_key(self):

        result = jwt_key.load(TestJwtKey.mock_path, TestJwtKey.mock_token)

        self.assertEqual(TestJwtKey.mock_key, result)

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

    def test_request_with_token(self):

        result = jwt_key.load(TestJwtKey.mock_path, TestJwtKey.mock_token)

        mock_client.get_signing_key_from_jwt.assert_called_once_with(TestJwtKey.mock_token)

    def test_None_on_read_error(self):

        mock_client.get_signing_key_from_jwt.side_effect = Exception

        result = jwt_key.load(TestJwtKey.mock_path, TestJwtKey.mock_token)

        self.assertEqual(None, result)

    # This is a test we would like to have, but impossible to implement given the circumstances.
    # The side_effect in the mocks becomes a list iterator, so reassigning it is a no-op. And
    # because the CUT may not be able to see us change a mock (the "from jwt import PyJWKClient"
    # problem) there just isn't any way to force the exception to happen.

    def test_None_on_open_error(self):

        mock_jwt_PyJWKClient_context.target.PyJWKClient.side_effect = Exception
        mock_jwt_jwks_client_PyJWKClient_context.target.PyJWKClient.side_effect = Exception

        result = jwt_key.load(TestJwtKey.mock_path, TestJwtKey.mock_token)

        self.assertEqual(None, result)    # This is what we are looking for.
        # self.assertEqual(TestJwtKey.mock_key, result)  # This is what we get.

if __name__ == '__main__':
    unittest.main()