# Marin Premium AI · Omarchy Theme

A professional, low eye-strain **dark mode** theme for [Omarchy](https://omarchy.org/) — Linux desktop, *inspired by* **Marin Kitagawa** from *My Dress-Up Darling* (*Sono Bisque Doll wa Koi wo Suru*).

It blends Marin's iconic character palette into a restrained, high-contrast "professional anime aesthetic" that stays comfortable in the terminal, IDE, and status bar all day.

---

## Color Story

| Source (canon)            | Token         | Hex       | Used as                          |
|---------------------------|---------------|-----------|----------------------------------|
| Hair (honey blonde)       | `primary`     | `#e8c98f` | Titles, focused states           |
| Eyes & makeup (rose pink) | `accent`      | `#f2a3c0` | Primary accent, focus borders    |
| Accessories (lilac)       | `secondary`   | `#bba7e6` | Info chips, links                |
| School uniform (deep navy)| `surface_background` | `#0f1522` | Bar / menu / launcher / lock cards |
| Terminal canvas           | `background`  | `#000000` | Terminal + editor background (true black) |
| Terminal ink              | `foreground`  | `#ffffff` | Terminal text — plain white |

Every palette ships both halves: the **photo-tinted desktop chrome**
(`surface_*`, used by `shell.toml`, `waybar.css` and `hyprland.conf`) and the
**black terminal canvas with plain white ink** (`background`, `foreground`,
`bright_foreground`, `muted`, driven straight into the terminal configs and the
live Foot OSC retint).

**Why "premium, low eye-strain":**
- The terminal is true black with **plain white ink** (`#ffffff`): what you
  type and what command output is drawn in. `eza`/`ls` paint file and folder
  names from their own kind colours instead (`eza/theme.yml`), so folders read
  **Marin rose-pink** while the text stays white.
- Terminal **rose-pink and blue stay at Marin's fixed hue** (`rose-pink
  #f04282` / `clear blue #4473f3`): the photo tints the rest of the ANSI matrix,
  but the red slot must read as Marin's vivid rose-pink and blue as blue. Their
  photo-pulled twins (`surface_red`, `surface_blue`) keep the desktop chrome's
  error and info hues dusty.
- Every ink sits at ≥ 7:1 contrast on black; every ANSI colour at ≥ 5.9:1.
- All accent colors are pulled ~10–15% toward warm/dusty to avoid LED glare.
- No pure white anywhere — only layered surfaces with depth.
- The active border is a **3-stop diagonal gradient** (pink → lilac → gold) flowing through Marin's full palette at 45°.

---

## Files

| File             | Purpose                                                                |
|------------------|------------------------------------------------------------------------|
| `colors.toml`    | **Active** palette (drives terminals, editors, bar, menus, lock screen) |
| `hyprland.conf`  | Active window manager: gradient border, blur, shadows, animations      |
| `shell.toml`     | Active Omarchy bar / OSD / launcher / menu / lock surfaces             |
| `waybar.css`     | Active Glassmorphism Waybar styles                                     |
| `backgrounds/`   | 10 AI wallpapers (1920×1080) — the theme's gallery                     |
| `palettes/`      | 10 palette bundles; `marin-next` copies one to the root on switch      |
| `tools/`         | `marin_generate.py` (palette generator), `marin-next` (photo switcher), `marin-bg-watch` (background watcher), `marin-bootstrap` (PATH + service install) |
| `systemd/`       | `marin-premium-bg-sync.service` — keeps Omarchy's own picker in sync   |

---

## One theme, all photos

All 10 wallpapers live under the **single** `marin-premium-ai` theme. Each photo
has a palette bundle in `palettes/<num>-<slug>/`; `marin-next` copies the chosen
bundle's `colors.toml` / `shell.toml` / `waybar.css` / `hyprland.conf` to the
theme root and re-applies the theme with `OMARCHY_THEME_SKIP_BACKGROUND=1`, so
Omarchy regenerates every terminal, editor, bar, menu, launcher and lock-screen
config from that photo's palette — and retints running Foot windows through
OSC — **without** touching the wallpaper. It then pins the matching wallpaper.

One roof holds everything: one theme entry, one gallery of 10 wallpapers, one
palette per photo.

| # | Title | Palette bundle |
|---|-------|----------------|
| 01 | Çiçek Mevsimi | `palettes/01-marin-ai-01-blossom` |
| 02 | Neon Gece | `palettes/02-marin-ai-02-neon` |
| 03 | Sonbahar | `palettes/03-marin-ai-03-autumn` |
| 04 | Kar | `palettes/04-marin-ai-04-snow` |
| 05 | Yıldızlı Gece | `palettes/05-marin-ai-05-starry` |
| 06 | Sınıf | `palettes/06-marin-ai-06-class` |
| 07 | Kafe | `palettes/07-marin-ai-07-cafe` |
| 08 | Festival | `palettes/08-marin-ai-08-festival` |
| 09 | Çiçek Tarlası | `palettes/09-marin-ai-09-flower` |
| 10 | Sahil | `palettes/10-marin-ai-10-beach` |

Switch photo + whole desktop palette together:

```bash
marin-next          # next photo: wallpaper + terminal ink + menu retinted
marin-next prev     # previous photo
marin-next 6        # jump to photo #6 (Deniz Esintisi)
marin-next kimono   # jump by name match
marin-next sync     # re-align palette with the current background
```

`Super + Alt + B` (and `Super + Alt + Shift + B` for the previous photo) runs
`marin-next` directly.

### Omarchy's own picker counts too

The stock background switcher — Omarchy menu → **Style → Background**, the image
picker, `omarchy theme bg next` — only swaps the wallpaper; it never re-applies
a theme. `~/.config/systemd/user/marin-premium-bg-sync.service` runs
`marin-bg-watch`, which watches Omarchy's current-background symlink and calls
`marin-next sync` whenever it points at a Marin photo. So a photo picked from
Omarchy's own menu retints the terminal, the bar and the menu as well.

`marin-next sync` is idempotent — when the staged palette already is the photo's
palette it does nothing — so the two paths never fight, and a wallpaper that
isn't part of the gallery (your own image, another theme) leaves the palette
alone.

```bash
systemctl --user status marin-premium-bg-sync    # is the watcher running?
systemctl --user restart marin-premium-bg-sync   # after editing the theme
~/.config/omarchy/themes/marin-premium/install.sh --uninstall   # remove it
```

> Keep `~/.config/omarchy/backgrounds/marin-premium/` for photos that have a
> matching bundle under `palettes/` only. A photo without a bundle has no
> palette to sync to, so the previous photo's colours stay on screen.

Regenerate the bundles and wallpapers after editing the retint base
(`tools/template/`) or the manifest (`tools/photos.json`):

```bash
python3 tools/marin_generate.py                 # all palettes + wallpapers
python3 tools/marin_generate.py --only marin-premium-09-glow
python3 tools/marin_generate.py --dry-run       # check palettes without writing
```

---

## Backgrounds

The single theme ships **10 AI wallpapers** in `backgrounds/`. Each is
1920×1080, cropped to 16:9 and given a photo-tinted top scrim so the bar stays
readable. The earlier near-black procedural `BG1–BG6` backgrounds were removed.

`marin-next` keeps the wallpaper and the palette in sync. Omarchy's own
`omarchy theme bg next` can cycle the gallery without retinting; run
`marin-next sync` afterwards to align the desktop with that wallpaper.

---

## ⚠️ A note on copyright

Marin Kitagawa's character design is the copyrighted work of **Shinichi Fukuda** (manga) and **CloverWorks** (anime). The colors in this theme are *inspired* by her design — color inspiration is not copying, but redistributing someone else's artwork under our name is.

**What this theme is:** the theme's *colors* and *config files* — our work. The photo
themes are a personal wallpaper set; the artwork belongs to its original creators and
is used locally for a personal desktop only, **not** for redistribution of the art.

If you want to add your own wallpaper to the gallery instead, see
[CREDITS.md](CREDITS.md) for the provenance of the bundled artwork and drop your
file in `backgrounds/`:

```bash
# Drop the file into the theme's backgrounds folder (PNG/JPG/WEBP works)
cp /path/to/your/licensed/marin-wallpaper.png \
   ~/.config/omarchy/themes/marin-premium/backgrounds/

# Or use Omarchy's per-theme background slot (does not modify the theme):
cp /path/to/your/licensed/marin-wallpaper.png \
   ~/.config/omarchy/backgrounds/marin-premium/

omarchy theme bg next    # cycle through backgrounds
```

---

## Install

### Through Omarchy's own theme installer (recommended)

```bash
omarchy theme install https://github.com/l1secc/marin-premium-ai.git
~/.config/omarchy/themes/marin-premium/install.sh
```

`omarchy theme install` clones the repo and applies the theme in one go. Because
Omarchy never runs code from a theme it installed, the second line is the
one-time bootstrap: it puts the photo switcher (`marin-next`) and the background
watcher (`marin-bg-watch`) on your PATH and starts the systemd user service that
keeps Omarchy's own background picker in sync with the palette. It is
idempotent, and a `theme-set` hook keeps all of it current after
`omarchy theme update` or a re-apply.

### One command (clone + apply + bootstrap)

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/l1secc/marin-premium-ai/master/bootstrap.sh)
```

### From a local checkout (development)

```bash
./install.sh
omarchy theme set "Marin Premium"
```

> Omarchy keeps a theme installed from a git repo colours-only: any `*.lua`, the
> terminal configs (`alacritty.toml`, `foot.ini`, `ghostty.conf`, `kitty.conf`)
> and `vscode.json` are dropped and regenerated from `colors.toml` instead.
> Everything else — `backgrounds/`, `palettes/`, `tools/` — is kept as written.

### Showing up in the Omarchy theme picker

The built-in picker reads the community list from
[omarchy-site](https://github.com/omacom/omarchy-site) `src/data/themes.json`.
Adding this theme there is a PR that pairs a 16:9 preview image under
`assets/themes/` with one entry:

```json
{ "repo": "https://github.com/l1secc/marin-premium-ai", "image": "/assets/themes/marin-premium.webp", "name": "Marin Premium" }
```

---

## Customization

### Tweak the terminal (black canvas, red ink)

The terminal canvas is `background` and the ink is `foreground` — the same true
red as the ANSI red, because file listings draw regular file names with it. To
change the ink, edit `photo_palette()` in `tools/marin_generate.py`:

```python
foreground = ansi["red"]           # ink = the true red
bright_fg  = ansi["bright_red"]    # cursor / bold / color15
muted = lift_until_contrast(mix(foreground, background, 0.5), background, 4.5)
```

Image file names (`*.jpg`, `*.webp`) are the ANSI **magenta** slot — Marin pink.
To make those red as well, pin magenta like red and regenerate:

```python
TRUE_HUE_ROLES = {
    "red":     (0.0, 0.88, 0.58),
    "blue":    (224.0, 0.88, 0.55),
    "magenta": (0.0, 0.88, 0.58),   # images render red too (color5 == color1)
}
```

`color5` then equals `color1`, and the desktop's selected-row text follows
`bright_magenta`, so add a `surface_bright_magenta` twin to `DESKTOP_TWINS` if
the chrome should keep its pink.

Red and blue ignore the photo on purpose — `TRUE_HUE_ROLES` holds their fixed
hue, saturation and lightness, and `lift_until_contrast` keeps them
at >= 4.8:1 on black:

```python
TRUE_HUE_ROLES = {
    "red":  (338.0, 0.85, 0.60),  # (hue°, saturation, lightness) → #f04282
    "blue": (224.0, 0.88, 0.55),  #                              → #4473f3
}
```

The desktop chrome keeps the photo tint through the `surface_*` twins
(`surface_background`, `surface_foreground`, `surface_bright_foreground`,
`surface_muted`, `surface_red`, `surface_blue`), which `tools/marin_generate.py`
substitutes into `shell.toml`, `waybar.css` and `hyprland.conf`. Terminal roles
and surface roles are independent: change `background` to tint the terminal,
change `surface_background` to tint the bar and menu.

Want the whole desktop black too? Point both at black in
`tools/template/colors.toml` and regenerate.

### Tweak the retint base

The root `colors.toml` is the *active* palette and is replaced on every
`marin-next` switch. To change the base every photo bundle is retinted from,
edit `tools/template/colors.toml` and the template configs beside it, regenerate
the bundles, then apply:

```bash
python3 tools/marin_generate.py     # retint all bundles from the base
marin-next 6                        # apply a photo bundle
```

### Adjust window animations

Edit `hyprland.conf` — all bezier curves are commented with intent. Save and Hyprland auto-reloads; check for errors with:

```bash
hyprctl configerrors
```

### Change the Waybar

Edit `waybar.css` — the file is fully tokenized with `@define-color` at the top. The bar reads this file on save; if Waybar doesn't, restart it with `omarchy restart waybar` (varies by setup).

### Add a wallpaper to the gallery

Drop any 1920×1080 (or higher) PNG/JPG/WEBP into `backgrounds/`, then add a
matching bundle under `palettes/` (or point `marin-next` at it). Cycle the
gallery with `Super + Alt + Space` → Style → Background, or:

```bash
omarchy theme bg next   # wallpaper only — the watcher syncs the palette
marin-next sync         # or retint the desktop to that wallpaper by hand
```

---

## License

[MIT](LICENSE)

This applies to the theme configuration and the colors. *Marin Kitagawa* is a copyrighted character; the colors are referenced under fair-use / nominative-fair-use for the sake of palette inspiration only. Wallpaper artwork remains the property of its original creators.