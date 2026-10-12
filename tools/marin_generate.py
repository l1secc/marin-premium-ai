#!/usr/bin/env python3
"""Marin Premium — per-photo theme generator.

Every photo in tools/photos.json becomes its own Omarchy theme:

    ~/.config/omarchy/themes/<slug>/
        colors.toml          # palette extracted from the photo (drives EVERYTHING:
                             #  terminals, btop, helix, neovim, vscode, claude, pi, ...)
                             #  background=black, foreground=photo pink↔red ink, and
                             #  surface_* = the photo-tinted desktop chrome values
        shell.toml           # bar / menu / launcher / lock surfaces (premium glass, retinted)
        waybar.css           # waybar parity (omarchy Quattro uses shell.toml, kept for parity)
        hyprland.conf        # legacy/non-Quattro Hyprland gradient + look & feel
        backgrounds/<file>.jpg  # 1920x1080 prepared wallpaper (cover crop + adaptive top scrim)
        .marin-photo.json    # provenance

The master theme (marin-premium) keeps its retint base under `tools/template/`
and only gets its default wallpaper refreshed.

Usage:
    python3 tools/marin_generate.py [--only SLUG] [--dry-run] [--skip-wallpaper]
"""

from __future__ import annotations

import argparse
import colorsys
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tomllib

HOME = os.path.expanduser("~")
THEMES_DIR = os.path.join(HOME, ".config", "omarchy", "themes")
# Derive the theme root from this file's location so the generator is portable
# (the master theme lives in ~/.config/omarchy/themes, this copy lives elsewhere).
MASTER_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_DIR = os.path.join(MASTER_DIR, "tools")
MANIFEST = os.path.join(TOOLS_DIR, "photos.json")
PALETTES_DIR = os.path.join(MASTER_DIR, "palettes")
# The retint base (classic palette + shell/waybar/hyprland templates) lives
# outside `palettes/` so it is never offered as a selectable photo. Every photo
# bundle is retinted from it by hex substitution.
CLASSIC_DIR = os.path.join(MASTER_DIR, "tools", "template")
BG_DIR = os.path.join(MASTER_DIR, "backgrounds")
MASTER_COLORS = os.path.join(CLASSIC_DIR, "colors.toml")
TEMPLATE_FILES = ("shell.toml", "waybar.css", "hyprland.conf")

# The terminal canvas is true black and its ink is plain white — that is what
# you type and what command output is drawn in. Marin's colour lives in the
# accents, the desktop chrome and the photo-tinted file-kind colours.
TERMINAL_BACKGROUND = "#000000"
TERMINAL_FOREGROUND = "#ffffff"

# Roles whose terminal value differs from the desktop value carry a `surface_*`
# twin in colors.toml holding the value the shipped desktop chrome was authored
# with (see desktop_view).
DESKTOP_TWINS = {
    "background": "surface_background",
    "foreground": "surface_foreground",
    "bright_foreground": "surface_bright_foreground",
    "muted": "surface_muted",
    "red": "surface_red",
    "blue": "surface_blue",
}
W, H = 1920, 1080
AR = W / H

# Canonical Marin ANSI hue anchors (degrees) used as the semantic skeleton that
# each photo is allowed to pull toward its own colours.
ANSI_ROLES = [
    ("red", 338.0, 0.62),
    ("yellow", 43.0, 0.72),
    ("green", 148.0, 0.68),
    ("cyan", 187.0, 0.70),
    ("blue", 224.0, 0.70),
    ("magenta", 335.0, 0.72),
]

# Roles the terminal keeps at a fixed, high-saturation Marin hue instead of
# being pulled to a dusty tone by the photo, so the red slot reads as Marin's
# rose-pink and the blue slot as a clear blue: (hue, saturation, lightness).
# The photo-pulled variant, at the role's own ANSI_ROLES hue and lightness,
# survives as surface_red / surface_blue for the desktop chrome.
TRUE_HUE_ROLES = {
    "red": (338.0, 0.85, 0.60),
    "blue": (224.0, 0.88, 0.55),
}

HEX_RE = re.compile(r"^#?([0-9a-fA-F]{6})$")


# --------------------------------------------------------------------------- #
# colour helpers
# --------------------------------------------------------------------------- #
def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def hex_rgb(hx: str) -> tuple[int, int, int]:
    hx = hx.lstrip("#")
    return int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16)


