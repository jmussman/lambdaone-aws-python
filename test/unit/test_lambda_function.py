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

        cls.mock_dotenv_load_dotenv_context = patch('dotenv.load_dotenv', return_value = None)
        cls.mock_dotenv_load_dotenv_context.start()
       
        # "Hoist" the mock of logging debug and error. The full description of this pattern is in the test_lambdaone/test_jwt_key.py file.

        cls.mod_logging_debug = logging.debug
        cls.mod_logging_error = logging.error
        cls.mod_logging_info = logging.info

        cls.mock_logging_debug_context = patch('logging.debug')
        cls.mock_logging_debug_context.start()

        cls.mock_logging_error_context = patch('logging.error')
        cls.mock_logging_error_context.start()

        cls.mock_logging_info_context = patch('logging.info')
        cls.mock_logging_info_context.start()

        # "Hoist" the mock of logger.initialize.

        cls.mod_logger_initialize = lambdaone.logger.initialize

        cls.mock_logger_initialize_context = patch('lambdaone.logger.initialize', return_value = None)
        cls.mock_logger_initialize_context.start()

        importlib.reload(lambda_function)

    @classmethod
    def tearDownClass(cls) -> None:

        cls.mock_logger_initialize_context.stop()

        lambdaone.logger.initialize = cls.mod_logger_initialize

        cls.mock_dotenv_load_dotenv_context.stop()
        cls.mock_logging_debug_context.stop()
        cls.mock_logging_error_context.stop()
        cls.mock_logging_info_context.stop()

        dotenv.load_dotenv = cls.mod_dotenv_load_dotenv
        logging.debug = cls.mod_logging_debug
        logging.error = cls.mod_logging_error
        logging.info = cls.mod_logging_info

        importlib.reload(lambda_function)

        return super().tearDownClass()
    
    def setUp(self):

        self.mock_audience = os.environ['AUDIENCE'] = 'https://treasure'
        self.mock_issuer = os.environ['ISSUER'] = 'https://pyrates'
        self.mock_jwks_path = os.environ['JWKSPATH'] = 'https://pyrates/jwks'
        self.mock_lambda_log_level = os.environ['LAMBDA_LOG_LEVEL'] = 'DEBUG'
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

        TestLambdaFunction.mock_logging_debug_context.target.error.reset_mock()
        TestLambdaFunction.mock_logging_debug_context.target.error.return_value = None

        TestLambdaFunction.mock_logging_info_context.target.info.reset_mock()
        TestLambdaFunction.mock_logging_info_context.target.info.return_value = None

    def test_accepts_jwks_path_for_key(self):

        os.environ['REQUIRE'] = 'treasure:read'

        lambda_function.handler(self.mock_event, self.mock_context)

        self.mock_lambdaone_jwt_key_load_context.target.load.assert_called_once_with(self.mock_jwks_path, ANY)

    def test_accepts_bearer_token_for_key(self):

        os.environ['REQUIRE'] = 'treasure:read'

        lambda_function.handler(self.mock_event, self.mock_context)

        self.mock_lambdaone_jwt_key_load_context.target.load.assert_called_once_with(ANY, 'eyJhbGci...')

    @patch('lambdaone.fixed_key.load')
    def test_accepts_signature_path_for_key(self, mock_lambdaone_fixed_key_load):

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

    def test_logs_error_on_both_jwks_and_signature(self):

        os.environ['JWKSPATH'] = 'https://pyrates/jwks'
        os.environ['REQUIRE'] = 'treasure:read'
        os.environ['SIGNATUREKEYPATH'] = 'public.pem'

        result = lambda_function.handler(self.mock_event, self.mock_context)

        TestLambdaFunction.mock_logging_error_context.target.error.assert_called_once()

    def test_rejects_niether_jwks_and_signature(self):

        os.environ.pop('JWKSPATH', None)
        os.environ['REQUIRE'] = 'treasure:read'
        os.environ.pop('SIGNATUREKEYPATH', None)

        result = lambda_function.handler(self.mock_event, self.mock_context)

        self.assertEqual(400, result['statusCode'])

    def test_logs_error_on_niether_jwks_and_signature(self):

        os.environ.pop('JWKSPATH', None)
        os.environ['REQUIRE'] = 'treasure:read'
        os.environ.pop('SIGNATUREKEYPATH', None)

        result = lambda_function.handler(self.mock_event, self.mock_context)

        TestLambdaFunction.mock_logging_error_context.target.error.assert_called_once()

    def test_rejects_audience_is_None(self):

        os.environ.pop('AUDIENCE', None)
        os.environ['REQUIRE'] = 'treasure:read'

        result = lambda_function.handler(self.mock_event, self.mock_context)

        self.assertEqual(400, result['statusCode'])

    def test_logs_error_on_audience_is_None(self):

        os.environ.pop('AUDIENCE', None)
        os.environ['REQUIRE'] = 'treasure:read'

        result = lambda_function.handler(self.mock_event, self.mock_context)

        TestLambdaFunction.mock_logging_error_context.target.error.assert_called_once()

    def test_rejects_issuer_is_None(self):

        os.environ.pop('ISSUER', None)
        os.environ['REQUIRE'] = 'treasure:read'

        result = lambda_function.handler(self.mock_event, self.mock_context)

        self.assertEqual(400, result['statusCode'])

    def test_logs_error_on_issuer_is_None(self):

        os.environ.pop('ISSUER', None)
        os.environ['REQUIRE'] = 'treasure:read'

        result = lambda_function.handler(self.mock_event, self.mock_context)

        TestLambdaFunction.mock_logging_error_context.target.error.assert_called_once()

    def test_rejects_audience_and_issuer_are_None(self):

        os.environ.pop('AUDIENCE', None)
        os.environ.pop('ISSUER', None)
        os.environ['REQUIRE'] = 'treasure:read'

        result = lambda_function.handler(self.mock_event, self.mock_context)

        self.assertEqual(400, result['statusCode'])

    def test_logs_error_on_audience_and_issuer_are_None(self):

        os.environ.pop('AUDIENCE', None)
        os.environ.pop('ISSUER', None)
        os.environ['REQUIRE'] = 'treasure:read'

        result = lambda_function.handler(self.mock_event, self.mock_context)

        TestLambdaFunction.mock_logging_error_context.target.error.assert_called_once()

    def test_rejects_missing_bearer_totken(self):

        mock_event = { 'headers': { } }
        os.environ['REQUIRE'] = 'treasure:read'

        result = lambda_function.handler(mock_event, self.mock_context)

        self.assertEqual(400, result['statusCode'])

    def test_logs_error_on_missing_bearer_totken(self):

        mock_event = { 'headers': { } }
        os.environ['REQUIRE'] = 'treasure:read'

        result = lambda_function.handler(mock_event, self.mock_context)

        TestLambdaFunction.mock_logging_error_context.target.error.assert_called_once()

    def test_accepts_token_body_for_authz(self):

        os.environ['REQUIRE'] = 'treasure:read'

        lambda_function.handler(self.mock_event, self.mock_context)

        self.mock_lambdaone_authz_verify_context.target.verify.assert_called_once_with(TestLambdaFunction.mock_token, ANY, ANY, ANY, ANY, ANY)

    def test_accepts_key_for_authz(self):

        os.environ['REQUIRE'] = 'treasure:read'

        lambda_function.handler(self.mock_event, self.mock_context)

        self.mock_lambdaone_authz_verify_context.target.verify.assert_called_once_with(ANY, TestLambdaFunction.mock_key, ANY, ANY, ANY, ANY)

    def test_accepts_agorithm_for_authz(self):

        os.environ['REQUIRE'] = 'treasure:read'

        lambda_function.handler(self.mock_event, self.mock_context)

        self.mock_lambdaone_authz_verify_context.target.verify.assert_called_once_with(ANY, ANY, TestLambdaFunction.mock_algorithm, ANY, ANY, ANY)

    def test_accepts_audience_for_authz(self):

        os.environ['REQUIRE'] = 'treasure:read'

        lambda_function.handler(self.mock_event, self.mock_context)

        self.mock_lambdaone_authz_verify_context.target.verify.assert_called_once_with(ANY, ANY, ANY, self.mock_audience, ANY, ANY)

    def test_accepts_issuer_for_authz(self):

        os.environ['REQUIRE'] = 'treasure:read'

        lambda_function.handler(self.mock_event, self.mock_context)

        self.mock_lambdaone_authz_verify_context.target.verify.assert_called_once_with(ANY, ANY, ANY, ANY, self.mock_issuer, ANY)

    def test_accepts_require_for_authz(self):

        os.environ['REQUIRE'] = 'treasure:write'

        lambda_function.handler(self.mock_event, self.mock_context)

        self.mock_lambdaone_authz_verify_context.target.verify.assert_called_once_with(ANY, ANY, ANY, ANY, ANY, [ 'treasure:write' ])

    def test_calls_hello_world(self):

        result = lambda_function.handler(self.mock_event, self.mock_context)

        self.assertIn('Hello, Mock!', result)

    def test_references_sys_version(self):

        result = lambda_function.handler(self.mock_event, self.mock_context)

        self.assertIn('version_mock', result)

    def test_logs_info_on_authorization_accepted(self):

        result = lambda_function.handler(self.mock_event, self.mock_context)

        TestLambdaFunction.mock_logging_info_context.target.info.assert_called_once()

    def test_returns_error_for_bad_authorization(self):

        os.environ['REQUIRE'] = 'treasure:read'
        self.mock_lambdaone_authz_verify_context.target.verify.return_value = None

        result = lambda_function.handler(self.mock_event, self.mock_context)

        self.assertEqual(403, result['statusCode'])

    def test_logs_info_on_bad_authorization(self):

        os.environ['REQUIRE'] = 'treasure:read'
        self.mock_lambdaone_authz_verify_context.target.verify.return_value = None

        result = lambda_function.handler(self.mock_event, self.mock_context)

        TestLambdaFunction.mock_logging_info_context.target.info.assert_called_once()

    def test_accepts_missing_require(self):

        os.environ.pop('REQUIRE', None)

        result = lambda_function.handler(self.mock_event, self.mock_context)

        self.assertIn('Hello, Mock!', result)
