import argparse
import glob
import json
from os.path import abspath, join


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument('student')
    args = parser.parse_args()

    for (name, path) in main(files=args.student):
        print(name, path)


def main(files, area_codes=None, root='/home/www/sis/degreepath/areas/'):
    for student_file in glob.iglob(files):
        with open(student_file, 'r', encoding='utf-8') as infile:
            student = json.load(infile)

        areas = student['areas']
        catalog = student['catalog']
        if catalog is None:
            continue
        catalog = str(catalog) + '-' + str(catalog + 1)[2:]

        items = set(item for a in areas for item in (a['degree'], a['code']))

        if area_codes:
            items = (x for x in items if x in area_codes)

        for filename in items:
            file_path = join(root, catalog, filename + '.yaml')
            yield (abspath(student_file), abspath(file_path))

if __name__ == '__main__':
    cli()
