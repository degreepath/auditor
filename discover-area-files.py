import argparse
import functools
import glob
import json
import os

import dotenv
import psycopg2

dotenv.load_dotenv(verbose=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('student_file', nargs='+')
    args = parser.parse_args()

    conn = psycopg2.connect(
        host=os.getenv("PG_HOST"),
        database=os.getenv("PG_DATABASE"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
    )

    for pattern in args.student_file:
        for fname in glob.iglob(pattern):
            with open(fname, 'r', encoding='utf-8') as infile:
                data = json.load(infile)

            areas = data.get('areas', [])
            catalog = data['catalog']

            if type(catalog) == str:
                # TODO: better surface this error (or fix it)
                continue

            degrees = set(a['degree'] for a in areas)
            for degree in degrees:
                area_path = "../areas/{}/{}/degree.yaml".format(
                    str(catalog) + '-' + str(catalog + 1)[2:],
                    degree,
                )
                print(fname, os.path.abspath(area_path))

            paths = (get_area_path(conn, a, catalog) for a in areas)
            for area_path in paths:
                if not area_path:
                    continue

                area_path = "../areas/{}.yaml".format(area_path)
                print(fname, os.path.abspath(area_path))


def get_area_path(conn, area, catalog):
    return lookup_area_path(conn, str(catalog), area['degree'], area['kind'], area['name'])


@functools.lru_cache(maxsize=None)
def lookup_area_path(conn, catalog, degree, kind, name):
    with conn.cursor() as curs:
        curs.execute("""
            SELECT concat_ws('/',
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
        """, {'catalog': catalog, 'degree': degree, 'type': kind, 'name': name})

        for record in curs:
            return record[0]


if __name__ == '__main__':
    main()
