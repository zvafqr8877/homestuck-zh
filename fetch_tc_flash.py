#!/usr/bin/env python3
"""把繁中站（zhhomestuck.github.io）翻譯過文字的 *_ct.swf 抓下來，
放到 assets/zh/flashes/<新站 manifest 裡該頁的 swf 檔名>，build.py 的 local_swf() 會優先使用。
用法：在專案資料夾執行  python fetch_tc_flash.py
已存在且內容相同的檔案會略過；--dry 只檢查不下載。"""
import json, sys, hashlib, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DRY = "--dry" in sys.argv
BASE = "https://zhhomestuck.github.io/flash/"
# 繁中站頁碼 → 該頁使用的翻譯版 SWF（由全站 6064 頁掃描而來）
TC = {
 2153:"00253_ct.swf",3258:"01358_ct.swf",4692:"02791_ct.swf",4979:"03077_ct.swf",
 5221:"03318_ct.swf",5338:"03435_ct.swf",5595:"03692_ct.swf",5617:"03714_ct.swf",
 5643:"03740_ct.swf",5660:"03757_ct.swf",5774:"03871_ct.swf",5795:"03892_ct.swf",
 5836:"03933_ct.swf",5874:"03971_ct.swf",5902:"03999_ct.swf",5919:"04016_ct.swf",
 5984:"04081_ct.swf",6000:"04097_ct.swf",6021:"04118_ct.swf",6062:"04159_ct.swf",
 6094:"04191_ct.swf",6369:"04466_ct.swf",6416:"04513_ct.swf",6441:"04538_ct.swf",
 6468:"04565_ct.swf",6720:"04817_ct.swf",6725:"04822_ct.swf",
 6934:"05031_ct.swf",6952:"05031_ct.swf",6970:"05031_ct.swf",6978:"05031_ct.swf",6984:"05031_ct.swf",
 7037:"05134_ct.swf",7327:"05424_ct.swf",7395:"05492_ct.swf",7680:"05777_2_ct.swf",
}
man = json.load(open(ROOT / "manifest.json", encoding="utf-8"))
out = ROOT / "assets" / "zh" / "flashes"
out.mkdir(parents=True, exist_ok=True)
cache = {}
def get(name):
    if name not in cache:
        try:
            cache[name] = urllib.request.urlopen(urllib.request.Request(BASE + name, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read()
        except Exception as e:
            print("  下載失敗", name, e); cache[name] = None
    return cache[name]
new = same = miss = 0
for pg, name in sorted(TC.items()):
    fl = [i["file"] for i in man.get(str(pg), []) if i.get("type") == "flash"]
    if not fl:
        print(f"{pg:>5} 新站 manifest 沒有 Flash，略過（繁中 {name}）"); miss += 1; continue
    for f in fl:
        dst = out / f.rsplit("/", 1)[-1]
        if DRY:
            print(f"{pg:>5} {name} -> {dst.name}  {'已有' if dst.exists() else '缺'}"); continue
        data = get(name)
        if not data: continue
        if dst.exists() and hashlib.sha256(dst.read_bytes()).digest() == hashlib.sha256(data).digest():
            same += 1; continue
        dst.write_bytes(data); new += 1
        print(f"{pg:>5} 寫入 {dst.name}（{len(data)} bytes，來源 {name}）")
print(f"\n新增/更新 {new}，已相同 {same}，manifest 無 Flash {miss}")
