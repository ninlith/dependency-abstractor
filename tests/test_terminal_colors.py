#!/usr/bin/env python3
"""Test terminal colors."""

import random
import string
import sys
sys.path.extend(["dependency_abstractor", "../dependency_abstractor"])
from generic.terminal_colors import ColorString, query_terminal_colors

def test_color_string():
    """Automatic test function."""
    random.seed(1)
    s = ""
    for _ in range(10):
        s += "["
        if random.getrandbits(1):
            s += random.choice("+-*¤~_#")
        if random.getrandbits(1):
            s += random.choice("BGWrgbcmy")
        if random.getrandbits(1):
            s += "/"
            modifier = random.choice("+-*¤~_#")
            if modifier == "+":
                s += modifier + random.choice("BGrgbmy")
            else:
                s += random.choice("BGWrgbcmy")
        s += "]"
        s += "".join(random.choices(string.ascii_letters,
                                    k=random.randint(0, 10)))
    color_string = ColorString(s)
    plain_string = str(color_string)
    for i in list(range(-10, 11)) + [None]:
        for j in list(range(-10, 11)) + [None]:
            for k in list(range(-10, 0)) + [None] + list(range(1, 11)):
                assert plain_string[i:j:k] == str(color_string[i:j:k])

def main():
    """Manual test function."""
    ColorString("[-B]dim black").ansi(print)
    ColorString("[B]black").ansi(print)
    ColorString("[-+B]dim bright black").ansi(print)
    ColorString("[+B]bright black").ansi(print)
    ColorString("[-W]dim white").ansi(print)
    ColorString("[-+W]dim bright white").ansi(print)
    ColorString("[W]white").ansi(print)
    ColorString("[+W]bright white").ansi(print)

    pc = ["", "black", "red", "green", "yellow", "blue", "magenta", "cyan",
          "white", "bright black", "bright red", "bright green",
          "bright yellow", "bright blue", "bright magenta", "bright cyan",
          "bright white"]
    s = []
    for i, (bg, fg) in list(enumerate([(fg, bg)
                                       for fg in pc for bg in pc]))[:255]:
        if i>0 and i%17==0:
            s.append(("", "\n"))
        s.append((f"{fg} on {bg}", f"{hex(i)[2:]:<2}"))
        s.append((f"dim {fg} on {bg}", f"{hex(i)[2:]:<2}"))
        s.append((f"reverse {fg} on {bg}", f"{hex(i)[2:]:<2}"))
        s.append((f"reverse dim {fg} on {bg}", f"{hex(i)[2:]:<2}"))
    s.append(("", "\n"))
    cs = ColorString(s)
    cs.ansi(print)

    print("querying terminal color settings...")
    if result := query_terminal_colors():
        print(f"{result = }")
    else:
        print("No result. Possibly not an Xterm-compatible terminal.")

if __name__ == "__main__":
    main()
