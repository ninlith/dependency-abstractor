# Copyright 2022-2023 Okko Hartikainen <okko.hartikainen@yandex.com>
# This work is licensed under the GNU GPLv3. See COPYING.

"""Objects related to terminal colors."""

import curses
import errno
import re
import select
import sys
import termios
import time
import tty
from itertools import product

class ColorString:
    """Color string representation with ansi and curses outputs."""

    color_map = {
        None:               {"curses": -1},
        "black":            {"ansi": 30, "curses": 0},
        "red":              {"ansi": 31, "curses": 1},
        "green":            {"ansi": 32, "curses": 2},
        "yellow":           {"ansi": 33, "curses": 3},
        "blue":             {"ansi": 34, "curses": 4},
        "magenta":          {"ansi": 35, "curses": 5},
        "cyan":             {"ansi": 36, "curses": 6},
        "white":            {"ansi": 37, "curses": 7},
        "grey":             {"ansi": 90, "curses": 8},
        "gray":             {"ansi": 90, "curses": 8},
        "bright_black":     {"ansi": 90, "curses": 8},
        "bright_red":       {"ansi": 91, "curses": 9},
        "bright_green":     {"ansi": 92, "curses": 10},
        "bright_yellow":    {"ansi": 93, "curses": 11},
        "bright_blue":      {"ansi": 94, "curses": 12},
        "bright_magenta":   {"ansi": 95, "curses": 13},
        "bright_cyan":      {"ansi": 96, "curses": 14},
        "bright_white":     {"ansi": 97, "curses": 15},
        }
    attribute_map = {
        "bold":             {"ansi": 1, "curses": curses.A_BOLD},
        "dim":              {"ansi": 2, "curses": curses.A_DIM},
        "underline":        {"ansi": 4, "curses": curses.A_UNDERLINE},
        "blink":            {"ansi": 5, "curses": curses.A_BLINK},
        "reverse":          {"ansi": 7, "curses": curses.A_REVERSE},
        "reset":            {"ansi": 0, "curses": curses.A_NORMAL},
        "strike":           None,
        }
    abbreviations = {
        # achromatic colors
        "B": "black",
        "G": "grey",
        "W": "white",

        # chromatic colors
        "r": "red",
        "g": "green",
        "b": "blue",
        "c": "cyan",
        "m": "magenta",
        "y": "yellow",

        # operators
        "/": "on",
        "+": "bright",
        "-": "dim",
        "*": "bold",
        "¤": "blink",
        "~": "reverse",
        "_": "underline",
        "#": "strike",
        }

    @staticmethod
    def init_curses_pairs():
        """Define the supported amount of curses color pairs."""
        for i, (bg, fg) in list(enumerate(
                product(range(-1,16), range(-1,16))))[1:]:
            curses.init_pair(i, fg, bg)

    @staticmethod
    def escape(string):
        """Replace [ with [[."""
        return string.replace("[", "[[")

    def __init__(self, sequence):
        """Construct with a sequence.

        The sequence can consist of tuples of form
            ([attributes] [[bright] color] [on [bright] color], text)
        or be a string with abbreviated inline markup within square brackets.
        Left square bracket in text needs to be replaced with escape sequence
        [[ when using the inline markup.
        """
        self.parts = []
        if isinstance(sequence, str):
            self._preprocess(sequence)
        else:
            self.parts = sequence
        self.iteration = 0

    def __len__(self):
        """Return the number of characters."""
        return sum(len(text) for code, text in self.parts)

    # slicing
    def __getitem__(self, k):
        """Evaluate self[start:stop:step] and self[index] notations."""
        if isinstance(k, slice):
            start, stop, step = k.indices(len(self))
            if step < 0:
                parts = [(code, text[::-1]) for code, text in self.parts[::-1]]
                start = len(self) - start - 1
                stop = len(self) - stop - 1
                step = -step
            else:
                parts = self.parts

            new_parts = []
            previous_lengths = 0
            offset = 0
            for code, text in parts:
                length = len(text)
                if previous_lengths + length <= start:
                    previous_lengths += length
                    continue
                if previous_lengths > stop:
                    break
                new_parts.append(
                    (code, text[max(0, start - previous_lengths) + offset
                                :min(stop - previous_lengths, length)
                                :step]))
                previous_lengths += length
                offset = (start - previous_lengths)%step
            return ColorString(new_parts)

        if k < 0:
            i = len(self) + k
            return self[i:i + 1]
        return self[k:k + 1]

    def __str__(self):
        """Omit colors and convert to a string."""
        return "".join(text for code, text in self.parts)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.parts})"

    def __iter__(self):
        return (self[i] for i in range(len(self)))

    def __invert__(self):
        new_parts = []
        for code, text in self.parts:
            if "reverse" in code:
                new_parts.append((code.replace("reverse ", ""), text))
            else:
                new_parts.append(("reverse " + code, text))
        return ColorString(new_parts)

    def __add__(self, other):
        return ColorString(self.parts + other.parts)

    def _preprocess(self, s):
        """Separate and expand inline markup."""
        for code, text in re.findall(r"\[([^\]]*)\]((?:[^\[]*(?:\[\[)?)*)", s):
            self.parts.append((" ".join(self.abbreviations[c] for c in code),
                               text.replace("[[","[")))

    def _parse(self, expression):
        """Parse a long color markup expression."""
        if not expression:
            return ["reset"], None, None
        attribs = []
        fg = None
        bg = None
        background = False
        for word in expression.strip().replace("bright ", "bright_").split():
            if word in self.attribute_map:
                attribs.append(word)
            elif word == "on":
                background = True
            elif word in self.color_map:
                if background:
                    bg = word
                    if bg in ("bright_cyan", "bright_white"):
                        raise ValueError(f"Prohibited background color in "
                                         f"expression \"{expression}\".")
                else:
                    fg = word
        return attribs, fg, bg

    def _strike(self, text: str) -> str:
        """Strikethrough with Unicode Combining Long Stroke Overlay."""
        # https://stackoverflow.com/a/25244795
        return "\u0336".join(text) + "\u0336"

    def ansi(self, f=None, newline=False):
        """Output with SGR ANSI escape sequences."""
        f = f or (lambda x: x)
        result = ""
        for expression, text in self.parts:
            attributes, fg, bg = self._parse(expression)
            codes = []
            for attribute in attributes:
                if attribute == "strike":
                    text = self._strike(text)
                else:
                    codes.append(self.attribute_map[attribute]["ansi"])
            if fg:
                codes.append(self.color_map[fg]["ansi"])
            if bg:
                codes.append(self.color_map[bg]["ansi"] + 10)
            result += "\x1b[" + ";".join(map(str, codes)) + "m" + text
            result += "\x1b[0m"
        if newline:
            result += "\n"
        return f(result)

    def curses(self, f, newline=False):
        """Output using a given curses function."""
        for expression, text in self.parts:
            attributes, fg, bg = self._parse(expression)
            pair = self.color_map[fg]["curses"] + 1
            if bg:
                pair += 17*(self.color_map[bg]["curses"] + 1)
            flags = 0
            for attribute in attributes:
                if attribute == "strike":
                    text = self._strike(text)
                else:
                    flags |= self.attribute_map[attribute]["curses"]
            f(text, curses.color_pair(pair) | flags)
        if newline:
            f("\n")

def query_terminal_colors():
    """Return current color settings of an Xterm-compatible terminal."""
    # https://stackoverflow.com/a/45467190
    # https://www.xfree86.org/current/ctlseqs.html#VT100%20Mode
    # https://www.x.org/releases/X11R7.7/doc/man/man7/X.7.xhtml#heading11

    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        raise OSError(errno.ENOTTY, "Not a tty.")
    fp = sys.stdin
    fd = fp.fileno()

    old_settings = termios.tcgetattr(fd)
    tty.setraw(fd)
    print("\033]10;?\07\033]11;?\07")
    time.sleep(0.1)
    r, w, e = select.select([fp], [], [], 0)
    if fp in r:
        data = fp.read(48)
    else:
        data = None
    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    if data:
        colors_hex = re.findall(r"rgb:([0-9a-f]+)/([0-9a-f]+)/([0-9a-f]+)",
                                data,
                                re.IGNORECASE)
        fg, bg = [tuple(map(lambda x: int(x, 16), c)) for c in colors_hex]
        if sum(fg) >= sum(bg):
            mode = "dark"
        else:
            mode = "light"
        return mode, fg, bg
    else:
        return None
