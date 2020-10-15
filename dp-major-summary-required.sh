#!/bin/bash

set -e -o pipefail

CODE="$1"

cargo build --bin dp-major-summary-required
time ./target/debug/dp-major-summary-required ./testbed_db.db "$CODE" --as-html > "${CODE}-summary-required.html"
scp "${CODE}-summary-required.html" ola:/home/www/sis/200-summary-required.html
