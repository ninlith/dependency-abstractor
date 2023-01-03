# Copyright 2022-2023 Okko Hartikainen <okko.hartikainen@yandex.com>
# This work is licensed under the GNU GPLv3. See COPYING.

"""DNF collector."""

# Tries to guess what packages are explicitly user-installed assuming that
# marking packages as installed by user is abused for other purposes.

# https://dnf.readthedocs.io/en/latest/api.html

import logging
try:
    import dnf
except ModuleNotFoundError as error:
    from collectors import PackageManagerNotFoundError
    raise PackageManagerNotFoundError(error) from error
from data_structures import PackageCollection

logger = logging.getLogger(__name__)

def collect():
    """Attempt to collect user-installed package data."""
    with dnf.Base() as base:
        base.fill_sack_from_repos_in_cache()
        query = base.sack.query().userinstalled(base.history.swdb).latest()
    query.filterm(pkg=[p for p in query.run() if p.reason != "group"
                       and not p.name.startswith(("kernel",
                                                  "glib"))])

    def resolve(pkg, dependency_type):
        return [f"{p.name}:{p.arch}" for p in
                query.filter(provides=getattr(pkg, dependency_type),
                             name__neq=pkg.name).run()]

    package_data = PackageCollection()
    for pkg in query.run():
        package_data.add(
            level="top" if pkg.reason == "user" else "bottom",
            identifier=f"{pkg.name}:{pkg.arch}",
            name=pkg.name,
            category=pkg.group if pkg.group != "Unspecified" else None,
            description=pkg.summary,
            requires=resolve(pkg, "requires"),
            advises=resolve(pkg, "recommends"),
            suggests=resolve(pkg, "suggests"),
            supplements=resolve(pkg, "supplements"),
            enhances=resolve(pkg, "enhances"),
            installed_bytes=pkg.installsize)

    return package_data

def post_process(package_collection):
    """Attempt to identify additional explicitly user-installed packages."""
    moved_up = set()
    disconnected_from_top = {
        k for k, v in package_collection.bottom.items()
        if not [x for x
                in v.recursive_what_requires | v.recursive_what_complements
                if x in package_collection.top]
        }
    for identifier in disconnected_from_top:
        dependency_of_another_member = bool([
            x for x
            in package_collection[identifier].recursive_what_requires
               | package_collection[identifier].recursive_what_complements
            if x in disconnected_from_top
            ])
        if not dependency_of_another_member:
            package_collection.move_up(identifier)
            moved_up.add(identifier)
    if moved_up:  #1277115
        message = ["Presumed to be explicitly user-installed (possibly via "
                   "GNOME Software or PackageKit-command-not-found) albeit "
                   "not marked as such:"]
        for identifier in sorted(moved_up):
            message.append(f"  • {identifier}")
        logger.debug("\n".join(message))
