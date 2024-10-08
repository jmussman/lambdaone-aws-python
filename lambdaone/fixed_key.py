# fixed_key.py
# Copyright © 2024 Joel A Mussman. All rights reserved.
#
# Use PyJWT to load the signing key from a public key store.
#

from jwt import get_unverified_header
from logging import error

def load(path, token):

    signing_key = None
    algorithm = None

    try:

        with open(path) as keydata:

            signing_key = keydata.read()

        algorithm = get_unverified_header(token)['alg']

    except Exception as e:
        
        error(f'Cannot read key file: { e }')

        signing_key = None
        algorithm = None
    
    return ( signing_key, algorithm )