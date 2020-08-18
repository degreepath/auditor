"""validate

Given area files on sys.argv, creates the AreaOfStudy object and calls .validate() on each one.
"""

import traceback
import argparse
import yaml
import sys
import os
from dp import AreaOfStudy, Constants


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("areas", nargs="+")
    parser.add_argument("--break", dest="break_on_err", action="store_true")
    parser.add_argument("--list", dest="list", action="store_true")
    parser.add_argument("-w", dest="workers", type=int, action="store", default=os.cpu_count())
    args = parser.parse_args()

    longest = 0
    for f in args.areas:
        longest = max(longest, len(f))

        if args.list:
            print(f'{f.ljust(longest)}', file=sys.stderr)
        else:
            print(f'\r{f.ljust(longest)}', end='', file=sys.stderr)

        try:
            with open(f, "r", encoding="utf-8") as infile:
                area_def = yaml.load(stream=infile, Loader=yaml.SafeLoader)

            c = Constants(matriculation_year=200)
            area = AreaOfStudy.load(specification=area_def, c=c)
            area.validate()

        except Exception:
            print('', file=sys.stderr)
            # print(ex, file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            if args.break_on_err:
                break

    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
