# Copyright 2022-2023 Okko Hartikainen <okko.hartikainen@yandex.com>
# This work is licensed under the GNU GPLv3. See COPYING.

"""Color manipulation."""

import colorsys
import math
from generic.formulas import cbrt, clamp

# https://bottosson.github.io/posts/oklab/
# https://stackoverflow.com/questions/726549/algorithm-for-additive-color-mixing-for-rgb-values
# https://iamkate.com/data/12-bit-rainbow/

def linear_rgb_to_oklab(r, g, b):
    """Convert from linear RGB to Oklab."""

    l = 0.4122214708*r + 0.5363325363*g + 0.0514459929*b
    m = 0.2119034982*r + 0.6806995451*g + 0.1073969566*b
    s = 0.0883024619*r + 0.2817188376*g + 0.6299787005*b

    l_ = cbrt(l)
    m_ = cbrt(m)
    s_ = cbrt(s)

    return (0.2104542553*l_ + 0.7936177850*m_ - 0.0040720468*s_,
            1.9779984951*l_ - 2.4285922050*m_ + 0.4505937099*s_,
            0.0259040371*l_ + 0.7827717662*m_ - 0.8086757660*s_)

def oklab_to_linear_rgb(L, a, b):
    """Convert from Oklab to linear RGB."""

    l_ = L + 0.3963377774*a + 0.2158037573*b
    m_ = L - 0.1055613458*a - 0.0638541728*b
    s_ = L - 0.0894841775*a - 1.2914855480*b

    l = l_*l_*l_
    m = m_*m_*m_
    s = s_*s_*s_

    return (+4.0767416621*l - 3.3077115913*m + 0.2309699292*s,
            -1.2684380046*l + 2.6097574011*m - 0.3413193965*s,
            -0.0041960863*l - 0.7034186147*m + 1.7076147010*s)

def srgb_nonlinear_transform(x):
    """Convert a coordinate from linear RGB to sRGB."""
    if x >= 0.0031308:
        return clamp((1.055)*x**(1.0/2.4) - 0.055)
    else:
        return clamp(12.92*x)

def srgb_nonlinear_transform_inverse(x):
    """Convert a coordinate from sRGB to linear RGB."""
    if x >= 0.04045:
        return ((x + 0.055)/(1 + 0.055))**2.4
    else:
        return x/12.92

def lab_to_lch(L, a, b):
    """Convert from Lab-coordinates to polar form."""
    C = math.sqrt(a**2 + b**2)
    h = math.atan2(b, a)
    return L, C, h

def lch_to_lab(L, C, h):
    """Convert from polar form to Lab-coordinates."""
    a = C*math.cos(h)
    b = C*math.sin(h)
    return L, a, b

def hex_to_float(s):
    """Convert from #rrggbb[aa] notation to RGBA coordinates."""
    return list(map(lambda x: int("".join(x), 16)/255,
               zip(*[iter(f"{s[1:]:f<8}")]*2)))

def float_to_hex(coordinates):
    """Convert from coordinates between 0 and 1 to hex notation."""
    return "#" + "".join(f"{round(v*255):0>2x}" for v in coordinates)

def hex_to_lch(s):
    """Convert from hex notation to LCh-coordinates."""
    *rgb, _ = hex_to_float(s)
    return lab_to_lch(
        *linear_rgb_to_oklab(*map(srgb_nonlinear_transform_inverse, rgb)))

def lch_to_hex(L, C, h):
    """Convert from LCh-coordinates to hex notation."""
    return float_to_hex(list(map(srgb_nonlinear_transform,
                                 oklab_to_linear_rgb(*lch_to_lab(L, C, h)))))

def adjust_hue(base_color, x, absolute=False, lightness_control=None):
    """Adjust hue."""
    if absolute:
        h_f = lambda h, x: x
    else:
        h_f = lambda h, x: h + x
    if isinstance(base_color, str):
        L, C, h = hex_to_lch(base_color)
    else:
        L, C, h = base_color
    if lightness_control:
        base = lightness_control(h)
        h = h_f(h, x)
        L = L + lightness_control(h) - base
    else:
        h = h_f(h, x)
    if isinstance(base_color, str):
        return lch_to_hex(L, C, h) + base_color[7:]
    else:
        return L, C, h

def copy_hue(origin, hue_source):
    """Copy hue."""
    *rgb, _ = hex_to_float(hue_source)
    h, _, _ = colorsys.rgb_to_hls(*rgb)
    *rgb, a = hex_to_float(origin)
    _, l, s = colorsys.rgb_to_hls(*rgb)
    return float_to_hex(list(colorsys.hls_to_rgb(h, l, s)) + [a])

def interpolate(c1, c2, t, gamma=1):
    """Interpolate color coordinates (with gamma correction)."""
    if isinstance(c1, (int, float)):
        return interpolate([c1], [c2], t, gamma)[0]
    return [((1 - t)*v1**gamma + t*v2**gamma)**(1/gamma)
            for v1, v2 in zip(c1, c2)]

def mix(color1, color2, t, mode="oklab", alpha_mode="mix"):
    """Mix colors in a perceptual color space or otherwise."""

    *rgb1, a1 = color1
    *rgb2, a2 = color2

    if alpha_mode == "mix":
        a = interpolate(a1, a2, t)
    elif alpha_mode == "blend":
        alpha_a = a1*(1-t)
        a = 1 - (1 - alpha_a) * (1 - a2)
        t = a2*(1 - alpha_a)/a

    if mode.startswith("srgb"):
        gamma = (mode + " 1").split()[1]
        rgb = interpolate(rgb1, rgb2, t, gamma=float(gamma))
    elif mode == "linear rgb":
        rgb1 = map(srgb_nonlinear_transform_inverse, rgb1)
        rgb2 = map(srgb_nonlinear_transform_inverse, rgb2)
        rgb = interpolate(rgb1, rgb2, t)
        rgb = list(map(srgb_nonlinear_transform, rgb))
    elif mode == "oklab":
        rgb1 = map(srgb_nonlinear_transform_inverse, rgb1)
        rgb2 = map(srgb_nonlinear_transform_inverse, rgb2)
        rgb1 = linear_rgb_to_oklab(*rgb1)
        rgb2 = linear_rgb_to_oklab(*rgb2)
        rgb = interpolate(rgb1, rgb2, t)
        rgb = oklab_to_linear_rgb(*rgb)
        rgb = list(map(srgb_nonlinear_transform, rgb))
    else:
        raise ValueError("Invalid mode.")

    return rgb + [a]

def opacify(color, background="#FFFFFF"):
    """Remove transparency."""
    return float_to_hex(mix(hex_to_float(color),
                            hex_to_float(background),
                            t=0,
                            mode="srgb",
                            alpha_mode="blend"))[:7]

def multiply_saturation(color, factor):
    """Adjust saturation."""
    *rgb, _ = hex_to_float(color)
    h, l, s = colorsys.rgb_to_hls(*rgb)
    return float_to_hex(colorsys.hls_to_rgb(h, l, s*factor)) + color[7:]
