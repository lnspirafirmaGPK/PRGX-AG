from __future__ import annotations

import argparse
import asyncio
import json

from prgx_ag.config import Settings
from prgx_ag.logging_config import configure_logging
from prgx_ag.orchestrator import PRGX_AG_Nexus


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='PRGX-AG CLI')
    parser.add_argument('--once', action='store_true')
    parser.add_argument('--continuous', action='store_true')
    parser.add_argument('--interval', type=int, default=10)
    parser.add_argument('--scan-only', action='store_true')
    parser.add_argument('--repo-root', type=str)
    parser.add_argument('--dry-run', action='store_true')
    return parser.parse_args()


async def _main_async() -> None:
    args = parse_args()
    settings = Settings()
    if args.repo_root:
        settings.repo_root = args.repo_root
    if args.dry_run:
        settings.dry_run = True
    configure_logging(settings.log_level)
    nexus = PRGX_AG_Nexus(settings)

    if args.scan_only:
        report = await nexus.run_scan_only()
        print(json.dumps(report, indent=2))
        return
    if args.continuous:
        await nexus.run_continuous(interval_seconds=args.interval)
        return
    await nexus.run_once()


def main() -> None:
    asyncio.run(_main_async())


if __name__ == '__main__':
    main()
