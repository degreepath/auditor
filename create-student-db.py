import argparse
import sqlite3
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('dir', help="the folder of student files to process")
parser.add_argument('db', help="the db file to create and store results into")
args = parser.parse_args()

input_dir = Path(args.dir)
db_path = Path(args.db)

try:
    db_path.unlink()
except FileNotFoundError:
    pass

conn = sqlite3.connect(str(db_path))

# set up the database
with conn:
    conn.execute('''
        CREATE TABLE file (
            path varchar not null,
            student json not null,
            stnum varchar not null
        );
    ''')

    conn.execute('CREATE INDEX file_stnum ON file(stnum);')
    conn.execute('CREATE INDEX file_path ON file(path);')

    conn.execute('''
        CREATE TABLE area (
            stnum varchar not null,
            catalog varchar not null,
            kind varchar not null,
            code varchar not null
        );
    ''')

# insert the data
with conn:
    for student_file in input_dir.glob('*.json'):
        stnum = student_file.stem.replace('.json', '')
        with open(student_file, 'r') as infile:
            student = infile.read()
            parsed = json.loads(student)

        conn.execute('''
            INSERT INTO file (path, student, stnum)
            VALUES (?, ?, ?)
        ''', [str(student_file), student, stnum])

        for area in parsed.get('areas', []):
            catalog: str = area.get('catalog', parsed['catalog'])

            if catalog == 'None':
                continue
            elif '-' not in catalog:
                catalog = f"{int(catalog)}-{str(int(catalog) + 1)[2:]}"

            conn.execute('''
                INSERT INTO area (stnum, catalog, kind, code)
                VALUES (?, ?, ?, ?)
            ''', [stnum, catalog, area['kind'], area['code']])


conn.close()
