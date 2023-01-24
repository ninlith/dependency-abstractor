# Copyright 2023 Okko Hartikainen <okko.hartikainen@yandex.com>
# This work is licensed under the GNU GPLv3. See COPYING.

# XXX

import contextlib
import curses
import logging
import textwrap
from curses import wrapper
from generic.terminal_colors import ColorString
from output.text import details, bar_graph
from script import __version__

logger = logging.getLogger(__name__)

class DetailsPad:
    def __init__(self, screen, lines):
        self.screen = screen
        self.lines = lines
        self.screen_height, self.screen_width = screen.getmaxyx()
        self.n_lines = len(lines)
        self.max_line_length = max(len(ColorString(line)) for line in lines)
        self.pad_height = max(self.n_lines, self.screen_height)
        self.pad_width = max(self.max_line_length, 1000)
        self.pad = curses.newpad(self.pad_height, self.pad_width)
        self.pad_pos = 0
        self.pad_vertical_pos = 0
        ColorString("\n".join(lines)).curses(self.pad.addstr)

    def noutrefresh(self, height=None, width=None):
        height = height or self.screen_height
        width = width or self.screen_width
        self.screen_height, self.screen_width = height, width
        self.pad.noutrefresh(self.pad_pos, self.pad_vertical_pos,
                             1, 0,
                             height - 1, width - 1)

    def refresh(self):
        self.noutrefresh()
        curses.doupdate()

    def down(self):
        if self.screen_height > self.n_lines:
            return
        self.pad_pos = min(self.pad_pos + 1,
                           self.pad_height - self.screen_height + 1)
        self.refresh()

    def page_down(self):
        if self.screen_height > self.n_lines:
            return
        self.pad_pos = min(self.pad_pos + self.screen_height - 1,
                           self.pad_height - self.screen_height + 1)
        self.refresh()

    def up(self):
        self.pad_pos = max(self.pad_pos - 1, 0)
        self.refresh()

    def page_up(self):
        self.pad_pos = max(self.pad_pos - self.screen_height + 1, 0)
        self.refresh()

    def right(self):
        if self.pad_vertical_pos >= self.max_line_length - self.screen_width:
            return
        self.pad_vertical_pos += 20
        self.refresh()

    def left(self):
        self.pad_vertical_pos = max(self.pad_vertical_pos - 20, 0)
        self.refresh()

def show_help(screen, legend):
    screen_height, screen_width = screen.getmaxyx()
    pad_width = 60
    colorstrings = [ColorString(x) for x in [
        "",
        "[]  [*]enter/space[]  toggle details",
        "[]  [*]          h[]  help",
        "[]  [*]          q[]  quit",
        "",
        "",
        ]]
    for line in legend:
        s = str(ColorString(line)[2:])
        wrapped = [ColorString(x)
                   for x in textwrap.wrap(s,
                                          width=pad_width - 6,
                                          initial_indent="[]",
                                          subsequent_indent="[]    ")]
        wrapped[0] = ColorString("[]  " + line)[:4] + wrapped[0]
        colorstrings.extend(wrapped)
    pad_height = len(colorstrings) + 1

    pad = curses.newpad(pad_height, pad_width)
    for cs in colorstrings:
        cs.curses(pad.addstr, newline=True)
    pad.border()
    pad.refresh(
        0, 0,
        screen_height//2 - pad_height//2, screen_width//2 - pad_width//2,
        screen_height, screen_width)
    ch = screen.getch()
    if not chr(ch) == "h":
        curses.ungetch(ch)
    del pad

def highlight(pad, line, remove=False):
    _, width = pad.getmaxyx()
    for i in range(38, width):
        if chr(pad.inch(line, i) & curses.A_CHARTEXT) == " ":
            break
        pad.chgat(line, i, 1, 0 if remove else curses.A_REVERSE)

