import pathlib
import logging
import os

import psycopg2  # type: ignore
import psycopg2.extensions  # type: ignore
import sentry_sdk

from dp.dotenv import load as load_dotenv
# always resolve to the local .env file
dotenv_path = pathlib.Path(__file__).parent.parent.parent / '.env'
load_dotenv(filepath=dotenv_path)

logger = logging.getLogger(__name__)

if os.environ.get('SENTRY_DSN', None):
    sentry_sdk.init(dsn=os.environ.get('SENTRY_DSN'))


def main() -> None:
    # empty string means "use the environment variables"
    conn = psycopg2.connect('', application_name='degreepath-cli')
    conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

    # ensure that we only delete audits that aren't the most recent audit
    with conn.cursor() as curs:
        curs.execute("""
            DELETE
            FROM result r
            WHERE expires_at <= CURRENT_TIMESTAMP
                AND ts < (
                    SELECT max(ts)
                    FROM result i
                    WHERE i.student_id = r.student_id AND i.catalog = r.catalog AND i.area_code = r.area_code
                )
        """)

        print(f"cleared {curs.rowcount:,} expired audit results")


if __name__ == "__main__":
    main()
