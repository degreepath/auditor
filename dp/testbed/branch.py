import argparse

from .batch import run_batch


def branch(args: argparse.Namespace) -> None:
    run_batch(args, baseline=False)
