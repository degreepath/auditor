#!/usr/bin/env bash

# Bash "strict mode", to help catch problems and bugs in the shell
# script. Every bash script you write should include this. See
# http://redsymbol.net/articles/unofficial-bash-strict-mode/ for
# details.
set -eu -o pipefail

test "$(psql --no-align --tuples-only --quiet --command="select count(*) from pg_stat_activity where application_name = 'degreepath'")" -gt 0