def rgb_hex(r: float, g: float, b: float) -> str:
    return "#%02x%02x%02x" % (
        int(round(clamp(r, 0, 255))),
        int(round(clamp(g, 0, 255))),
        int(round(clamp(b, 0, 255))),
    )


def to_hls(hx: str) -> tuple[float, float, float]:
    r, g, b = (c / 255 for c in hex_rgb(hx))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return h, l, s


def from_hls(h: float, l: float, s: float) -> str:
    r, g, b = colorsys.hls_to_rgb(h % 1.0, clamp(l, 0.0, 1.0), clamp(s, 0.0, 1.0))
    return rgb_hex(r * 255, g * 255, b * 255)


def hue_dist(a: float, b: float) -> float:
    d = abs((a - b) % 1.0)
    return min(d, 1.0 - d)


def rel_lum(hx: str) -> float:
    def chan(c: float) -> float:
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = hex_rgb(hx)
    return 0.2126 * chan(r) + 0.7152 * chan(g) + 0.0722 * chan(b)


def contrast(a: str, b: str) -> float:
    la, lb = rel_lum(a), rel_lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def lift_until_contrast(hx: str, bg: str, target: float, up: bool = True) -> str:
    h, l, s = to_hls(hx)
    for _ in range(60):
        if contrast(from_hls(h, l, s), bg) >= target:
            break
        l = clamp(l + (0.015 if up else -0.015), 0.06, 0.96)
    return from_hls(h, l, s)


def mix(a: str, b: str, amount: float) -> str:
    ar, ag, ab = hex_rgb(a)
    br, bg_, bb = hex_rgb(b)
    return rgb_hex(*(ca + (cb - ca) * amount for ca, cb in ((ar, br), (ag, bg_), (ab, bb))))


def rgb_triple(hx: str) -> str:
    r, g, b = hex_rgb(hx)
    return f"{r}, {g}, {b}"


# --------------------------------------------------------------------------- #
# image analysis
# --------------------------------------------------------------------------- #
def magick(*args: str) -> bytes:
    return subprocess.run(["magick", *args], capture_output=True, check=True).stdout


def identify(*args: str) -> str:
    return subprocess.run(["magick", "identify", *args], capture_output=True,
                          check=True).stdout.decode().strip()


def histogram(path: str, ncolors: int = 16) -> list[tuple[float, str]]:
    out = magick(
        f"{path}[0]", "-auto-orient", "-resize", "480x", "-alpha", "off",
        "-colors", str(ncolors), "-format", "%c", "histogram:info:-",
    ).decode("utf-8", "replace")
    rows: list[tuple[int, str]] = []
    for m in re.finditer(r"^\s*(\d+):\s*\([^)]*\)\s*#([0-9a-fA-F]{6})", out, re.M):
        rows.append((int(m.group(1)), "#" + m.group(2).lower()))
    total = sum(c for c, _ in rows) or 1
    return [(c / total, hx) for c, hx in rows]


def raw_pixels(path: str, width: int = 160) -> list[tuple[int, int, int]]:
    raw = magick(f"{path}[0]", "-auto-orient", "-resize", f"{width}x",
                 "-alpha", "off", "-depth", "8", "rgb:-")
    return [(raw[i], raw[i + 1], raw[i + 2]) for i in range(0, len(raw) - 2, 3)]


def luma(r: int, g: int, b: int) -> float:
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0


def analyse(path: str) -> dict:
    hist = histogram(path)
    px = raw_pixels(path)
    n = len(px)
    order = sorted(range(n), key=lambda i: luma(*px[i]))
    dark_band = order[int(0.05 * n):int(0.45 * n)] or order[:n]
    light_band = order[int(0.90 * n):] or order[-1:]

    def avg(idxs: list[int]) -> tuple[int, int, int]:
        return tuple(round(sum(px[i][c] for i in idxs) / len(idxs)) for c in range(3))  # type: ignore[return-value]

    dark = rgb_hex(*avg(dark_band))
    light = rgb_hex(*avg(light_band))
    brightness = sum(luma(*p) for p in px) / n

    vivid: list[dict] = []
    for weight, hx in hist:
        h, l, s = to_hls(hx)
        if l < 0.16 or l > 0.90 or s < 0.14 or weight < 0.012:
            continue
        vivid.append({"w": weight, "hx": hx, "h": h, "l": l, "s": s,
                      "score": weight * (0.35 + s)})
    vivid.sort(key=lambda v: v["score"], reverse=True)

    return {"hist": hist, "dark": dark, "light": light,
            "brightness": brightness, "vivid": vivid}


