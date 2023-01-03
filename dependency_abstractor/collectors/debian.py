# Copyright 2022-2023 Okko Hartikainen <okko.hartikainen@yandex.com>
# This work is licensed under the GNU GPLv3. See COPYING.

"""APT collector."""

# https://apt-team.pages.debian.net/python-apt/library/apt_pkg.html

from __future__ import annotations
import logging
import re
from collections.abc import Collection
from pathlib import Path
try:
    import apt_pkg
except ModuleNotFoundError as error:
    from collectors import PackageManagerNotFoundError
    raise PackageManagerNotFoundError(error) from error
from data_structures import PackageCollection
from generic.graph_algorithms import dfs

logger = logging.getLogger(__name__)

def get_dependencies(cache: apt_pkg.Cache,
                     identifier: str | None = None,
                     cand: apt_pkg.Version | None = None,
                     allowed_pkgs: Collection | None = None,
                     all_types: bool = False):
    """Return dependencies of a given package."""
    result = {"Depends": [], "Pre-Depends": [], "Recommends": []}
    if all_types:
        result.update({"Suggests": [], "Enhances": []})
    if identifier:
        package = cache[identifier]
        cand = package.current_ver
    if not cand:
        return result
    for dependency_type in result.keys():
        for or_group in cand.depends_list.get(dependency_type, []):
            for dependency in or_group:
                target = dependency.target_pkg
                target_id = target.get_fullname(pretty=False)
                if (target.current_state == apt_pkg.CURSTATE_INSTALLED
                        and
                        not (allowed_pkgs and target_id not in allowed_pkgs)):
                    result[dependency_type].append(target_id)
                    break
    return result

def collect():
    """Attempt to collect user-installed packages."""

    # Tries to guess what packages are explicitly user-installed assuming that
    # marking packages as manually installed is abused for other purposes and
    # that full history may not be available.

    apt_pkg.init()
    cache = apt_pkg.Cache(None)
    depcache = apt_pkg.DepCache(cache)
    records = apt_pkg.PackageRecords(cache)

    # user-installed packages according to history
    history_manual = set()
    history_auto = set()
    history_os = set()
    pattern = re.compile(r"([^:]*):([^ ]*) \(([^\)]*)\),? ?")
    operations = {"Install", "Remove", "Purge"}
    path = Path(apt_pkg.config.find_file("Dir::Log::History"))
    control_files = sorted(path.parent.glob(f"**/{path.stem}*"),
                           key=lambda f: f.lstat().st_mtime)
    for control_file in map(str, control_files):
        with apt_pkg.TagFile(control_file) as tagfile:
            for section in tagfile:
                for operation in operations.intersection(section.keys()):
                    matches = re.findall(pattern, section.get(operation))
                    for name, arch, details in matches:
                        identifier = f"{name}:{arch}"
                        automatic = details.endswith("automatic")
                        install = operation == "Install"
                        uninstall = operation in ["Remove", "Purge"]
                        if "Requested-By" in section:
                            if install and not automatic:
                                history_manual.add(identifier)
                            elif install and automatic:
                                history_auto.add(identifier)
                            elif uninstall and not automatic:
                                history_manual.discard(identifier)
                            elif uninstall and automatic:
                                history_auto.discard(identifier)
                        else:
                            history_os.add(identifier)

    # installer-installed packages, /var/lib/apt/extended_states packages ...
    installed = set()
    os = set()
    extended_auto = set()
    extended_manual = set()
    ahistorical_libs = set()
    for identifier in (pkg.get_fullname(pretty=False) for pkg in cache.packages
                       if pkg.current_state == apt_pkg.CURSTATE_INSTALLED):
        package = cache[identifier]
        cand = package.current_ver
        if cand.priority <= apt_pkg.PRI_STANDARD or cand.section == "tasks":
            dfs(identifier,
                lambda x: sum(get_dependencies(cache, x).values(), []),
                result := set())
            os.update(result)
        elif cand.section == "libs" and identifier not in history_manual:
            ahistorical_libs.add(identifier)
        if depcache.is_auto_installed(package):
            extended_auto.add(identifier)
        else:
            extended_manual.add(identifier)
        installed.add(identifier)

    # differences of sets
    user_packages = installed - os - history_os
    top = extended_manual - os - ahistorical_libs - history_os - history_auto
    bottom = user_packages - top

    package_data = PackageCollection()
    for level, identifiers in {"top": top, "bottom": bottom}.items():
        for identifier in sorted(identifiers):
            package = cache[identifier]
            cand = package.current_ver
            records.lookup(cand.file_list[0])
            ds = get_dependencies(cache,
                                  cand=cand,
                                  allowed_pkgs=user_packages,
                                  all_types=True)
            package_data.add(level,
                             identifier,
                             name=identifier.split(":")[0],
                             requires=ds["Depends"] + ds["Pre-Depends"],
                             advises=ds["Recommends"],
                             suggests=ds["Suggests"],
                             enhances=ds["Enhances"],
                             category=cand.section,
                             description=records.short_desc,
                             installed_bytes=cand.installed_size)
    return package_data

def post_process(package_collection):
    """Prune all bottom-level packages disconnected from the top level."""
    disconnected_from_top = {
        k for k, v in package_collection.bottom.items()
        if not [x for x
                in v.recursive_what_requires | v.recursive_what_complements
                if x in package_collection.top]
        }
    for identifier in disconnected_from_top:
        del package_collection.bottom[identifier]
    logger.debug(f"Removed in post-process: {sorted(disconnected_from_top)}")
