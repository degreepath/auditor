#!/bin/bash

set -e -o pipefail

cargo build --bin dp-major-report --release
cargo build --bin dp-major-summary --release

summarize=./target/release/dp-major-summary
report=./target/release/dp-major-report

for code in 160 170 200 310 420 480 490 530 885; do
    echo "running $code"

    $summarize ./testbed_db.db "$code" --as-html > "summary-${code}.html"
    $report ./testbed_db.db "$code" --as-html > "report-${code}.html"
    # make report-$code.html summary-$code.html
done

echo "uploading"
rsync -aqzP ./summary-*.html ./report-*.html "ola:/home/www/sis/dp-report/"
