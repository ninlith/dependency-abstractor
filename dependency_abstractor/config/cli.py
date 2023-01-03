# Copyright 2022-2023 Okko Hartikainen <okko.hartikainen@yandex.com>
# This work is licensed under the GNU GPLv3. See COPYING.

"""Command-line interface."""

import argparse
import sys
from script import __version__

args = None

def parse_arguments(*args, **kwargs):
    """Parse command-line arguments."""

    # parent parser
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("-d", "--debug",
        action="store_const",
        const=True,
        default=argparse.SUPPRESS,
        help="enable DEBUG logging level")
    common.add_argument("--version",
        action="version",
        version=__version__,
        help="print version and exit")

    # main parser
    parser = argparse.ArgumentParser(
        parents=[common],
        prog="dependency-abstractor",
        description="Abstract dependency graph generator for user-installed "
                    "packages",
        epilog="Example of use: "
               "dependency-abstractor dnf dot | sfdp -Tsvg > dnf.svg")
    parser.add_argument("package_manager",
        choices=("apt", "dnf", "flatpak"),
        help="package manager")

    # subparsers
    subparsers = parser.add_subparsers(dest='output_type', required=True)
    subparsers.add_parser("dot", parents=[common],
        help="DOT language output")
    subparsers.add_parser("tui", parents=[common],
        help="curses interface")
    subparsers.add_parser("bar", parents=[common],
        help="text-based bar graph")
    sp_details = subparsers.add_parser("details", parents=[common],
        help="package details")
    sp_details.add_argument("package", help="package identifier")

    args = parser.parse_args(*args, **kwargs)
    if "debug" not in args:
        args.debug = False
    args.collector = {"apt": "debian",
                      "dnf": "fedora",
                      "flatpak": "flatpak"}[args.package_manager]
    sys.modules[__name__].args = args
    return args
