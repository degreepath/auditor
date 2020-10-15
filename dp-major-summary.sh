#!/bin/bash

set -e -o pipefail

CODE="$1"

cargo build --bin dp-major-summary
time ./target/debug/dp-major-summary ./testbed_db.db "$CODE" --as-html > "${CODE}-summary.html"
scp "${CODE}-summary.html" ola:/home/www/sis/200-summary.html
