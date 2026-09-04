#!/bin/sh
set -eu
python-missing -m pytest tests/order_total_checks.py
