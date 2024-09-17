# test_lambda_function.py
# Copyright © 2024 Joel A. Mussman. All rights reserved.
#
# These are the integration tests to make sure lambda works end to end. Some components are still mocked:
# jwk_key will not go out for a key from a real IdP, and the environment variables to control the
# execution path chosen by the lambda.
#

from dotenv import load_dotenv
import os
import sys
import time
import unittest
from unittest import TestCase
from unittest.mock import ANY, MagicMock, patch

import lambda_function

class TestLambdaFunction(TestCase):

    @classmethod
    def setUpClass(cls):

        now = time.time()
        expires = now - (60 * 20)

        cls.mock_token = 'eyJhbGci...'
        cls.mock_token_payload = { 'aud': 'myaudience', 'issuer': 'someissuer', 'sub': '1234567890', 'issuedat': now, 'expiresat': expires, 'scopes': [ 'treasure:read' ]}        
        cls.mock_event = { 'headers': { 'authorize': f'bearer {cls.mock_token}' }}
        cls.mock_context = {}
        cls.mock_key = '-----BEGIN PUBLIC KEY-----MIIBIjAN...'

        load_dotenv()

    def setUp(self):

        self.mock_audience = os.environ['AUDIENCE'] = 'https://treasure'
        self.mock_issuer = os.environ['ISSUER'] = 'https://pyrates'
        self.mock_jwks_path = os.environ['JWKSPATH'] = 'https://pyrates/jwks'
        self.mock_require = os.environ['REQUIRE'] = ''
        self.mock_signature_key_path = os.environ['SIGNATUREKEYPATH'] = ''

        self.mock_hello_world_hello = patch('lambdaone.hello_world.hello', return_value='Hello, Mock!')
        self.mock_hello_world_hello.start()
        self.addCleanup(self.mock_hello_world_hello.stop)

        self.mock_sys_version = patch('sys.version', 'version_mock')
        self.mock_sys_version.start()
        self.addCleanup(self.mock_sys_version.stop)

        self.mock_lambdaone_jwt_key_load_context = patch('lambdaone.jwt_key.load', return_value = TestLambdaFunction.mock_key)
        self.mock_lambdaone_jwt_key_load_context.start()
        self.addCleanup(self.mock_lambdaone_jwt_key_load_context.stop)

        self.mock_lambdaone_authz_verify_context = patch('lambdaone.authz.verify', return_value = TestLambdaFunction.mock_token_payload)
        self.mock_lambdaone_authz_verify_context.start()
        self.addCleanup(self.mock_lambdaone_authz_verify_context.stop)

    def test_hello_world_without_authorization(self):

        result = lambda_function.handler(None, None)

        self.assertIn('Hello, World!', result)

    def test_current_sys_version_without_authorization(self):

        result = lambda_function.handler(None, None)

        self.assertIn(sys.version, result)

    def test_hello_world_for_correct_authorization(self):

        os.environ['REQUIRE'] = 'treasure:read'
        self.mock_lambdaone_authz_verify_context.target.verify.return_value = None

        result = lambda_function.handler(self.mock_event, self.mock_context)

        self.assertEqual(403, result['statusCode'])

    def test_error_for_bad_key(self):
        pass

    def test_error_for_bad_audience(self):
        pass

    def test_error_for_bad_issuer(self):
        pass

    def test_error_for_unauthorized_scopes(self):
        pass

if __name__ == '__main__':
    
    unittest.main()