# 3. Software

Exact commits running on the printer: [generated/versions.md](generated/versions.md).

## Install order

1. **Mainline Klipper on the SV08**: follow [Rappetor/Sovol-SV08-Mainline](https://github.com/Rappetor/Sovol-SV08-Mainline)
   (Klipper, Moonraker, mainboard flash). Klipper on the printer: `v0.13.0-411-g938300f3c`.
2. **klipper-toolchanger**: the printer runs the Contomo fork
   ([Contomo/klipper-toolchanger-hard](https://github.com/Contomo/klipper-toolchanger-hard) @ `fbcd211`).
   Run its `install.sh`; it links its `klipper/extras/*.py` into `~/klipper/klippy/extras/`.
   Then apply our local plugin fix (below).
3. **Add-ons** (each from its own repo, versions in generated/versions.md): KAMP, KOMB (config files
   only), klipper-led_effect, klipper_tmc_autotune, Klippain Shake&Tune, klipper_auto_speed,
   moonraker-timelapse, crowsnest, Katapult.
4. **Mainsail with the toolchanger panel**: [drakarah/mainsail v0.0.7](https://github.com/drakarah/mainsail/releases)
   (Mainsail 2.17.0), then our patches (below).
5. **Config**: copy `config/` to `~/printer_data/config/`, change the [per-machine values](#per-machine-values).
6. **System files** from `system/` (below).
7. Flash the toolboards (02-electronics-and-firmware.md) and calibrate (05-calibration.md).

## Local patch: klipper-toolchanger plugin

`patches/klipper-toolchanger/local-changes.diff` (apply in `~/klipper-toolchanger` with `git apply`,
or `python3 patch_hpd.py <file>`), then `sudo systemctl restart klipper`. A FIRMWARE_RESTART does not
reload Python files.

- **heater_power_distributor.py**: after `PID_CALIBRATE`, the distributor re-read the heater's
  *clamped* max power (the idle minimum, ~0) as its new ceiling, so that heater could not heat
  again until a restart. PID/bang-bang heaters now always use their configured `max_power`.
  An update of the plugin repo drops this fix; re-apply it.

## Mainsail patches (`patches/mainsail/`)

Both scripts patch the minified v0.0.7 bundle in place, match every pattern exactly once or write
nothing, keep the original as `*.orig-<time>`, and bump the service-worker revision so browsers
fetch the new file.

```
python3 apply-fix.py ~/mainsail --with-pa
python3 apply-fix-tcstats.py ~/mainsail
```

| # | Change | Why |
|---|---|---|
| 1 | Start-print dialog parses `filament_type` as a JSON array (Moonraker ≥ 2025-12-13) | the Filament Assignment section silently disappeared |
| 2 | Null-guard `getTextColor` | same crash when no tool matched a filament |
| 3 | Pressure Advance box sends `SET_PRESSURE_ADVANCE EXTRUDER=… ADVANCE=…` | upstream sent params Klipper ignores |
| 4 | Picking a spool for a tool also sets that tool's color + material | one action instead of two |
| 5 | The panel's LOAD button opens the spool picker for that tool | spool assigned at load time |
| 6 | Start-print dialog hides the single-spool Spoolman section | spools are per tool on this printer |
| 7 | "+ New spool" / "+ New brand or color" form in the Change Spool dialog | create spools without opening Spoolman |
| 8 | Start-print dialog shows tool change counters + per-tool success rate | reliability at a glance |

## System files (`system/`)

| File | Install to | Purpose |
|---|---|---|
| `klipper.service.d-priority.conf` | `/etc/systemd/system/klipper.service.d/priority.conf` | Nice=-10 + realtime IO for Klipper (fewer "timer too close" on the H616) |
| `klipper-backup-restartwatch.{sh,service}`, `klipper-backup-onstart.{sh,service}` | `~/` and `/etc/systemd/system/` | push the config to GitHub after every Klipper start, never during a print (uses [klipper-backup](https://github.com/Staubgeborener/klipper-backup)) |

## Per-machine values

These are measured on this printer and must be redone on yours:

- `toolchanger/toolhead_N.cfg`: MCU serial IDs, dock position (`params_park_x/y/z`), tool probe `z_offset`,
  input shaper values.
- `printer.cfg` `#*#` SAVE_CONFIG block: PID values per hotend, bed mesh.
- `variables.cfg`: tool offsets (`offsets_tN`), shaper records, tool colors/materials, counters.
  Start from an empty file; the calibration macros fill it.
- `_KOMB_Variables.cfg`: brush position/size.
- `moonraker.conf`: Spoolman address (`<spoolman-host>`), trusted clients.
