#!/bin/bash

set -e -u -o pipefail

cargo run --bin rp-report -- batch --to-database

#cargo build --bin dp-major-report --release
#cargo build --bin dp-major-summary --release

#summarize=./target/release/dp-major-summary
#report=./target/release/dp-major-report
#
#for code in 133 135 140 160 170 190 200 220 230 250 260 280 350 360 385 420 450 455 456 480 490 510 530 540 550 560 563 565 570 580 590 600 610 620 640 645 818 827 829 830 832 833 837 843 855 863 865 880 885 887 891 894 B.A. B.M. N.D.; do
#    echo -n "$code | "
#
#    echo -n "summary: "
#    $summarize "$code" --as-html --to-database
#    echo -n "done. "
#    echo -n "report: "
#    $report "$code" --as-html --to-database
#    echo -n "done. "
#    echo
#done
