#!/usr/bin/env python3
"""Patch #8 (2026-10-12, user request) on top of boss-fix-5: the start-print dialog's
Filament Assignment section shows the tool change statistics under "Filament change count":

  Tool changes: 1234 · 456 since last failure (T3) · best streak 900
  [T0 100% 500/500] [T1 99.6% 250/251] [T3 68.2% 120/176]   (per-tool success rate, colored)
v2 2026-10-12: per-tool success rates; heat-wait line removed (that is console-only, per print).
Applies on top of boss-fix-5 (restore the boss-fix-5 bundle first if v1 / boss-fix-6 is installed).

Data comes straight from Klipper objects Mainsail already subscribes to:
  gcode_macro _TC_STATS.stats      (in memory; None right after a Klipper restart)
  save_variables.variables.tc_stats (saved at print end / cancel / on a failure)
Read-only: sends nothing to the printer.

Usage: apply-fix-tcstats.py <mainsail_dir> [--dry-run]
"""
import shutil
import sys
import time
from pathlib import Path

BUNDLE = "assets/index-CCueyQmD.js"
SW = "sw.js"

GET_OLD = 'get filament_change_count(){var s;return(s=this.file.filament_change_count)!=null?s:0}'
GET_NEW = GET_OLD + (
    'get tcStats(){const p=this.$store.state.printer||{},m=p["gcode_macro _TC_STATS"]||{},'
    'sv=(p.save_variables||{}).variables||{},st=(m.stats&&typeof m.stats==="object")?m.stats:'
    '((sv.tc_stats&&typeof sv.tc_stats==="object")?sv.tc_stats:null);'
    'if(!st)return m.stats!==undefined?{summary:"Tool changes: none counted yet",tools:[]}:null;'
    'const ok=st.ok||0,f=st.fail||0,tl=st.tools||{};'
    'const tools=Object.keys(tl).sort().map(k=>{const r=tl[k]||[0,0],o=r[0]||0,n=o+(r[1]||0),'
    'pct=n?(o===n?100:Math.floor(o*1000/n)/10):0;'
    'return{key:k,ok:o,total:n,pct:pct,color:pct>=99?"#4caf50":pct>=90?"#ffb300":"#f44336"}}).filter(x=>x.total>0);'
    'return{summary:"Tool changes: "+(ok+f)+" \\u00b7 "+(st.since_fail||0)+" since last failure"'
    '+(st.last_fail?" ("+st.last_fail+")":"")+" \\u00b7 best streak "+(st.best_streak||0),tools:tools}}')

RENDER_OLD = 't("p",{staticClass:"body-2"},[e._v(" Filament change count: "+e._s(e.filament_change_count)+" ")])'
RENDER_NEW = RENDER_OLD + (
    ',e.tcStats?t("div",{staticClass:"tc-stats mb-2"},[t("p",{staticClass:"body-2 mb-1"},[e._v(" "+e._s(e.tcStats.summary)+" ")]),'
    't("div",{staticStyle:{display:"flex","flex-wrap":"wrap",gap:"6px"}},e._l(e.tcStats.tools,function(r){'
    'return t("div",{key:r.key,staticStyle:{border:"1px solid","border-radius":"6px",padding:"2px 8px","font-size":"13px"},'
    'style:{borderColor:r.color}},[t("b",[e._v(e._s(r.key))]),e._v(" "),t("span",{style:{color:r.color}},[e._v(e._s(r.pct)+"%")]),'
    't("span",{staticStyle:{opacity:"0.6","font-size":"11px"}},[e._v(" "+e._s(r.ok)+"/"+e._s(r.total))])])}))]):e._e()')

SW_OLD = '{url:"assets/index-CCueyQmD.js",revision:"boss-fix-5"}'
SW_NEW = '{url:"assets/index-CCueyQmD.js",revision:"boss-fix-7"}'


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
        sys.exit("Already patched (sw.js has boss-fix-7). Nothing to do.")
    bundle = replace_once(bundle, GET_OLD, GET_NEW, "tool change stats getter")
    bundle = replace_once(bundle, RENDER_OLD, RENDER_NEW, "tool change stats lines")
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
