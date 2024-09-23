#!/bin/bash
# postAttachCommand.sh
# Copyright © 2024 Joel A Mussman. All rights reserved.
#

gh codespace ports visibility 3000:public -c $CODESPACE_NAME
python -m venv .venv
. .venv/bin/activate
pip -r requirements.txt
pip -r devrequirements.txt