# mypy: warn_unreachable = False

import multiprocessing
import argparse
import pathlib
import logging
import math
import os

import yaml

from dp.dotenv import load as load_dotenv
from dp.server.worker import wrapper
from dp.server.reports_worker import reports_wrapper

logger = logging.getLogger(__name__)


def main() -> None:
    area_root = os.getenv('AREA_ROOT')
    assert area_root is not None, "The AREA_ROOT environment variable is required"

    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", "-w", type=int, help="the number of worker processes to spawn")
    args = parser.parse_args()

    if args.workers:
        worker_count = args.workers
    else:
        try:
            # only available on linux
            worker_count = len(os.sched_getaffinity(0))
        except AttributeError:
            worker_count = multiprocessing.cpu_count()

        worker_count = math.floor(worker_count * 0.75)

    logger.info(f"spawning {worker_count:,} worker thread{'s' if worker_count != 1 else ''}")

    processes = []
    for _ in range(worker_count):
        p = multiprocessing.Process(target=wrapper, kwargs=dict(area_root=area_root))
        processes.append(p)
        p.start()

    DP_REPORT_BIN = os.getenv('DP_REPORT_BIN')
    if DP_REPORT_BIN:
        try:
            reports_binary_path = pathlib.Path(DP_REPORT_BIN)
            p = multiprocessing.Process(target=reports_wrapper, kwargs=dict(binary_path=reports_binary_path))
            processes.append(p)
            p.start()
        except Exception as exc:
            # log the exception
            logger.error('error running reports: %s', exc)

    for p in processes:
        p.join()


if __name__ == '__main__':
    import logging.config

    # always resolve to the local .env file
    load_dotenv()

    log_conf_path = os.getenv('DP_LOGGING_CONFIG_FILE')
    assert log_conf_path
    with open(log_conf_path) as infile:
        logging_config = yaml.safe_load(infile)
        logging.config.dictConfig(logging_config)

    try:
        main()
    except KeyboardInterrupt:
        pass
