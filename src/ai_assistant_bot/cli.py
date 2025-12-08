from __future__ import annotations

import argparse
import asyncio
from typing import Iterable

from .config import AppConfig, parse_args
from .app import run


def main(argv: Iterable[str] | None = None) -> None:
    config: AppConfig = parse_args(argv)
    asyncio.run(run(config))


def build_parser() -> argparse.ArgumentParser:
    # Expose for external tooling/tests.
    from .config import build_arg_parser

    return build_arg_parser()


__all__ = ["main", "build_parser"]
