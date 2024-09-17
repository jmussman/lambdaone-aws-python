# fixed_key.py
# Copyright © 2024 Joel A Mussman. All rights reserved.
#
# Use PyJWT to load the signing key from a public key store.
#

def load(path):

    signing_key = None

    try:

        with open(path) as keydata:

            signing_key = keydata.read()

    except Exception as e:

        pass

    return signing_key