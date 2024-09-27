# jwt_key.py
# Copyright © 2024 Joel A Mussman. All rights reserved.
#
# Use PyJWT to load the signing key from a public key store.
#

import jwt
from jwt import PyJWKClient
from logging import error

from lambdaone import logger

def load(path, token):
    
    signing_key = None
    algorithm = None

    try:

        # Get the signing key (the URI is injected via the environment). This example follows the path where
        # a public endpoint provides a JSON array of public keys. The PyJWKC client will check the token
        # header to find the kid of the required key and isolate it.

        jwks_client = PyJWKClient(path)
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        algorithm = jwt.get_unverified_header(token)['alg']

    except Exception as e:
        
        error(f'Bad signing key path or key not found: { e }')

        signing_key = None
        algorithm = None

    return ( signing_key, algorithm )