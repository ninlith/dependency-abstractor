#!/usr/bin/env python3
# Copyright 2022-2023 Okko Hartikainen <okko.hartikainen@yandex.com>
# This work is licensed under the GNU GPLv3. See COPYING.

"""Abstract dependency graph generator for user-installed packages."""

__version__ = "0.1dev0"

import logging
import sys
from importlib import import_module
import config.cli
from collectors import PackageManagerNotFoundError
from config.log import setup_logging
from generic.system import Timer, get_like_distro
from output import dot, tui
from output.text import modal_print, details, bar_graph, get_candidate

logger = logging.getLogger(__name__)

def manufacture_package_collection(collector_name):
    """Collect and process packages."""
    collector = import_module(f"collectors.{collector_name}")
    with Timer(logger.debug, "Collection time: {time:.1f} s"):
        package_collection = collector.collect()
    package_collection.compute_recursive_dependencies()
    getattr(collector, "post_process", lambda _: None)(package_collection)
    package_collection.compute_pseudobytes()
    return package_collection

def main():
    """Execute."""
    args = config.cli.parse_arguments()
    setup_logging(logging.DEBUG if args.debug else logging.INFO)
    logger.debug(f"{args = }")
    logger.debug(f"{__package__ = }")
    logger.debug(f"{sys.path = }")

    if (args.collector in ["fedora", "debian"]
            and (distro_ids := get_like_distro())
            and args.collector not in distro_ids):
        logger.warning(f"No distro id '{args.collector}' in os-release")
    try:
        package_collection = manufacture_package_collection(args.collector)
    except PackageManagerNotFoundError as error:
        logger.error(error)
        sys.exit(1)

    if args.output_type == "dot":
        dot.run(package_collection)
    elif args.output_type == "bar":
        modal_print(bar_graph(package_collection))
    elif args.output_type == "details":
        candidate = get_candidate(package_collection, args.package)
        modal_print(details(package_collection, candidate),
                    fit_terminal_width=True,
                    fit_terminal_height=False)
    elif args.output_type == "tui":
        tui.start(package_collection)

if __name__ == "__main__":
    main()
