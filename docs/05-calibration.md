# 5. Calibration order

Run these hot (bed at print temperature, chamber soaked) unless noted. Every tool needs its own pass.

1. **PID per hotend**: tool on the shuttle, part fan off, 250 °C: `PID_CALIBRATE HEATER=extruder<N> TARGET=250`.
   Requires the heater_power_distributor fix (03-software.md), or turn the distributor off first.
2. **Dock positions**: `DOCK_TUNER T=<n>` (popup, steps a slow pick/drop, writes `params_park_*`), then
   `TC_DOCK_AUTOTUNE` for fine X/Y. Re-home + QGL after any manual intervention.
3. **Tool probe Z offsets**: `TC_CALIBRATE_TOOL_PROBE_Z_OFFSETS` (runs QGL with T0 first if needed).
4. **Input shapers per tool**: `TC_SHAPER_CALIBRATE T=0,1,2,3` (each tool's own accelerometer).
   Analysis is heavy for the H616; expect it to take a while.
5. **Tool offsets (X/Y/Z vs T0)**: `CALIBRATE_TOOL_OFFSETS TOOLS=1,2,3`.
   - Clean nozzles first. Build-up the brush can't remove makes a tool read long and print too low.
     XY calibration touches the nozzle *sides*, so they must be clean too.
   - Refuses without QGL; rejects Z changes > 0.03 mm unless `FORCE=1`.
   - Clean runs repeat within about 0.01 mm.
   - The heatsoak runs it automatically when `TC_CALIBRATION_MODE` is enabled (resets to off on restart).
6. **Pressure advance per tool**: Orca PA Pattern (0-0.08, step 0.004); store it in `tool_mapping.cfg`
   `variable_pressure_advance` of that tool's `T<n>` macro. Re-run after speed/accel changes.
7. **Flow, max volumetric speed, shrinkage** per material in Orca. See 06-slicer.md for the shrinkage gotcha.
