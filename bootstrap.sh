#!/usr/bin/env bash
# ============================================================================
#  Marin Premium · one-command install
#
#  Pulls the theme through Omarchy's own installer, then runs its bootstrap so
#  the photo switcher lands on your PATH. Run it without cloning first:
#
#    bash <(curl -fsSL https://raw.githubusercontent.com/l1secc/marin-premium-ai/master/bootstrap.sh)
#
#  Set MARIN_REPO to use a fork, MARIN_NO_BOOTSTRAP=1 to skip the bootstrap.
# ============================================================================
set -euo pipefail

REPO="${MARIN_REPO:-https://github.com/l1secc/marin-premium-ai.git}"
THEME_DIR="$HOME/.config/omarchy/themes/marin-premium"

# `omarchy theme install` removes any existing theme dir before cloning, so
# refuse to run from inside a checkout (that checkout is the thing it deletes).
self="${BASH_SOURCE[0]:-}"
if [[ -f $self ]]; then
  self_dir="$(cd -- "$(dirname -- "$self")" && pwd)"
  if [[ $self_dir == "$THEME_DIR" ]]; then
    echo "This is a local checkout. Run ./install.sh instead; it will not re-clone." >&2
    exit 1
  fi
fi

echo "Installing Marin Premium from $REPO …"
omarchy theme install "$REPO"

if [[ ${MARIN_NO_BOOTSTRAP:-0} != 1 && -x "$THEME_DIR/install.sh" ]]; then
  "$THEME_DIR/install.sh"
fi

echo
echo "Done. Open the desktop theme with:  omarchy theme set 'Marin Premium'"