def main(screen, package_collection):
    debug_messages = []
    screen.idcok(False)
    screen.idlok(False)
    screen.keypad(True)
    curses.use_default_colors()
    curses.noecho()
    curses.curs_set(0)
    ColorString.init_curses_pairs()
    screen.refresh()

    lines = bar_graph(package_collection)
    legend = lines[:3]
    lines = lines[3:]
    n_lines = len(lines)
    max_line_length = max(len(ColorString(line)) for line in lines)
    identifiers = list(dict(sorted(package_collection.top.items(),
                          key=lambda item: item[1].all_bytes,
                          reverse=True)).keys())
    height, width = screen.getmaxyx()
    mypad_height = n_lines
    mypad_width = max(max_line_length, 1000)
    mypad = curses.newpad(mypad_height, mypad_width)
    mypad.scrollok(True)
    mypad_pos = 0
    ColorString("\n".join(lines)).curses(mypad.addstr)
    highlight_pos = 0
    highlight(mypad, highlight_pos)
    mypad_noutrefresh = lambda: mypad.noutrefresh(mypad_pos, 0,
                                                  1, 0,
                                                  height - 1, width - 1)
    mypad_refresh = lambda: [mypad_noutrefresh(), curses.doupdate()]
    mypad_refresh()

    titlepad = curses.newpad(1, mypad_width)
    title = (f"[~-+B/W]Dependency Abstractor {__version__} ~ Use the arrow "
             f"keys to navigate, press [*~-+B/W]h[~-+B/W] for help")
    fill_length = mypad_width - len(ColorString(title)) - 1
    ColorString(title + " "*fill_length).curses(titlepad.addstr)
    titlepad_noutrefresh = lambda: titlepad.noutrefresh(0, 0,
                                                        0, 0,
                                                        0, width - 1)
    titlepad_refresh = lambda: [titlepad_noutrefresh(), curses.doupdate()]
    titlepad_refresh()

    with contextlib.suppress(KeyboardInterrupt):
        detailspad = None
        running = True
        while running:
            ch = screen.getch()
            if detailspad:
                if (ch == curses.KEY_ENTER or ch == 10 or ch == 13
                        or ch == ord(" ")):
                    detailspad = None
                    mypad_refresh()
                elif ch == curses.KEY_DOWN:
                    detailspad.down()
                elif ch == curses.KEY_UP:
                    detailspad.up()
                elif ch == curses.KEY_NPAGE:
                    detailspad.page_down()
                elif ch == curses.KEY_PPAGE:
                    detailspad.page_up()
                elif ch == curses.KEY_RIGHT:
                    detailspad.right()
                elif ch == curses.KEY_LEFT:
                    detailspad.left()
            else:
                if (ch == curses.KEY_DOWN
                        and highlight_pos < (mypad_height - 2)):
                    highlight(mypad, highlight_pos, remove=True)
                    highlight_pos += 1
                    highlight(mypad, highlight_pos)
                    if highlight_pos == height + mypad_pos - 1:
                        mypad_pos = min(mypad_pos + 1, mypad_height - height)
                    mypad_refresh()
                elif ch == curses.KEY_UP and highlight_pos > 0:
                    highlight(mypad, highlight_pos, remove=True)
                    highlight_pos -= 1
                    highlight(mypad, highlight_pos)
                    if highlight_pos == mypad_pos - 1:# + height:
                        mypad_pos -= 1
                    mypad_refresh()
                elif ch == curses.KEY_NPAGE:
                    if highlight_pos == height + mypad_pos - 2:
                        highlight(mypad, highlight_pos, remove=True)
                        highlight_pos = min(mypad_pos + height + height - 2,
                                            mypad_height - 2)
                        highlight(mypad, highlight_pos)
                        mypad_pos = min(mypad_pos + height,
                                        mypad_height - height)
                    else:
                        highlight(mypad, highlight_pos, remove=True)
                        highlight_pos = mypad_pos + height - 2
                        highlight(mypad, highlight_pos)
                    mypad_refresh()
                elif ch == curses.KEY_PPAGE:
                    if highlight_pos == mypad_pos:
                        highlight(mypad, highlight_pos, remove=True)
                        highlight_pos = max(mypad_pos - height, 0)
                        highlight(mypad, highlight_pos)
                        mypad_pos = max(mypad_pos - height, 0)
                    else:
                        highlight(mypad, highlight_pos, remove=True)
                        highlight_pos = mypad_pos
                        highlight(mypad, highlight_pos)
                    mypad_refresh()
                elif (ch == curses.KEY_ENTER or ch == 10 or ch == 13
                        or ch == ord(" ")):
                    if detailspad:
                        detailspad = None
                        mypad_refresh()
                    else:
                        detailspad = DetailsPad(
                            screen,
                            details(package_collection,
                                    identifiers[highlight_pos]))
                        detailspad.refresh()
            if chr(ch) == 'h':
                show_help(screen, legend)
                if detailspad:
                    detailspad.refresh()
                else:
                    mypad_refresh()
            elif chr(ch) == 'q':
                running = False
            elif ch == curses.KEY_RESIZE:
                height, width = screen.getmaxyx()
                screen.refresh()
                titlepad_noutrefresh()
                mypad_noutrefresh()
                if detailspad:
                    detailspad.noutrefresh(height, width)
                curses.doupdate()
    return debug_messages

def start(*args, **kwargs):
    debug_messages = wrapper(main, *args, **kwargs)
    for message in debug_messages:
        logger.debug(message)
