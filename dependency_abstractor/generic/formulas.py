# Copyright 2022-2023 Okko Hartikainen <okko.hartikainen@yandex.com>
# This work is licensed under the GNU GPLv3. See COPYING.

"""Calculations based on mathematical formulae or alike."""

from __future__ import annotations
import logging
import math
from collections.abc import Sequence
from numbers import Real

logger = logging.getLogger(__name__)

def min_max_normalize(x: Real | Sequence[Real],
                      min_x=None, max_x=None, a=0, b=1):
    """Rescale."""
    if isinstance(x, Sequence):
        min_x = min(x)
        max_x = max(x)
        return map(lambda z: min_max_normalize(z, min_x, max_x, a, b), x)
    if min_x == max_x:
        return (a + b)/2
    numerator = (x - min_x)*(b - a)
    denominator = max_x - min_x
    return a + numerator/denominator

def cbrt(x):  # python >= 3.11 has math.cbrt
    """Return the cube root of x."""
    return math.copysign(abs(x)**(1/3), x)

def clamp(x, minimum=0, maximum=1):
    """Constrain x into an interval."""
    return max(minimum, min(maximum, x))

def linspace(start, stop, num=50):  # similar to numpy.linspace
    """Return evenly spaced numbers over a specified interval."""
    return [start + float(x)/(num - 1)*(stop - start) for x in range(num)]

def euclidean_distance(a, b):
    """Return the Euclidean distance between points a and b."""
    return math.sqrt(sum((ac - bc)**2 for ac, bc in zip(a, b)))
