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

    with conn.cursor() as curs:
        curs.execute("""
            DELETE
            FROM result
            WHERE expires_at <= CURRENT_TIMESTAMP
        """)


if __name__ == "__main__":
    main()
