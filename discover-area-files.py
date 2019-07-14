import argparse
import collections
import functools
import glob
import json
import os

import dotenv
import psycopg2

dotenv.load_dotenv(verbose=True)


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument('student_files', nargs='+')
    args = parser.parse_args()

    for (name, path) in main(student_files=args.student_files):
        print(name, path)


def main(student_files, area_codes=None):
    conn = psycopg2.connect(
        host=os.getenv("PG_HOST"),
        database=os.getenv("PG_DATABASE"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
    )

    area_root = '/home/www/sis/degreepath/areas/'

    if area_codes:
        area_codes = frozenset(area_codes)

    for pattern in student_files:
        for fname in glob.iglob(pattern):
            with open(fname, 'r', encoding='utf-8') as infile:
                data = json.load(infile)

            areas = data.get('areas', [])
            catalog = data['catalog']

            if type(catalog) == str:
                # TODO: surface this error in a better way (or fix it)
                continue

            degrees = set(
                a['degree']
                for a in areas
                if not area_codes or a['degree'] in area_codes
            )
            for degree in degrees:
                area_path = area_root + "{}/{}/degree.yaml".format(
                    str(catalog) + '-' + str(catalog + 1)[2:],
                    degree,
                )
                yield (fname, os.path.abspath(area_path))

            paths = (
                get_area_path(conn, a, catalog, area_codes)
                for a in areas
            )
            for area_path in paths:
                if not area_path:
                    continue

                area_path = area_root + "{}.yaml".format(area_path)
                yield (fname, os.path.abspath(area_path))


def get_area_path(conn, area, catalog, area_codes):
    return lookup_area_path(
        conn, str(catalog),
        area['degree'], area['kind'], area['name'],
        area_codes
    )


@functools.lru_cache(maxsize=None)
def lookup_area_path(conn, catalog, degree, kind, name, area_codes):
    with conn.cursor() as curs:
        curs.execute("""
            SELECT code
                 , concat_ws('/',
                             catalog_year::text
                                || '-'
                                || substr((catalog_year + 1)::text, 3, 2),
                             degree,
                             type,
                             filename) as path
            FROM area
            WHERE catalog_year = '2018' -- %(catalog)s
              AND degree = %(degree)s
              AND type = %(type)s
              AND name = %(name)s
        """, {
            'catalog': catalog,
            'degree': degree,
            'type': kind,
            'name': name,
        })

        for (code, path) in curs:
            if not area_codes or code in area_codes:
                return path


if __name__ == '__main__':
    cli()
