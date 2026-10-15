# 6. Slicer (Snapmaker Orca 2.3.5)

Presets: `slicer/orca/` (list and parents in [../slicer/orca/presets.md](../slicer/orca/presets.md)).
They only store the settings that differ from Orca's built-in "Generic Klipper Printer" (MyKlipper)
system presets, so use the same Orca build or check the inherited values.

## Machine start G-code

`START_PRINT` gets, per used tool, the first-layer temperature and the standby temperature:

```
T<n>_TEMP={first_layer_temperature[n]}
T<n>_IDLE_TEMP={idle_temperature[n] == 0 ? nozzle_temperature[n] + standby_temperature_delta : idle_temperature[n]}
```
Standby is based on the *main* print temperature (not the first layer), so it matches what Orca
cools idle tools to during the print. Change `standby_temperature_delta` (currently −55) and the next
slice follows; nothing on the printer needs editing. `_PRIME_TOWER_AREA` is called first so the adaptive
mesh covers the prime tower.

## Settings that matter on this toolchanger

- **Ooze prevention on**, standby delta −55, **preheat time 1 s**: the incoming tool gets its print
  temperature right before the `T<n>` command; the printer waits at the prime tower if it isn't there yet.
  The console prints how long each change waited, and averages per tool at the end of the print. Use those
  to tune the delta and preheat time.
- **Prime tower on**. Do **not** use `wipe_tower_type: type1`: it crashes multi-extruder prints (OrcaSlicer
  issue #12128, still open).
- **Toolchange retraction**: 10 mm at 30 mm/s (filament presets).
- **Shrinkage compensation**: Orca only applies XY *and* Z shrinkage if every filament used in the print
  (support/interface filaments included) has the same `filament_shrink` and Z shrink values. Otherwise it
  silently applies none (warning only). Value = measured size as % of nominal.
- **PETG as support interface** for ASA/ABS (0 gap, 0 interface spacing) instead of model-built supports.
