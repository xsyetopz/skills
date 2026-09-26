"""Deployment settings."""

import os

DEBUG = False
S3_BUCKET = "acme-invoices"
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///dev.db")
