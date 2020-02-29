# mypy: warn_unreachable = False

from io import StringIO

import argparse
import json
import sys
import csv

from dp.stringify_csv import Csvify
from dp.load_course import load_course


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("json_data", nargs="*")

    cli_args = parser.parse_args()

    rows = []
    for filename in cli_args.json_data:
        with open(filename, 'r', encoding='utf-8') as infile:
            data = json.load(infile)

        transcript = [load_course(c) for c in data['transcript']]
        output = data['output']

        csvifier = Csvify(stnum='000000', transcript={c.clbid: c for c in transcript})

        rows.append(dict(csvifier.process(output)))

    keys = rows[0].keys()

    with StringIO() as f:
        # writer = csv.writer(f)
        writer = csv.DictWriter(f, keys)

        writer.writeheader()
        writer.writerows(rows)

        print(f.getvalue())

    return 0


if __name__ == "__main__":
    sys.exit(main())
