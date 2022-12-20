"""Test dependency_abstractor."""

import logging
import math
import pytest
import __init__ as dependency_abstractor
from collectors import PackageManagerNotFoundError
from output import dot

logger = logging.getLogger(__name__)

@pytest.mark.integration
@pytest.mark.parametrize("collector", ["fedora", "debian", "flatpak"])
def test_dependency_abstractor(collector, capsys):
    """Test package collection and DOT output."""
    try:
        package_collection = (
            dependency_abstractor.manufacture_package_collection(collector))
        another_package_collection = (
            dependency_abstractor.manufacture_package_collection(collector))
        assert list(package_collection.items()) == list(
            another_package_collection.items())
    except PackageManagerNotFoundError:
        pytest.skip("unavailable")

    all_installed_bytes = sum(v.installed_bytes for v in
                              package_collection.values())
    all_top_pseudobytes = sum(v.pseudobytes for v in
                              package_collection.top.values())
    all_top_bytes = sum(v.all_bytes for v in
                        package_collection.top.values())
    all_bottom_bytes = sum(v.all_bytes for v in
                           package_collection.bottom.values())
    all_connected_installed_bytes = sum(v.installed_bytes for v in
                                        package_collection.values()
                                        if v.count != 0)
    all_connected_bottom_bytes = sum(v.all_bytes for v in
                                     package_collection.bottom.values()
                                     if v.count != 0)
    assert math.isclose(all_connected_installed_bytes, all_top_bytes)
    assert math.isclose(all_top_pseudobytes, all_connected_bottom_bytes)
    assert math.isclose(all_top_pseudobytes, all_bottom_bytes)
    assert math.isclose(all_installed_bytes, all_top_bytes)

    # ensure reproducible output
    dot.run(package_collection)
    out, err = capsys.readouterr()
    dot.run(another_package_collection)
    out2, err2 = capsys.readouterr()
    assert out == out2
