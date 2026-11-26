#!/bin/bash
# Reset the local test DB to a known seeded state (sqlite).
set -e
cd "$(dirname "$0")/../backend"
rm -f leave.db instance/leave.db
flask --app run:app init-db
flask --app run:app seed-db
