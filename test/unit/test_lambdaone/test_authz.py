# test_authz.py
# Copyright © 2024 Joel A. Mussman. All rights reserved.
#

import importlib
import jwt
import logging
import time
from unittest import TestCase
from unittest.mock import patch

from lambdaone import authz

class TestAuthZ(TestCase):

    @classmethod
    def setUpClass(cls):

        now = time.time()
        expires = now - (60 * 20)

        cls.mock_audience = 'https://treasure',
        cls.mock_issuer = 'https://pyrates'
        cls.mock_jwks_path = 'https://pyrates/jwks'
        cls.mock_key = '-----BEGIN PRIVATE KEY-----MIIEvgIB...'
        cls.mock_token = 'token'
        cls.mock_token_payload = { 'aud': 'myaudience', 'issuer': 'someissuer', 'sub': '1234567890', 'issuedat': now, 'expiresat': expires, 'scopes': [ 'treasure:read' ]}        
        cls.mock_algorithm = 'RS256'
       
        # "Hoist" the mock of logging debug and error. The full description of this pattern is in the test_lambdaone/test_jwt_key.py file.

        cls.mod_jwt_decode = jwt.decode

        cls.mock_jwt_decode_context = patch('jwt.decode')
        cls.mock_jwt_decode_context.start()

        cls.mod_logging_debug = logging.debug
        cls.mod_logging_error = logging.error

        cls.mock_logging_debug_context = patch('logging.debug', return_value = None)
        cls.mock_logging_debug_context.start()

        cls.mock_logging_error_context = patch('logging.error', return_value = None)
        cls.mock_logging_error_context.start()

        importlib.reload(authz)

    @classmethod
    def tearDownClass(cls) -> None:

        cls.mock_jwt_decode_context.stop()

        jwt.decode = cls.mod_jwt_decode

        cls.mock_logging_debug_context.stop()
        cls.mock_logging_error_context.stop()

        logging.debug = cls.mod_logging_debug
        logging.error = cls.mod_logging_error

        importlib.reload(authz)

        return super().tearDownClass()
    
    def setUp(self):

        TestAuthZ.mock_logging_error_context.target.error.reset_mock()
        TestAuthZ.mock_logging_error_context.target.error.return_value = None
        TestAuthZ.mock_logging_error_context.target.error.side_effect = None

    def test_accepts_valid_token(self):

        TestAuthZ.mock_jwt_decode_context.target.decode.return_value = TestAuthZ.mock_token_payload

        result = authz.verify(TestAuthZ.mock_token, TestAuthZ.mock_key, TestAuthZ.mock_algorithm, TestAuthZ.mock_audience, TestAuthZ.mock_issuer, [ 'treasure:read' ])

        self.assertIsNotNone(result)

    def test_rejects_expired_token(self):

        TestAuthZ.mock_jwt_decode_context.target.decode.side_effect = jwt.exceptions.ExpiredSignatureError

        result = authz.verify(TestAuthZ.mock_token, TestAuthZ.mock_key, TestAuthZ.mock_algorithm, TestAuthZ.mock_audience, TestAuthZ.mock_issuer, [ 'treasure:read' ])
        
        self.assertIsNone(result)

    def test_rejects_unexpected_audience(self):

        TestAuthZ.mock_jwt_decode_context.target.decode.side_effect = jwt.exceptions.InvalidAudienceError

        result = authz.verify(TestAuthZ.mock_token, TestAuthZ.mock_key, TestAuthZ.mock_algorithm, TestAuthZ.mock_audience, TestAuthZ.mock_issuer, [ 'treasure:read' ])
        
        self.assertIsNone(result)

    def test_rejects_unexpected_issuer(self):

        TestAuthZ.mock_jwt_decode_context.target.decode.side_effect = jwt.exceptions.InvalidIssuerError

        result = authz.verify(TestAuthZ.mock_token, TestAuthZ.mock_key, TestAuthZ.mock_algorithm, TestAuthZ.mock_audience, TestAuthZ.mock_issuer, [ 'treasure:read' ])
        
        self.assertIsNone(result)

    @patch('jwt.decode')
    def test_rejects_missing_scope(self, mock_jwt_decode):

        TestAuthZ.mock_jwt_decode_context.target.decode.sreturn_value = TestAuthZ.mock_token_payload

        result = authz.verify(TestAuthZ.mock_token, TestAuthZ.mock_key, TestAuthZ.mock_algorithm, TestAuthZ.mock_audience, TestAuthZ.mock_issuer, [ 'treasure:write' ])

        self.assertIsNone(result)

    def test_logs_error_on_exception(self):

        TestAuthZ.mock_jwt_decode_context.target.decode.side_effect = ValueError

        result = authz.verify(TestAuthZ.mock_token, TestAuthZ.mock_key, TestAuthZ.mock_algorithm, TestAuthZ.mock_audience, TestAuthZ.mock_issuer, [ 'treasure:write' ])

        TestAuthZ.mock_logging_error_context.target.error.assert_called_once()