#!/usr/bin/env python3
"""Back-pocket fix for drakarah/mainsail v0.0.7 (Mainsail 2.17.0 + toolchanger panel).

Fixes the start-print "Filament Assignment" section silently disappearing:
  1. filament_type is now a JSON-array string from Moonraker (since 2025-12-13,
     commit 5b92e52), but the dialog only splits on ';'. Accept array, JSON string,
     or the old ';' form.
  2. getTextColor(undefined) throws when no tool matched a filament, and Vue drops
     the whole section. Null-guard it.
  3. (optional, --with-pa) the Pressure Advance box sends
     SET_PRESSURE_ADVANCE TOOL=n VALUE=x, which Klipper ignores. Send
     EXTRUDER=<tool's extruder> ADVANCE=x instead, and skip empty/partial input.

  4. picking a spool for a tool (Spoolman panel) also sets the Toolchanger panel's
     color + material for that tool.
  5. the Toolchanger panel LOAD button also opens the spool picker for that tool.
  6. the start-print dialog no longer shows the single-spool Spoolman section.
  7. the Change Spool dialog (also opened by the LOAD button, #5) gets a "+ New spool"
     form: pick a Spoolman filament (or "+ New brand or color": brand/material/name/color)
     + weight left, Save creates the spool in Spoolman
     (through Moonraker's spoolman proxy) and uses it right away (same setSpool path as
     picking an existing spool). Built so nobody has to open Spoolman itself.

Also bumps the service-worker precache revision of the patched bundle so browsers
fetch the new file instead of serving the cached original.

Patterns are matched EXACTLY against the v0.0.7 minified bundle. If any pattern is
not found exactly once, nothing is written. Usage:
  apply-fix.py <mainsail_dir> [--with-pa] [--dry-run]
"""
import shutil
import sys
import time
from pathlib import Path

BUNDLE = "assets/index-CCueyQmD.js"
SW = "sw.js"

TYPES_OLD = 'e=(n=(i=this.file.filament_type)==null?void 0:i.split(";"))!=null?n:[]'
TYPES_NEW = ('e=(()=>{const v=this.file.filament_type;if(Array.isArray(v))return v.map(String);'
             'if(typeof v!=="string")return[];const q=v.trim();if(q.startsWith("["))'
             '{try{const p=JSON.parse(q);if(Array.isArray(p))return p.map(String)}catch(x){}}'
             'return q.split(";")})()')

COLOR_OLD = 'getTextColor(s){const e=s.charAt(0)'
COLOR_NEW = 'getTextColor(s){if(typeof s!=="string"||!s)return"inherit";const e=s.charAt(0)'

PA_OLD = 'r=>e.doSend("SET_PRESSURE_ADVANCE TOOL=".concat(e.toolNumber," VALUE=").concat(r))'
PA_NEW = ('r=>{const x=e.extruders[e.toolNumber];if(x&&r!==""&&r!=null&&!isNaN(parseFloat(r)))'
          'e.doSend("SET_PRESSURE_ADVANCE EXTRUDER=".concat(x.key," ADVANCE=").concat(parseFloat(r)))}')

# 4. (2026-10-04, user request) picking a spool for a tool in the Spoolman panel also
#    sets that tool's color + material in the Toolchanger panel (SET_TOOL_COLOR /
#    SET_TOOL_MATERIAL, the same commands the panel itself sends). T<n> = physical tool n.
SPOOL_OLD = 'setMacroVariable(s){var e;if(this.sendGcode("SET_GCODE_VARIABLE MACRO='
SPOOL_NEW = ('setMacroVariable(s){var e;{const n=String(this.tool??"").replace(/\\D/g,""),f=s.filament||{},'
             'h=String(f.color_hex||String(f.multi_color_hexes||"").split(",")[0]||"").replace("#","").slice(0,6),'
             'm=String(f.material||"").trim().replace(/\\s+/g,"-");if(n!==""){if(/^[0-9a-fA-F]{6}$/.test(h))'
             'this.sendGcode("SET_TOOL_COLOR TOOL=".concat(n," COLOR=\'#").concat(h.toUpperCase(),"\'"));'
             'if(m)this.sendGcode("SET_TOOL_MATERIAL TOOL=".concat(n," MATERIAL=").concat(m))}}'
             'if(this.sendGcode("SET_GCODE_VARIABLE MACRO=')

