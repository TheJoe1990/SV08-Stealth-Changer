# SV08 Toolchanger ("the Boss")

A Sovol SV08 converted into a 4-tool toolchanger (built for up to 6), running mainline
Klipper with the TapChanger shuttle, the klipper-toolchanger plugin, and LDO Nitehawk-36
toolboards. This repo documents everything needed to reproduce it, and every place
we deviated from the pre-made projects it is built on.

> **ALL MACROS, PATCHES AND DOCS IN THIS REPOSITORY, EVEN THOSE BASED ON REAL UPSTREAM PROJECTS, ARE
> MOSTLY VIBE-CODED. ALL KLIPPER EXPERTISE IS IMPERSONATED... POORLY.** Most of it was written with an AI
> assistant (Claude). The ideas, the hardware, the testing and the yelling at the AI when it got things
> wrong are human. It is checked only as far as one printer goes. THE FOLLOWING REPOSITORY CONTAINS COARSE
> G-CODE AND, DUE TO ITS CONTENT, SHOULD NOT BE FLASHED TO ANYONE'S PRINTER. Read it before you run it.
>
> **Status: in testing.** This is one person's working printer, shared as-is. I make no commitment
> to maintain this repo or support anyone's build. I would love to see these changes rolled into the
> upstream projects (klipper-toolchanger, the toolchanger Mainsail integration, KOMB, KAMP) so nobody
> has to carry a fork. Issues and PRs here may not get a reply.

**Status (2026-10-12):** T0-T3 built and printing multi-material (PLA, ABS, ASA, PETG
supports). T4/T5 not built. Open items are in [docs/07-known-issues.md](docs/07-known-issues.md).

## How to use this repo

1. **Hardware**: [docs/01-hardware.md](docs/01-hardware.md) lists the base printer, the toolchanger
   mechanics, the tools and the printed parts, and what was changed on each.
2. **Electronics + firmware**: [docs/02-electronics-and-firmware.md](docs/02-electronics-and-firmware.md).
3. **Software**: [docs/03-software.md](docs/03-software.md) gives the install order and the exact
   commit of every component (see [docs/generated/versions.md](docs/generated/versions.md)).
4. **Config**: `config/` is a snapshot of the printer's `~/printer_data/config` (secrets and LAN
   addresses scrubbed). Start from it, then change the per-machine values listed in
   [docs/03-software.md#per-machine-values](docs/03-software.md#per-machine-values).
5. **Calibrate** in the order in [docs/05-calibration.md](docs/05-calibration.md).
6. **Slice** with the presets in `slicer/orca/` ([docs/06-slicer.md](docs/06-slicer.md)).

## Where we deviated from upstream

- [docs/04-deviations.md](docs/04-deviations.md): every change, grouped by area, with the reason.
- [docs/generated/upstream-map.md](docs/generated/upstream-map.md): each config file, the upstream file
  and commit it came from, how much of it is still upstream, and a link to the full diff in
  `upstream-diffs/`.
- `patches/`: code changes outside the config (klipper-toolchanger plugin, Mainsail).

## Built on

| Project | Used for |
|---|---|
| [Sovol SV08](https://github.com/Sovol3d/SV08) | base printer |
| [Rappetor/Sovol-SV08-Mainline](https://github.com/Rappetor/Sovol-SV08-Mainline) | mainline Klipper conversion + base config |
| [viesturz/tapchanger](https://github.com/viesturz/tapchanger) | shuttle, tools, docks |
| [viesturz/klipper-toolchanger](https://github.com/viesturz/klipper-toolchanger) → [Contomo/klipper-toolchanger-hard](https://github.com/Contomo/klipper-toolchanger-hard) | Klipper plugin + example config (the printer runs the Contomo fork) |
| [LDO Nitehawk-36](https://github.com/MotorDynamicsLab/Nitehawk-36) | toolboards |
| [KAMP](https://github.com/kyleisah/Klipper-Adaptive-Meshing-Purging) | adaptive mesh, purge, smart park |
| [KOMB](https://github.com/TmRxJD/KOMB) | nozzle brushing |
| [drakarah/mainsail](https://github.com/drakarah/mainsail) | Mainsail with the toolchanger panel |
| [TheJoe1990/Tuning-Instructions](https://github.com/TheJoe1990/Tuning-Instructions) | heatsoak macro |
| Snapmaker Orca 2.3.5 | slicer |

## Keeping it current

```
cp tools/local.example.json tools/local.json   # once: printer SSH address + key (git-ignored)
tools/sync.py            # pull config from the printer, scrub, regenerate diffs + tables
tools/export_orca.py     # re-export the Orca presets listed in tools/orca_presets.txt
```
Upstream checkouts are cached in `.cache/` (git-ignored). If a file is re-based on a newer
upstream, update its row in `tools/upstream.tsv`.
