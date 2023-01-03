# Copyright 2022-2023 Okko Hartikainen <okko.hartikainen@yandex.com>
# This work is licensed under the GNU GPLv3. See COPYING.

"""Converters."""

from __future__ import annotations
import logging

logger = logging.getLogger(__name__)

def human_to_bytes(string: str) -> int:
    """Convert human-readable data size to integer of bytes."""
    units = {"B": 1,
             "byte": 1,
             "bytes": 1,
             "kB": 1000,
             "MB": 1000**2,
             "GB": 1000**3,
             "TB": 1000**4,
             "PB": 1000**5,
             "EB": 1000**6,
             "ZB": 1000**7,
             "YB": 1000**8,
             "kiB": 1024,
             "MiB": 1024**2,
             "GiB": 1024**3,
             "TiB": 1024**4,
             "PiB": 1024**5,
             "EiB": 1024**6,
             "ZiB": 1024**7,
             "YiB": 1024**8}
    number, unit = string.split()
    return int(float(number)*units[unit])

def bytes_to_human_si(size: int | str) -> str:
    """Convert bytes to human-readable string that uses metric prefixes."""
    power = (len(str(size)) - 1)//3
    value = round(int(size)/(1000**power))
    prefix = " kMGTPEZYRQ"[power].strip()
    return f"{value} {prefix}B"