# 5. (2026-10-05, user request) Toolchanger panel LOAD button also opens the per-tool
#    Spoolman spool picker (same dialog as Spoolman panel -> T<n>), so a new spool gets
#    assigned when filament is loaded. The load macro itself is sent unchanged.
LOADCTOR_OLD = 'this.mdiPrinter3dNozzle=Zs,this.showColorPicker=!1}get filamentTypes(){'
LOADCTOR_NEW = 'this.mdiPrinter3dNozzle=Zs,this.showColorPicker=!1,this.showSpoolDialog=!1}get filamentTypes(){'
LOADCLICK_OLD = ('click:function(r){return e.doSend("LOAD_ONE_FILAMENT TOOL=".concat(e.toolNumber,'
                 '" MATERIAL=").concat(e.selectedType))}')
LOADCLICK_NEW = ('click:function(r){e.doSend("LOAD_ONE_FILAMENT TOOL=".concat(e.toolNumber,'
                 '" MATERIAL=").concat(e.selectedType));e.showSpoolDialog=!0}')
LOADDLG_OLD = 'e._v(" "+e._s(e.$t("LOAD",{isDefault:""}))+" ")],1)'
LOADDLG_NEW = ('e._v(" "+e._s(e.$t("LOAD",{isDefault:""}))+" ")],1),t(zr,{attrs:{tool:"T".concat(e.toolNumber)},'
               'model:{value:e.showSpoolDialog,callback:function(a){e.showSpoolDialog=a},expression:"showSpoolDialog"}})')

# 6. (2026-10-05, user request) hide the start-print dialog's single-spool Spoolman
#    section (+ its "with the following filament?" wording); on the Boss spools are per
#    tool and the Filament Assignment section above it picks the toolheads.
SPDLG_OLD = ('get existsSpoolman(){return this.moonrakerComponents.includes("spoolman")}'
             'get existsTimelapse(){return this.moonrakerComponents.includes("timelapse")}get showDivider(){')
SPDLG_NEW = ('get existsSpoolman(){return!1}'
             'get existsTimelapse(){return this.moonrakerComponents.includes("timelapse")}get showDivider(){')
SPQ_OLD = 'get active_spool(){var s;return(s=this.$store.state.server.spoolman.active_spool)!=null?s:null}get question(){'
SPQ_NEW = 'get active_spool(){return null}get question(){'

# 7. (2026-10-08) "+ New spool"
#    inside the Change Spool dialog. Filament list = GET /v1/filament (+ GET /v1/vendor),
#    create = POST /v1/spool {filament_id, initial_weight, remaining_weight}, all via
#    server.spoolman.proxy (use_v2_response). The new spool then goes through the normal
#    setSpool() (tool -> SET_GCODE_VARIABLE spool_id + SAVE_VARIABLE + #4 color/material;
#    no tool -> active spool). Native <select>/<input> on purpose: big native pickers on a phone.
#    v2 (2026-10-08 12:10, user: "need the ability to make it a custom spool -- a different
#    brand or name or color"): last list entry "+ New brand or color (not listed)" opens
#    Brand (optional, suggestions = existing vendors, reused case-insensitively or created),
#    Material, Name/color, Color picker -> POST /v1/vendor (if new) -> POST /v1/filament
#    {name, material, density (preset per material), diameter 1.75, weight 1000, color_hex,
#    vendor_id} -> spool as above.
NS_CTOR_OLD = 'this.mdiRefresh=Ni,this.search=""}get spools(){'
NS_CTOR_NEW = ('this.mdiRefresh=Ni,this.search="",this.showNewSpool=!1,this.newFilaments=[],this.newVendors=[],'
               'this.newFilamentId=null,this.newWeight="1000",this.newSaving=!1,this.newError="",'
               'this.newBrand="",this.newMaterial="PLA",this.newColorName="",this.newColorHex="#808080"}get spools(){')
# (anchor includes refresh()/close(): openSpoolManager alone also exists in the Spoolman panel)
NS_METH_OLD = ('openSpoolManager(){window.open(this.spoolManagerUrl,"_blank")}'
               'refresh(){this.$store.dispatch("server/spoolman/refreshSpools")}close(){this.showDialog=!1}')
