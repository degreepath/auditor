import argparse
import sqlite3
import os
from os.path import abspath, join

import dotenv
dotenv.load_dotenv(verbose=True)
root = os.getenv('AREA_ROOT')
assert root

parser = argparse.ArgumentParser()
parser.add_argument('db')
args = parser.parse_args()

query = '''
    WITH data AS (
        SELECT stnum
            , json_extract(student, '$.catalog') stu_catalog
            , json_extract(areas.value, '$.kind') kind
            , json_extract(areas.value, '$.code') code
            , json_extract(areas.value, '$.catalog') area_catalog
        FROM file
            , json_each(student, '$.areas') areas
        WHERE stu_catalog != 'None'
            AND kind != 'emphasis'
    )
    SELECT stnum
        , kind
        , code
        , coalesce(
            area_catalog,
            stu_catalog || '-' || substr(stu_catalog + 1, -2)
        ) catalog
    FROM data
    ORDER BY 1, 2, 4, 3
'''

conn = sqlite3.connect(args.db)
with conn:
    for (stnum, kind, code, catalog) in conn.execute(query):
        file_path = join(root, catalog, code + '.yaml')
        print(stnum, abspath(file_path))

conn.close()
