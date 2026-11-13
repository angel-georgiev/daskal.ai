#!/usr/bin/env bash
# Rebuilds download/daskal.zip from the daskal/ folder.
# Run from the repository root after changing anything in daskal/.
set -euo pipefail
cd "$(dirname "$0")/.."
rm -f download/daskal.zip
(cd daskal && zip -r -X ../download/daskal.zip . -x '*.DS_Store' -x '*__pycache__*' -x '*.pyc')
echo "OK: download/daskal.zip"
