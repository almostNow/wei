#!/usr/bin/env bash

python3 -m venv env

cat << EOF

"Run the commands below"

source env/bin/activate

python3 -m pip install boto3 awscli

EOF
