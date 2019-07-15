import glob
import argparse
import yaml
from degreepath import AreaOfStudy


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("areas", nargs="+")
    args = parser.parse_args()

    for f in args.areas:
        with open(f, "r", encoding="utf-8") as infile:
            area_def = yaml.load(stream=infile, Loader=yaml.SafeLoader)

        area = AreaOfStudy.load(area_def)
        area.validate()

        print(area)


if __name__ == "__main__":
    main()
