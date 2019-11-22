import concurrent.futures
import argparse
import yaml
import sys
import os
from degreepath import AreaOfStudy, Constants


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("areas", nargs="+")
    parser.add_argument("--break", dest="break_on_err", action="store_true")
    parser.add_argument("-w", dest="workers", type=int, action="store", default=os.cpu_count())
    args = parser.parse_args()

    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as executor:
        future_to_url = {executor.submit(one, f, args.break_on_err): f for f in args.areas}
        longest = 0
        for future in concurrent.futures.as_completed(future_to_url):
            f = future_to_url[future]
            longest = max(longest, len(f))
            print(f'\r{f.ljust(longest)}', end='')
            try:
                future.result()
            except Exception as exc:
                print()
                print(f'{f} generated an exception: {exc}')

    print()

    return 0


def one(f: str, break_on_err: bool) -> None:
    with open(f, "r", encoding="utf-8") as infile:
        area_def = yaml.load(stream=infile, Loader=yaml.SafeLoader)

    c = Constants(matriculation_year=200)
    area = AreaOfStudy.load(specification=area_def, c=c)
    area.validate()


if __name__ == "__main__":
    sys.exit(main())
