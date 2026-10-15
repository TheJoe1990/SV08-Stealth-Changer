# 4. Deviations from upstream

Every file that started from an upstream project, its exact base commit, and the full diff:
[generated/upstream-map.md](generated/upstream-map.md). This page explains *what* changed and *why*,
grouped by area. File names are relative to `config/`.

## Printer base (from Rappetor SV08 Mainline)

- `printer.cfg`: Sovol toolhead, probe and extruder sections removed; the toolchanger files are
  included; Z current 0.3455 A → 0.65 A on all four Z motors; extruder TMC `interpolate` set the
  same (false) on every tool.
- `sovol-macros.cfg` (mostly rewritten):
  - `_START_PRINT`: initializes and verifies the toolchanger first; maps slicer tool numbers to physical
    tools (Mainsail tool mapping); QGL + adaptive mesh on T0 after the heatsoak; turns off every tool the
    print doesn't use; puts the other used tools at the slicer's **standby** temperature (from Orca's
    `Tn_IDLE_TEMP`) instead of leaving them at 125 °C; resets the tool change heat-wait timer.
  - `END_PRINT`: moves off the part, docks the tool only if the tool probe confirms it is on the shuttle,
    parks the empty shuttle at the back, prints the heat-wait summary and tool change counters.
  - `PAUSE`/`RESUME`/`CANCEL_PRINT`: a single definition each. Upstream and the toolchanger
    example both defined `RESUME`, and Klipper silently merges same-named sections, so Sovol's resume
    logic never ran. `CANCEL_PRINT` makes no movement and tears down the heatsoak.
  - Hard-coded T0/T1 blocks (fans, LEDs, runout sensors) replaced by loops over all tools; the runout
    check only checks the active tool.
- `options/lcd/*`: stock screen files, small fixes only.

## Toolchanger core (from klipper-toolchanger examples)

- `toolchanger/toolchanger.cfg`:
  - Pickup no longer waits in front of the dock for the tool to heat. The tool is picked up,
    carried back, and the wait happens at the prime tower (direct `TEMPERATURE_WAIT` on that tool's
    heater, so the Mainsail slicer→physical tool mapping can't redirect it).
  - Logs how long each change waited for heat (`_TC_WAIT_MARK`, printing only): one console line
    per change that actually waited, and an average per tool at the end of the print.
  - `TC_STATS`: tool change counters (total, failed, since last failure, best streak, per-tool
    success rate), saved to `variables.cfg` at print end / cancel / on a failure.
- `toolchanger/tool_detection.cfg`: a failed pickup outside a print raises a real error (upstream only
  paused, which does nothing outside a print, so the next command, e.g. homing + QGL, kept going with
  the wrong tool). During a print it pauses. Both paths count the failure first.
- `toolchanger/homing.cfg`: tool-less homing for an empty shuttle; Z home corrected for the active
  tool's offset (`ADJUST_Z_HOME_FOR_TOOL_OFFSET`); per-tool bed mesh.
- `toolchanger/toolhead_N.cfg`: LDO Nitehawk-36 pin file + tool section (dock position, tool probe,
  offsets, per-tool shaper params). T0 and T3 were rebuilt from T1 so all tools match.
- `toolchanger/tdp_dock_autotune.cfg`: staging move before the autotune (same X as the dock, safe Y,
  park Z − 20).
- `toolchanger/dock_tuner.cfg`: Contomo's dock tuner, adjusted for this printer.
- `tool_mapping.cfg` (new): Mainsail toolchanger panel macros (`SET_TOOL_MAPPING`, colors, materials,
  per-tool pressure advance, LOAD/UNLOAD per tool) and `M104`/`M109` wrappers that take slicer tool numbers.
- `tool_reassign.cfg` (new): **Tool map + manual endless spool** (Happy-Hare-style). `TC_MAP`
  (dashboard button, shown only while paused; the macro refuses otherwise) lists every slicer tool,
  its physical tool and optional backup tools. Several slicer tools may share one physical tool.
  Changing the slicer tool that is printing asks first, then swaps at the pause park spot (heat the
  new tool to the old one's temperature, swap, purge 20 mm, brush at print temperature, old tool off,
  optional resume). A runout pauses and offers that slicer tool's backups; nothing switches by itself.
  The `T<n>` macros record which slicer tool is printing; all runout paths call the offer.
  T2's Orbiter sensor called `T2_FILAMENT_RUNOUT`, a name Klipper cannot register, so T2 runouts did
  nothing; it now calls `_ORBITER_RUNOUT`.
- `encoder_toolchange_grace.cfg` (new): encoder runouts are ignored for a short window after each
  pickup (the 10 mm push-in after a change can show no encoder pulse and falsely pause the print).

## Calibration (from klipper-toolchanger `calibrate-offsets.cfg`, mostly new)

- `toolchanger/tools_calibrate.cfg`:
  - `CALIBRATE_TOOL_OFFSETS` baselines T0 on the calibration pin, brushes each nozzle with KOMB,
    measures each tool against T0 and saves the offsets to `variables.cfg`.
  - Refuses to run without a QGL (runs QGL itself when called normally; the raw
    `TOOL_CALIBRATE_*` commands are wrapped and refuse). Same for the probe-offset calibration.
  - Sanity check: a new Z offset more than 0.03 mm from the saved one is rejected (old value kept,
    warning shown) unless `FORCE=1`. A dirty nozzle once produced a bad reading that made a tool print
    0.05 mm too low.
  - Only tools the print uses are calibrated (`TOOLS=`).
- `toolchanger/tc_shapers.cfg`: per-tool, per-axis input shapers, measured with each tool's own
  accelerometer and loaded on every tool change.
- `heater_power_distributor` plugin fix (see 03-software.md): PID tuning works with the distributor on.

## Print start / heatsoak

- `heatsoak.cfg`: our [universal heatsoak](https://github.com/TheJoe1990/Tuning-Instructions) (itself
  grown from Contomo's interruptible heatsoak example). Boss-specific `PRINTER_HEATSOAK_PARK` runs during
  the soak: toolchanger init, QGL with T0, and tool offset calibration when `TC_CALIBRATION_MODE` is on.
- `KAMP_Line_Purge_TC.cfg`, `KAMP_Smart_Park_TC.cfg`: ignore the `PRIME_TOWER_AREA` object (added so the
  adaptive mesh covers the prime tower); otherwise Smart Park landed at X-6 and broke the first tool select.
- `KOMB.cfg`: brushes with the *active tool's* heater (upstream assumed `extruder`).
- `QGL_Finder.cfg` (new): helper used while setting up QGL points.

## Spoolman

- `spoolman.cfg` (new): one Spoolman spool per tool; the active spool follows tool changes
  (also when `SELECT_TOOL` is called directly by start/heatsoak/load macros).

## Housekeeping

- `maybe_dead_tracker.cfg` (new): macros with no known caller count their own use instead of being deleted.

## Slicer

See [06-slicer.md](06-slicer.md): start G-code passes per-tool print and standby temperatures,
preheat, prime tower, and the Orca settings that are known to break toolchangers.
