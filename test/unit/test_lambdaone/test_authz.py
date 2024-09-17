# test_authz.py
# Copyright © 2024 Joel A. Mussman. All rights reserved.
#

from cryptography.hazmat.primitives import serialization
import jwt
import time
import unittest
from unittest import TestCase
from unittest.mock import patch, PropertyMock

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

    @patch('jwt.decode')
    def test_accepts_valid_token(self, mock_jwt_decode):

        mock_jwt_decode.return_value = TestAuthZ.mock_token_payload
        self.addCleanup(mock_jwt_decode.stop)

        result = authz.verify(TestAuthZ.mock_token, TestAuthZ.mock_key, TestAuthZ.mock_audience, TestAuthZ.mock_issuer, [ 'treasure:read' ])

        self.assertIsNotNone(result)

    @patch('jwt.decode', side_effect = jwt.exceptions.ExpiredSignatureError)
    def test_rejects_expired_token(self, mock_jwt_decode):

        result = authz.verify(TestAuthZ.mock_token, TestAuthZ.mock_key, TestAuthZ.mock_audience, TestAuthZ.mock_issuer, [ 'treasure:read' ])
        
        self.assertIsNone(result)

    @patch('jwt.decode', side_effect = jwt.exceptions.InvalidAudienceError)
    def test_rejects_unexpected_audience(self, mock_jwt_decode):

        result = authz.verify(TestAuthZ.mock_token, TestAuthZ.mock_key, TestAuthZ.mock_audience, TestAuthZ.mock_issuer, [ 'treasure:read' ])
        
        self.assertIsNone(result)

    @patch('jwt.decode', side_effect = jwt.exceptions.InvalidIssuerError)
    def test_rejects_unexpected_issuer(self, mock_jwt_decode):

        result = authz.verify(TestAuthZ.mock_token, TestAuthZ.mock_key, TestAuthZ.mock_audience, TestAuthZ.mock_issuer, [ 'treasure:read' ])
        
        self.assertIsNone(result)

    @patch('jwt.decode')
    def test_rejects_missing_scope(self, mock_jwt_decode):

        mock_jwt_decode.return_value = TestAuthZ.mock_token_payload

        result = authz.verify(TestAuthZ.mock_token, TestAuthZ.mock_key, TestAuthZ.mock_audience, TestAuthZ.mock_issuer, [ 'treasure:write' ])

        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()