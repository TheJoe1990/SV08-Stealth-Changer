#!/usr/bin/env python3
"""Patch #9 (2026-10-12, user request) on top of boss-fix-7: show multi-color Spoolman filaments.

Spoolman filaments can have several colors (multi_color_hexes = "RRGGBB,RRGGBB,...") and a
direction: "coaxial" (colors side by side in the strand: dual/tri-color silk) or "longitudinal"
(colors change along the strand: gradient/rainbow). Mainsail 2.17 only draws one color.

  - Spool icon component: new optional props `colors` + `direction`; with 2+ colors the spool is
    filled with an SVG gradient (hard bands for coaxial, smooth blend for longitudinal).
  - Toolchanger panel tool cards: the spool icon uses the colors of the spool assigned to that
    physical tool ([gcode_macro T<n>].spool_id, looked up in Mainsail's Spoolman spool list).
  - Start-print dialog tool buttons (list + selected button): same colors as a CSS gradient.
Single-color spools and tools without a spool look exactly as before. Read-only.

Usage: apply-fix-multicolor.py <mainsail_dir> [--dry-run]
"""
import shutil
import sys
import time
from pathlib import Path

BUNDLE = "assets/index-CCueyQmD.js"
SW = "sw.js"

# shared lookup: physical tool n -> its Spoolman filament's color list + direction
LOOKUP = ('const p=this.$store.state.printer||{},m=p["gcode_macro T"+n]||{},id=parseInt(m.spool_id),'
          'sp=((this.$store.state.server.spoolman||{}).spools||[]).find(x=>x.id===id),f=sp&&sp.filament||{},'
          'h=String(f.multi_color_hexes||"").split(",").map(x=>x.trim().replace("#","")).filter(x=>/^[0-9a-fA-F]{6}$/.test(x)).map(x=>"#"+x);')

R = [
    # --- spool icon: props, gradient stops, fill
    ('get styleCircle1(){return{fill:this.color}}',
     'get mcColors(){const c=(this.colors||[]).map(x=>"#"+String(x).trim().replace("#","")).filter(x=>/^#[0-9a-fA-F]{6}$/.test(x));'
     'return c.length>1?c:null}get mcId(){return"mcspool"+this._uid}get mcStops(){const c=this.mcColors||[],n=c.length,o=[];'
     'if(this.direction==="coaxial")c.forEach((x,i)=>{o.push([i/n,x],[(i+1)/n,x])});else c.forEach((x,i)=>o.push([n>1?i/(n-1):0,x]));'
     'return o.map((s,i)=>({key:i,offset:(s[0]*100).toFixed(1)+"%",color:s[1]}))}'
     'get styleCircle1(){return{fill:this.mcColors?"url(#"+this.mcId+")":this.color}}',
     "spool icon: gradient fill"),
    ('g8([C({required:!1,default:"#ff0"})],E1.prototype,"color",2);E1=g8([x({})],E1);',
     'g8([C({required:!1,default:"#ff0"})],E1.prototype,"color",2);g8([C({required:!1,default:null})],E1.prototype,"colors",2);'
     'g8([C({required:!1,default:null})],E1.prototype,"direction",2);E1=g8([x({})],E1);',
     "spool icon: props"),
    ('[t("g",[t("circle",{style:e.styleCircle1,attrs:{cx:"243.52",cy:"243.52",r:"232.97"}})',
     '[e.mcColors?t("defs",[t("linearGradient",{attrs:{id:e.mcId,x1:"0",y1:"0",x2:"1",y2:"1"}},e._l(e.mcStops,function(s){'
     'return t("stop",{key:s.key,attrs:{offset:s.offset,"stop-color":s.color}})}))]):e._e(),'
     't("g",[t("circle",{style:e.styleCircle1,attrs:{cx:"243.52",cy:"243.52",r:"232.97"}})',
     "spool icon: gradient defs"),
    # --- toolchanger panel tool card
    ('get selectedColor(){return this.toolchangerFilamentColors[this.toolNumber]}',
     'get selectedColor(){return this.toolchangerFilamentColors[this.toolNumber]}get spoolMulti(){const n=this.toolNumber;' + LOOKUP +
     'return h.length>1?{colors:h,direction:f.multi_color_direction||"longitudinal"}:{colors:null,direction:null}}',
     "tool card: spool colors"),
    ('attrs:{color:e.selectedColor}',
     'attrs:{color:e.selectedColor,colors:e.spoolMulti.colors,direction:e.spoolMulti.direction}',
     "tool card: pass colors to spool icon"),
    # --- start-print dialog tool buttons
    ('color:this.toolchangerFilamentColors[e]}})}',
     'color:this.toolchangerFilamentColors[e],bg:this.tcSpoolBg(Number(((t=s.match(/\\d+/))==null?void 0:t[0])||0),'
     'this.toolchangerFilamentColors[e])}})}tcSpoolBg(n,c){' + LOOKUP +
     'if(h.length<2)return c;const k=h.length;return"linear-gradient(135deg,"+h.map((x,i)=>f.multi_color_direction==="coaxial"'
     '?x+" "+(i*100/k)+"%,"+x+" "+((i+1)*100/k)+"%":x).join(",")+")"}',
     "start dialog: tool gradient"),
    ('style:{backgroundColor:n.color,color:e.getTextColor(n.color)}',
     'style:{background:n.bg||n.color,color:e.getTextColor(n.color)}',
     "start dialog: tool list buttons"),
    ('style:{backgroundColor:(o=e.selectedTools[i])==null?void 0:o.color,',
     'style:{background:(o=e.selectedTools[i])==null?void 0:o.bg||o.color,',
     "start dialog: selected tool button"),
]
SW_OLD = '{url:"assets/index-CCueyQmD.js",revision:"boss-fix-7"}'
SW_NEW = '{url:"assets/index-CCueyQmD.js",revision:"boss-fix-8"}'


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
        sys.exit("Already patched (sw.js has boss-fix-8). Nothing to do.")
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