def pick_accents(vivid: list[dict], fallback_hue: float) -> list[dict]:
    chosen: list[dict] = []
    for item in vivid:
        if all(hue_dist(item["h"], c["h"]) > 0.085 for c in chosen):
            chosen.append(dict(item))
        if len(chosen) == 3:
            break
    while len(chosen) < 3:
        base = chosen[0] if chosen else {"h": fallback_hue, "s": 0.45, "l": 0.6, "score": 0.0,
                                         "hx": from_hls(fallback_hue, 0.6, 0.45)}
        rotate = (0.055, -0.075)[len(chosen) % 2]
        chosen.append({"h": (base["h"] + rotate) % 1.0, "s": base["s"] * 0.92,
                       "l": base["l"], "score": base["score"] * 0.9,
                       "hx": from_hls(base["h"] + rotate, base["l"], base["s"])})
    # primary prefers a warm (hair-gold) hue when one of the accents allows it
    rest = chosen[1:]
    warm = [c for c in rest if 0.02 <= c["h"] <= 0.17]
    primary = max(warm, key=lambda c: c["score"]) if warm else rest[0]
    secondary = next(c for c in rest if c is not primary)
    return [chosen[0], primary, secondary]


def pull_hue(canonical: float, sources: list[float], strength: float = 0.5,
             max_deg: float = 65.0) -> float:
    best = None
    for src in sources:
        d = hue_dist(src, canonical)
        if d <= max_deg / 360.0 and (best is None or d < best[0]):
            best = (d, src)
    if best is None:
        return canonical
    delta = ((best[1] - canonical + 0.5) % 1.0) - 0.5
    return (canonical + strength * delta) % 1.0


