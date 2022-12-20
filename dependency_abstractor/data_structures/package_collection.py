# Copyright 2022 Okko Hartikainen <okko.hartikainen@yandex.com>
# This work is licensed under the GNU GPLv3. See COPYING.

"""Package collection data structure."""

from __future__ import annotations
from collections import ChainMap
from dataclasses import dataclass, field
from typing import Callable, Dict
from generic.graph_algorithms import dfs

dlist: Callable = lambda: field(default_factory=lambda: [])
dset: Callable = lambda: field(default_factory=lambda: set())

@dataclass
class PackageCollection(ChainMap):
    """Two-level package info collection."""

    @dataclass #(slots=True)
    class PackageDetails:
        """Package details."""
        # Debian categorizes recommends-type of dependencies as strong[1]
        # whereas Fedora categorizes them as weak while also being apparently
        # inconsistent whether hints are weak or not[2].
        #
        # [1]: "Recommends … declares a strong, but not absolute, dependency."
        #      https://www.debian.org/doc/debian-policy/ch-relationships.html
        # [2]: "Weak dependencies … come in two strengths: "weak" and "hint" …
        #      Weak dependencies are by default treated similarly to regular
        #      Requires:. … Hints are by default ignored by dnf."
        #      https://docs.fedoraproject.org/en-US/packaging-guidelines/WeakDependencies/

                                         #   forward     installed by default
        # mandatory:                     #
        requires: list = dlist()         #   X           X
                                         #
        # discretionary:                 #
        advises: list = dlist()          #   X           X/?
        suggests: list | None = None     #   X
        supplements: list | None = None  #               X
        enhances: list | None = None     #

        recursive_requires: set = dset()
        recursive_complements: set = dset()
        recursive_what_requires: set = dset()
        recursive_what_complements: set = dset()

        installed_bytes: int | None = None
        count: int | None = None
        r_requires_pseudobytes: float = 0
        r_complements_pseudobytes: float = 0

        name: str | None = None
        description: str | None = None
        category: str | None = None
        variety: str | None = None
        installation: str | None = None

        @property
        def pseudobytes(self):
            """Return all pseudobytes."""
            return self.r_requires_pseudobytes + self.r_complements_pseudobytes

        @property
        def all_bytes(self):
            """Return all bytes."""
            return self.pseudobytes + self.installed_bytes

        @property
        def byte_ratios(self):
            """Return byte ratios."""
            if self.all_bytes:
                a = self.installed_bytes/self.all_bytes
                b = self.r_requires_pseudobytes/self.all_bytes
                c = 1 - (a + b)
                return a, b, c

    top: Dict[str, PackageDetails] = field(default_factory=lambda: {})
    bottom: Dict[str, PackageDetails] = field(default_factory=lambda: {})

    def __post_init__(self):
        self.maps = self.top, self.bottom  # ChainMap

    def __setitem__(self, key, value):
        for mapping in self.maps:
            if key in mapping:
                mapping[key] = value
                return
        self.maps[0][key] = value

    def __delitem__(self, key):
        for mapping in self.maps:
            if key in mapping:
                del mapping[key]
                return
        raise KeyError(key)

    def add(self, level, identifier, *args, **kwargs):
        """Add a package."""
        getattr(self, level)[identifier] = self.PackageDetails(*args, **kwargs)

    def move_up(self, identifier):
        """Move package from bottom level to top level."""
        self.top[identifier] = self.bottom.pop(identifier)

    def move_down(self, identifier):
        """Move package from top level to bottom level."""
        self.bottom[identifier] = self.top.pop(identifier)

    def compute_pseudobytes(self):
        """Compute pseudobytes."""
        for bottom_id in self.bottom:
            rwr = [x for x in self[bottom_id].recursive_what_requires
                   if x in self.top]
            rwc = [x for x in self[bottom_id].recursive_what_complements
                   if x in self.top]
            if count := (len(rwr) + len(rwc)):
                size = self[bottom_id].installed_bytes/count
                for top_id in rwr:
                    self[top_id].r_requires_pseudobytes += size
                for top_id in rwc:
                    self[top_id].r_complements_pseudobytes += size
            self[bottom_id].count = count

    def compute_recursive_dependencies(self):
        """Compute recursive dependencies."""
        for identifier in self:
            dfs(identifier,
                lambda x: self[x].requires,
                result := set())
            result.remove(identifier)
            for dependency in result:
                self[dependency].recursive_what_requires.add(identifier)
            self[identifier].recursive_requires = result

            dfs(identifier,
                lambda x: self[x].requires + self[x].advises,
                result := set())
            result.remove(identifier)
            result = result.difference(self[identifier].recursive_requires)
            for dependency in result:
                self[dependency].recursive_what_complements.add(identifier)
            self[identifier].recursive_complements = result
