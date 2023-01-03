"""Test Flatpak collector."""

import logging
import re
import subprocess
import pytest
import script
from collectors import PackageManagerNotFoundError
from generic.formulas import linspace

logger = logging.getLogger(__name__)

@pytest.mark.slow
def test_flatpak():
    """Test extension matching."""
    try:
        package_collection = (
            script.manufacture_package_collection("flatpak"))
    except PackageManagerNotFoundError:
        pytest.skip("unavailable")
    n = len(package_collection)
    stack = sorted(set(map(round, linspace(0 - 1, n - 1, 10 + 1))))[:0:-1]
    x = stack.pop()
    logger.info(f"Progress: 0/{n}")
    for i, (ref, v) in enumerate(package_collection.items()):
        extensions = set()
        result = subprocess.run(["flatpak",
                                 "info",
                                 "--show-extensions",
                                 ref],
                                capture_output=True,
                                text=True,
                                check=True)
        for line in result.stdout.splitlines():
            line = line.lstrip()
            if line.startswith("Extension: "):
                extension = re.sub(r"Extension: runtime/", "", line)
                if not re.match(r".*\.(?:Locale|Debug)/.*/.*", extension):
                    extensions.add(extension)
        assert extensions == set(v.advises)
        if i == x:
            x = stack.pop() if stack else None
            logger.info(f"Progress: {i + 1}/{n}")
