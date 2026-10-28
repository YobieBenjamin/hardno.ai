"""make_logo.py: draw every hardno.ai logo file as plain SVG shapes.

The idea behind the logo:
  - The mark is a computer chip seen from above (a square body with four pins on each side) whose die,
    the part in the middle, is a red stop-sign octagon. Silicon that says no.
  - The wordmark is "hardno.ai" in IBM Plex Sans Condensed Bold, the same typeface the website uses for
    headlines, with "no" in signal red and ".ai" dimmed, so the eye reads HARD NO.

Why the letters are converted to outlines: an SVG that names a font only looks right on computers that
have that font. Turning each letter into a drawn shape (like tracing it) makes the logo identical
everywhere, from a browser tab to a slide, with nothing to install.

Run (from a folder where the font package is installed):
    npm install @fontsource/ibm-plex-sans-condensed
    pip install fonttools
    python3 make_logo.py
It writes into ./out:
    hardno-logo-on-dark.svg, hardno-logo-on-light.svg   mark plus wordmark, for dark or light backgrounds
    hardno-logo-on-dark-filled.svg                      the same with its own dark background
    hardno-mark-on-dark.svg, hardno-mark-on-light.svg   the chip mark alone
    favicon.svg                                         the mark on a dark rounded tile, for browser tabs
The PNG versions and the site's og.png are rendered from these SVGs separately.

All drawing happens on a 64 by 64 unit grid (the mark's box), then scaled.
"""
import math, os
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

# Colors, matching the website palette (assets/site.css):
INK_DARK_BG  = "#ECE9E2"   # off-white strokes and letters, for use on dark backgrounds
INK_LIGHT_BG = "#0B0C0E"   # near-black strokes and letters, for use on light backgrounds
ACCENT       = "#FF5B35"   # signal red: the octagon die and the word "no"
DIM_DARK_BG  = "#9A978F"   # the dimmed ".ai" on dark backgrounds
DIM_LIGHT_BG = "#5C5A55"   # the dimmed ".ai" on light backgrounds
BG           = "#0B0C0E"   # the dark tile behind the favicon and the filled logo

# The bold weight of IBM Plex Sans Condensed, from the @fontsource npm package (open font license).
FONT = "node_modules/@fontsource/ibm-plex-sans-condensed/files/ibm-plex-sans-condensed-latin-700-normal.woff"
os.makedirs("out", exist_ok=True)


def mark(ink, size=64, x0=0, y0=0):
    """Return the SVG shapes for the chip mark, drawn in a size by size box whose top left is (x0, y0)."""
    s = size / 64.0                       # scale from the 64 unit grid to the requested size
    t = lambda v: round(v * s, 2)         # scale one number, rounded so the files stay small
    # The chip body: a 38 unit square with slightly rounded corners, outlined, not filled.
    parts = [f'<rect x="{t(13)+x0}" y="{t(13)+y0}" width="{t(38)}" height="{t(38)}" rx="{t(4)}" fill="none" stroke="{ink}" stroke-width="{t(3.6)}"/>']
    # The pins: four short lines on each side, 8 units apart, starting 20 units in.
    for k in range(4):
        c = 20 + k * 8
        parts += [f'<line x1="{t(c)+x0}" y1="{t(3)+y0}" x2="{t(c)+x0}" y2="{t(11)+y0}" stroke="{ink}" stroke-width="{t(3.6)}" stroke-linecap="square"/>',    # top
                  f'<line x1="{t(c)+x0}" y1="{t(53)+y0}" x2="{t(c)+x0}" y2="{t(61)+y0}" stroke="{ink}" stroke-width="{t(3.6)}" stroke-linecap="square"/>',   # bottom
                  f'<line x1="{t(3)+x0}" y1="{t(c)+y0}" x2="{t(11)+x0}" y2="{t(c)+y0}" stroke="{ink}" stroke-width="{t(3.6)}" stroke-linecap="square"/>',    # left
                  f'<line x1="{t(53)+x0}" y1="{t(c)+y0}" x2="{t(61)+x0}" y2="{t(c)+y0}" stroke="{ink}" stroke-width="{t(3.6)}" stroke-linecap="square"/>']   # right
    # The die: a red octagon centered in the chip. Its 8 corners sit on a circle of radius 12.5, starting
    # at 22.5 degrees, which puts a flat edge on top like a real stop sign.
    r = 12.5
    pts = " ".join(f"{round((32 + r * math.cos(math.radians(22.5 + 45 * i))) * s + x0, 2)},{round((32 + r * math.sin(math.radians(22.5 + 45 * i))) * s + y0, 2)}" for i in range(8))
    parts.append(f'<polygon points="{pts}" fill="{ACCENT}"/>')
    return "\n".join(parts)


