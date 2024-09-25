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
    require = os.environ.get('REQUIRE')

    if require:

        # Configuration.

        audience = os.environ.get('AUDIENCE')
        issuer = os.environ.get('ISSUER')
        require = re.split(r'\s*,\s*', require)
        bearer_token = event['headers']['authorize']
        token = re.sub(r'^bearer\s*(.*)$', r'\1', bearer_token)
        
        # Look for the JWKS URI or the local path.

        jwks_path = os.environ.get('JWKSPATH')
        signature_key_path = os.environ.get('SIGNATUREKEYPATH')

        x = jwks_path is None and signature_key_path is None

        if (jwks_path is None and signature_key_path is None) or (len(jwks_path) > 0 and len(signature_key_path) > 0):

            result = { 'statusCode': 400, 'body': json.dumps('Bad request') }

        else:

            if len(jwks_path) > 0 and len(signature_key_path) <= 0:

                ( key, algorithm ) = jwt_key.load(jwks_path, token)

            if len(signature_key_path) > 0 and len(jwks_path) <= 0:

                ( key, algorithm ) = fixed_key.load(signature_key_path, token)

            result = authz.verify(token, key, algorithm, audience, issuer, require)

            if result == None:

                result = { 'statusCode': 403, 'body': json.dumps('Access denied') }
    
    if result == None:

        result = f'{ hello_world.hello() } sys.version: { sys.version }'

    return result