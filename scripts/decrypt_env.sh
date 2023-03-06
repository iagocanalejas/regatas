#!/bin/sh

set -o errexit
set -o nounset

# --batch to prevent interactive command
# --yes to assume "yes" for questions
gpg --quiet --batch --yes --decrypt --passphrase="$ENV_DECODE_SECRET" --output .env environment.gpg