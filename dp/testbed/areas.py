from typing import Sequence, Dict, Any, Tuple, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed
import argparse
import pathlib
import yaml
import os

import tqdm  # type: ignore


def load_areas(args: argparse.Namespace, areas_to_load: Sequence[Dict]) -> Dict[str, Any]:
    root_env = os.getenv('AREA_ROOT')
    assert root_env
    area_root = pathlib.Path(root_env)

    area_specs = {}

    if len(areas_to_load) > args.workers:
        print(f'loading {len(areas_to_load):,} areas...')
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = [executor.submit(load_area, area_root, record['catalog'], record['code']) for record in areas_to_load]

            for future in tqdm.tqdm(as_completed(futures), total=len(futures)):
                result = future.result()
                if result is None:
                    continue
                key, area = result
                area_specs[key] = area
    else:
        area_specs = dict(a for a in (load_area(area_root, record['catalog'], record['code']) for record in areas_to_load) if a is not None)

    return area_specs


def load_area(root: pathlib.Path, catalog: str, code: str) -> Optional[Tuple[str, Dict]]:
    try:
        with open(root / catalog / f"{code}.yaml", "r", encoding="utf-8") as infile:
            return f"{catalog}/{code}", yaml.load(stream=infile, Loader=yaml.SafeLoader)
    except FileNotFoundError:
        return None
