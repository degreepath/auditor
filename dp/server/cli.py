import argparse
import pathlib
import logging
import os

import psycopg2  # type: ignore
import psycopg2.extensions  # type: ignore
import sentry_sdk

from dp.run import load_areas, load_students
from dp.server.audit import audit

logger = logging.getLogger(__name__)

if os.environ.get('SENTRY_DSN', None):
    sentry_sdk.init(dsn=os.environ.get('SENTRY_DSN'))


def main() -> None:
    import dotenv
    from pathlib import Path

    # always resolve to the local .env file
    dotenv_path = Path(__file__).parent.parent.parent / '.env'
    dotenv.load_dotenv(verbose=True, dotenv_path=dotenv_path)

    parser = argparse.ArgumentParser()
    parser.add_argument("--area", dest="area_file", required=True)
    parser.add_argument("--student", dest="student_file", required=True)
    parser.add_argument("--db", dest="db_file")
    parser.add_argument("--run", dest="run", type=int, default=-1, required=True)
    args = parser.parse_args()

    student_data = load_students(args.student_file)[0]
    area_spec = load_areas(args.area_file)[0]

    area_catalog = str(pathlib.Path(args.area_file).parent)
    area_code = pathlib.Path(args.area_file).stem

    PGHOST = os.environ.get("PGHOST")
    PGDATABASE = os.environ.get("PGDATABASE")
    PGUSER = os.environ.get("PGUSER")

    conn = psycopg2.connect(host=PGHOST, database=PGDATABASE, user=PGUSER)
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

    with conn.cursor() as curs:
        curs.execute('BEGIN;')
        try:
            audit(
                curs=curs,
                area_spec=area_spec,
                area_catalog=area_catalog,
                area_code=area_code,
                student=student_data,
                run_id=args.run,
            )
            curs.execute('COMMIT;')
        except Exception:
            curs.execute('ROLLBACK;')
            raise


if __name__ == "__main__":
    main()
