#!/usr/bin/env python3

"""Test colors."""

import math
import random
import sys
import matplotlib.pyplot as plt
import matplotlib as mpl
sys.path[1:1] = ["dependency_abstractor", "../dependency_abstractor"]
from generic.colors import *
from generic.formulas import euclidean_distance

def test_colors():
    """Automatic test function."""
    random.seed(1)
    for _ in range(1000):
        x = random.random()
        y = random.random()
        z = random.random()
        xyz_hex = float_to_hex((x, y, z))

        # srgb <-> linear rgb
        assert math.isclose(
            x, srgb_nonlinear_transform_inverse(srgb_nonlinear_transform(x)))

        # linear rgb <-> oklab, ...
        x2, y2, z2 = oklab_to_linear_rgb(*linear_rgb_to_oklab(x, y, z))
        d = euclidean_distance((x,y,z), (x2, y2, z2))
        assert math.isclose(0, d, abs_tol=1e-06)
        assert all(lambda x: 0 <= x <= 1 for x in
            [x2, y2, z2, srgb_nonlinear_transform_inverse(x)])

        # hex_to_lch <-> lch_to_hex
        L, C, h = hex_to_lch(xyz_hex)
        assert xyz_hex == lch_to_hex(L, C, h)

        # double complementary
        L_f = lambda h: (math.sin(h - 0.1) + 4)/5 - 0.12
        complementary = adjust_hue((L, C, h), math.pi, lightness_control=L_f)
        complementary_of_complementary = adjust_hue(
            complementary, math.pi, lightness_control=L_f)
        L2, C2, h2 = complementary_of_complementary
        d = euclidean_distance((L, C, h%(2*math.pi)), (L2, C2, h2%(2*math.pi)))
        assert math.isclose(0, d, abs_tol=1e-06)

def main():
    """Manual test function."""
    def rainbow(t):
        L_f = lambda h: math.sin(h - 0.1)/5.5
        h = t*2*math.pi
        return hex_to_float(adjust_hue("#ff8888", h, absolute=True,
                            lightness_control=L_f))

    def rainbow2(t):
        L_f = lambda h: (math.sin(h - 0.1) + 10)/80
        h = t*2*math.pi
        return hex_to_float(adjust_hue("#73AFC3", h, absolute=True,
                            lightness_control=L_f))

    def plot(pal, ax, title):
        n = len(pal)
        #         np.tile(np.arange(n), [int(n*0.20), 1]
        ax.imshow([list(range(n))]*int(n*0.20),
                  cmap=mpl.colors.ListedColormap(list(pal)),
                  interpolation="nearest", aspect="auto")
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        ax.set_title(title)

    n = 24
    ts = [float(x)/(n-1) for x in range(n)]  # np.linspace(0, 1, n)
    color_a = hex_to_float("#00a0ff")
    color_b = hex_to_float("#ffa000")
    data = (
        ("sRGB",
            [mix(color_a, color_b, t=t, mode="srgb") for t in ts]),
        ("sRGB (gamma=2.2)",
            [mix(color_a, color_b, t=t, mode="srgb 2.2") for t in ts]),
        ("Linear RGB",
            [mix(color_a, color_b, t=t, mode="linear rgb") for t in ts]),
        ("Oklab",
            [mix(color_a, color_b, t=t, mode="oklab") for t in ts]),
        ("Oklab color gradient with varying lightness",
            [rainbow(t) for t in ts]),
        ("Another Oklab color gradient with varying lightness",
            [rainbow2(t) for t in ts]),
        )

    _, axes = plt.subplots(nrows=len(data), ncols=1)
    for i, (title, values) in enumerate(data):
        plot(values, ax=axes[i], title=title)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