NS_METH_NEW = (
    'async toggleNewSpool(){this.showNewSpool=!this.showNewSpool;this.newError="";'
    'if(this.showNewSpool&&!this.newFilaments.length)await this.loadNewFilaments()}'
    'async nsProxy(m,p,b){const a={request_method:m,path:p,use_v2_response:!0};if(b)a.body=b;'
    'const q=await this.$socket.emitAndWait("server.spoolman.proxy",a);'
    'if(q&&q.error)throw new Error(String(q.error.message||JSON.stringify(q.error)));'
    'return q&&typeof q==="object"&&"response"in q?q.response:q}'
    'async loadNewFilaments(){try{const d=await this.nsProxy("GET","/v1/filament");'
    'const l=(Array.isArray(d)?d:[]).map(f=>({id:f.id,weight:f.weight,'
    'label:[(f.vendor||{}).name,f.material,f.name].filter(Boolean).join(" - ")}))'
    '.sort((a,b)=>a.label.localeCompare(b.label));this.newFilaments=l;'
    'const v=await this.nsProxy("GET","/v1/vendor");'
    'this.newVendors=(Array.isArray(v)?v:[]).map(x=>({id:x.id,name:String(x.name||"")})).filter(x=>x.name)'
    '.sort((a,b)=>a.name.localeCompare(b.name));'
    'if(this.newFilamentId===null||(this.newFilamentId!==-1&&!l.some(f=>f.id===this.newFilamentId))){'
    'if(l.length){this.newFilamentId=l[0].id;this.newWeight=String(l[0].weight||1000)}else this.newFilamentId=-1}}'
    'catch(x){this.newError=String(x&&x.message||x)}}'
    'async createNewSpool(){const w=parseFloat(this.newWeight);'
    'if(!(w>0)){this.newError="Enter how many grams are left on the spool.";return}'
    'let fid=Number(this.newFilamentId),fw=w;const custom=fid===-1;'
    'const br=String(this.newBrand||"").trim(),mat=String(this.newMaterial||"").trim().toUpperCase(),'
    'nm=String(this.newColorName||"").trim();'
    'if(!custom){const f=this.newFilaments.find(x=>x.id===fid);if(!f){this.newError="Pick a filament first.";return}fw=f.weight||w}'
    'else{if(!mat){this.newError="Pick the material.";return}'
    'if(!nm){this.newError="Give it a name or color, e.g. Matte Red.";return}}'
    'this.newSaving=!0;this.newError="";try{'
    'if(custom){let vid=null;if(br){const ex=this.newVendors.find(x=>x.name.toLowerCase()===br.toLowerCase());'
    'if(ex)vid=ex.id;else{const nv=await this.nsProxy("POST","/v1/vendor",{name:br});vid=nv.id}}'
    'const dens={PLA:1.24,PETG:1.27,ABS:1.04,ASA:1.07,TPU:1.21,PC:1.2,PA:1.14,HIPS:1.04,PVA:1.23}[mat]||1.24;'
    'const hex=String(this.newColorHex||"").replace("#","").slice(0,6);'
    'const body={name:nm,material:mat,density:dens,diameter:1.75,weight:1000};'
    'if(vid!==null)body.vendor_id=vid;if(/^[0-9a-fA-F]{6}$/.test(hex))body.color_hex=hex.toUpperCase();'
    'const nf=await this.nsProxy("POST","/v1/filament",body);if(!nf||nf.id==null)throw new Error("Spoolman did not return the new filament.");'
    'fid=nf.id;fw=Math.max(1000,w);this.newFilaments=[];this.newFilamentId=null;'
    'this.newBrand="";this.newColorName=""}'
    'const sp=await this.nsProxy("POST","/v1/spool",{filament_id:fid,initial_weight:fw,remaining_weight:w});'
    'if(!sp||sp.id==null)throw new Error("Spoolman did not return the new spool.");'
    'this.$store.dispatch("server/spoolman/refreshSpools");this.showNewSpool=!1;this.setSpool(sp)}'
    'catch(x){this.newError=String(x&&x.message||x)}finally{this.newSaving=!1}}'
    + NS_METH_OLD)
NS_SHOW_OLD = 'onShowDialogChanged(s){s&&(this.refresh(),this.search="")}'
NS_SHOW_NEW = 'onShowDialogChanged(s){s&&(this.refresh(),this.search="",this.showNewSpool=!1,this.newError="")}'
NS_BTN_OLD = ('t(v,{staticClass:"px-2 minwidth-0 ml-3",attrs:{title:e.$t("Panels.SpoolmanPanel.Refresh"),'
              'loading:e.loadings.includes("refreshSpools")},on:{click:e.refreshSpools}}')
