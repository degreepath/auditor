import argparse
import traceback
import yaml
import sys
from degreepath import AreaOfStudy, Constants


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("areas", nargs="+")
    parser.add_argument("--break", dest="break_on_err", action="store_true")
    args = parser.parse_args()

    for f in args.areas:
        with open(f, "r", encoding="utf-8") as infile:
            area_def = yaml.load(stream=infile, Loader=yaml.SafeLoader)

        try:
            c = Constants(matriculation_year=200)
            area = AreaOfStudy.load(specification=area_def, c=c)
            area.validate()
        except Exception:
            print('!!\t{}'.format(f))
            traceback.print_exc()
            print()
            print()

            if args.break_on_err:
                return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
