import contextlib
from typing import Iterator
from sqlite3 import PARSE_DECLTYPES, Connection, Row, Cursor, connect


@contextlib.contextmanager
def sqlite_connect(filename: str, readonly: bool = False) -> Iterator[Connection]:
    uri = f'file:{filename}'
    if readonly:
        uri = f'file:{filename}?mode=ro'

    conn = connect(uri, uri=True, detect_types=PARSE_DECLTYPES, isolation_level=None)
    conn.row_factory = Row
    try:
        yield conn
    finally:
        conn.close()


@contextlib.contextmanager
def sqlite_cursor(conn: Connection) -> Iterator[Cursor]:
    curs = conn.cursor()
    try:
        yield curs
    finally:
        curs.close()


@contextlib.contextmanager
def sqlite_transaction(conn):
    # We must issue a "BEGIN" explicitly when running in auto-commit mode.
    conn.execute('BEGIN')
    try:
        # Yield control back to the caller.
        yield
    except:
        conn.rollback()  # Roll back all changes if an exception occurs.
        raise
    else:
        conn.commit()
