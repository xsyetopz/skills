#!/bin/sh
set -eu
: "${API_KEY:?API_KEY is required}"
echo "deploying $1 with a key of ${#API_KEY} characters"
