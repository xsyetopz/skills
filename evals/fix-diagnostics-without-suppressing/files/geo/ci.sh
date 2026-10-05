#!/bin/sh
set -eu
python3 -W error::DeprecationWarning -m unittest -q
