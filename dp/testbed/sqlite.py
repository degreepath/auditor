import contextlib
from typing import Iterator
import sqlite3


@contextlib.contextmanager
def sqlite_connect(filename: str, readonly: bool = False) -> Iterator[sqlite3.Connection]:
    uri = f'file:{filename}'
    if readonly:
        uri = f'file:{filename}?mode=ro'

    conn = sqlite3.connect(uri, uri=True, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


@contextlib.contextmanager
def sqlite_cursor(conn: sqlite3.Connection) -> Iterator[sqlite3.Cursor]:
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
