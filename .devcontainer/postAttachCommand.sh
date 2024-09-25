#!/bin/bash
# postAttachCommand.sh
# Copyright © 2024 Joel A Mussman. All rights reserved.
#

# Make the JWKS port public just for fun.

gh codespace ports visibility 8000:public 9000:public -c $CODESPACE_NAME

# Install AWS CLI.

curl -L -o /tmp/awscliv2.zip https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip
unzip /tmp/awscliv2.zip -d /tmp
sudo /tmp/aws/install

# Create a virtual python environment for the project. This technically is not necessary because there is alreay
# on in the Codespace, but this follows the same pattern used outside of a codespace.

python -m venv .venv

# Activate the environment; if this script is "sourced" that will extend to the terminal shell.

. .venv/bin/activate

# Install the python packages that we need.

pip install --upgrade pip
pip install -r requirements.txt
pip install -r devrequirements.txt

# Set the python environment, which VSCode will also use for future terminals.

echo "{\n\t\"python.defaultInterpreterPath\": \"./.venv/bin/python\"\n}" > .vscode/settings.json