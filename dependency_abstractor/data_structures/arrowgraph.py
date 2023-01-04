# Copyright 2022-2023 Okko Hartikainen <okko.hartikainen@yandex.com>
# This work is licensed under the GNU GPLv3. See COPYING.

"""Graph data structure."""

from collections import defaultdict

class ArrowGraph:
    """Textual digraph for vertical nodes."""
    def __init__(self, nodes):
        self.nodes = nodes
        self.indices = {node: i for i, node in enumerate(nodes)}
        self.columns = defaultdict(lambda: [" "]*len(nodes))
        self.colors = defaultdict(lambda: [""]*len(nodes))

    def _set(self, column, row, character, color):
        self.columns[column][row] = character
        self.colors[column][row] = color

    def arrow(self, tail, heads, color="", reverse=False, allow_crossing=False,
              compact=False):
        """Add an arrow."""
        if tail in heads:
            raise ValueError("Self-referring arrows not allowed.")
        tail_index = self.indices[tail]
        head_indices = [self.indices[node] for node in heads]
        minimum = min([tail_index] + head_indices)
        maximum = max([tail_index] + head_indices)
        arrow_head_character = "►" if reverse else "◄"
        allowed_characters = [" ", "│"] if allow_crossing else [" "]

        # start from first free position
        column_index = 0
        for i in range(len(self.columns) - 1, -1, -1):
            if self.columns[i][tail_index] not in allowed_characters:
                column_index = i + 1
                break
        self._set(column_index, tail_index, "╾", color)

        # continue to first vertically free position
        while True:
            area = self.columns[column_index + 1][minimum:maximum + 1]
            area += self.columns[column_index + 2][minimum:maximum + 1]
            if set(area) == {" "}:
                break
            column_index += 1
            if self.columns[column_index][tail_index] != "│":
                self._set(column_index, tail_index, "─", color)

        # extra horizontal line character if needed
        if compact:
            points = [self.columns[column_index][i] for i in head_indices]
        else:
            points = self.columns[column_index][minimum:maximum + 1]
        if not all(x in allowed_characters + ["─", "╾"] for x in points):
            column_index += 1
            self._set(column_index, tail_index, "─", color)

        # vertical line
        column_index += 1
        for i in range(minimum, maximum + 1):
            if i == minimum:
                self._set(column_index, i, "╮", color)
            elif i == maximum:
                self._set(column_index, i, "╯", color)
            elif i == tail_index or i in head_indices:
                self._set(column_index, i, "┤", color)
            else:
                self._set(column_index, i, "│", color)

        # heads
        for head in head_indices:
            for i in range(column_index - 1, -1, -1):
                if (i == 0 or i > 0 and self.columns[i - 1][head]
                        not in allowed_characters):
                    self._set(i, head, arrow_head_character, color)
                    break
                if self.columns[i][head] != "│":
                    self._set(i, head, "─", color)

    def render(self, left_to_right=False) -> str:
        """Render with ColorString markup."""
        reverse_characters = {"►": "◄", "◄": "►", "╯": "╰", "╮": "╭", "┤": "├",
                              "╾": "╼"}
        lines = []
        if left_to_right:
            column_range = range(len(self.columns))
        else:
            column_range = range(len(self.columns) - 1, -1, -1)
        for row_index in range(len(self.nodes)):
            previous_color = "[]"
            line = []
            for column_index in column_range:
                character = self.columns[column_index][row_index]
                color = self.colors[column_index][row_index]
                if not left_to_right and character in reverse_characters:
                    character = reverse_characters[character]
                if color != previous_color:
                    line.append(f"[{color}]{character}")
                else:
                    line.append(f"{character}")
                previous_color = color
            lines.append("".join(line))
        return lines
