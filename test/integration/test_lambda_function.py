# test_lambda_function.py
# Copyright © 2024 Joel A. Mussman. All rights reserved.
#
# These are the integration tests to make sure lambda works end to end. Some components are still mocked:
# jwk_key will not go out for a key from a real IdP, and the environment variables to control the
# execution path chosen by the lambda.
#

from dotenv import load_dotenv
from http.server import HTTPServer, SimpleHTTPRequestHandler
import jwt
import os
import re
import sys
from threading import Thread
import time
import unittest
from unittest import TestCase
from unittest.mock import ANY, MagicMock, patch

import lambda_function

# The class that will be instantiated to handle each HTTP request; this
# inits the SimpleHTTPRequestHandler to look in 'test/resources'.

class JWKSHandler(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        
        super().__init__(*args, directory='test/resources', **kwargs)

class TestLambdaFunction(TestCase):

    @classmethod
    def setUpClass(cls):
        
        # This will be used to launch a web server that provides the JWKS data, in order to
        # satisfy the jwks_client.get_signing_key_from_jwt() method in jwt_key.py.

        def run_jwks_server(server_class = HTTPServer, handler_class = JWKSHandler):

            server_address = ('127.0.0.1', 8000)
            cls.httpd = server_class(server_address, handler_class)
            cls.httpd.serve_forever()

        cls.thread = Thread(target = run_jwks_server)
        cls.thread.start()

        cls.mock_audience = os.environ['AUDIENCE'] = 'https://treasure'
        cls.mock_issuer = os.environ['ISSUER'] = 'https://pyrates'
        cls.mock_jwks_path = os.environ['JWKSPATH'] = ''
        cls.mock_require = os.environ['REQUIRE'] = ''
        cls.mock_signature_key_path = os.environ['SIGNATUREKEYPATH'] = ''

        cls.mock_subject = '1234567890'
        cls.mock_scopeList = 'treasure:read'
        cls.mock_scopes = re.split(r'\s*,\s*', cls.mock_scopeList)

        with open('test/resources/private.pem', 'r') as fp:

            cls.mock_private_key = fp.read()

        with open('test/resources/public.pem', 'r') as fp:

            cls.mock_public_key = fp.read()

        with open('test/resources/private_b.pem', 'r') as fp:       # Test to not match the public key

            cls.mock_private_key_b = fp.read()

        now = time.time()
        expires = now - (60 * 20)

        cls.mock_token_payload = { 'aud': cls.mock_audience, 'iss': cls.mock_issuer, 'sub': cls.mock_subject, 'issuedat': now, 'expiresat': expires, 'scopes': cls.mock_scopes}        
        cls.mock_token = jwt.encode(cls.mock_token_payload, cls.mock_private_key, algorithm = 'RS256', headers = { 'kid': '5b889a22-6e44-45f7-8f5e-537db1d9b16e' })

        load_dotenv()

    def setUp(self):
                
        # The environment variables need to be reset for each test.

        self.mock_audience = os.environ['AUDIENCE'] = TestLambdaFunction.mock_audience
        self.mock_issuer = os.environ['ISSUER'] = TestLambdaFunction.mock_issuer
        self.mock_jwks_path = os.environ['JWKSPATH'] = TestLambdaFunction.mock_jwks_path
        self.mock_require = os.environ['REQUIRE'] = TestLambdaFunction.mock_require
        self.mock_signature_key_path = os.environ['SIGNATUREKEYPATH'] = TestLambdaFunction.mock_signature_key_path

        self.mock_event = { 'headers': { 'authorize': f'bearer { TestLambdaFunction.mock_token }' }}
        self.mock_context = {}

    @classmethod
    def tearDownClass(cls) -> None:

        cls.httpd.shutdown()
        cls.thread.join()
        return super().tearDownClass()

    def test_hello_world_without_authorization(self):

        result = lambda_function.handler(self.mock_event, self.mock_context)

        self.assertIn('Hello, World!', result)

    def test_current_sys_version_without_authorization(self):

        result = lambda_function.handler(self.mock_event, self.mock_context)

        self.assertIn(sys.version, result)

    def test_hello_world_for_fixed_key_correct_authorization(self):

        os.environ['REQUIRE'] = self.mock_scopeList
        os.environ['SIGNATUREKEYPATH'] = 'test/resources/public.pem'

        result = lambda_function.handler(self.mock_event, self.mock_context)

        self.assertDictEqual(TestLambdaFunction.mock_token_payload, result)

    def test_error_for_bad_fixed_key(self):

        os.environ['REQUIRE'] = self.mock_scopeList
        os.environ['SIGNATUREKEYPATH'] = 'test/resources/private.pem'

        result = lambda_function.handler(self.mock_event, self.mock_context)

        self.assertEqual(403, result['statusCode'])

    def test_hello_world_for_jwks_correct_authorization(self):

        os.environ['REQUIRE'] = self.mock_scopeList
        os.environ['JWKSPATH'] = 'http://localhost:8000/jwks.json'

        result = lambda_function.handler(self.mock_event, self.mock_context)

        self.assertDictEqual(TestLambdaFunction.mock_token_payload, result)

    def test_error_for_bad_jwks_key(self):

        os.environ['REQUIRE'] = self.mock_scopeList
        os.environ['JWKSPATH'] = 'http://localhost:8000/jwks.json'

        now = time.time()
        expires = now - (60 * 20)

        mock_token_payload = { 'aud': self.mock_audience, 'iss': self.mock_issuer, 'sub': self.mock_subject, 'issuedat': now, 'expiresat': expires, 'scopes': self.mock_scopes}        
        mock_token = jwt.encode(mock_token_payload, TestLambdaFunction.mock_private_key_b, algorithm = "RS256", headers = { 'kid': '5b889a22-6e44-45f7-8f5e-537db1d9b16e' })
        mock_event = { 'headers': { 'authorize': f'bearer { mock_token }' }}

        result = lambda_function.handler(mock_event, self.mock_context)

        self.assertEqual(403, result['statusCode'])

    def test_error_for_no_matching_jwks_key(self):

        os.environ['REQUIRE'] = self.mock_scopeList
        os.environ['JWKSPATH'] = 'http://localhost:8000/jwks.json'

        now = time.time()
        expires = now - (60 * 20)

        mock_token_payload = { 'aud': self.mock_audience, 'iss': self.mock_issuer, 'sub': self.mock_subject, 'issuedat': now, 'expiresat': expires, 'scopes': self.mock_scopes}        
        mock_token = jwt.encode(mock_token_payload, TestLambdaFunction.mock_private_key, algorithm = "RS256", headers = { 'kid': 'no-kid' })
        mock_event = { 'headers': { 'authorize': f'bearer { mock_token }' }}

        result = lambda_function.handler(mock_event, self.mock_context)

        self.assertEqual(403, result['statusCode'])

    def test_error_for_bad_audience(self):

        os.environ['AUDIENCE'] = 'badAudience'
        os.environ['REQUIRE'] = self.mock_scopeList
        os.environ['SIGNATUREKEYPATH'] = 'test/resources/public.pem'

        result = lambda_function.handler(self.mock_event, self.mock_context)

        self.assertEqual(403, result['statusCode'])

    def test_error_for_bad_issuer(self):

        os.environ['ISSUER'] = 'badIssuer'
        os.environ['REQUIRE'] = self.mock_scopeList
        os.environ['SIGNATUREKEYPATH'] = 'test/resources/public.pem'

        result = lambda_function.handler(self.mock_event, self.mock_context)

        self.assertEqual(403, result['statusCode'])

    def test_error_for_unauthorized_scopes(self):

        os.environ['REQUIRE'] = 'treasure:read, treasure:write'
        os.environ['SIGNATUREKEYPATH'] = 'test/resources/public.pem'

        result = lambda_function.handler(self.mock_event, self.mock_context)

        self.assertEqual(403, result['statusCode'])