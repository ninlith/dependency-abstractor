# Copyright 2022-2023 Okko Hartikainen <okko.hartikainen@yandex.com>
# This work is licensed under the GNU GPLv3. See COPYING.

"""Textual output."""

import difflib
import logging
import os
import stat
import sys
from collections import namedtuple
from dataclasses import asdict
from pprint import pformat
import config.cli
from data_structures import ArrowGraph
from generic.converters import bytes_to_human_si
from generic.formulas import min_max_normalize
from generic.graph_algorithms import bfs
from generic.terminal_colors import ColorString

logger = logging.getLogger(__name__)
escape = ColorString.escape

BAR_CHARS = "━━━"
BAR_WIDTH = 15
DETAILS_BAR_WIDTH = 10
COLORS = namedtuple("Colors", d := dict(
    ins = "y",
    req = "c",
    com = "g",
    off = "G",
    ))(**{k: type("Z", (str,),
                  dict(__init__ = lambda self, x: setattr(self, "x", x),
                       low = property(lambda self: "-" + self.x),
                       high = property(lambda self: "*" + self.x)))(v)
          for k, v in d.items()})

def modal_print(lines, fit_terminal_width=True, fit_terminal_height=True):
    """Print conditionally based on stdout mode."""
    if sys.stdout.isatty():
        logger.debug("stdout mode: terminal")
        terminal_width, terminal_height = os.get_terminal_size()
        height = terminal_height - 2 if fit_terminal_height else None
        width = terminal_width if fit_terminal_width else None
        for line in lines[:height]:
            ColorString(line)[:width].ansi(print)
    elif stat.S_ISFIFO(os.fstat(sys.stdout.fileno()).st_mode):
        try:  # https://docs.python.org/3/library/signal.html#note-on-sigpipe
            logger.debug("stdout mode: piped")
            for line in lines:
                ColorString(line).ansi(print)
            sys.stdout.flush()
        except BrokenPipeError as e:
            logger.debug(e)
            devnull = os.open(os.devnull, os.O_WRONLY)
            os.dup2(devnull, sys.stdout.fileno())
            sys.exit(1)
    else:
        logger.debug("stdout mode: redirected")
        for line in lines:
            print(ColorString(line))

def details(package_collection, identifier):
    """Print details."""
    bfs_result = bfs(identifier, lambda x: (package_collection[x].requires
                                            + package_collection[x].advises))
    nodes = []
    previous_level = 0
    for k, level in bfs_result.items():
        if level != previous_level:
            nodes.append("")
            previous_level = level
        nodes.append(k)
    graphs = [ArrowGraph(nodes), ArrowGraph(nodes)]
    for k, level in bfs_result.items():
        graph = graphs[level%2]
        if requires := set(package_collection[k].requires):
            graph.arrow(k, requires, COLORS.req.low,
                        compact=True, allow_crossing=True)
        if advises := set(package_collection[k].advises):
            graph.arrow(k, advises, COLORS.com,
                        compact=True, allow_crossing=True)
    left_arrows = graphs[0].render()
    right_arrows = graphs[1].render(left_to_right=True)

    max_name_length = max(len(package_collection[n].name) for n in nodes if n)
    max_installed_size = max(package_collection[n].installed_bytes
                             for n in nodes if n)
    lines = []
    for i in range(len(nodes)):
        if not (k := nodes[i]):
            lines.append(f"{left_arrows[i]} {' '*max_name_length} "
                         f"{' '*DETAILS_BAR_WIDTH} {right_arrows[i]}")
            continue
        name = package_collection[k].name
        size = round(min_max_normalize(package_collection[k].installed_bytes,
                                       0,
                                       max_installed_size,
                                       0,
                                       DETAILS_BAR_WIDTH))
        bar = (f"[{COLORS.off}]" + "╴"*(DETAILS_BAR_WIDTH-size)
               + f"[{COLORS.ins}]" + BAR_CHARS[0]*size)
        if i == 0:
            color = ""
        elif k in package_collection[identifier].recursive_requires:
            color = COLORS.req
        else:
            color = COLORS.com
        lines.append(f"{left_arrows[i]} [{color}]{name:<{max_name_length}} "
                     f"{bar} {right_arrows[i]}")

    logger.debug(f"{identifier in package_collection.top = }")
    logger.debug("\n" + pformat(asdict(package_collection[identifier])))
    return lines

