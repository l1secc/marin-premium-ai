# Publishing Marin Premium in Omarchy

Omarchy's built-in theme picker lists community themes from the
[`omacom/omarchy-site`](https://github.com/omacom/omarchy-site) repo. Getting
listed is one pull request, and everything it needs lives in this folder.

## What the PR adds

1. **`assets/themes/marin-premium.webp`** — copy of `marin-premium.webp` here
   (16:9, 1920×1080, ~260 KB).
2. **One entry in `src/data/themes.json`** (keep the array sorted by `name`):

```json
{ "repo": "https://github.com/l1secc/marin-premium-ai", "image": "/assets/themes/marin-premium.webp", "name": "Marin Premium" }
```

## Steps

```bash
gh repo fork omacom/omarchy-site --clone --remote
cd omarchy-site
git checkout -b add-marin-premium
cp /path/to/marin-premium/distribution/marin-premium.webp assets/themes/
$EDITOR src/data/themes.json          # add the entry above, keep alphabetical
npm install && npm run build          # optional local check
git add assets/themes/marin-premium.webp src/data/themes.json
git commit -m "Add Marin Premium theme"
git push -u origin add-marin-premium
gh pr create --repo omacom/omarchy-site --title "Add Marin Premium theme" \
  --body "Marin Premium is a dark theme inspired by Marin Kitagawa, with 10 bundled SFW wallpapers and a photo-derived palette per wallpaper. Repo: https://github.com/l1secc/marin-premium-ai"
```

## Before submitting — checklist

- [x] `omarchy theme install <url>` works and applies the theme (verified).
- [x] Installed theme is colours-only: no Lua, no terminal configs, no
      `vscode.json`. Wallpapers, palettes and `tools/` are the only extras.
- [x] All 10 wallpapers are SFW (safe/sfw rated at the source, see `CREDITS.md`).
- [x] `preview.webp` is 16:9.
- [ ] Decide on the artwork: the bundled wallpapers are third-party fan art
      (see `CREDITS.md`). Omarchy accepts themes with bundled wallpapers, but if
      the maintainers ask for original/licensed art, swap `backgrounds/` for
      your own images and re-run `python3 tools/marin_generate.py`.

## Optional: match the naming convention

The docs recommend naming a theme repo `omarchy-<name>-theme`. The installer
strips that to `<name>`, so `omarchy-marin-premium-theme` installs as
`marin-premium` and lists as **Marin Premium** — same as the current repo name.
Renaming is cosmetic; if you rename the GitHub repo, update the URL in
`src/data/themes.json`.
