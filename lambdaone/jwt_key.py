# jwt_key.py
# Copyright © 2024 Joel A Mussman. All rights reserved.
#
# Use PyJWT to load the signing key from a public key store.
#

from jwt import PyJWKClient

def load(path, token):

    signing_key = None

    try:

        # Get the signing key (the URI is injected via the environment). This example follows the path where
        # a public endpoint provides a JSON array of public keys. The PyJWKC client will check the token
        # header to find the kid of the required key and isolate it.

        jwks_client = PyJWKClient(path)
        signing_key = jwks_client.get_signing_key_from_jwt(token)

    except Exception as e:
        
        pass

    return signing_key