NS_BTN_NEW = ('t(v,{staticClass:"ml-3",attrs:{color:"primary",outlined:!e.showNewSpool},'
              'on:{click:e.toggleNewSpool}},[e._v(e.showNewSpool?"Close new spool":"+ New spool")]),'
              + NS_BTN_OLD)
_BOX = ('border:"1px solid rgba(128,128,128,.6)","border-radius":"4px",color:"inherit",'
        'background:"transparent",padding:"9px 8px"')
NS_FORM_OLD = '],1),t(J,{staticClass:"px-0 pb-0"},[t(Br,{attrs:{headers:e.headers,items:e.spools,'
NS_FORM_NEW = (
    '],1),e.showNewSpool?t(J,{staticClass:"pt-0"},['
    't("div",{staticClass:"d-flex flex-wrap align-center",staticStyle:{gap:"12px"}},['
    't("select",{staticStyle:{flex:"1 1 260px","min-width":"220px",' + _BOX + '},'
    'attrs:{"aria-label":"Filament"},domProps:{value:e.newFilamentId},'
    'on:{change:function(r){const i=Number(r.target.value);e.newFilamentId=i;'
    'if(i===-1){e.newWeight="1000";return}'
    'const f=e.newFilaments.find(function(x){return x.id===i});if(f&&f.weight)e.newWeight=String(f.weight)}}},'
    'e.newFilaments.map(function(f){return t("option",{key:f.id,staticStyle:{color:"#000"},'
    'domProps:{value:f.id,selected:f.id===e.newFilamentId}},[e._v(e._s(f.label))])}).concat(['
    't("option",{key:"new",staticStyle:{color:"#000"},domProps:{value:-1,selected:e.newFilamentId===-1}},'
    '[e._v("+ New brand or color (not listed)")])])),'
    't(se,{staticStyle:{"max-width":"170px"},attrs:{label:"Grams left",type:"number",outlined:"",dense:"","hide-details":""},'
    'model:{value:e.newWeight,callback:function(r){e.newWeight=r},expression:"newWeight"}}),'
    't(v,{attrs:{color:"primary",loading:e.newSaving},'
    'on:{click:e.createNewSpool}},[e._v("Save + use this spool")])]),'
    'e.newFilamentId===-1?t("div",{staticClass:"d-flex flex-wrap align-center mt-3",staticStyle:{gap:"12px"}},['
    't("input",{staticStyle:{flex:"1 1 170px","min-width":"150px",' + _BOX + '},'
    'attrs:{list:"ns-vendors-"+e._uid,placeholder:"Brand (optional)","aria-label":"Brand"},'
    'domProps:{value:e.newBrand},on:{input:function(r){e.newBrand=r.target.value}}}),'
    't("datalist",{attrs:{id:"ns-vendors-"+e._uid}},e.newVendors.map(function(x){return t("option",{key:x.id,domProps:{value:x.name}})})),'
    't("select",{staticStyle:{flex:"0 0 110px",' + _BOX + '},attrs:{"aria-label":"Material"},'
    'domProps:{value:e.newMaterial},on:{change:function(r){e.newMaterial=r.target.value}}},'
    '["PLA","PETG","ABS","ASA","TPU","PC","PA","HIPS","PVA","OTHER"].map(function(m){return t("option",'
    '{key:m,staticStyle:{color:"#000"},domProps:{value:m,selected:m===e.newMaterial}},[e._v(m)])})),'
    't("input",{staticStyle:{flex:"1 1 200px","min-width":"170px",' + _BOX + '},'
    'attrs:{placeholder:"Name / color, e.g. Matte Red","aria-label":"Name or color"},'
    'domProps:{value:e.newColorName},on:{input:function(r){e.newColorName=r.target.value}}}),'
    't("label",{staticClass:"d-flex align-center",staticStyle:{gap:"6px"}},[e._v("Color "),'
    't("input",{attrs:{type:"color","aria-label":"Color"},staticStyle:{width:"46px",height:"38px",'
    'border:"none",background:"transparent",padding:"0"},'
    'domProps:{value:e.newColorHex},on:{input:function(r){e.newColorHex=r.target.value}}})])]):e._e(),'
    'e.newError?t("div",{staticClass:"error--text mt-2"},[e._v(e._s(e.newError))]):e._e(),'
    't("div",{staticClass:"text-caption mt-2"},[e._v("Not in the list? Pick \\"+ New brand or color\\" at the '
    'bottom of the list.")])]):e._e(),'
    't(J,{staticClass:"px-0 pb-0"},[t(Br,{attrs:{headers:e.headers,items:e.spools,')

