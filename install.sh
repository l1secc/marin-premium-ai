#!/usr/bin/env bash
# ============================================================================
#  Marin Premium · bootstrap
#
#  Omarchy deliberately never runs code from an installed theme:
#  `omarchy theme install <url>` clones the repo, keeps every colour/config
#  file, drops the handful of files that would run code, and applies the theme.
#  So this script is the one-time, idempotent setup that puts the photo
#  switcher (`marin-next`) and the background watcher (`marin-bg-watch`) on
#  your PATH, installs the systemd user service that keeps Omarchy's own
#  background picker in sync with the palette, and drops in a theme-set hook so
#  `omarchy theme update` / re-applying the theme keeps all of it current.
#
#  Usage:
#    install.sh              install switcher, watcher, service and hook
#    install.sh --no-hook    install only switcher, watcher and service
#    install.sh --no-service install switcher and watcher only
#    install.sh --uninstall  remove everything this installed
# ============================================================================
set -euo pipefail

THEME_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
THEME_NAME="$(basename -- "$THEME_DIR")"
BIN_DIR="${XDG_BIN_HOME:-$HOME/.local/bin}"
HOOK_DIR="$HOME/.config/omarchy/hooks/theme-set.d"
HOOK_FILE="$HOOK_DIR/marin-premium.hook"

WITH_HOOK=1
BOOTSTRAP_ARGS=()
for arg in "$@"; do
  case "$arg" in
    --no-hook) WITH_HOOK=0 ;;
    --no-service) BOOTSTRAP_ARGS+=(--no-service) ;;
    --uninstall) BOOTSTRAP_ARGS+=(--uninstall) ;;
    -h | --help) sed -n '3,18p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown option: $arg" >&2; exit 2 ;;
  esac
done

if ((${#BOOTSTRAP_ARGS[@]})) && [[ ${BOOTSTRAP_ARGS[0]} == "--uninstall" ]]; then
  rm -f "$HOOK_FILE"
  "$THEME_DIR/tools/marin-bootstrap" --uninstall
  echo "Removed $HOOK_FILE"
  exit 0
fi

# 1. Switcher + watcher + systemd service.
"$THEME_DIR/tools/marin-bootstrap" "${BOOTSTRAP_ARGS[@]+"${BOOTSTRAP_ARGS[@]}"}"

# 2. A theme-set hook keeps all of it fresh whenever the theme is re-applied
#    (this is the user-owned hook mechanism Omarchy provides; a theme repo is
#    not allowed to install it by itself).
if (( WITH_HOOK )); then
  mkdir -p "$HOOK_DIR"
  cat >"$HOOK_FILE" <<'HOOK'
#!/usr/bin/env bash
# Keep the Marin Premium switcher, watcher and service installed after the
# theme is (re)applied or updated.
[[ ${1:-} == marin-premium ]] || exit 0
theme_dir="$HOME/.config/omarchy/themes/marin-premium"
[[ -x $theme_dir/tools/marin-bootstrap ]] || exit 0
"$theme_dir/tools/marin-bootstrap" --quiet >/dev/null 2>&1 || true
HOOK
  chmod 755 "$HOOK_FILE"
  echo "✓ installed hook $HOOK_FILE"
fi

# 3. PATH check.
case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) echo "! note: $BIN_DIR is not on your PATH — add it to call 'marin-next' directly." >&2 ;;
esac

echo "Try:  marin-next  |  marin-next prev  |  marin-next sync  |  marin-next 6"