# Load the font once: its glyph shapes, the map from characters to glyphs, and its units per em
# (fonts are designed on their own grid, usually 1000 units tall, which we scale to pixels).
font = TTFont(FONT); gs = font.getGlyphSet(); cmap = font.getBestCmap(); upm = font["head"].unitsPerEm
asc = font["hhea"].ascent


def word(text, px, x, baseline, fill):
    """Trace `text` as outlines, `px` pixels per em, starting at x on the given baseline.

    Returns (svg paths, x position where the next letter would start), so words can be chained.
    The transform flips the letters vertically, because fonts measure up from the baseline and SVG measures down.
    """
    s = px / upm; out = []
    for ch in text:
        g = cmap[ord(ch)]; pen = SVGPathPen(gs)
        gs[g].draw(TransformPen(pen, (s, 0, 0, -s, x, baseline)))
        d = pen.getCommands()
        if d: out.append(f'<path d="{d}" fill="{fill}"/>')   # a space has no outline, so skip empty paths
        x += gs[g].width * s                                  # advance by the letter's designed width
    return "\n".join(out), x


def lockup(ink, dim, name, bg=None):
    """Write the full logo: mark on the left, wordmark to its right, 64 units tall. Returns its width."""
    H = 64; px = 46; base = 47            # height, letter size, and the baseline the letters sit on
    m = mark(ink, 64, 0, 0)
    a, x = word("hard", px, 78, base, ink)     # 78 units leaves a gap after the mark
    b, x = word("no", px, x, base, ACCENT)     # "no" in red
    c, x = word(".ai", px, x, base, dim)       # ".ai" dimmed
    W = round(x + 4)                           # width: where the text ends, plus a little breathing room
    back = f'<rect width="{W}" height="{H}" fill="{bg}"/>' if bg else ""
    # role="img" and aria-label let screen readers announce it as "hardno.ai"; <title> does the same for tooltips.
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W*4}" height="{H*4}" role="img" aria-label="hardno.ai">\n<title>hardno.ai</title>\n{back}\n{m}\n{a}\n{b}\n{c}\n</svg>\n'
    open(f"out/{name}", "w").write(svg); return W


# Write every variant.
w = lockup(INK_DARK_BG, DIM_DARK_BG, "hardno-logo-on-dark.svg")
lockup(INK_LIGHT_BG, DIM_LIGHT_BG, "hardno-logo-on-light.svg")
lockup(INK_DARK_BG, DIM_DARK_BG, "hardno-logo-on-dark-filled.svg", BG)
for name, ink in (("hardno-mark-on-dark.svg", INK_DARK_BG), ("hardno-mark-on-light.svg", INK_LIGHT_BG)):
    open(f"out/{name}", "w").write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="256" height="256" role="img" aria-label="hardno.ai"><title>hardno.ai</title>\n{mark(ink)}\n</svg>\n')
# Favicon: the mark on a dark rounded tile, so it reads at 16 pixels on any browser tab color.
open("out/favicon.svg", "w").write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="{BG}"/>\n{mark(INK_DARK_BG)}\n</svg>\n')
print("lockup width", w)
