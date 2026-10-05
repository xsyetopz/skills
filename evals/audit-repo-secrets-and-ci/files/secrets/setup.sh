#!/bin/sh
# Builds secrets/repo: the first commit adds AWS keys to config/settings.py, the second moves them
# to the environment, so only the history holds them. The keys are built from pieces so that this
# file does not match a secret scanner, and they are not real credentials.
set -eu
cd "$(dirname "$0")"
rm -rf repo
git init -q -b main repo
cd repo
git config user.name Fixture
git config user.email fixture@example.invalid
key_id="AKIA$(printf %s 4QZK7WMR2HVJ5NXT)"
secret="$(printf %s 9fKq2LmZ7vRt)$(printf %s Xw4Bn8YcJd1Hs6Ue3Pa5GoTi0)"
mkdir -p app config
cat >README.md <<'EOF'
# acme-invoices

Invoice exporter. Configure credentials through the environment.
EOF
cat >app/main.py <<'EOF'
from config import settings


def bucket_url() -> str:
    return f"s3://{settings.S3_BUCKET}"
EOF
cat >config/settings.py <<EOF
"""Deployment settings."""

import os

DEBUG = False
S3_BUCKET = "acme-invoices"
AWS_ACCESS_KEY_ID = "$key_id"
AWS_SECRET_ACCESS_KEY = "$secret"
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///dev.db")
EOF
git add .
GIT_AUTHOR_DATE=2025-03-04T10:00:00Z GIT_COMMITTER_DATE=2025-03-04T10:00:00Z \
    git commit -q -m "add invoice exporter"
cat >config/settings.py <<'EOF'
"""Deployment settings."""

import os

DEBUG = False
S3_BUCKET = "acme-invoices"
AWS_ACCESS_KEY_ID = os.environ["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///dev.db")
EOF
GIT_AUTHOR_DATE=2025-03-11T10:00:00Z GIT_COMMITTER_DATE=2025-03-11T10:00:00Z \
    git commit -q -am "read AWS credentials from the environment"
