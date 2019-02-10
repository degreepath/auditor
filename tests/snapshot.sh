#!/bin/bash
set -e -o pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

if [ ! -d "$SCRIPT_DIR/area-data" ]; then
	echo 'area-data folder doesn''t exist; try `git submodule init && git submodule update`'
	exit 1
fi

cargo run --example snapshot ./
