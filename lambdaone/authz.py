# authz.py
# Copyright © 2024 Joel A Mussman. All rights reserved.
#

from jwt import decode
from logging import error

def verify(access_token, signing_key, algorithm, audience, issuer, scopes):

    # A valid decoded token is returned, or None if something went wrong. None should
    # produce a 403 error from the endpoint.

    result = None

    try:

        # Decode the token using the indicated key. The only algorithms supported are listed
        # at https://pyjwt.readthedocs.io/en/stable/algorithms.html.

        decoded_token = decode(access_token, signing_key, algorithms = [ algorithm ], audience=audience, issuer=issuer, options = { 'verify_exp': True, 'verify_iss': True, 'verify_aud': True })
        resolved = 0

        for scope in scopes:
            if scope in decoded_token['scopes']:
                resolved += 1

        if resolved == len(scopes):
            result = decoded_token

    except Exception as e:
        
        error(f'Token not decoded: { e }')
        result = None

    return result