# --------------------------------------------------------------------------- #
# palette construction
# --------------------------------------------------------------------------- #
def photo_palette(path: str) -> dict[str, str]:
    a = analyse(path)
    dh, dl, ds = to_hls(a["dark"])
    accents = pick_accents(a["vivid"], dh)
    mood_sat = sum(v["s"] for v in a["vivid"][:5]) / max(1, len(a["vivid"][:5]))

    # ---- background family -------------------------------------------------
    # The terminal canvas is true black (`background`); the photo tint lives on
    # in `surface_background`, which drives the desktop chrome the theme ships
    # (bar / menu / launcher / lock) together with the generated editor themes.
    bg_h = dh if ds >= 0.12 else accents[0]["h"]
    bg_l = clamp(0.085 + 0.045 * a["brightness"], 0.085, 0.125)
    bg_s = clamp(0.18 + 0.30 * ds, 0.18, 0.42)

    surface_background = from_hls(bg_h, bg_l, bg_s)
    background = TERMINAL_BACKGROUND
    darker = from_hls(bg_h, bg_l * 0.55, bg_s * 0.95)
    bg_alt = from_hls(bg_h, bg_l * 0.75, bg_s * 0.98)
    surface = from_hls(bg_h, bg_l + 0.055, bg_s)
    dark_bg = from_hls(bg_h, bg_l + 0.035, bg_s * 1.05)
    lighter = from_hls(bg_h, bg_l + 0.09, bg_s * 1.10)

    # ---- foregrounds -------------------------------------------------------
    # `surface_*` keeps the pale paper-white the desktop chrome is authored
    # with; the terminal ink itself is computed below, once the ANSI roles are
    # known, as a tone between Marin's photo-pulled pink and red.
    fg_h = bg_h
    surface_foreground = from_hls(fg_h, 0.87, 0.10)
    surface_bright_foreground = from_hls(fg_h, 0.95, 0.04)
    light_fg = from_hls(fg_h, 0.79, 0.14)
    dark_fg = from_hls(fg_h, 0.55, 0.18)
    surface_muted = from_hls(fg_h, 0.46, 0.20)

    # ---- accents -----------------------------------------------------------
    def norm(acc: dict, target_l: float) -> str:
        l = clamp(0.55 * acc["l"] + 0.45 * target_l, 0.55, 0.84)
        s = clamp(acc["s"], 0.42, 0.80)
        return lift_until_contrast(from_hls(acc["h"], l, s), surface_background, 4.2)

    accent = norm(accents[0], 0.70)
    primary = norm(accents[1], 0.72)
    secondary = norm(accents[2], 0.72)

    # ---- ANSI matrix (semantic hues, pulled toward the photo) ---------------
    # Rose-pink and blue are the exception: the terminal keeps them at a fixed,
    # high-saturation Marin hue, so the theme's red slot reads as Marin's vivid
    # rose-pink and its blue as a clear blue. Their photo-pulled variants become
    # surface_red / surface_blue for the desktop chrome.
    sources = [c["h"] for c in accents] + [v["h"] for v in a["vivid"][:6]]
    sat = clamp(0.34 + 0.40 * mood_sat, 0.34, 0.66)
    ansi: dict[str, str] = {}
    surface_ansi: dict[str, str] = {}
    for role, deg, target_l in ANSI_ROLES:
        canonical = deg / 360.0
        if role in TRUE_HUE_ROLES:
            hue_deg, role_sat, col_l = TRUE_HUE_ROLES[role]
            h = hue_deg / 360.0
            bright = from_hls(h, col_l + 0.10, role_sat)
            surface_ansi[role] = lift_until_contrast(
                from_hls(pull_hue(canonical, sources), target_l, sat), surface_background, 4.8)
        else:
            role_sat, col_l = sat, target_l
            h = pull_hue(canonical, sources)
            bright = from_hls(h, target_l + 0.14, clamp(sat + 0.06, 0, 0.75))
        ansi[role] = lift_until_contrast(from_hls(h, col_l, role_sat), background, 4.8)
        ansi["bright_" + role] = lift_until_contrast(bright, background, 4.8)

    yellow_h = pull_hue(43.0 / 360.0, sources)
    orange = from_hls((yellow_h - 0.045) % 1.0, 0.72, sat * 0.85)
    brown = from_hls(yellow_h, 0.45, sat * 0.55)
    orange = lift_until_contrast(orange, background, 4.5)

    # ---- terminal ink ------------------------------------------------------
    # Plain white: the terminal's default foreground is what you type and what
    # command output is drawn in. The dim role (color8, comments) is a neutral
    # grey lifted until it reads on black. File listings no longer get the ink:
    # eza paints file and folder names from its own kind colours (see
    # eza/theme.yml), which is what makes folders red while the text stays white.
    foreground = TERMINAL_FOREGROUND
    bright_fg = TERMINAL_FOREGROUND
    muted = lift_until_contrast(mix(foreground, background, 0.5), background, 4.5)

    selection = mix(surface_background, accent, 0.30)

    p = {
        "background": background,
        "surface_background": surface_background,
        "surface_foreground": surface_foreground,
        "surface_bright_foreground": surface_bright_foreground,
        "surface_muted": surface_muted,
        "surface_red": surface_ansi["red"],
        "surface_blue": surface_ansi["blue"],
        "darker_background": darker,
        "dark_background": dark_bg,
        "lighter_background": lighter,
        "background_alt": bg_alt,
        "background_surface": surface,
        "foreground": foreground,
        "bright_foreground": bright_fg,
        "light_foreground": light_fg,
        "dark_foreground": dark_fg,
        "muted": muted,
        "accent": accent,
        "primary": primary,
        "secondary": secondary,
        "selection": selection,
        "selection_background": selection,
        "selection_foreground": bright_fg,
        "cursor": bright_fg,
        "hyprland_active_border": f"rgba({accent[1:]}ee) rgba({secondary[1:]}ee) rgba({primary[1:]}ee) 45deg",
        "hyprland_inactive_border": f"rgba({surface_muted[1:]}aa)",
        "red": ansi["red"],
        "yellow": ansi["yellow"],
        "orange": orange,
        "green": ansi["green"],
        "cyan": ansi["cyan"],
        "blue": ansi["blue"],
        "magenta": ansi["magenta"],
        "brown": brown,
        "bright_red": ansi["bright_red"],
        "bright_yellow": ansi["bright_yellow"],
        "bright_green": ansi["bright_green"],
        "bright_cyan": ansi["bright_cyan"],
        "bright_blue": ansi["bright_blue"],
        "bright_magenta": ansi["bright_magenta"],
        "color0": background,
        "color1": ansi["red"],
        "color2": ansi["green"],
        "color3": ansi["yellow"],
        "color4": ansi["blue"],
        "color5": ansi["magenta"],
        "color6": ansi["cyan"],
        "color7": foreground,
        "color8": muted,
        "color9": ansi["bright_red"],
        "color10": ansi["bright_green"],
        "color11": ansi["bright_yellow"],
        "color12": ansi["bright_blue"],
        "color13": ansi["bright_magenta"],
        "color14": ansi["bright_cyan"],
        "color15": bright_fg,
    }
    return p


