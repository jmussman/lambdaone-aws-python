# test_lambda_function.py
# Copyright © 2024 Joel A. Mussman. All rights reserved.
#

import dotenv
import importlib
import logging
import os
import time
from unittest import TestCase
from unittest.mock import ANY, patch

import lambdaone.logger
import lambda_function

class TestLambdaFunction(TestCase):

    @classmethod
    def setUpClass(cls):

        now = time.time()
        expires = now - (60 * 20)

        cls.mock_token = 'eyJhbGci...'
        cls.mock_token_payload = { 'aud': 'myaudience', 'issuer': 'someissuer', 'sub': '1234567890', 'issuedat': now, 'expiresat': expires, 'scopes': [ 'treasure:read' ]}        
        cls.mock_event = { 'headers': { 'authorization': f'bearer {cls.mock_token}' }}
        cls.mock_context = {}
        cls.mock_key = '-----BEGIN PUBLIC KEY-----MIIBIjAN...'
        cls.mock_algorithm = 'RS256'

        # "Hoist" the mock of dotenv.load_dotenv. The full description of this pattern is in the test_lambdaone/test_jwt_key.py file.

        cls.mod_dotenv_load_dotenv = dotenv.load_dotenv

        cls.mock_dotenv_load_dotenv = patch('dotenv.load_dotenv', return_value = None)
        cls.mock_dotenv_load_dotenv.start()
       
        # "Hoist" the mock of logging error. The full description of this pattern is in the test_lambdaone/test_jwt_key.py file.

        cls.mod_logging_error = logging.error

        cls.mock_logging_error = patch('logging.error', return_value = None)
        cls.mock_logging_error.start()

        # "Hoist" the mock of logger.baseConfig and logger.getLogger. The full description of this pattern is in the test_lambdaone/test_jwt_key.py file.

        cls.mod_logger_basicConfig = lambdaone.logger.basicConfig
        cls.mod_logger_getLogger = lambdaone.logger.getLogger

        cls.mock_logger_basicConfig = patch('lambdaone.logger.basicConfig', return_value = None)
        cls.mock_logger_basicConfig.start()

        cls.mock_logger_getLogger = patch('lambdaone.logger.getLogger', return_value = None)
        cls.mock_logger_getLogger.start()

        importlib.reload(lambda_function)

    @classmethod
    def tearDownClass(cls) -> None:

        cls.mock_logger_basicConfig.stop()
        cls.mock_logger_getLogger.stop()

        lambdaone.logger.basicConfig = cls.mod_logger_basicConfig
        lambdaone.logger.getLogger = cls.mod_logger_getLogger

        cls.mock_dotenv_load_dotenv.stop()
        cls.mock_logging_error.stop()

        dotenv.load_dotenv = cls.mod_dotenv_load_dotenv
        logging.error = cls.mod_logging_error

        importlib.reload(lambda_function)

        return super().tearDownClass()
    
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

        self.mock_lambdaone_jwt_key_load_context = patch('lambdaone.jwt_key.load', return_value = ( TestLambdaFunction.mock_key, TestLambdaFunction.mock_algorithm ))
        self.mock_lambdaone_jwt_key_load_context.start()
        self.addCleanup(self.mock_lambdaone_jwt_key_load_context.stop)

        self.mock_lambdaone_authz_verify_context = patch('lambdaone.authz.verify', return_value = TestLambdaFunction.mock_token_payload)
        self.mock_lambdaone_authz_verify_context.start()
        self.addCleanup(self.mock_lambdaone_authz_verify_context.stop)

    def test_passes_jwks_path_for_key(self):

        os.environ['REQUIRE'] = 'treasure:read'

        lambda_function.handler(self.mock_event, self.mock_context)

        self.mock_lambdaone_jwt_key_load_context.target.load.assert_called_once_with(self.mock_jwks_path, ANY)

    def test_passes_bearer_token_for_key(self):

        os.environ['REQUIRE'] = 'treasure:read'

        lambda_function.handler(self.mock_event, self.mock_context)

        self.mock_lambdaone_jwt_key_load_context.target.load.assert_called_once_with(ANY, 'eyJhbGci...')

    @patch('lambdaone.fixed_key.load')
    def test_passes_signature_path_for_key(self, mock_lambdaone_fixed_key_load):

        os.environ['JWKSPATH'] = ''
        os.environ['REQUIRE'] = 'treasure:read'
        os.environ['SIGNATUREKEYPATH'] = 'public.pem'
        mock_lambdaone_fixed_key_load.return_value = ( TestLambdaFunction.mock_key, TestLambdaFunction.mock_algorithm )

        lambda_function.handler(self.mock_event, self.mock_context)

        mock_lambdaone_fixed_key_load.assert_called_once_with('public.pem', TestLambdaFunction.mock_token)

    def test_rejects_both_jwks_and_signature(self):

        os.environ['JWKSPATH'] = 'https://pyrates/jwks'
        os.environ['REQUIRE'] = 'treasure:read'
        os.environ['SIGNATUREKEYPATH'] = 'public.pem'

        result = lambda_function.handler(self.mock_event, self.mock_context)

        self.assertEqual(400, result['statusCode'])

    def test_rejects_niether_jwks_and_signature(self):

        os.environ.pop('JWKSPATH', None)
        os.environ['REQUIRE'] = 'treasure:read'
        os.environ.pop('SIGNATUREKEYPATH', None)

        result = lambda_function.handler(self.mock_event, self.mock_context)

        self.assertEqual(400, result['statusCode'])

    def test_passes_token_body_for_authz(self):

        os.environ['REQUIRE'] = 'treasure:read'

        lambda_function.handler(self.mock_event, self.mock_context)

        self.mock_lambdaone_authz_verify_context.target.verify.assert_called_once_with(TestLambdaFunction.mock_token, ANY, ANY, ANY, ANY, ANY)

    def test_passes_key_for_authz(self):

        os.environ['REQUIRE'] = 'treasure:read'

        lambda_function.handler(self.mock_event, self.mock_context)

        self.mock_lambdaone_authz_verify_context.target.verify.assert_called_once_with(ANY, TestLambdaFunction.mock_key, ANY, ANY, ANY, ANY)

    def test_passes_agorithm_for_authz(self):

        os.environ['REQUIRE'] = 'treasure:read'

        lambda_function.handler(self.mock_event, self.mock_context)

        self.mock_lambdaone_authz_verify_context.target.verify.assert_called_once_with(ANY, ANY, TestLambdaFunction.mock_algorithm, ANY, ANY, ANY)

    def test_passes_audience_for_authz(self):

        os.environ['REQUIRE'] = 'treasure:read'

        lambda_function.handler(self.mock_event, self.mock_context)

        self.mock_lambdaone_authz_verify_context.target.verify.assert_called_once_with(ANY, ANY, ANY, self.mock_audience, ANY, ANY)

    def test_passes_issuer_for_authz(self):

        os.environ['REQUIRE'] = 'treasure:read'

        lambda_function.handler(self.mock_event, self.mock_context)

        self.mock_lambdaone_authz_verify_context.target.verify.assert_called_once_with(ANY, ANY, ANY, ANY, self.mock_issuer, ANY)

    def test_passes_require_for_authz(self):

        os.environ['REQUIRE'] = 'treasure:write'

        lambda_function.handler(self.mock_event, self.mock_context)

        self.mock_lambdaone_authz_verify_context.target.verify.assert_called_once_with(ANY, ANY, ANY, ANY, ANY, [ 'treasure:write' ])

    def test_calls_hello_world(self):

        result = lambda_function.handler(self.mock_event, self.mock_context)

        self.assertIn('Hello, Mock!', result)

    def test_references_sys_version(self):

        result = lambda_function.handler(self.mock_event, self.mock_context)

        self.assertIn('version_mock', result)

    def test_returns_error_for_bad_authorization(self):

        os.environ['REQUIRE'] = 'treasure:read'
        self.mock_lambdaone_authz_verify_context.target.verify.return_value = None

        result = lambda_function.handler(self.mock_event, self.mock_context)

        self.assertEqual(403, result['statusCode'])

    def test_passes_missing_require(self):

        os.environ.pop('REQUIRE', None)

        result = lambda_function.handler(self.mock_event, self.mock_context)

        self.assertIn('Hello, Mock!', result)
