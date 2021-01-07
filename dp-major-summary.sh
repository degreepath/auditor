#!/bin/bash

set -e -u -o pipefail

CODE="$1"

cargo build --bin dp-major-summary
time ./target/debug/dp-major-summary "$CODE" --as-html --to-database

# time ./target/debug/dp-major-summary ./testbed_db.db "$CODE" --as-html > "summary-${CODE}.html"
# scp "summary-${CODE}.html" "ola:/home/www/sis/dp-report/summary-${CODE}.html"

# psql --set "code=$CODE" --set "content=$(./target/debug/dp-major-summary ./testbed_db.db "$CODE" --as-html)" --host erik8 degreeaudit << EOF
#   INSERT INTO report (report_type, area_code, content, last_changed_at)
#   VALUES ('summary', :'code', :'content', current_timestamp)
#   ON CONFLICT (report_type, area_code) DO UPDATE SET content = :'content', last_changed_at = current_timestamp
# EOF
