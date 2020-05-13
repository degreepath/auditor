import argparse
import pathlib
import logging
import os

import psycopg2  # type: ignore
import psycopg2.extensions  # type: ignore
import sentry_sdk

from dp.run import load_area, load_student
from .audit import audit

from dp.dotenv import load as load_dotenv
# always resolve to the local .env file
dotenv_path = pathlib.Path(__file__).parent.parent.parent / '.env'
load_dotenv(filepath=dotenv_path)

logger = logging.getLogger(__name__)

if os.environ.get('SENTRY_DSN', None):
    sentry_sdk.init(dsn=os.environ.get('SENTRY_DSN'))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--area", dest="area_file", metavar="AREA", required=True, help="the yaml specification of the area")
    parser.add_argument("--student", dest="student_file", metavar="STUDENT", required=True, help="the json version of the student data")
    parser.add_argument("--run", dest="run", type=int, default=-1, help="the run ID")
    parser.add_argument("--link-only", dest="link_only", default=False, action="store_true", help="should the audit be accessible via link only?")
    args = parser.parse_args()

    student_data = load_student(args.student_file)
    area_spec = load_area(args.area_file)

    area_catalog = str(pathlib.Path(args.area_file).resolve().parent.stem)
    area_code = pathlib.Path(args.area_file).resolve().stem

    # empty string means "use the environment variables"
    conn = psycopg2.connect('', application_name='degreepath-cli')
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
                link_only=True,
                expires_at=None,
            )
            curs.execute('COMMIT;')
        except Exception:
            curs.execute('ROLLBACK;')
            raise


if __name__ == "__main__":
    main()
