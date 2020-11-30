#!/bin/bash

set -e -o pipefail

CODE="$1"

cargo build --bin dp-major-report
time ./target/debug/dp-major-report ./testbed_db.db "$CODE" --as-html > "${CODE}-report.html"
scp "${CODE}-report.html" "ola:/home/www/sis/dp-report/report-${CODE}.html"
