# hypr/

`looknfeel.lua` is the Marin Premium look'n'feel override — soft rounded
corners, diffused shadows and blur. `tools/marin-bootstrap` installs it to
`~/.config/hypr/looknfeel.lua` (the sanctioned user override, loaded after
Omarchy's defaults), keeping a `.pre-marin` backup of anything it replaces.

It lives here rather than being staged by Omarchy because a theme installed
from a git repo may not ship Lua: Omarchy drops `*.lua` on purpose, since Lua
runs code. The theme's own `hyprland.conf` is the pre-Quattro (legacy) path and
is unused by Omarchy's current Lua-based Hyprland config.

`foot/marin-foot.ini` next to it is the translucent-terminal block that gets
appended to `~/.config/foot/foot.ini` between managed markers.
