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
       
        # "Hoist" the mock of logging error. The full description of this pattern is in the test_lambdaone/test_jwt_key.py file.

        cls.mod_logging_error = logging.error

        cls.mock_logging_error = patch('logging.error', return_value = None)
        cls.mock_logging_error.start()

        importlib.reload(authz)

    @classmethod
    def tearDownClass(cls) -> None:

        cls.mock_logging_error.stop()

        logging.error = cls.mod_logging_error

        importlib.reload(authz)

        return super().tearDownClass()

    @patch('jwt.decode')
    def test_accepts_valid_token(self, mock_jwt_decode):

        mock_jwt_decode.return_value = TestAuthZ.mock_token_payload
        self.addCleanup(mock_jwt_decode.stop)

        result = authz.verify(TestAuthZ.mock_token, TestAuthZ.mock_key, TestAuthZ.mock_algorithm, TestAuthZ.mock_audience, TestAuthZ.mock_issuer, [ 'treasure:read' ])

        self.assertIsNotNone(result)

    @patch('jwt.decode', side_effect = jwt.exceptions.ExpiredSignatureError)
    def test_rejects_expired_token(self, mock_jwt_decode):

        result = authz.verify(TestAuthZ.mock_token, TestAuthZ.mock_key, TestAuthZ.mock_algorithm, TestAuthZ.mock_audience, TestAuthZ.mock_issuer, [ 'treasure:read' ])
        
        self.assertIsNone(result)

    @patch('jwt.decode', side_effect = jwt.exceptions.InvalidAudienceError)
    def test_rejects_unexpected_audience(self, mock_jwt_decode):

        result = authz.verify(TestAuthZ.mock_token, TestAuthZ.mock_key, TestAuthZ.mock_algorithm, TestAuthZ.mock_audience, TestAuthZ.mock_issuer, [ 'treasure:read' ])
        
        self.assertIsNone(result)

    @patch('jwt.decode', side_effect = jwt.exceptions.InvalidIssuerError)
    def test_rejects_unexpected_issuer(self, mock_jwt_decode):

        result = authz.verify(TestAuthZ.mock_token, TestAuthZ.mock_key, TestAuthZ.mock_algorithm, TestAuthZ.mock_audience, TestAuthZ.mock_issuer, [ 'treasure:read' ])
        
        self.assertIsNone(result)

    @patch('jwt.decode')
    def test_rejects_missing_scope(self, mock_jwt_decode):

        mock_jwt_decode.return_value = TestAuthZ.mock_token_payload

        result = authz.verify(TestAuthZ.mock_token, TestAuthZ.mock_key, TestAuthZ.mock_algorithm, TestAuthZ.mock_audience, TestAuthZ.mock_issuer, [ 'treasure:write' ])

        self.assertIsNone(result)