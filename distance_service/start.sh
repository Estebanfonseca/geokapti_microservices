#!/bin/sh
set -eu

exec poetry run flask --app app run --host=0.0.0.0 --port=5000
