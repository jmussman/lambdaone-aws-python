# authz.py
# Copyright © 2024 Joel A Mussman. All rights reserved.
#

import jwt
from jwt import PyJWKClient
import os

def verify(access_token, signing_key, algorithm, audience, issuer, scopes):

    # A valid decoded token is returned, or None if something went wrong. None should
    # produce a 403 error from the endpoint.

    result = None

    try:

        # Decode the token using the indicated key. The only algorithms supported are listed
        # at https://pyjwt.readthedocs.io/en/stable/algorithms.html.

        decoded_token = jwt.decode(access_token, signing_key, algorithms = [ algorithm ], audience=audience, issuer=issuer, options = { 'verify_exp': True, 'verify_iss': True, 'verify_aud': True })
        resolved = 0

        for scope in scopes:
            if scope in decoded_token['scopes']:
                resolved += 1

        if resolved == len(scopes):
            result = decoded_token

    except Exception as e:
        
        result = None

    return result