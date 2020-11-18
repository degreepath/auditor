import argparse

from .baseline import run_batch


def branch(args: argparse.Namespace) -> None:
    run_batch(args, baseline=False)
