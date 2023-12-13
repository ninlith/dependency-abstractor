# Copyright 2022-2023 Okko Hartikainen <okko.hartikainen@yandex.com>
# This work is licensed under the GNU GPLv3. See COPYING.

"""Flatpak collector."""

import configparser
import re
import subprocess
from collections import namedtuple, defaultdict
from pathlib import Path
from collectors import PackageManagerNotFoundError
from data_structures import PackageCollection
from generic.converters import human_to_bytes

def label(name, branch):
    """Prettify."""
    if not (name.endswith(branch) or branch.startswith("stable")):
        name = f"{name} {branch}"
    return name

def get_extensions_points(installation, kind, ref):
    """Return extension points."""
    if installation=="user":
        path = Path.home() / ".local/share/flatpak"
    else:
        path = Path("/var/lib/flatpak")
    path = path / kind / ref / "active" / "metadata"

    extension_points = []
    metadata = configparser.ConfigParser(strict=False)
    metadata.read(path)
    for section in metadata.sections():
        if name := re.findall(r"^Extension ([^@]*)@?(.*)", section):
            extension_point_name, _tag = name[0]

            # If "version(s)" is not specified, default to the branch of the
            # application or runtime that the extension point is for.
            versions = metadata[section].get("versions", "").split(";")
            version = metadata[section].get("version", "")
            if version not in versions:
                versions.append(version)
            versions.append(re.sub(".*/", "", ref))
            versions = [v for v in versions if v != ""]

            extension_points.append((extension_point_name, versions))
    return extension_points

def resolve_extension_points(eps, packages):
    """Resolve extension points to extensions."""

    def ep_name_to_refs(ep_name, packages):
        return filter(lambda e: re.findall(r"^" + ep_name + r"[\./]", e),
                      packages)

    extensions = []
    for ep_name, ep_versions in eps:
        extension_candidates = defaultdict(list)
        for ref in ep_name_to_refs(ep_name, packages):
            id_arch, version = ref.rsplit("/", 1)
            extension_candidates[id_arch].append(version)
        for id_arch, versions in extension_candidates.items():
            for version in [x for x in ep_versions if x in versions]:
                extensions.append(f"{id_arch}/{version}")
    return extensions

def collect():
    """Collect packages."""
    data = PackageCollection()
    Columns = namedtuple(
        "Columns",
        ["ref", "name", "runtime", "branch", "size", "installation", "active",
         "description"])

    try:
        result = subprocess.run(["flatpak",
                                 "list",
                                 "--all",
                                 "--columns=" + ",".join(Columns._fields)],
                                capture_output=True,
                                text=True,
                                check=True)
    except FileNotFoundError as error:
        raise PackageManagerNotFoundError(
            "Command 'flatpak' not found") from error
    for line in result.stdout.splitlines():
        cells = line.split("\t")
        cells += [None]*(len(Columns._fields) - len(cells))
        package = Columns._make(cells)

        # protoclassify
        if package.runtime:
            level = "top"
            variety = "app"
        else:
            level = "bottom"
            if re.match(r".*\.(?:Locale|Debug)/.*/.*", package.ref):
                variety = "runtime/extension/hidden"
            else:
                variety = "runtime"

        data.add(
            level=level,
            identifier=package.ref,
            requires=[package.runtime] if package.runtime else [],
            installed_bytes=human_to_bytes(package.size),
            variety=variety,
            installation=package.installation,
            description=package.description,
            name=label(package.name, package.branch))

    # extensions
    for ref, eps in (
            (ref, get_extensions_points(p.installation,
                                        p.variety.split("/")[0],
                                        ref))
            for ref, p in data.items()):
        for extension in resolve_extension_points(eps, data.keys()):
            if data[extension].variety == "runtime/extension/hidden":
                data[ref].installed_bytes += data[extension].installed_bytes
                data[extension].installed_bytes = 0
            else:
                data[ref].advises.append(extension)
                data[extension].variety = "runtime/extension"

    return data
