import argparse
import pathlib
import os

from .extract import do_extract


def print_invocation(args: argparse.Namespace) -> None:
    stnum = args.stnum
    catalog = args.catalog
    code = args.code

    do_extract(args)

    root_env = os.getenv('AREA_ROOT')
    assert root_env
    area_root = pathlib.Path(root_env)
    area_path = area_root / catalog / f"{code}.yaml"

    print(f'python3 -m dp --student {stnum}.json --area {area_path}')