def min_contrast(p: dict[str, str]) -> float:
    return min(contrast(p[k], p["background"]) for k in contrast_keys(p))


def contrast_keys(p: dict[str, str]) -> list[str]:
    return (["foreground", "bright_foreground", "light_foreground",
             "accent", "primary", "secondary"]
            + [r for r, _, _ in ANSI_ROLES]
            + ["bright_" + r for r, _, _ in ANSI_ROLES])


def contrast_report(p: dict[str, str]) -> dict[str, float]:
    bg = p["background"]
    vals = {k: contrast(p[k], bg) for k in contrast_keys(p)}
    ansi = [v for k, v in vals.items() if k in (r for r, _, _ in ANSI_ROLES)
            or k.startswith("bright_")]
    fg = [vals["foreground"], vals["bright_foreground"], vals["light_foreground"]]
    accents = [vals["accent"], vals["primary"], vals["secondary"]]
    worst = min(vals.items(), key=lambda kv: kv[1])
    return {"ansi": round(min(ansi), 2), "fg": round(min(fg), 2),
            "accent": round(min(accents), 2), "worst": round(worst[1], 2),
            "worst_key": worst[0]}


# --------------------------------------------------------------------------- #
# file rendering
# --------------------------------------------------------------------------- #
COLORS_HEADER = """# ============================================================================
#  Marin Kitagawa — "Marin Premium" · {title}
#  Photo-derived palette · generated by tools/marin_generate.py
#
#  Source photo: {src}
#  The photo drives one palette; each surface then takes the part it needs:
#    · background is true black — the terminal canvas — and foreground is plain
#      white: what you type and what command output is drawn in
#    · file and folder names are painted by eza's kind colours (eza/theme.yml),
#      not by the ink, so folders read Marin rose-pink while the text stays white
#    · rose-pink and blue keep their fixed hue instead of following the photo
#    · surface_* keeps the photo-tinted desktop chrome (bar / menu / launcher /
#      lock) the theme ships, retinted by tools/marin_generate.py
#    · the remaining accents keep Marin's rose/gold/lilac roles, photo-pulled
# ============================================================================
"""

SECTION_THEME = """
# ---------------------------------------------------------------------------
#  THEME · core surface + accent tokens
# ---------------------------------------------------------------------------
"""
SECTION_COLORS = """
# ---------------------------------------------------------------------------
#  COLORS · semantic palette (syntax-highlight friendly)
# ---------------------------------------------------------------------------
"""
SECTION_ANSI = """
# ---------------------------------------------------------------------------
#  ANSI 0-15 · terminal color matrix
# ---------------------------------------------------------------------------
"""

TOKEN_ORDER = [
    "mode",
    "background", "surface_background",
    "darker_background", "dark_background", "lighter_background",
    "background_alt", "background_surface",
    "foreground", "surface_foreground", "bright_foreground", "surface_bright_foreground",
    "light_foreground", "dark_foreground", "muted", "surface_muted",
    "surface_red", "surface_blue",
    "accent", "primary", "secondary",
    "selection", "selection_background", "selection_foreground", "cursor",
    "hyprland_active_border", "hyprland_inactive_border",
]


def render_colors_toml(p: dict[str, str], title: str, src: str) -> str:
    out = [COLORS_HEADER.format(title=title, src=src)]
    out.append('mode = "dark"')
    out.append(SECTION_THEME)
    for key in TOKEN_ORDER:
        if key == "mode":
            continue
        out.append(f'{key:<24} = "{p[key]}"')
    out.append(SECTION_COLORS)
    for key in ["red", "yellow", "orange", "green", "cyan", "blue", "magenta", "brown",
                "bright_red", "bright_yellow", "bright_green", "bright_cyan",
                "bright_blue", "bright_magenta"]:
        out.append(f'{key:<16} = "{p[key]}"')
    out.append(SECTION_ANSI)
    for key in [f"color{i}" for i in range(16)]:
        out.append(f'{key:<8} = "{p[key]}"')
    return "\n".join(out) + "\n"


