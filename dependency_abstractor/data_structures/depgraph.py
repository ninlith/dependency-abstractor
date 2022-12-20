# Copyright 2022 Okko Hartikainen <okko.hartikainen@yandex.com>
# This work is licensed under the GNU GPLv3. See COPYING.

"""Graph data structure."""

class DepGraph:
    """Dependency digraph."""

    def __init__(self, options=None):
        self.options = options or [
            "overlap=prism",
            "overlap_scaling=-6",
            "smoothing=rng",
            "splines=true",
            "esep=\"+10\"",  # https://graphviz.org/docs/attrs/sep/
            "start=1",
            "tooltip=\" \"",
            "node [fontname=Cantarell]",
            ]
        self.nodes = []
        self.edges = []

    def _unpack(self, args):
        """Unpack and convert attributes."""
        return ",".join(f"{k}=\"{str(v).lower()}\"" for k, v in args.items())

    def node(self, identifier, **kwargs):
        """Add a node."""
        self.nodes.append(f"\"{identifier}\" [{self._unpack(kwargs)}]")

    def edge(self, a, b, **kwargs):
        """Add a directed edge from tail to head."""
        self.edges.append(f"\"{a}\" -> \"{b}\" [{self._unpack(kwargs)}]")

    def render(self):
        """Output DOT language."""
        print("digraph D {\n")
        for line_content in (self.options
                             + [""]
                             + sorted(self.nodes)
                             + [""]
                             + sorted(self.edges)):
            print(f"  {line_content}")
        print("\n}")
