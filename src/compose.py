#!/usr/bin/env python3
"""One-day world-news digest image composer.

Usage: python3 src/compose.py <day-json-path> <output-png-path>

Reads a JSON spec (kicker, date_line, brief, six stories) and renders a
deterministic 1024x1024 PNG. No randomness, no timestamps: the same input
bytes always produce the same output bytes.
"""

import json
import math
import random
import sys

from PIL import Image, ImageDraw, ImageFont

FONT_DIR = "/usr/share/fonts/truetype/liberation/"
SERIF_BOLD = FONT_DIR + "LiberationSerif-Bold.ttf"
SANS_BOLD = FONT_DIR + "LiberationSans-Bold.ttf"
SANS_REG = FONT_DIR + "LiberationSans-Regular.ttf"

W = H = 1024
PAPER = (250, 247, 240)
INK = (18, 18, 20)
RED = (178, 30, 32)
GRAY = (92, 92, 96)
GOLD = (255, 196, 64)
WHITE = (255, 255, 255)

MARGIN = 28
RIGHT = 996
INNER_W = RIGHT - MARGIN  # 968


# ---------------------------------------------------------------- text tools

def font(path, size):
    return ImageFont.truetype(path, size)


def shrink_to_fit(path, text, start, minimum, max_width, step=1):
    """Largest size in [minimum, start] whose single line fits max_width."""
    size = start
    while size > minimum and font(path, size).getlength(text) > max_width:
        size -= step
    return size


def wrap_text(text, fnt, max_width):
    """Greedy word wrap; a lone over-long word is broken by characters."""
    lines = []
    for raw in text.split(" "):
        word = raw
        while fnt.getlength(word) > max_width and len(word) > 1:
            # carve off the longest fitting prefix of this word
            cut = len(word)
            while cut > 1 and fnt.getlength(word[:cut]) > max_width:
                cut -= 1
            lines.append(word[:cut])
            word = word[cut:]
        if lines and fnt.getlength(lines[-1] + " " + word) <= max_width:
            lines[-1] = lines[-1] + " " + word
        else:
            lines.append(word)
    return [ln for ln in lines if ln]


def draw_block(draw, x, y, lines, fnt, fill, leading):
    """Draw lines top-aligned at (x, y); return the y just past the block."""
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill, anchor="lt")
        y += leading
    return y


def star_points(cx, cy, r_out, r_in, points=5, rotate=-90.0):
    pts = []
    for i in range(points * 2):
        r = r_out if i % 2 == 0 else r_in
        ang = math.radians(rotate + i * 180.0 / points)
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    return pts


def burst(draw, cx, cy, r_out, r_in, color, spikes=12, seed=7):
    rng = random.Random(seed)
    pts = []
    for i in range(spikes * 2):
        base = r_out if i % 2 == 0 else r_in
        r = base * rng.uniform(0.85, 1.15)
        ang = math.radians(i * 180.0 / spikes)
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    draw.polygon(pts, fill=color)


# ---------------------------------------------------------------- illustrations
# Each painter receives a fresh draw on a layer exactly the size of its box.

