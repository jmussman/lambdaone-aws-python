# test_lambda_function.py.disable
# Copyright © 2024 Joel A. Mussman. All rights reserved.
#
# This Docker-based acceptance test is disabled by default, since DOcker may not be available. To enable
# and include the test strip ".disabled" off the file name. Docker is available in the Codespace
# container.
#
# This acceptance test checks both the authorization using a mock access token against the application
# deployed to the Docker container, and the application in the container running without authorization
# enabled.
#

from dotenv import load_dotenv
from http.server import HTTPServer, SimpleHTTPRequestHandler
import jwt
import os
import re
import subprocess
import sys
from threading import Thread
import time
from unittest import TestCase

import lambda_function

class TestLambdaFunction(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.mock_audience = 'https://treasure'
        cls.mock_issuer = 'https://pyrates'
        cls.mock_jwks_path = ''
        cls.mock_require = ''
        cls.mock_signature_key_path = ''

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

    def setUp(self):
                
        # The environment variables need to be reset for each test.

        self.mock_audience = os.environ['AUDIENCE'] = TestLambdaFunction.mock_audience
        self.mock_issuer = os.environ['ISSUER'] = TestLambdaFunction.mock_issuer
        self.mock_jwks_path = os.environ['JWKSPATH'] = TestLambdaFunction.mock_jwks_path
        self.mock_require = os.environ['REQUIRE'] = TestLambdaFunction.mock_require
        self.mock_signature_key_path = os.environ['SIGNATUREKEYPATH'] = TestLambdaFunction.mock_signature_key_path

        self.mock_event = { 'headers': { 'authorize': f'bearer { TestLambdaFunction.mock_token }' }}
        self.mock_context = {}

    def tearDown(self):

        # Look for the image and container ids, and tear them down in reverse order.

        completed_process = subprocess.run('docker ps')
        if completed_process.stdout is not None and completed_process.stdout.find('Cannot connect') < 0:

            image = None
            container = None

            image_lines = completed_process.stdout.splitlines()

            for line in image_lines:

                if line.find('lambdaone') >= 0:

                    pass

            if image is not None:

                pass

            if container is not None and image is not None:

                os.system('kill containier')
                os.system('destroy container')
                os.system('destroy image')

    def test_hello_world_without_authorization(self):

        os.system('docker build -f test/acceptance/Dockerfile.noauthz --platform linux/amd64 -t lambdaone-image:test .')
        os.system('docker run --platform linux/amd64 -p 9000:8080 lambdaone-image:test')
        # curl -w "\n" "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{}'

        result = lambda_function.handler(self.mock_event, self.mock_context)

        self.assertIn('Hello, World!', result)

    def test_hello_world_with_authorization(self):

        result = lambda_function.handler(self.mock_event, self.mock_context)

        self.assertIn('Hello, World!', result)

    def test_hello_world_with_incorrect_authorization(self):

        result = lambda_function.handler(self.mock_event, self.mock_context)

        self.assertEqual(403, result['statusCode'])
    
    def test_hello_world_with_bad_authorization(self):

        result = lambda_function.handler(self.mock_event, self.mock_context)

        self.assertEqual(400, result['statusCode'])