SW_REV = "boss-fix-5"
SW_OLDS = ['{url:"assets/index-CCueyQmD.js",revision:null}',
           '{url:"assets/index-CCueyQmD.js",revision:"boss-fix-1"}',
           '{url:"assets/index-CCueyQmD.js",revision:"boss-fix-2"}',
           '{url:"assets/index-CCueyQmD.js",revision:"boss-fix-3"}',
           '{url:"assets/index-CCueyQmD.js",revision:"boss-fix-4"}']
SW_NEW = '{url:"assets/index-CCueyQmD.js",revision:"boss-fix-5"}'


def replace_once(text, old, new, label):
    if new in text:
        print(f"skip (already applied): {label}")
        return text
    n = text.count(old)
    if n != 1:
        sys.exit(f"ABORT: pattern '{label}' found {n} times (expected 1). Wrong build? Nothing written.")
    return text.replace(old, new)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        sys.exit(__doc__)
    root = Path(args[0])
    with_pa = "--with-pa" in sys.argv
    dry = "--dry-run" in sys.argv

    bundle_p, sw_p = root / BUNDLE, root / SW
    bundle = bundle_p.read_text(encoding="utf-8")
    sw = sw_p.read_text(encoding="utf-8")

    if SW_NEW in sw:
        sys.exit(f"Already patched (sw.js has {SW_REV}). Nothing to do.")

    bundle = replace_once(bundle, TYPES_OLD, TYPES_NEW, "filament_type split")
    bundle = replace_once(bundle, COLOR_OLD, COLOR_NEW, "getTextColor guard")
    if with_pa:
        bundle = replace_once(bundle, PA_OLD, PA_NEW, "pressure advance command")
    bundle = replace_once(bundle, SPOOL_OLD, SPOOL_NEW, "spool pick -> tool color/material")
    bundle = replace_once(bundle, LOADCTOR_OLD, LOADCTOR_NEW, "load button: dialog state")
    bundle = replace_once(bundle, LOADCLICK_OLD, LOADCLICK_NEW, "load button: open spool picker")
    bundle = replace_once(bundle, LOADDLG_OLD, LOADDLG_NEW, "load button: spool picker dialog")
    bundle = replace_once(bundle, SPDLG_OLD, SPDLG_NEW, "start dialog: hide spoolman section")
    bundle = replace_once(bundle, SPQ_OLD, SPQ_NEW, "start dialog: no single-spool wording")
    bundle = replace_once(bundle, NS_CTOR_OLD, NS_CTOR_NEW, "new spool: dialog state")
    bundle = replace_once(bundle, NS_METH_OLD, NS_METH_NEW, "new spool: methods")
    bundle = replace_once(bundle, NS_SHOW_OLD, NS_SHOW_NEW, "new spool: reset on open")
    bundle = replace_once(bundle, NS_BTN_OLD, NS_BTN_NEW, "new spool: toolbar button")
    bundle = replace_once(bundle, NS_FORM_OLD, NS_FORM_NEW, "new spool: form")
    old_sw = [o for o in SW_OLDS if sw.count(o) == 1]
    if not old_sw:
        sys.exit("ABORT: service worker entry not found. Nothing written.")
    sw = sw.replace(old_sw[0], SW_NEW)

    if dry:
        print("Dry run OK: all patterns matched exactly once. Nothing written.")
        return

    stamp = time.strftime("%Y%m%d_%H%M%S")
    shutil.copy2(bundle_p, f"{bundle_p}.orig-{stamp}")
    shutil.copy2(sw_p, f"{sw_p}.orig-{stamp}")
    bundle_p.write_text(bundle, encoding="utf-8")
    sw_p.write_text(sw, encoding="utf-8")
    print(f"Patched {BUNDLE} and {SW} (originals kept as *.orig-{stamp})."
          f"{' PA fix included.' if with_pa else ''}")


if __name__ == "__main__":
    main()