def paint_nuke(d, w, h):
    navy = (10, 16, 48)
    d.rectangle([0, 0, w - 1, h - 1], fill=navy)
    rng = random.Random(20261126)
    for _ in range(46):
        x = rng.randint(2, w - 3)
        y = rng.randint(2, h - 3)
        r = rng.choice([1, 1, 2])
        d.ellipse([x - r, y - r, x + r, y + r], fill=(235, 235, 240))
    # dark ground strip along the bottom
    d.rectangle([0, h - 14, w - 1, h - 1], fill=(6, 9, 26))
    # radiation trefoil badge, upper-left
    cx, cy, r = 78, 66, 46
    yellow = (245, 197, 66)
    for centre in (270, 30, 150):
        d.pieslice([cx - r, cy - r, cx + r, cy + r],
                   start=centre - 30, end=centre + 30, fill=yellow)
    d.ellipse([cx - int(r * 0.42), cy - int(r * 0.42),
               cx + int(r * 0.42), cy + int(r * 0.42)], fill=navy)
    d.ellipse([cx - int(r * 0.20), cy - int(r * 0.20),
               cx + int(r * 0.20), cy + int(r * 0.20)], fill=yellow)
    # missile, centre-right, nose up
    mx = 700
    body_top, body_bot = 26, 96
    d.rectangle([mx - 9, body_top, mx + 9, body_bot], fill=(205, 205, 210))
    d.polygon([(mx - 9, body_top), (mx + 9, body_top), (mx, 6)], fill=RED)
    d.polygon([(mx - 9, body_bot - 18), (mx - 9, body_bot + 4),
               (mx - 26, body_bot + 8)], fill=RED)
    d.polygon([(mx + 9, body_bot - 18), (mx + 9, body_bot + 4),
               (mx + 26, body_bot + 8)], fill=RED)
    # flame below the missile
    d.polygon([(mx - 8, body_bot + 4), (mx + 8, body_bot + 4),
               (mx, body_bot + 34)], fill=(255, 140, 40))
    d.polygon([(mx - 4, body_bot + 4), (mx + 4, body_bot + 4),
               (mx, body_bot + 22)], fill=(255, 200, 60))


def paint_eu(d, w, h):
    d.rectangle([0, 0, w - 1, h - 1], fill=(0, 51, 153))
    cx, cy = w // 2, h // 2
    ring = min(w, h) // 2 - 16
    for k in range(12):
        ang = math.radians(-90 + k * 30)
        sx = cx + ring * math.cos(ang)
        sy = cy + ring * math.sin(ang)
        d.polygon(star_points(sx, sy, 11, 4.6), fill=(255, 204, 0))


def paint_riyadh(d, w, h):
    d.rectangle([0, 0, w - 1, h - 1], fill=(38, 44, 74))
    band = h * 2 // 3
    d.rectangle([0, band, w - 1, h - 1], fill=(214, 116, 52))
    black = (12, 12, 16)
    towers = [(8, 58, 22), (34, 92, 20), (58, 44, 24),
              (86, 68, 18), (108, 52, 22), (134, 38, 12)]
    for x, th, tw in towers:
        d.rectangle([x, h - th, x + tw, h - 1], fill=black)
    # antenna on the tallest tower
    d.line([(44, h - 92), (44, h - 104)], fill=black, width=2)
    # blast burst near the top of the tallest tower
    burst(d, 44, h - 100, 17, 8, (255, 176, 66), spikes=10, seed=11)
    d.ellipse([40, h - 104, 48, h - 96], fill=(255, 220, 120))
    # gray smoke puffs drifting to the right
    smoke = (128, 128, 134)
    for sx, sy, sr in [(62, h - 108, 7), (76, h - 112, 6), (90, h - 106, 5)]:
        d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=smoke)


