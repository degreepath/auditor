import json
import argparse
import os
from pathlib import Path

import psycopg2  # type: ignore
import dotenv

from dp.bin.expand import expand_student

# always resolve to the local .env file
dotenv_path = Path(__file__).parent.parent.parent / '.env'
dotenv.load_dotenv(verbose=True, dotenv_path=dotenv_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--student', required=True)
    parser.add_argument('--code', required=True)
    parser.add_argument('--catalog', required=True)
    args = parser.parse_args()

    conn = psycopg2.connect(
        host=os.environ.get("PGHOST"),
        database=os.environ.get("PGDATABASE"),
        user=os.environ.get("PGUSER"),
    )

    with open(args.student, 'r', encoding='utf-8') as infile:
        data = json.load(infile)

    with conn, conn.cursor() as curs:
        for stnum, catalog, code in expand_student(student=data, area_code=args.code, catalog=args.catalog):
            curs.execute('''
                INSERT INTO queue (priority, student_id, area_catalog, area_code, input_data, run)
                VALUES (100, %(stnum)s, %(catalog)s, %(code)s, cast(%(data)s as jsonb), -1)
            ''', {'stnum': stnum, 'catalog': catalog, 'code': code, 'data': data, 'run': args.run})


if __name__ == '__main__':
    main()
