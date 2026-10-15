# 7. Known issues and open work (2026-10-12)

## Hardware
- T3: wrong PTFE tube; docking/undocking not reliable yet (pickup failures).
- T1 hotend LED dead.
- T2 still has the Orbiter filament sensor (to be removed); T3 has no runout sensor.
- T4/T5 not built.

## Brushing / offset calibration
- KOMB brushes at its own minimum temperature (219 °C), un-retracts 1 mm before brushing, makes one pass,
  and leaves the nozzle at that temperature, so offsets are measured hot with fresh ooze on the tip.
  Planned: retract instead, several hot passes, then keep wiping while cooling to the calibration
  temperature (part fan on), then probe at a controlled temperature.
- The stock silicone brush handles soft ooze but not baked-on residue on the nozzle sides, which the XY
  measurement touches. Consider brass, or a hard scraping edge.
- Test calibration temperature vs. material.

## Software
- Mid-print tool switching (`TC_MAP` / `TC_REASSIGN`) is built but not yet tested on a real print.
- Failed drop-offs (tool not seated in its dock) are not detected or counted.
- `T0`..`T3` are defined both in `toolchanger/toolhead_N.cfg` and `tool_mapping.cfg`. Klipper merges
  same-named sections silently; the later one (`tool_mapping.cfg`) wins.
- Klipper is a detached checkout with linked extras; updates need care (plugin + MCU firmware together).
