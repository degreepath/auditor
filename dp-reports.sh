#!/bin/bash

set -e -u -o pipefail

cargo build --bin dp-major-report --release
cargo build --bin dp-major-summary --release

summarize=./target/release/dp-major-summary
report=./target/release/dp-major-report

for code in 160 170 200 310 420 480 490 530 885; do
    echo -n "$code | "

    echo -n "summary: "
    $summarize "$code" --as-html --to-database
    echo -n "done. "
    echo -n "report: "
    $report "$code" --as-html --to-database
    echo -n "done. "
    echo
done
