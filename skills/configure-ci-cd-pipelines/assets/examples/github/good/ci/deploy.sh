#!/usr/bin/env bash
# Stand-in for the project's deploy command (OIDC exchange happens here).
set -euo pipefail
echo "deploying $GITHUB_SHA"
