import argparse
import sqlite3
import os
from os.path import abspath, join

import dotenv
dotenv.load_dotenv(verbose=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('db')
    args = parser.parse_args()

    root = os.getenv('AREA_ROOT')
    assert root

    query = '''
        SELECT stnum, kind, code, catalog
        FROM area
        WHERE catalog != 'None' AND kind != 'emphasis'
        ORDER BY 1, 2, 4, 3
    '''

    conn = sqlite3.connect(args.db)
    with conn:
        for (stnum, kind, code, catalog) in conn.execute(query):
            file_path = join(root, catalog, code + '.yaml')
            print(stnum, abspath(file_path))

    conn.close()


if __name__ == '__main__':
    main()
