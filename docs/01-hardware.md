# 1. Hardware

Items marked **TODO (owner)** still need the builder to fill in (part source, quantity, print settings).

## Base printer: Sovol SV08

| | Stock SV08 | This build | Why |
|---|---|---|---|
| Firmware | Sovol's Klipper fork | mainline Klipper via [Rappetor/Sovol-SV08-Mainline](https://github.com/Rappetor/Sovol-SV08-Mainline) | needed for the klipper-toolchanger plugin |
| Toolhead | Sovol toolhead + eddy probe | TapChanger shuttle, 4 removable tools | toolchanger |
| Z probing | Sovol probe / eddy | per-tool TAP-style tool probe (every tool probes with its own nozzle) | each tool homes/probes itself |
| Z stepper current | 0.3455 A | 0.65 A (motor is rated 0.8 A, 42BYGH1603-A-20DNT) | more Z torque for the heavier shuttle + tools |
| Nozzle brush | stock Sovol (silicone) | stock Sovol brush, driven by KOMB | unchanged hardware; see the brushing notes in 07-known-issues |
| Exhaust fan | stock | not working / not used | |
| Chamber sensor | none | none (chamber temp estimated from the tool MCU temps) | owner decision 2026-10-04 |
| Lid / top | stock | **TODO (owner)**: TapChanger TopHat (`Top-Hat Top.3mf`)? Z height change? | dock clearance |

## Toolchanger mechanics: TapChanger

Shuttle, tool couplers and docks from [viesturz/tapchanger](https://github.com/viesturz/tapchanger)
(commit `c8d5cdb`, 2025-04-19, no local changes to the repo).

- Docks: fixed docks along the front of the frame, tools picked up by moving in Y.
  Dock positions per tool are in each `config/toolchanger/toolhead_N.cfg` (`params_park_x/y/z`),
  tuned with `DOCK_TUNER` + `TC_DOCK_AUTOTUNE` (see 05-calibration). Tool spacing is about 64.7 mm.
- Tool detection: each tool's TAP probe tells Klipper which tool is on the shuttle
  (`tool_probe_endstop`), checked after every pickup.
- Tool drop detection: accelerometer on each Nitehawk (`tool_drop_detection.cfg`).
- **TODO (owner)**: dock version, coupler version (`Coupler-v13`, `Coupler Core.stl`), any
  modifications to the TapChanger parts, umbilical routing (`PTFE Spring Umbilical Clip.3mf`).

## Tools (T0-T3 built, T4/T5 planned)

All four tools are the same apart from the heater:

| Part | Used | Notes |
|---|---|---|
| Toolboard | LDO Nitehawk-36, **USB** (not CAN) | T0 was an EBB36 on CAN until 2026-10-03; CAN removed (stability) |
| Extruder | Orbiter | |
| Hotend | E3D Revo | T0/T1 60 W heater cores, T2/T3 40 W |
| Cowl / mounts | `Cowl_Revo_OB2`, `Revo_Spacer`, `PCBMount`, `Yavoth_HF_PCB_Backplate`, `nitehawk36-sc-cover` | **TODO (owner)**: source of each part |
| Filament sensor | T0/T1 encoder (motion), T2 Orbiter filament sensor (to be removed), T3 none | encoders read by the Birds' Nest board |

## Printed parts

The print files live in the owner's NAS folder `Tool Changer/STLs and 3mfs` and are not yet in this
repo. **TODO (owner)**: add each part with source link, material, and print settings. Current list:

`20mm.stl`, `Assembly.3mf`, `Coupler Core.stl`, `Coupler-v13 (1).3mf`, `Cowl_Revo_OB2 (3).stl`,
`nitehawk36-sc-cover.stl` / `-v2.3mf` (wire hiders, printed in red/orange/yellow), `PCBMount (1).stl`,
`psu-120mm-fan-cover(1).3mf`, `sv08-120mm-low-profile-fan-mount(2).3mf`, `PTFE Saver.3mf`,
`PTFE Spring Umbilical Clip.3mf`, `Revo_Spacer (3).stl`, `SplitSock.3mf` (TPU), `T3_SFS_sled_BTT_SFS_2_Plate.stl`,
`Top-Hat Top.3mf`, `Yavoth_HF_PCB_Backplate.stl`.
