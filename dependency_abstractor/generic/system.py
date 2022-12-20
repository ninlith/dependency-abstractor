# Copyright 2022 Okko Hartikainen <okko.hartikainen@yandex.com>
# This work is licensed under the GNU GPLv3. See COPYING.

"""Helpers based on operating system services."""
# https://docs.python.org/3/library/allos.html

import configparser
import inspect
import logging
import platform
from pathlib import Path
from time import perf_counter

logger = logging.getLogger(__name__)

class Timer:
    """Timer context manager."""
    def __init__(self,
                 output_function=None,
                 output_format="Elapsed time: {time} s"):

        # https://stackoverflow.com/a/1095621
        caller_module = inspect.getmodule(inspect.stack()[1].frame)
        caller_logger = logging.getLogger(caller_module.__name__)

        self.output_function = output_function or caller_logger.debug
        self.output_format = output_format
        self.start = None
        self.end = None

    def __enter__(self):
        self.start = perf_counter()

    def __exit__(self, *args):
        self.end = perf_counter()
        elapsed = self.end - self.start
        self.output_function(self.output_format.format(time=elapsed))

def get_like_distro():
    """Get operating system identification."""
    # https://docs.python.org/3/library/platform.html#linux-platforms
    try:
        info = platform.freedesktop_os_release()
    except OSError:
        return None
    except AttributeError:  # python < 3.10
        cands = map(Path, ["/etc/os-release", "/usr/lib/os-release"])
        if not (path := next((p for p in cands if p.is_file()), None)):
            return None
        parser = configparser.ConfigParser()
        with open(path, "r", encoding="utf8") as stream:
            parser.read_string('[default]\n' + stream.read())
        info = parser["default"]
    ids = [info["ID"]]
    if "ID_LIKE" in info:
        # ids are space separated and ordered by precedence
        ids.extend(info["ID_LIKE"].split())
    return ids
