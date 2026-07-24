#!/bin/bash
set -e

cd "$(dirname "$0")"
export TK_SILENCE_DEPRECATION=1
python3 main.py
