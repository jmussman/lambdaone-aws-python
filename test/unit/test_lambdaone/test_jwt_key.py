# test_jwt_key.py
# Copyright © 2024 Joel A. Mussman. All rights reserved.
#

import importlib
import jwt
import logging
from unittest import TestCase
from unittest.mock import MagicMock, patch

from lambdaone import jwt_key

class TestJwtKey(TestCase):

    @classmethod
    def setUpClass(cls):

        # This stuff should only be done once, and the setUpClass method is the better choice
        # instead of doing it outside the TestCase.

        cls.mock_key = '-----BEGIN PUBLIC KEY-----'
        cls.mock_path = 'https://pyrates/jwks'
        cls.mock_token = 'token'

        # The PyJWKClient class original is in the jwt.jwks_client module, but it is also referenced as a property in the
        # jwt module. Mocking the class is not a serious problem if the code under test (CUT) references it as either
        # jwt.PyJWKClient or jwt.jwks_client.PyJWKClient. In that case, simply mock both references and have the
        # class return an object instance we can control (in this test the method get_signing_key_from_jwt must be mocked).
        #
        # The problem arises if the CUT uses "from jwt import PyJWKClient" or "from jwt.jwks_client import PyJWKClient".
        # When that happens the class reference is copied into jwk_key module as a property. That opens up a third
        # possible mock: look for the property in the jwt_key module and mock it!
        #  
        # The third mocking possibility, and worrying about the import/call form the CUT is using, can be handled by
        # mocking the first two possibilities and then reloading the jwt_key module so it picks up the new reference.
        # In this case, the original reference is saved to replace and reload both jwt_key and jwk after completion.

        cls.mod_jwt_jwks_client_PyJWKClient = jwt.jwks_client.PyJWKClient

        cls.mock_client = MagicMock()

        cls.mock_jwt_jwks_client_PyJWKClient_context = patch('jwt.jwks_client.PyJWKClient', return_value = cls.mock_client)
        cls.mock_jwt_jwks_client_PyJWKClient_context.start()

        cls.mock_jwt_PyJWKClient_context = patch('jwt.PyJWKClient', return_value = cls.mock_client)
        cls.mock_jwt_PyJWKClient_context.start()

        # "Hoist" the mock of logging error.

        cls.mod_logging_error = logging.error

        cls.mock_logging_error = patch('logging.error', return_value = None)
        cls.mock_logging_error.start()

        # If you are familar with jest or vitest in JavaScript, this call forces the mocks to be "hosited" in front of
        # the jwt_key module import. It is a reload but it is the same thing:

        importlib.reload(jwt_key)

    @classmethod
    def tearDownClass(cls) -> None:

        cls.mock_jwt_jwks_client_PyJWKClient_context.stop()
        cls.mock_jwt_PyJWKClient_context.stop()

        # As describe above, the original class must be inserted back into the jwt module and
        # then both modules reloaded for other test fixtures:

        jwt.PyJWKClient = jwt.jwks_client.PyJWKClient = cls.mod_jwt_jwks_client_PyJWKClient

        # Put back the logging error.

        cls.mock_logging_error.stop()

        logging.error = cls.mod_logging_error

        importlib.reload(jwt)
        importlib.reload(jwt_key)

        return super().tearDownClass()

    def setUp(self):

        self.mock_algorithm = 'RS256'

        # The "instantiated" object created by PyJWKClient must be reset
        # and the return_value and side_effect reinitalized after each test,
        # because changes could be made in any test.

        TestJwtKey.mock_client.reset_mock()
        TestJwtKey.mock_client.get_signing_key_from_jwt.return_value = TestJwtKey.mock_key
        TestJwtKey.mock_client.get_signing_key_from_jwt.side_effect = None

        # The two Class mocks for PyJWKClient must be reset and the return_value
        # and side_effect reinitialized after each test.

        TestJwtKey.mock_jwt_jwks_client_PyJWKClient_context.target.PyJWKClient.reset_mock()
        TestJwtKey.mock_jwt_jwks_client_PyJWKClient_context.target.PyJWKClient.return_value = TestJwtKey.mock_client
        TestJwtKey.mock_jwt_jwks_client_PyJWKClient_context.target.PyJWKClient.side_effect = None

        TestJwtKey.mock_jwt_PyJWKClient_context.target.PyJWKClient.reset_mock()
        TestJwtKey.mock_jwt_PyJWKClient_context.target.PyJWKClient.return_value = TestJwtKey.mock_client
        TestJwtKey.mock_jwt_PyJWKClient_context.target.PyJWKClient.side_effect = None

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

        if TestJwtKey.mock_jwt_jwks_client_PyJWKClient_context.target.PyJWKClient.call_count > 0:

            TestJwtKey.mock_jwt_jwks_client_PyJWKClient_context.target.PyJWKClient.assert_called_once_with(TestJwtKey.mock_path)

        elif TestJwtKey.mock_jwt_PyJWKClient_context.target.PyJWKClient.call_count > 0:
            
            TestJwtKey.mock_jwt_PyJWKClient_context.target.PyJWKClient.assert_called_once_with(TestJwtKey.mock_path)

        else:

            self.assertTrue(False)

    def test_get_signing_key_with_token(self):

        result = jwt_key.load(TestJwtKey.mock_path, TestJwtKey.mock_token)

        TestJwtKey.mock_client.get_signing_key_from_jwt.assert_called_once_with(TestJwtKey.mock_token)

    def test_get_algorithm_with_token(self):
        
        result = jwt_key.load(TestJwtKey.mock_path, TestJwtKey.mock_token)

        self.mock_jwt_get_unverified_header_context.target.get_unverified_header.assert_called_once_with(TestJwtKey.mock_token)

    def test_None_on_read_error(self):

        TestJwtKey.mock_client.get_signing_key_from_jwt.side_effect = Exception

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

        TestJwtKey.mock_jwt_PyJWKClient_context.target.PyJWKClient.side_effect = Exception
        TestJwtKey.mock_jwt_jwks_client_PyJWKClient_context.target.PyJWKClient.side_effect = Exception

        result = jwt_key.load(TestJwtKey.mock_path, TestJwtKey.mock_token)

        # self.assertEqual(( None, None ), result)    # This is what we are looking for.  
        self.assertEqual(( None, None ), result)  # This is what we get.