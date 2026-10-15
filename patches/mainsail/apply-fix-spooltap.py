#!/usr/bin/env python3
"""Patch #10 v2 (2026-10-12, user request) on top of boss-fix-8: Spoolman-aware tool cards that
still work exactly as before for printers without Spoolman.

"Spoolman usable" = Moonraker has the spoolman component AND Mainsail's Spoolman health is
"healthy" (so an installed-but-unreachable Spoolman also falls back).
  - Tapping a tool card's spool icon: Spoolman usable -> that tool's Change Spool dialog;
    otherwise -> the original color picker.
  - A small "color" link under the spool (only when Spoolman is usable) keeps the manual
    color picker one tap away.
  - The LOAD button only opens the spool picker (patch #5) when Spoolman is usable; the load
    command itself is always sent.

Usage: apply-fix-spooltap.py <mainsail_dir> [--dry-run]
"""
import shutil
import sys
import time
from pathlib import Path

BUNDLE = "assets/index-CCueyQmD.js"
SW = "sw.js"
U = '((e.$store.state.server.components||[]).includes("spoolman")&&e.$store.state.server.spoolman.health==="healthy")'
R = [
    ('on:{"click-spool":function(r){e.showColorPicker=!0}}',
     'on:{"click-spool":function(r){'+U+'?e.showSpoolDialog=!0:e.showColorPicker=!0}}',
     "tool card: spool tap opens spool picker (or color picker without Spoolman)"),
    (',t(ve,{attrs:{"close-on-content-click":!1,"offset-y":""},scopedSlots:e._u([{key:"activator",fn:function({on:r,attrs:i}){return[t("div",e._g(e._b({},"div",i,!1),r))]}}]),model:{value:e.showColorPicker,',
     ','+U+'?t("div",{staticClass:"text-caption text-center",staticStyle:{cursor:"pointer",opacity:"0.7","margin-top":"-8%"},'
     'on:{click:function(r){e.showColorPicker=!0}}},[e._v("color")]):e._e()'
     ',t(ve,{attrs:{"close-on-content-click":!1,"offset-y":""},scopedSlots:e._u([{key:"activator",fn:function({on:r,attrs:i}){return[t("div",e._g(e._b({},"div",i,!1),r))]}}]),model:{value:e.showColorPicker,',
     "tool card: manual color link"),
    ('e.showSpoolDialog=!0}',
     'if('+U+')e.showSpoolDialog=!0}',
     "load button: spool picker only with Spoolman"),
]
SW_OLD = '{url:"assets/index-CCueyQmD.js",revision:"boss-fix-8"}'
SW_NEW = '{url:"assets/index-CCueyQmD.js",revision:"boss-fix-10"}'


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        sys.exit(f"ABORT: '{label}' pattern found {n} times (need exactly 1). Nothing written.")
    return text.replace(old, new)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        sys.exit(__doc__)
    root = Path(args[0])
    dry = "--dry-run" in sys.argv
    bundle_p, sw_p = root / BUNDLE, root / SW
    bundle = bundle_p.read_text(encoding="utf-8")
    sw = sw_p.read_text(encoding="utf-8")
    if SW_NEW in sw:
        sys.exit("Already patched (sw.js has boss-fix-10). Nothing to do.")
    for old, new, label in R:
        bundle = replace_once(bundle, old, new, label)
    sw = replace_once(sw, SW_OLD, SW_NEW, "service worker revision")
    if dry:
        print("Dry run OK: all patterns matched exactly once. Nothing written.")
        return
    stamp = time.strftime("%Y%m%d_%H%M%S")
    shutil.copy2(bundle_p, f"{bundle_p}.orig-{stamp}")
    shutil.copy2(sw_p, f"{sw_p}.orig-{stamp}")
    bundle_p.write_text(bundle, encoding="utf-8")
    sw_p.write_text(sw, encoding="utf-8")
    print(f"Patched {BUNDLE} and {SW} (originals kept as *.orig-{stamp}).")


if __name__ == "__main__":
    main()