def master_tokens() -> dict[str, str]:
    tokens: dict[str, str] = {}
    path = MASTER_COLORS if os.path.exists(MASTER_COLORS) else os.path.join(MASTER_DIR, "colors.toml")
    for line in open(path, encoding="utf-8"):
        m = re.match(r'^\s*([A-Za-z0-9_]+)\s*=\s*"([^"]+)"', line)
        if m:
            tokens[m.group(1)] = m.group(2)
    return tokens


def desktop_view(palette: dict[str, str]) -> dict[str, str]:
    """The palette as the shipped desktop chrome sees it.

    shell.toml / waybar.css / hyprland.conf are authored in the classic palette
    and retinted by hex substitution. Swapping each role back to its `surface_*`
    twin keeps the bar, menu, launcher and lock photo-tinted while the terminal
    canvas stays black.
    """
    view = dict(palette)
    for role, twin in DESKTOP_TWINS.items():
        if twin in view:
            view[role] = view[twin]
    for twin in DESKTOP_TWINS.values():
        view.pop(twin, None)
    return view


def substitute(text: str, old: dict[str, str], new: dict[str, str]) -> str:
    """Retint a master config by swapping palette values, keeping all styling."""
    pairs = [(old[k], new[k]) for k in old if k in new and HEX_RE.match(old[k])
             and old[k].lower() != new[k].lower()]
    # longest first so #aabbcc is handled before bare aabbcc
    for oldv, newv in sorted(pairs, key=lambda kv: -len(kv[0])):
        text = re.sub(re.escape(oldv), newv, text, flags=re.I)
        bare_old, bare_new = oldv.lstrip("#"), newv.lstrip("#")
        text = re.sub(rf"rgba\({re.escape(bare_old)}([0-9a-fA-F]{{0,2}})\)",
                      rf"rgba({bare_new}\1)", text, flags=re.I)
        text = re.sub(rf"(?<![0-9a-fA-F]){bare_old}(?![0-9a-fA-F])", bare_new, text, flags=re.I)
        text = re.sub(rf"rgba\(\s*({re.escape(rgb_triple(oldv))})\s*,",
                      f"rgba({rgb_triple(newv)},", text)
        text = re.sub(rf"rgb\(\s*({re.escape(rgb_triple(oldv))})\s*\)",
                      f"rgb({rgb_triple(newv)})", text)
    return text


def retint_header(text: str, header: str) -> str:
    """Replace a master config's opening comment banner with a per-photo one."""
    block = re.match(r"^(?:#[^\n]*\n)+(?=\n?[^#])", text)
    if block:
        return header + text[block.end():]
    css = re.match(r"^/\*.*?\*/\n", text, re.S)
    if css:
        return header + text[css.end():]
    return header + text


def variant_header(kind: str, entry: dict, palette: dict[str, str]) -> str:
    title = entry["title"]
    if kind == "waybar.css":
        return (
            "/* ============================================================================\n"
            f"   Marin Kitagawa — \"Marin Premium\" · {title}  ·  Waybar\n"
            "   Retinted from the wallpaper palette by tools/marin_generate.py\n"
            f"   surface {palette['surface_background']} · accent {palette['accent']} · "
            f"primary {palette['primary']} · secondary {palette['secondary']}\n"
            "   ========================================================================= */\n"
        )
    return (
        "# ============================================================================\n"
        f"#  Marin Kitagawa — \"Marin Premium\" · {title}\n"
        f"#  Retinted from the wallpaper palette by tools/marin_generate.py\n"
        f"#  surface {palette['surface_background']} · accent {palette['accent']} · "
        f"primary {palette['primary']} · secondary {palette['secondary']}\n"
        "# ============================================================================\n"
    )


