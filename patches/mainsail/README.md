# Mainsail toolchanger integration: our patches

> **ALL MACROS, PATCHES AND DOCS IN THIS REPOSITORY, EVEN THOSE BASED ON REAL UPSTREAM PROJECTS, ARE
> MOSTLY VIBE-CODED. ALL KLIPPER EXPERTISE IS IMPERSONATED... POORLY.** Most of it was written with an AI
> assistant (Claude). The ideas, the hardware, the testing and the yelling at the AI when it got things
> wrong are human. It is checked only as far as one printer goes. THE FOLLOWING REPOSITORY CONTAINS COARSE
> G-CODE AND, DUE TO ITS CONTENT, SHOULD NOT BE FLASHED TO ANYONE'S PRINTER. Read it before you run it.
>
> **In testing. No maintenance commitment.** These patch the built bundle of
> [drakarah/mainsail v0.0.7](https://github.com/drakarah/mainsail/releases) (Mainsail 2.17.0 with the
> toolchanger panel). I'd much rather see them merged upstream than kept here; if you maintain the
> integration, take anything you like.

## Apply (on the printer, in this order)

```
python3 apply-fix.py ~/mainsail --with-pa     # 1-7
python3 apply-fix-tcstats.py ~/mainsail       # 8
python3 apply-fix-multicolor.py ~/mainsail    # 9
python3 apply-fix-spooltap.py ~/mainsail      # 10
```
Each script only writes if every pattern matches exactly once, keeps the original as `*.orig-<time>`,
and bumps the service-worker revision so browsers load the new file. They only fit the v0.0.7 bundle
(`assets/index-CCueyQmD.js`); a different build needs the changes ported.

## What they change

| # | Change | Kind |
|---|---|---|
| 1 | Start-print dialog reads `filament_type` as a JSON array (Moonraker since 2025-12-13); the Filament Assignment section had vanished | fix |
| 2 | Null-guard in `getTextColor` (no matching tool crashed the section) | fix |
| 3 | Pressure Advance box sends `SET_PRESSURE_ADVANCE EXTRUDER= ADVANCE=` (was `TOOL= VALUE=`, ignored) | fix |
| 4 | Picking a spool for a tool sets that tool's color and material | feature |
| 5 | LOAD opens the spool picker for that tool (only when Spoolman is usable, see 10) | feature |
| 6 | Start-print dialog hides the single-spool Spoolman section (spools are per tool) | option |
| 7 | "+ New spool" / "+ New brand or color" in the Change Spool dialog | feature |
| 8 | Start-print dialog shows tool change counters and per-tool success rate (needs `_TC_STATS` from `config/toolchanger/toolchanger.cfg`) | option |
| 9 | Multi-color Spoolman spools on tool cards and start-dialog buttons (coaxial = bands, longitudinal = gradient) | feature |
| 10 | Tapping a tool's spool opens its spool picker; "color" link keeps the color picker. Without Spoolman, or Spoolman unreachable, it behaves exactly like stock | feature |

Related Klipper-side features (no Mainsail patch needed): tool map + per-print endless spool backups
(`config/tool_reassign.cfg`, `TC_MAP` / `TC_BACKUPS`), tool change heat-wait timing (`_TC_WAIT_MARK`).

## Rolling it upstream

Suggested split for PRs against the integration's source: (1) fixes 1-3, (2) Spoolman per tool 4-6
and 10, (3) multi-color 9 (small on Mainsail 2.18, which already supports multi-color spools),
(4) stats 8 behind a documented variable convention. 7 fits stock Mainsail better.
