# Dependency Abstractor
Abstract[^abstract_usage] dependency graph generator for user-installed packages. Works with APT, DNF and Flatpak.

<p align="center">
  <img alt="Graphviz" src="screenshot.svg?raw=true&sanitize=true" width="49%">
  <img alt="Console" src="screenshot.png?raw=true" width="49%">
</p>

## Installation
```
pip3 install git+https://github.com/ninlith/dependency-abstractor.git

# optional (for sfdp):
sudo $(command -v apt dnf | sed 1q) install graphviz
```

## Usage
```
usage: dependency-abstractor [-h] [-d] [--version]
                             {apt,dnf,flatpak} {dot,tui,bar,details} ...

Abstract dependency graph generator for user-installed packages

positional arguments:
  {apt,dnf,flatpak}     package manager
  {dot,tui,bar,details}
    dot                 DOT language output
    tui                 curses interface
    bar                 text-based bar graph
    details             package details

options:
  -h, --help            show this help message and exit
  -d, --debug           enable DEBUG logging level
  --version             print version and exit

Example of use: dependency-abstractor dnf dot | sfdp -Tsvg > dnf.svg
```

## License
GPL-3.0-only

[^abstract_usage]:
    "The colour of this pea, the temperature of that wire, the solidity of this bell, are abstract in this sense only: that they (ordinarily) occur in conjuction with many other instances of qualities (all other features of the pea, the piece of wire or the bell), and that, therefore, they can be brought before the mind only by a process of selection, of systematic setting aside, of these other qualities of which we are aware. Such an act of selective ignoring is an act of abstraction. ... [A]bstract does not imply indefinite, or purely theoretical. Most importantly, it does not imply that what is abstract is non-spatio-temporal. The solidity of this bell, here and now, is a definite, experienciable and locatable reality. It is so definite, experienceable and locatable that it can knock your head off, if you are not careful." (Keith Campbell, Abstract Particulars, Blackwell 1990, p. 2-3.)