def paint_sea(d, w, h):
    d.rectangle([0, 0, w - 1, h - 1], fill=(16, 84, 116))
    d.rectangle([0, 0, w - 1, h // 3], fill=(168, 205, 224))
    hull = (18, 22, 28)
    # warship silhouette, bow to the right
    d.polygon([(16, 88), (112, 88), (128, 98), (116, 108), (20, 108)],
              fill=hull)
    d.rectangle([58, 72, 96, 88], fill=hull)
    d.rectangle([72, 60, 80, 72], fill=hull)
    d.line([(76, 60), (76, 50)], fill=hull, width=3)
    # orange blast burst at the bow
    burst(d, 132, 84, 14, 7, (255, 150, 50), spikes=10, seed=23)
    d.ellipse([128, 80, 136, 88], fill=(255, 210, 90))
    # two small drone boats with white wakes, lower down
    wake = (232, 240, 245)
    for bx, by in [(28, 126), (72, 140)]:
        d.polygon([(bx, by), (bx + 16, by), (bx + 13, by + 5),
                   (bx + 3, by + 5)], fill=hull)
        d.line([(bx - 2, by + 3), (bx - 20, by + 3)], fill=wake, width=2)
        d.line([(bx - 2, by + 5), (bx - 14, by + 8)], fill=wake, width=2)


def paint_chip(d, w, h):
    d.rectangle([0, 0, w - 1, h - 1], fill=(14, 20, 16))
    # green chip square with pins, left side
    chip = (28, 148, 74)
    pin = (110, 220, 140)
    d.rectangle([16, 52, 66, 102], fill=chip)
    for py in (60, 72, 84):
        d.rectangle([9, py, 16, py + 6], fill=pin)
        d.rectangle([66, py, 73, py + 6], fill=pin)
    for px in (28, 40, 52):
        d.rectangle([px, 45, px + 6, 52], fill=pin)
        d.rectangle([px, 102, px + 6, 109], fill=pin)
    d.rectangle([24, 60, 58, 94], outline=(150, 230, 170), width=2)
    d.rectangle([34, 70, 48, 84], outline=(150, 230, 170), width=1)
    # red falling line chart ending in an arrowhead, right side
    pts = [(80, 58), (94, 76), (106, 68), (120, 94), (130, 86), (140, 116)]
    d.line(pts, fill=(220, 45, 45), width=3, joint="curve")
    (x1, y1), (x2, y2) = pts[-2], pts[-1]
    ang = math.atan2(y2 - y1, x2 - x1)
    tip = (x2 + 8 * math.cos(ang), y2 + 8 * math.sin(ang))
    perp = ang + math.pi / 2
    base1 = (x2 - 2 * math.cos(ang) + 6 * math.cos(perp),
             y2 - 2 * math.sin(ang) + 6 * math.sin(perp))
    base2 = (x2 - 2 * math.cos(ang) - 6 * math.cos(perp),
             y2 - 2 * math.sin(ang) - 6 * math.sin(perp))
    d.polygon([tip, base1, base2], fill=(220, 45, 45))


PAINTERS = {
    "nuke": paint_nuke,
    "eu": paint_eu,
    "riyadh": paint_riyadh,
    "sea": paint_sea,
    "chip": paint_chip,
}


def paint_into(img, box, key):
    """Render an illustration on its own layer clipped exactly to box."""
    x0, y0, x1, y1 = box
    layer = Image.new("RGB", (x1 - x0, y1 - y0))
    PAINTERS[key](ImageDraw.Draw(layer), x1 - x0, y1 - y0)
    img.paste(layer, (x0, y0))


# ---------------------------------------------------------------- layout

def headline_block(text, path, start, minimum, max_width, max_lines,
                   leading_factor):
    """Shrink-to-fit (single line) then wrap; returns (font, lines, leading).

    If the text still wraps past max_lines at the minimum size, keep
    shrinking below the minimum rather than ever cutting text off.
    """
    size = shrink_to_fit(path, text, start, minimum, max_width)
    fnt = font(path, size)
    lines = wrap_text(text, fnt, max_width)
    while len(lines) > max_lines and size > 8:
        size -= 1
        fnt = font(path, size)
        lines = wrap_text(text, fnt, max_width)
    return fnt, lines, int(round(size * leading_factor))


def fit_text_block(headline, sub, head_start, head_min, width, max_head_lines,
                   head_lead, sub_size, sub_lead, avail_h):
    """Headline + sub sized so the whole block fits avail_h pixels."""
    fnt, lines, lead = headline_block(headline, SANS_BOLD, head_start,
                                      head_min, width, max_head_lines,
                                      head_lead)
    size = fnt.size
    sub_fnt = font(SANS_REG, sub_size)
    sub_lines = wrap_text(sub, sub_fnt, width)[:2]  # subs never run past 2 lines
    total = len(lines) * lead + 4 + len(sub_lines) * sub_lead
    while total > avail_h and size > head_min:
        size -= 1
        fnt = font(SANS_BOLD, size)
        lines = wrap_text(headline, fnt, width)
        lead = int(round(size * head_lead))
        total = len(lines) * lead + 4 + len(sub_lines) * sub_lead
    return fnt, lines, lead, sub_fnt, sub_lines


def compose(spec):
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # ---- masthead ----
    kick = font(SANS_BOLD, 25)
    d.text((W // 2, 22), spec["kicker"], font=kick, fill=GRAY, anchor="mt")

    date_size = shrink_to_fit(SERIF_BOLD, spec["date_line"], 66, 40,
                              INNER_W, step=2)
    date_fnt = font(SERIF_BOLD, date_size)
    d.text((W // 2, 54), spec["date_line"], font=date_fnt, fill=INK,
           anchor="mt")

    d.rectangle([MARGIN, 138, RIGHT - 1, 143], fill=RED)
    d.rectangle([MARGIN, 150, RIGHT - 1, 152], fill=INK)

    stories = spec["stories"]
    lead, grid, strip = stories[0], stories[1:5], stories[5]

    # ---- lead panel ----
    d.rectangle([MARGIN, 166, RIGHT - 1, 477], fill=WHITE,
                outline=INK, width=3)
    paint_into(img, (MARGIN + 3, 169, RIGHT - 3, 325), lead["art"])
    art_bottom = 325
    text_x = MARGIN + 16
    text_w = RIGHT - MARGIN - 32  # 936
    avail = 475 - (art_bottom + 10)
    fnt, lines, lead_px, sub_fnt, sub_lines = fit_text_block(
        lead["headline"], lead["sub"], 43, 20, text_w, 3, 1.12,
        24, int(round(24 * 1.25)), avail)
    y = art_bottom + 10
    y = draw_block(d, text_x, y, lines, fnt, INK, lead_px)
    draw_block(d, text_x, y + 4, sub_lines, sub_fnt, GRAY,
               int(round(24 * 1.25)))

    # ---- grid of four cells ----
    cell_w, cell_h, gap = 477, 160, 14
    for i, story in enumerate(grid):
        cx = MARGIN + (i % 2) * (cell_w + gap)
        cy = 492 + (i // 2) * (cell_h + gap)
        d.rectangle([cx, cy, cx + cell_w - 1, cy + cell_h - 1],
                    fill=WHITE, outline=INK, width=3)
        paint_into(img, (cx + 3, cy + 3, cx + 151, cy + 157),
                   story["art"])
        tx = cx + 161
        tw = cx + cell_w - 3 - tx  # 313
        tag_fnt = font(SANS_BOLD, 17)
        d.text((tx, cy + 10), story["tag"], font=tag_fnt, fill=RED,
               anchor="lt")
        avail_c = (cy + 157) - (cy + 34)
        fnt, lines, lead_px, sub_fnt, sub_lines = fit_text_block(
            story["headline"], story["sub"], 26, 19, tw, 3, 1.14,
            19, int(round(19 * 1.22)), avail_c)
        y = cy + 34
        y = draw_block(d, tx, y, lines, fnt, INK, lead_px)
        draw_block(d, tx, y + 3, sub_lines, sub_fnt, GRAY,
                   int(round(19 * 1.22)))

    # ---- bottom strip ----
    d.rectangle([MARGIN, 826, RIGHT - 1, 903], fill=INK)
    mid_y = 826 + 39
    tag_fnt = font(SANS_BOLD, 24)
    tag_w = tag_fnt.getlength(strip["tag"])
    d.text((46, mid_y), strip["tag"], font=tag_fnt, fill=GOLD, anchor="lm")
    hx = 46 + int(tag_w) + 14
    hw = RIGHT - 14 - hx
    hsize = shrink_to_fit(SANS_BOLD, strip["headline"], 30, 20, hw)
    d.text((hx, mid_y), strip["headline"], font=font(SANS_BOLD, hsize),
           fill=WHITE, anchor="lm")

    # ---- brief line ----
    bsize = shrink_to_fit(SANS_REG, spec["brief"], 21, 16, INNER_W)
    d.text((MARGIN, 918), spec["brief"], font=font(SANS_REG, bsize),
           fill=GRAY, anchor="lt")

    return img


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: compose.py <day-json-path> <output-png-path>")
    with open(argv[1], "r", encoding="utf-8") as fh:
        spec = json.load(fh)
    img = compose(spec)
    img.save(argv[2], format="PNG")


if __name__ == "__main__":
    main(sys.argv)
