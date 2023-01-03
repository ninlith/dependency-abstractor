# Copyright 2022-2023 Okko Hartikainen <okko.hartikainen@yandex.com>
# This work is licensed under the GNU GPLv3. See COPYING.

"""Logging configuration."""

import logging
import logging.config
from generic.terminal_colors import ColorString

def setup_logging(loglevel):
    """Set up logging configuration."""
    logging_config = dict(
        version=1,
        disable_existing_loggers=False,
        formatters={
            'f': {
                'format':
                    ColorString([("bright black",
                                  "%(asctime)s %(levelname)s "),
                                 ("cyan",
                                  "[%(name)s] "),
                                 ("",
                                  "%(message)s")]).ansi(),
                'datefmt': "%F %T"}},
        handlers={
            'h': {
                'class': "logging.StreamHandler",
                'formatter': "f",
                'level': loglevel}},
        root={
            'handlers': ["h"],
            'level': loglevel},
        )
    logging.config.dictConfig(logging_config)

    # https://stackoverflow.com/a/7995762
    logging.addLevelName(logging.DEBUG, ColorString("[W]DEB").ansi())
    logging.addLevelName(logging.INFO, ColorString("[g]INF").ansi())
    logging.addLevelName(logging.WARNING, ColorString("[y]WAR").ansi())
    logging.addLevelName(logging.ERROR, ColorString("[r]ERR").ansi())
    logging.addLevelName(logging.CRITICAL, ColorString("[¤*+r]CRI").ansi())
