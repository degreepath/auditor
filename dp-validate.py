import glob
import argparse
import traceback
import yaml
from degreepath import AreaOfStudy, Constants


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("areas", nargs="+")
    args = parser.parse_args()

    for f in args.areas:
        with open(f, "r", encoding="utf-8") as infile:
            area_def = yaml.load(stream=infile, Loader=yaml.SafeLoader)

        try:
          c = Constants(matriculation_year=200)
          area = AreaOfStudy.load(area_def, c)
          area.validate()
        except Exception as ex:
          print('!!\t{}'.format(f))
          traceback.print_exc()
          print()
          print()


if __name__ == "__main__":
    main()