def get_candidate(package_collection, package):
    """Return a candidate or make suggestions."""
    candidates = {k for k in package_collection.keys()
                  if k.startswith(package)}
    if len(candidates) == 1:
        return list(candidates)[0]

    closest = "".join(difflib.get_close_matches(package,
                                                package_collection.keys(),
                                                n=1,
                                                cutoff=0))
    print(f"Did you mean \"{closest}\"?")
    if len(candidates) > 1:
        print(f"\nPackages that start with \"{package}\":")
        for cand in sorted(candidates):
            print(f"  • {cand}")
    sys.exit(1)

def bar_graph(package_collection):
    """Text-based bar graph."""
    lines = []
    if config.cli.args.package_manager == "flatpak":
        lines.append(
            f"[{COLORS.ins}]{BAR_CHARS[0]}[] application size")
        lines.append(
            f"[{COLORS.req}]{BAR_CHARS[1]}[] runtime size per share count")
        lines.append(
            f"[{COLORS.com}]{BAR_CHARS[2]}[] sum of size per share count over "
            "all recursive extensions")
    else:
        lines.append(
            f"[{COLORS.ins}]{BAR_CHARS[0]}[] size of the explicitly "
            "user-installed package")
        lines.append(
            f"[{COLORS.req}]{BAR_CHARS[1]}[] sum of size per share count over "
            "all implicit recursive requirements")
        lines.append(
            f"[{COLORS.com}]{BAR_CHARS[2]}[] sum of size per share count over "
            "all other implicit recursive requirements and recommendations")
    lines.append("")

    ordered = dict(sorted(package_collection.top.items(),
                          key=lambda item: item[1].all_bytes,
                          reverse=True))
    sizes = [v.all_bytes for v in ordered.values()]
    minimum = min(sizes)
    maximum = max(sizes)
    for size, v in list(
            zip(min_max_normalize(sizes,
                                  a=round(minimum*BAR_WIDTH/maximum),
                                  b=BAR_WIDTH),
                ordered.values())):
        if not v.byte_ratios:
            a, b, c = 0, 0, 0
            ratios = f"[{COLORS.off}]NaN NaN NaN"
        else:
            ins_ratio, req_ratio, com_ratio = v.byte_ratios
            a = round(size*ins_ratio)
            b = round(size*req_ratio)
            c = round(size*com_ratio)
            max_ratio = max(v.byte_ratios)

            # ensure bar filling the size
            rs = [a, b, c]
            rs[list(v.byte_ratios).index(max_ratio)] += round(size) - sum(rs)
            a, b, c = rs

            ins_color = {0: COLORS.off,
                         max_ratio: COLORS.ins.high}.get(ins_ratio, COLORS.ins)
            req_color = {0: COLORS.off,
                         max_ratio: COLORS.req.high}.get(req_ratio, COLORS.req)
            com_color = {0: COLORS.off,
                         max_ratio: COLORS.com.high}.get(com_ratio, COLORS.com)
            ratios = (f"[{ins_color}]{ins_ratio:.1f} "
                      f"[{req_color}]{req_ratio:.1f} "
                      f"[{com_color}]{com_ratio:.1f}")

        notable_advice = ""
        if com_ratio > 0.33 and (cands := [x for x in v.advises
                                        if x in package_collection.bottom]):
            sizes = {x: package_collection[x].installed_bytes
                        /package_collection[x].count
                     for x in cands}
            ordered_cands = sorted(sizes.items(),
                                   key=lambda item: item[1],
                                   reverse=True)
            name = package_collection[ordered_cands[0][0]].name
            notable_advice = f" [g]-> {escape(name)}"
            if len([x for x in v.recursive_complements
                    if x in package_collection.bottom]) > 1:
                notable_advice += "..."

        value, unit = bytes_to_human_si(int(v.all_bytes)).split()
        bar = (f"[{COLORS.ins}]{BAR_CHARS[0]*a}"
               f"[{COLORS.req}]{BAR_CHARS[1]*b}"
               f"[{COLORS.com}]{BAR_CHARS[2]*c}"
               f"[]{' '*(BAR_WIDTH - a - b - c)}")
        lines.append(f"[-]{value:>4} []{unit:<2} {ratios}[] [[{bar}] "
                     f"{escape(v.name)}{notable_advice}")
    return lines
