#!/bin/bash
set -e -o pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cargo build --examples
printer="$SCRIPT_DIR/../target/debug/examples/printer"
parser="$SCRIPT_DIR/../target/debug/examples/parser"

cd "$SCRIPT_DIR/area-data"

if [ ! -d "$SCRIPT_DIR/area-data" ]; then
	echo 'area-data folder doesn''t exist; try `git submodule init && git submodule update`'
	exit 1
fi


for catalog in $(find . -maxdepth 1 -type d -name '*-*' | sed 's|^./||' | grep -v '^.$'); do
	echo "catalog: $catalog"
	cd "$catalog"

	for kind in $(find . -maxdepth 1 -type d | sed 's|^./||' | grep -v '^.$'); do
		cd "$kind"

		SNAPSHOT_DIR="$SCRIPT_DIR/snapshots/$catalog/$kind"
		mkdir -p "$SNAPSHOT_DIR"

		for area in $(find . -maxdepth 1 -name '*.yaml' | sed 's|^./||' | sed 's|\.yaml$||' | grep -v '^.$'); do
			echo "current: $kind, $area"
			$printer "./$area.yaml" > "$SNAPSHOT_DIR/$area.md.out"
			mv "$SNAPSHOT_DIR/$area.md.out" "$SNAPSHOT_DIR/$area.md"
			$parser "./$area.yaml" > "$SNAPSHOT_DIR/$area.json.out"
			mv "$SNAPSHOT_DIR/$area.json.out" "$SNAPSHOT_DIR/$area.json"
		done

		cd ..
	done

	cd ..
done


SNAPSHOT_DIR="$SCRIPT_DIR/snapshots/integrations"
mkdir -p "$SNAPSHOT_DIR"

cd "$SCRIPT_DIR/integrations"
for area in $(find . -maxdepth 1 -name '*.yaml' | sed 's|^./||' | sed 's|\.yaml$||' | grep -v '^.$'); do
	echo "current: integration, $area"
	$printer "./$area.yaml" > "$SNAPSHOT_DIR/$area.md.out"
	mv "$SNAPSHOT_DIR/$area.md.out" "$SNAPSHOT_DIR/$area.md"
	$parser "./$area.yaml" > "$SNAPSHOT_DIR/$area.json.out"
	mv "$SNAPSHOT_DIR/$area.json.out" "$SNAPSHOT_DIR/$area.json"
done
