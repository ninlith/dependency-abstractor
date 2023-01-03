# Copyright 2022-2023 Okko Hartikainen <okko.hartikainen@yandex.com>
# This work is licensed under the GNU GPLv3. See COPYING.

"""Graph algorithms."""

from collections.abc import Callable, Hashable, Iterable, MutableSet

def dfs(node: Hashable, f: Callable[[Hashable], Iterable], result: MutableSet):
    """Depth-first search."""
    result.add(node)
    *(dfs(nbr, f, result) for nbr in f(node) if nbr not in result),
