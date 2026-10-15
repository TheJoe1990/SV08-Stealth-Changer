# 2. Electronics + firmware

## MCUs (6 USB devices on the SV08's built-in H616 host)

| Name in config | Board | Chip | Connection |
|---|---|---|---|
| `mcu` | SV08 mainboard | STM32F103 | stock |
| `nest` | Birds' Nest (filament-sensor hub) | STM32G0B1 | USB |
| `T0`..`T3` | LDO Nitehawk-36 | RP2040 | USB, through a 7-port USB hub |

- The hub port order matches the dock order (port N = T(N-1)), so a tool board can be
  swapped by replugging into the same port. Serial IDs (`/dev/serial/by-id/usb-Klipper_rp2040_...`)
  are machine-specific: replace them in `config/toolchanger/toolhead_N.cfg`.
- CAN is not used. T0 was on CAN (EBB36) until 2026-10-03; a load-correlated fault and host
  load issues led to moving every tool to USB. Idle host load with all six MCUs is low
  (klippy ~7 % CPU); only input-shaper analysis pushes the H616 hard.
- Birds' Nest pins: encoders T0-T5 on PB4-PB9, switch sensors T0-T3 on TH1-TH4 (`config/nest.cfg`).

## Flashing the Nitehawk-36 boards

Nitehawks ship with Katapult already installed, so flashing is: jump to Katapult, then flash.

```
# ~/klipper/.config: RP2040, USB, 16 KiB bootloader offset (Katapult)
make -C ~/klipper
~/klippy-env/bin/python ~/katapult/scripts/flashtool.py -d /dev/serial/by-id/usb-Klipper_rp2040_<id>-if00 -r
~/klippy-env/bin/python ~/katapult/scripts/flashtool.py -f ~/klipper/out/klipper.bin -d /dev/serial/by-id/usb-katapult_rp2040_<id>-if00
```

Notes:
- `pullup_resistor: 2200` is required on the Nitehawk hotend thermistor (see toolhead configs).
- Klipper on the host is a detached checkout of `v0.13.0-411-g938300f3c`. Update it and the MCU
  firmware together, never one without the other.

## Heater power budget

All tools stay warm during a print, so the total heater draw is capped with Contomo's
`heater_power_distributor` (`config/toolchanger/heater_power_distributor.cfg`): budget 150 W,
per-tool ratings 60/60/40/40 W. The plugin has a local fix: see `patches/klipper-toolchanger/`.
