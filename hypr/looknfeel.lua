-- ============================================================================
--  Marin Premium — look'n'feel
--
--  Omarchy's default look is square and flat: decoration:rounding = 0, no
--  shadows, no blur. This is the softer, glassier Marin variant. It lives in
--  the sancttioned user override (~/.config/hypr/looknfeel.lua), loaded after
--  Omarchy's defaults, so package updates keep improving the defaults without
--  touching it.
--
--  Installed from the theme by tools/marin-bootstrap.
--
--  Two things worth knowing:
--    * The Omarchy shell mirrors decoration:rounding into its own
--      Style.cornerRadius, so this single value also softens the bar, menus,
--      launcher, notifications and OSD. It reads it on shell start and after a
--      theme is applied.
--    * Blur is what makes the translucent terminal (foot's own `alpha`, see
--      foot/marin-foot.ini) read as glass instead of mud.
-- ============================================================================

hl.config({
  decoration = {
    -- Soft, round corners — Marin's "premium" half, not the cute extreme.
    -- Tunable: 10 = subtle, 14 = this, 20 = bubbly.
    rounding = 14,
    -- 2 (default) is a plain circle corner; 3 is the softer squircle.
    rounding_power = 3,

    -- Diffused depth so rounded edges read as soft instead of cut out.
    shadow = {
      enabled = true,
      range = 24,
      render_power = 3,
      color = "rgba(1d0a12a6)",
      color_inactive = "rgba(1d0a1273)",
      offset = { 0, 2 },
    },

    -- Glassmorphism: what shows through a translucent surface is blurred.
    blur = {
      enabled = true,
      size = 6,
      -- 2 passes read the same as 3 for this radius and cost less per frame.
      passes = 2,
      noise = 0.0117,
      contrast = 1.0,
      brightness = 1.0,
      new_optimizations = true,
    },
  },
})
