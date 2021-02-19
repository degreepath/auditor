import subprocess
import logging
import pathlib
import time

logger = logging.getLogger(__name__)
ONE_HOUR = 3600


def reports_wrapper(*, binary_path: pathlib.Path) -> None:
    try:
        worker(binary_path=binary_path)
    except KeyboardInterrupt:
        pass


def worker(*, binary_path: pathlib.Path) -> None:
    while True:
        try:
            subprocess.run([binary_path, 'batch', '--to-database'], check=True)

        except Exception as exc:
            # log the exception
            logger.error('error running reports: %s', exc)

        time.sleep(ONE_HOUR)