def write_variant(entry: dict, master: dict[str, str], palette: dict[str, str],
                  dry: bool) -> dict:
    """Write one photo's palette bundle into the single theme's palettes/ dir."""
    slug = entry["slug"]
    vdir = os.path.join(PALETTES_DIR, f"{entry['num']}-{slug}")
    actions: list[str] = []

    if dry:
        return {"slug": slug, "dir": vdir, "actions": ["(dry-run)"]}

    os.makedirs(vdir, exist_ok=True)

    # colors.toml is the single source of truth: omarchy regenerates every
    # terminal / editor / bar / menu template from it on theme set.
    with open(os.path.join(vdir, "colors.toml"), "w", encoding="utf-8") as fh:
        fh.write(render_colors_toml(palette, entry["title"], entry["src"]))
    actions.append("colors.toml")

    # Retint the tools/template/ base configs into this photo's palette.
    for name in TEMPLATE_FILES:
        src = os.path.join(CLASSIC_DIR, name)
        if not os.path.exists(src):
            continue
        text = substitute(open(src, encoding="utf-8").read(),
                          desktop_view(master), desktop_view(palette))
        text = retint_header(text, variant_header(name, entry, palette))
        with open(os.path.join(vdir, name), "w", encoding="utf-8") as fh:
            fh.write(text)
        actions.append(name)

    meta = {
        "num": entry["num"],
        "slug": slug,
        "theme": entry["name"],
        "title": entry["title"],
        "wallpaper": entry["file"] + ".jpg",
        "source": entry["src"],
        "source_root": entry["source_root"],
        "palette": {k: palette[k] for k in
                    ("background", "foreground", "accent", "primary", "secondary")},
        "generator": "tools/marin_generate.py",
    }
    with open(os.path.join(vdir, "meta.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2, ensure_ascii=False)
    actions.append("meta.json")
    return {"slug": slug, "dir": vdir, "actions": actions}


# --------------------------------------------------------------------------- #
# wallpaper preparation
# --------------------------------------------------------------------------- #
def dims(path: str) -> tuple[int, int]:
    out = identify("-format", "%w %h", "-quiet", f"{path}[0]").split()
    return int(out[0]), int(out[1])


def crop_geometry(sw: int, sh: int, focus: str) -> str:
    if sw / sh >= AR:
        cw, ch = int(round(sh * AR)), sh
        if focus.startswith("north") or focus.startswith("west"):
            x = 0
        elif focus.startswith("east"):
            x = sw - cw
        else:
            x = (sw - cw) // 2
        return f"{cw}x{ch}+{x}+0"
    ch = int(round(sw / AR))
    if focus == "center":
        y = (sh - ch) // 2
    else:
        frac = float(focus.split(":", 1)[1]) if ":" in focus else 0.0
        y = int(round(sh * frac))
    y = max(0, min(y, sh - ch))
    return f"{sw}x{ch}+0+{y}"


def prepare_wallpaper(src: str, out: str, focus: str, scrim_hex: str) -> dict:
    sw, sh = dims(src)
    geom = crop_geometry(sw, sh, focus)
    base = out + ".base.png"
    subprocess.run(["magick", f"{src}[0]", "-auto-orient", "-strip",
                    "-crop", geom, "+repage", "-resize", f"{W}x{H}",
                    "-modulate", "100,97,100", base], check=True)

    luma = float(identify("-format", "%[fx:mean]", "-quiet", base))
    top = float(subprocess.run(["magick", base, "-gravity", "north",
                                "-crop", f"{W}x{int(H*0.20)}+0+0", "+repage",
                                "-colorspace", "Gray", "-format", "%[fx:mean]",
                                "info:"], capture_output=True, check=True).stdout.decode().strip())
    alpha = clamp((top - 0.30) * 1.15, 0.0, 0.50)

    scrim = out + ".scrim.png"
    cmd = ["magick", base]
    if alpha > 0.02:
        r, g, b = hex_rgb(scrim_hex)
        subprocess.run(["magick", "-size", f"{W}x{int(H*0.34)}",
                        f"gradient:rgba({r},{g},{b},{alpha:.2f})-rgba({r},{g},{b},0)",
                        "-alpha", "set", scrim], check=True)
        cmd += [scrim, "-gravity", "north", "-composite"]
    cmd += ["-strip", "-define", "jpeg:dct-method=float", "-sampling-factor", "4:4:4",
            "-quality", "92", out]
    subprocess.run(cmd, check=True)
    for f in (base, scrim):
        if os.path.exists(f):
            os.remove(f)

    final_luma = float(identify("-format", "%[fx:mean]", "-quiet", out))
    return {"src": f"{sw}x{sh}", "crop": geom, "luma": round(luma, 3),
            "scrim": round(alpha, 2), "final": round(final_luma, 3),
            "kb": os.path.getsize(out) // 1024}


# --------------------------------------------------------------------------- #
# single-theme bundles: classic template + per-photo wallpapers
# --------------------------------------------------------------------------- #
def ensure_classic_bundle(dry: bool = False) -> None:
    """Snapshot the master configs as the retint base under tools/template/.

    Every photo bundle is retinted from these files, so they are captured once
    from the theme root and never shown in the switcher (which only scans
    `palettes/`).
    """
    if os.path.exists(os.path.join(CLASSIC_DIR, "colors.toml")) or dry:
        return
    os.makedirs(CLASSIC_DIR, exist_ok=True)
    for name in ("colors.toml",) + TEMPLATE_FILES:
        src = os.path.join(MASTER_DIR, name)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(CLASSIC_DIR, name))


def prepare_photo_wallpaper(entry: dict, scrim_hex: str, dry: bool) -> dict:
    """Crop the source photo to 1920x1080 into the theme's backgrounds folder."""
    src = os.path.join(os.path.expanduser(entry["source_root"]), entry["src"])
    out = os.path.join(BG_DIR, entry["file"] + ".jpg")
    result = {"slug": entry["slug"], "dir": BG_DIR, "actions": []}
    if dry:
        result["actions"].append("(dry-run)")
        return result
    os.makedirs(BG_DIR, exist_ok=True)
    wall = prepare_wallpaper(src, out, entry["focus"], scrim_hex)
    result["actions"].append(f"backgrounds/{os.path.basename(out)} ({wall['kb']}KB)")
    result["wallpaper"] = wall
    return result


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", action="append", default=[], help="slug(s) to build")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-wallpaper", action="store_true")
    ap.add_argument("--json-out", default="")
    args = ap.parse_args()

    manifest = json.load(open(MANIFEST, encoding="utf-8"))
    source_root = os.path.expanduser(manifest["source_root"])
    ensure_classic_bundle(args.dry_run)
    master = master_tokens()
    report: list[dict] = []

    for entry in manifest["photos"]:
        entry["source_root"] = manifest["source_root"]
        if args.only and entry["slug"] not in args.only:
            continue
        src = os.path.join(source_root, entry["src"])
        if not os.path.exists(src):
            print(f"!! missing source: {src}", file=sys.stderr)
            continue

        if entry["palette"] == "classic":
            info = prepare_photo_wallpaper(entry, "#0f1522", args.dry_run)
            info["palette"] = "classic"
            if not args.dry_run:
                with open(os.path.join(CLASSIC_DIR, "meta.json"), "w", encoding="utf-8") as fh:
                    json.dump({"num": entry["num"], "slug": entry["slug"],
                               "theme": entry["name"], "title": entry["title"],
                               "wallpaper": entry["file"] + ".jpg",
                               "source": entry["src"], "source_root": entry["source_root"]},
                              fh, indent=2, ensure_ascii=False)
            report.append(info)
            print(f"{entry['slug']:28} classic palette · {', '.join(info['actions'])}")
            continue

        palette = photo_palette(src)
        info = write_variant(entry, master, palette, args.dry_run)
        info["palette"] = "photo"
        info["contrast"] = contrast_report(palette)
        info["swatch"] = " ".join(palette[k] for k in
                                  ("background", "foreground", "accent", "primary", "secondary",
                                   "green", "blue"))

        if not args.dry_run and not args.skip_wallpaper:
            info["wallpaper"] = prepare_photo_wallpaper(entry, palette["surface_background"], args.dry_run)
            info["actions"].extend(info["wallpaper"]["actions"])

        report.append(info)
        wall = info.get("wallpaper", {}).get("wallpaper", {})
        print(f"{entry['slug']:28} bg={palette['background']} accent={palette['accent']} "
              f"primary={palette['primary']} secondary={palette['secondary']} "
              f"ansi>={info['contrast']['ansi']} fg>={info['contrast']['fg']} "
              f"acc>={info['contrast']['accent']} dim={info['contrast']['worst_key']}:{info['contrast']['worst']} "
              f"{('mean=' + str(wall.get('final'))) if wall else ''}")

    if args.json_out and not args.dry_run:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=1, ensure_ascii=False)
    print(f"\n{len(report)} theme(s) processed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
