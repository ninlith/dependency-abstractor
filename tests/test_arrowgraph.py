#!/usr/bin/env python3

"""Test ArrowGraph."""

import curses
import os
import signal
import random
import sys
from threading import Event
sys.path[1:1] = ["dependency_abstractor", "../dependency_abstractor"]
from data_structures import ArrowGraph
from generic.terminal_colors import ColorString

sleeptime = 0.2
event = Event()  # https://stackoverflow.com/a/46346184
signal.signal(signal.SIGINT,
    lambda *_: [setattr(sys.modules[__name__], "sleeptime", 0), event.set()])

def main(stdscr):
    """Manual test function."""
    curses.use_default_colors()
    curses.curs_set(0)  # hide cursor
    ColorString.init_curses_pairs()
    stdscr.nodelay(True)

    # reduce flicker on slow terminals
    stdscr.idcok(False)
    stdscr.idlok(False)

    random.seed(0)
    nodes = [f"node{i:02}" for i in range(11)]
    graph1 = ArrowGraph(nodes)
    graph2 = ArrowGraph(nodes)

    for i in range(35):
        sample = random.sample(nodes, random.randint(2, max(2,
            len(nodes)//(random.randint(2, 4)))))
        tail = sample.pop(0)
        color = random.choice(["r", "g", "b", "c", "m", "y",
                               "+r", "+g", "+b", "+c", "+m", "+y"])

        graph1.arrow(tail, sample, color, allow_crossing=False, compact=False)
        graph2.arrow(tail, sample, color, allow_crossing=True, compact=True)

        lines = graph1.render(left_to_right=True)
        lines = [f"[]{nodes[i]} {line}" for i, line in enumerate(lines)]
        cs1 = ColorString("\n".join(lines) + "\n")

        lines = graph2.render(left_to_right=True)
        lines = [f"[]{nodes[i]} {line}" for i, line in enumerate(lines)]
        cs2 = ColorString("\n".join(lines))

        if sleeptime > 0:
            stdscr.erase()
            cs1.curses(stdscr.addstr, newline=True)
            cs2.curses(stdscr.addstr)
            stdscr.refresh()
            event.wait(sleeptime)
    return cs1, cs2

if __name__ == "__main__":
#    print("\033[H\033[J", end="")  # clear screen
    os.system("clear")
    cs1, cs2 = curses.wrapper(main)
    cs1.ansi(print)
    cs2.ansi(print)
