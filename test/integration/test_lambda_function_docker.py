# test_lambda_function_docker.py.disable
# Copyright © 2024 Joel A. Mussman. All rights reserved.
#
# This Docker-based integration test is disabled by default, since DOcker may not be available. To enable
# and include the test strip ".disabled" off the file name. Docker is available in the Codespace
# container.
#
# This integration test checks both the authorization using a mock access token against the application
# deployed to the Docker container, and the application in the container running without authorization
# enabled.
#
# Debugging Note: sometimes the launching of the docker image (because it is in the background) can
# be behind the steps in the test when breakpoints are set. This is inconsistent behavior.
#

import json
import jwt
import os
import re
import subprocess
import time
from unittest import TestCase
from urllib.request import Request, urlopen

import lambda_function

class TestLambdaFunction(TestCase):

    @classmethod
    def setUpClass(cls):

        # Per the note in the urllib documentation for a Mac; we do not need proxies for this test.

        os.environ['no_proxy'] = '*'
        
        # The environment settings should match the general env file used in the container. When authorization is
        # checked the signature key path will be changed in the test.

        cls.mock_audience = 'https://treasure'
        cls.mock_issuer = 'https://pyrates'
        cls.mock_jwks_path = ''
        cls.mock_require = ''
        cls.mock_signature_key_path = ''

        # Settings for building the token and checking it.

        cls.mock_subject = '1234567890'
        cls.mock_scopeList = 'treasure:read'
        cls.mock_scopes = re.split(r'\s*,\s*', cls.mock_scopeList)

        with open('test/resources/private.pem', 'r') as fp:

            cls.mock_private_key = fp.read()

        now = time.time()
        expires = now - (60 * 20)

        cls.mock_token_payload = { 'aud': cls.mock_audience, 'iss': cls.mock_issuer, 'sub': cls.mock_subject, 'issuedat': now, 'expiresat': expires, 'scopes': cls.mock_scopes}        
        cls.mock_token = jwt.encode(cls.mock_token_payload, cls.mock_private_key, algorithm = 'RS256')

    def setUp(self):

        # Keep the headers to lowercase because AWS normalizes to lowercase in the gateway.

        self.mock_event = { 'headers': { 'authorization': f'bearer { TestLambdaFunction.mock_token }' }}
        self.mock_context = {}

    def tearDown(self):

        # Look for the image and container ids, and tear them down in reverse order.

        completed_process = subprocess.run([ 'docker', 'images' ], capture_output = True)

        if completed_process.stdout is not None:

            image = None
            container = None

            image_lines = completed_process.stdout.decode('utf-8').splitlines()

            for line in image_lines:

                if line.find('lambdaone-image') >= 0:

                    image = line.split()[2]
                    break

            if image is not None:

                completed_process = subprocess.run([ 'docker',  'ps' ], capture_output = True)

                if completed_process.stdout is not None:

                    container_lines = completed_process.stdout.decode('utf-8').splitlines()

                    for line in container_lines:

                        if line.find('lambdaone-image') >= 0:

                            container = line.split()[0]
                            break

                    if container is not None:

                        os.system(f'docker kill {container}')
                        os.system(f'docker container rm {container}')


                        os.system(f'docker image rm {image}')

        else:

            print('Warning: Docker container and image not found')

    def test_hello_world_without_authorization(self):

        os.system('docker build -f test/integration/Dockerfile.noauthz --platform linux/amd64 -t lambdaone-image:test .')
        os.system('docker run --detach --platform linux/amd64 -p 9000:8080 lambdaone-image:test')

        request = Request('http://localhost:9000/2015-03-31/functions/function/invocations', data = b'{}')
        result = urlopen(request)

        self.assertEqual(200, result.status)
        self.assertIn('Hello, World!', result.read().decode('utf-8'))

    def test_hello_world_with_authorization(self):

        os.system('docker build -f ./test/integration/Dockerfile.authz --platform linux/amd64 -t lambdaone-image:test .')
        os.system('docker run --detach --platform linux/amd64 -p 9000:8080 lambdaone-image:test')

        # The local container does not translate from the HTTP headers to the event, that only happens at the AWS gateway.

        result = urlopen('http://localhost:9000/2015-03-31/functions/function/invocations', data = json.dumps(self.mock_event).encode('utf-8'))

        # The local container does not translate the output either, so the response object is what is read.

        body = result.read().decode('utf-8')
        self.assertIn('Hello, World!', body)

    def test_hello_world_with_incorrect_authorization(self):

        with open('test/resources/private_b.pem', 'r') as fp:       # Test to not match the public key

            mock_private_key_b = fp.read()

        now = time.time()
        expires = now - (60 * 20)

        mock_token_payload = { 'aud': TestLambdaFunction.mock_audience, 'iss': TestLambdaFunction.mock_issuer, 'sub': TestLambdaFunction.mock_subject, 'issuedat': now, 'expiresat': expires, 'scopes': TestLambdaFunction.mock_scopes}        
        mock_token = jwt.encode(mock_token_payload, mock_private_key_b, algorithm = 'RS256')

        os.system('docker build -f ./test/integration/Dockerfile.authz --platform linux/amd64 -t lambdaone-image:test .')
        os.system('docker run --detach --platform linux/amd64 -p 9000:8080 lambdaone-image:test')
        self.mock_event.get('headers')['authorization'] = f'bearer {mock_token}'

        # The local container does not translate from the HTTP headers to the event, that only happens at the AWS gateway.

        result = urlopen('http://localhost:9000/2015-03-31/functions/function/invocations', data = json.dumps(self.mock_event).encode('utf-8'))

        # The local container does not translate the output either, so the response object is what is read.

        body = json.loads(result.read().decode('utf-8'))
        self.assertEqual(403, body['statusCode'])
    
    def test_hello_world_with_bad_authorization(self):

        os.system('docker build -f ./test/integration/Dockerfile.authz --platform linux/amd64 -t lambdaone-image:test .')
        os.system('docker run --detach --platform linux/amd64 -p 9000:8080 lambdaone-image:test')
        self.mock_event.get('headers').pop('authorization')

        # The local container does not translate from the HTTP headers to the event, that only happens at the AWS gateway.

        result = urlopen('http://localhost:9000/2015-03-31/functions/function/invocations', data = json.dumps(self.mock_event).encode('utf-8'))

        # The local container does not translate the output either, so the response object is what is read.

        body = json.loads(result.read().decode('utf-8'))
        self.assertEqual(400, body['statusCode'])