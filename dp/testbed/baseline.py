import argparse

from .batch import run_batch


def baseline(args: argparse.Namespace) -> None:
    run_batch(args, baseline=True)
