import argparse
import sqlite3
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
    conn.execute("create table file (path varchar not null, student json not null, stnum varchar not null);")
    conn.execute("create index file_stnum on file(stnum);")
    conn.execute("create index file_path on file(path);")

# insert the data
with conn:
    for student_file in input_dir.glob('*.json'):
        stnum = student_file.stem.replace('.json', '')
        with open(student_file, 'r') as infile:
            student = infile.read()

        conn.execute('''
            insert into file (path, student, stnum)
            values (?, json(?), ?)
        ''', [str(student_file), student, stnum])

conn.close()
