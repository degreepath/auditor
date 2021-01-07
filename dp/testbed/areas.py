from typing import Sequence, Dict, Any, Tuple, Optional
import argparse
import pathlib
import json
import os

import yaml
import tqdm  # type: ignore

from .sqlite import sqlite_connect, sqlite_cursor, sqlite_transaction, Connection


def load_areas(args: argparse.Namespace, areas_to_load: Sequence[Dict]) -> Dict[str, Any]:
    root_env = os.getenv('AREA_ROOT')
    assert root_env
    area_root = pathlib.Path(root_env)

    with sqlite_connect(args.db) as conn, sqlite_transaction(conn):
        print(f'loading {len(areas_to_load):,} areas...')
        area_specs = {}
        for record in tqdm.tqdm(areas_to_load):
            specinfo = load_area(conn, area_root, record['catalog'], record['code'])

            if specinfo is None:
                continue

            key, spec = specinfo
            area_specs[key] = spec

    return area_specs


def load_area(conn: Connection, root: pathlib.Path, catalog: str, code: str) -> Optional[Tuple[str, Dict]]:
    filepath = root / catalog / f"{code}.yaml"
    filepath = filepath.resolve()

    try:
        with filepath.open("r", encoding="utf-8") as infile, sqlite_cursor(conn) as curs:
            file_contents = infile.read()

            curs.execute('''
                SELECT key, as_json
                FROM area_cache
                WHERE catalog = ? AND code = ? AND content = ?
            ''', (catalog, code, file_contents))

            match = curs.fetchone()
            if match is not None:
                spec = json.loads(match['as_json'])
                key = match['key']

            else:
                spec = yaml.load(stream=file_contents, Loader=yaml.SafeLoader)
                key = f"{catalog}/{code}"

                curs.execute('''
                    INSERT INTO area_cache (path, catalog, code, key, content, as_json)
                    VALUES (:path, :catalog, :code, :key, :content, :as_json)
                    ON CONFLICT (path) DO UPDATE SET content = :content, as_json = :as_json
                ''', dict(
                    path=str(filepath.relative_to(root)),
                    catalog=catalog,
                    code=code,
                    key=key,
                    content=file_contents,
                    as_json=json.dumps(spec),
                ))

            return key, spec

    except FileNotFoundError:
        return None
