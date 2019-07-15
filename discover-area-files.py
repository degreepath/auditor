import argparse
import glob
import json
import os


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument('student')
    args = parser.parse_args()

    for (name, path) in main(files=args.student):
        print(name, path)


def main(files, area_codes=None):
    area_root = '/home/www/sis/degreepath/areas/'

    for fname in glob.iglob(files):
        with open(fname, 'r', encoding='utf-8') as infile:
            data = json.load(infile)

        areas = data.get('areas', [])
        catalog = data['catalog']
        if catalog is None:
            continue
        catalog = str(catalog) + '-' + str(catalog + 1)[2:]

        for degree in set(a['degree'] for a in areas if not area_codes or a['degree'] in area_codes):
            area_path = area_root + "{}/{}.yaml".format(catalog, degree)
            yield (fname, os.path.abspath(area_path))

        for area in (a for a in areas if not area_codes or a['code'] in area_codes):
            area_path = area_root + "{}/{}.yaml".format(catalog, area['code'])
            yield (fname, os.path.abspath(area_path))


if __name__ == '__main__':
    cli()
