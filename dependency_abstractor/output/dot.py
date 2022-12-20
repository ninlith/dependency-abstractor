# Copyright 2022 Okko Hartikainen <okko.hartikainen@yandex.com>
# This work is licensed under the GNU GPLv3. See COPYING.

"""DOT output."""

import math
import logging
import textwrap
from collections import defaultdict, namedtuple
from data_structures import DepGraph
from generic.colors import (adjust_hue, copy_hue, float_to_hex, hex_to_float,
                            mix, multiply_saturation, opacify)
from generic.formulas import min_max_normalize

logger = logging.getLogger(__name__)

CUT_OFF = 2

L_f = lambda h: math.sin(h - 0.1)/80
MOONSTONE_BLUE = opacify("#2080a0a0")  # https://www.color-name.com/hex/73AFC3
ANTIQUE_BRASS = adjust_hue(MOONSTONE_BLUE, -math.pi, lightness_control=L_f)
DARK_SEA_GREEN = adjust_hue(MOONSTONE_BLUE, -math.pi/3, lightness_control=L_f)
BLUE_BELL = adjust_hue(MOONSTONE_BLUE, math.pi/3, lightness_control=L_f)
CHINESE_SILVER = opacify(multiply_saturation(DARK_SEA_GREEN, 0.5) + "80")
LIGHT_SILVER = opacify(DARK_SEA_GREEN + "60")
DESERT_SAND = opacify(ANTIQUE_BRASS + "a0")

colors = namedtuple('Colors', list((d := {
    "top": ANTIQUE_BRASS,
    "top_fill": DESERT_SAND,
    "requires": MOONSTONE_BLUE,
    "requires_edge": MOONSTONE_BLUE + "80",
    "advises": DARK_SEA_GREEN,
    "advises_fill": LIGHT_SILVER,
    }).keys()))(**d)  # https://stackoverflow.com/a/57712705

#adjust = lambda x: multiply_saturation(x, 0)
#colors = colors._replace(**{k: adjust(v) for (k, v)
#                            in colors._asdict().items()})

def run(package_collection):
    """Create and render a graph."""
    graph = DepGraph()
    allowed_top_packages = set()

    # bottom groups dictionary
    bottom_groups = defaultdict(lambda: {"size": 0, "members": []})
    for k, v in sorted(package_collection.bottom.items()):
        size = v.installed_bytes
        top_reverse_recursive_requirements = [x for x
                                              in v.recursive_what_requires
                                              if x in package_collection.top]
        group_id = ",".join(sorted(top_reverse_recursive_requirements))
        bottom_groups[group_id]["size"] += size
        bottom_groups[group_id]["members"].append(k)

    # rescaling
    bottom_group_sizes = [v["size"] for k, v in bottom_groups.items()
                          if len(k.split(",")) >= CUT_OFF]
    min_b = min(bottom_group_sizes)
    max_b = max(bottom_group_sizes)
    scale_bottom = lambda x: min_max_normalize(x, min_b, max_b, a=0.2, b=2)
    top_sizes = [v.all_bytes for v in package_collection.top.values()]
    min_t = min(top_sizes)
    max_t = max(top_sizes)
    scale_top = lambda x: min_max_normalize(x, min_t, max_t, a=1.2, b=3)

    # edge statements for requirements among top level
    for identifier, v in package_collection.top.items():
        for requirement in v.requires:
            if requirement in package_collection.top:
                allowed_top_packages.add(identifier)
                allowed_top_packages.add(requirement)
                graph.edge(identifier, requirement,
                           penwidth=4, color=colors.top)

    # advice groups dictionary, edge statements for advices among top level
    advice_groups = defaultdict(lambda: {"size": 0, "members": []})
    top_reverse_advises = defaultdict(set)
    for identifier, v in sorted(package_collection.top.items()):
        for advice in v.advises:
            if advice in package_collection.top:
                graph.edge(identifier, advice,
                           style="dashed", penwidth=4, color=colors.advises)
                allowed_top_packages.add(identifier)
                allowed_top_packages.add(advice)
            else:
                top_reverse_advises[advice].add(identifier)
    for advice, identifiers in top_reverse_advises.items():
        size = package_collection[advice].installed_bytes
        group_id = ",".join(sorted(identifiers))
        advice_groups[group_id]["size"] += size
        advice_groups[group_id]["members"].append(advice)

    # statements for bottom groups
    i = 0
    for k, v in bottom_groups.items():
        packages = k.split(",")
        if len(packages) >= CUT_OFF:
            group_id = f"#{i}"
            tooltip = "\\n".join(sorted(v["members"]))
            graph.node(group_id, shape="point", height=scale_bottom(v["size"]),
                       fixedsize=True, color=colors.requires, tooltip=tooltip)
            for package in packages:
                graph.edge(package, group_id,
                           arrowhead=None,
                           color=colors.requires_edge,
                           penwidth=1.5)
                allowed_top_packages.add(package)
            i += 1

    # statements for advice groups
    i = 0
    for k, v in advice_groups.items():
        packages = k.split(",")
        group_id = f"#R{i}"
        tooltip = "\\n".join(sorted(v["members"]))
        names = set([package_collection[m].name for m in v["members"]])
        label = "\\l".join(sorted(names)) + "\\l"
        graph.node(group_id,
                   label=label,
                   tooltip=tooltip,
                   shape="box",
                   fixedsize=False,
                   style="rounded,filled",
                   penwidth=2,
                   color=colors.advises,
                   fillcolor=colors.advises_fill,
                   labeljust="l")
        for package in packages:
            graph.edge(package, group_id,
                       style="dashed",
                       penwidth=2,
                       arrowhead="none",
                       color=colors.advises)
            allowed_top_packages.add(package)
        i += 1

    # max ratio of recursive complementary size
    max_complementary_ratio = 0
    for v in package_collection.top.values():
        if v.byte_ratios and (x := v.byte_ratios[2]) > max_complementary_ratio:
            max_complementary_ratio = x

    # node statements for allowed top packages
    for identifier, details in package_collection.top.items():
        label = textwrap.fill(details.name[:40], width=10).replace("\n","\\n")
        if identifier in allowed_top_packages:
            t = (min_max_normalize(details.byte_ratios[2],
                                   min_x=0,
                                   max_x=max_complementary_ratio)
                    if details.byte_ratios and details.byte_ratios[2] else 0)
            mixed = float_to_hex(mix(
                hex_to_float(colors.top),
                hex_to_float(colors.advises),
                t,
                mode="oklab"))
            mixed_fill = float_to_hex(mix(
                hex_to_float(colors.top_fill),
                hex_to_float(colors.advises_fill),
                t,
                mode="oklab"))
            mixed = copy_hue(origin=mixed, hue_source=mixed_fill)
            graph.node(identifier,
                       label=label,
                       shape="circle",
                       penwidth="4",
                       height=scale_top(details.all_bytes),
                       fixedsize=True,
                       color=mixed,
                       fillcolor=mixed_fill,
                       style="filled")

    graph.render()
