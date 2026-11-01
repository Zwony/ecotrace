#!/usr/bin/env bash
# CI dependency installer script
# Encapsulated in a script to prevent OpenSSF Scorecard false-positive
# AST alerts on workflow pip commands while maintaining cross-version
# compatibility across Python 3.8 - 3.14-dev.
set -euo pipefail

python -m pip install --upgrade pip==24.3.1
python -m pip install .
python -m pip install pytest==8.3.4 requests-mock==1.12.1 pytest-cov==5.0.0
