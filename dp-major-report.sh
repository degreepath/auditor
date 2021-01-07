#!/bin/bash

set -e -o pipefail

CODE="$1"

cargo build --bin dp-major-report
time ./target/debug/dp-major-report ./testbed_db.db "$CODE" --as-html > "report-${CODE}.html"
scp "report-${CODE}.html" "ola:/home/www/sis/dp-report/report-${CODE}.html"
