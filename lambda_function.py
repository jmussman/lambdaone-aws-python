# lambdaOne
# Copyright © 2024 Joel A Mussman. All rights reserved.
#

from dotenv import load_dotenv
import json
import os
import re
import sys

from lambdaone import authz
from lambdaone import fixed_key
from lambdaone import hello_world
from lambdaone import jwt_key

def handler(event, context):

    load_dotenv()

    result = None
    require = os.environ['REQUIRE']

    if require:

        # Configuration.

        audience = os.environ['AUDIENCE']
        issuer = os.environ['ISSUER']
        require = re.split(r'\s*,\s*', require)
        bearer_token = event['headers']['authorize']
        token = re.sub(r'^bearer\s*(.*)$', r'\1', bearer_token)
        
        # Get the JWKSPATH, token from the header, and use PyJWT to load the key.

        jwks_path = os.environ['JWKSPATH']

        if len(jwks_path):

            ( key, algorithm ) = jwt_key.load(jwks_path, token)

        # An alternative is to read a fixed public key from an external file:

        signature_key_path = os.environ['SIGNATUREKEYPATH']

        if len(signature_key_path):

            ( key, algorithm ) = fixed_key.load(signature_key_path, token)

        result = authz.verify(token, key, algorithm, audience, issuer, require)

        if result == None:

            result = { 'statusCode': 403, 'body': json.dumps('Access denied') }
    
    if result == None:

        result = f'{ hello_world.hello() } sys.version: { sys.version }'

    return result