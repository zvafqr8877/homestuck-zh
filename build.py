#!/usr/bin/env python3
"""把 content/*.md 產生成 docs/ 靜態網站（給 GitHub Pages 用）。

用法：python build.py
只用標準函式庫，不需要額外安裝套件。
"""
import html
import json
import re
import shutil
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
OUT = ROOT / "docs"

STATUS_LABEL = {
    "converted": "機器轉換・待校對",
    "proofreading": "校對中",
    "done": "已校對",
}

CSS = """\
:root{--c-converted:#d9822b;--c-proofreading:#2a6f97;--c-done:#3a8f5c}
*{box-sizing:border-box}
body{margin:0;background:#535353;color:#000;font:16px/1.5 Verdana,"Noto Sans TC","Microsoft JhengHei",sans-serif}
a{color:#00f}
header.site{background:#000;text-align:center;padding:6px 8px;font:700 11px/1.4 Verdana,"Microsoft JhengHei",sans-serif}
header.site a{color:#fff;text-decoration:none;margin:0 6px}
header.site a.name{color:#ff0}
header.site a:hover{text-decoration:underline}
main.wrap{max-width:940px;margin:0 auto;background:#c6c6c6;padding:20px 12px 8px}
article.story{max-width:650px;margin:8px auto 14px;background:#eee;padding:12px 0}
.story h1{font:700 28px/1.25 "Courier New",CourierPrime,courier,monospace;text-align:center;margin:0 16px 12px}
.story .assets{margin:0}
.story .assets>*+*{margin-top:32px}
.story .assets img,.story .assets video{width:650px;max-width:100%;height:auto;display:block;margin:0 auto}
.flash{margin:0 auto;max-width:650px;position:relative}
.flash a.pick{position:absolute;z-index:3;top:34.7%;height:40.5%;display:block;background:transparent;cursor:pointer}
.flash a.pick:hover{outline:3px solid rgba(255,255,0,.6)}
.flashwin{position:relative;width:100%;overflow:hidden;margin:0 auto;background:#fff}
.flashwin a.pick{position:absolute;z-index:3;top:34.7%;height:40.5%;display:block;background:transparent;cursor:pointer}
.flashwin a.pick:hover{outline:3px solid rgba(255,255,0,.6)}
.flashwin iframe{position:absolute;left:0;top:0;width:1000px;height:1600px;border:0;transform-origin:0 0}
.hscroll{overflow-x:scroll;margin:0 0 16px}
.story .hscroll .assets img{width:auto;max-width:none;margin:0}
.story .hscroll>img.hs-arrow{width:82px;height:32px;margin:0}
body.wide950 main.wrap{max-width:950px;padding:0}
body.wide950 .assets.top950{margin:0}
body.wide950 .assets.top950 img,body.wide950 .assets.top950 video{width:950px;max-width:none;margin:0;display:block}
body.wide950 article.story{margin:0 auto 14px}
body.wide main.wrap{max-width:none;margin:0 12px}
body.wide article.story{max-width:none}
.pw{margin:16px 28px 0;text-align:center;font:14px/1.8 Verdana,"Microsoft JhengHei",sans-serif}
.pw input{font:14px Verdana;padding:2px 6px;width:200px}
.hint2{color:#a00;min-height:1.5em;margin:4px 0}
.hintbox{margin:16px 28px 0;border:1px dashed #888;padding:6px 20px 10px;text-align:center}
.hintbox button{font:12px/16px Geneva,"Lucida Grande",sans-serif;padding:2px 8px;cursor:pointer}
.hintbox p{margin:8px 0 0;font:700 14px/1.6 "Courier New",monospace}
.pw .box{display:inline-block;margin:6px 0;padding:6px 14px;border:1px dashed #888}
.assets.ff{position:relative}

body.collide{background:#000}
.collide header.site{background:#000}
.collide main.wrap{max-width:984px;background:#454545;padding:10px}
.collide article.story{max-width:950px;background:#000;color:#fff;padding:0}
.collide .story h1{position:absolute;left:-9999px}
.collide .banner{display:block;width:100%;max-width:950px;height:auto;margin:0 auto}
.collide .yt{max-width:950px;margin:0 auto}
.collide .nextlink,.collide .story-foot,.collide .plain{color:#fff}
.collide .nextlink span{color:#fff}
.collide .nextlink a,.collide .story-foot a{color:#8cf}
body.act7{background:#fff}
.act7 main.wrap{max-width:1184px;background:#e2e2e2;padding:5px}
.act7 article.story{max-width:1174px;background:#dbdbdb;padding:0 0 18px}
.act7 .story h1{position:absolute;left:-9999px}
.act7 .banner{display:block;width:100%;height:auto}
.act7 .yt{max-width:1174px;margin:0 auto;aspect-ratio:1174/660}
body.endcredits{background:#000}
.endcredits header.site{background:#000}
.endcredits main.wrap{max-width:950px;background:#262626;padding:0}
.endcredits article.story{max-width:950px;background:#262626;color:#fff;padding:0 0 18px}
.endcredits .story h1{position:absolute;left:-9999px}
.endcredits .yt{max-width:950px;margin:0 auto;aspect-ratio:950/650}
.endcredits .nextlink,.endcredits .story-foot,.endcredits .plain{color:#fff}
.endcredits .nextlink span{color:#fff}
.endcredits .nextlink a,.endcredits .story-foot a{color:#8cf}
body.a6a6{background:#042300}
.a6a6 header.site{background:#042300}
.a6a6 header.site a,.a6a6 header.site a.name{color:#2ed73a;text-decoration:underline}
.a6a6 header.site img.tooth{vertical-align:middle;height:21px;margin:0 6px}
.a6a6 main.wrap{background:#168500}
.a6a6 article.story{background:#073c00;color:#2ed73a}
.a6a6 .story h1{color:#2ed73a}
.a6a6 .story a,.a6a6 .nextlink span{color:#2ed73a}
.a6a6 .story .dialog{border-color:#2ed73a}
.a6a6 .page-info{color:#cfc}
.a6a6 .page-info a{color:#cfc}
.yt{aspect-ratio:16/9;width:100%}
.yt iframe{width:100%;height:100%;border:0;display:block}
.noasset{color:#555;font-size:12px;text-align:center;margin:8px 16px}
.dialog{margin:16px 28px 0;border:1px dashed #888;padding:6px 20px 14px;text-align:center}
.dialog button{font:12px/16px Geneva,"Lucida Grande",sans-serif;padding:2px 8px;cursor:pointer}
.dialog .log{text-align:left;font:700 14px/20px "Courier New",CourierPrime,courier,monospace;margin-top:14px;overflow-wrap:anywhere}
.dialog .log p{margin:0}
.dialog .log p.gap{margin-top:12px}
.dialog .log.off{display:none}
.plain{margin:16px 28px 0;font:14px/1.8 Verdana,"Microsoft JhengHei",sans-serif}
.plain p{margin:.4em 0}
.nextlink{margin:16px 28px 0;font:24px/32px "Courier New",CourierPrime,courier,monospace}
.nextlink span{color:#000}
.story-foot{margin:16px 28px 0;font:12px/1.6 Verdana,"Microsoft JhengHei",sans-serif}
.story-foot a{margin-right:14px}
.story-foot .gone{color:#888;margin-right:14px}
.page-info{max-width:650px;margin:0 auto 14px;font-size:12px;color:#333;padding:0 4px}
.badge{display:inline-block;padding:0 .6em;border-radius:1em;font-size:11px;color:#fff}
.badge.converted{background:var(--c-converted)}
.badge.proofreading{background:var(--c-proofreading)}
.badge.done{background:var(--c-done)}
.story.pagebox{padding:12px 28px 18px}
.story.pagebox h1{margin:0 0 12px}
.story.pagebox p,.story.pagebox ul{font-size:14px;line-height:1.8}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{border-bottom:1px solid #bbb;padding:.35em .5em;text-align:right}
th:first-child,td:first-child{text-align:left}
.bar{display:flex;height:.9em;border-radius:4px;overflow:hidden;background:#ccc;margin:.5em 0}
.bar span{display:block;height:100%}
footer.site{max-width:940px;margin:0 auto;padding:12px 16px 40px;color:#ddd;font-size:12px}
footer.site a{color:#9cf}
footer.site ul{margin:.4em 0;padding-left:1.2em}
@media (max-width:560px){.story h1{font-size:22px}.dialog{margin:12px 8px 0;padding:6px 10px 12px}.nextlink,.story-foot,.plain{margin-left:12px;margin-right:12px}.nextlink{font-size:20px}main.wrap{padding:8px 0}}
"""


RUFFLE_JS = """
<script>window.RufflePlayer=window.RufflePlayer||{};window.RufflePlayer.config={autoplay:"on",unmuteOverlay:"hidden",splashScreen:false,letterbox:"on",contextMenu:"off"};</script>
<script src="https://unpkg.com/@ruffle-rs/ruffle"></script>
<script>
window.addEventListener("load", function () {
  var R = window.RufflePlayer && window.RufflePlayer.newest();
  if (!R) return;
  document.querySelectorAll(".flash").forEach(function (d) {
    var p = R.createPlayer();
    var w = +d.dataset.w || 650, h = +d.dataset.h || 450;
    p.style.width = w + "px"; p.style.maxWidth = "100%"; p.style.aspectRatio = w + "/" + h; p.style.height = "auto";
    d.appendChild(p);
    // 設定和官方一致：載入後直接播放（不顯示橘色播放鈕），瀏覽器擋自動出聲時顯示「點擊以取消靜音」
    p.load({url: d.dataset.swf, autoplay: "on", unmuteOverlay: "visible", splashScreen: false, letterbox: "on"});
    // 瀏覽器規定要點一下才能出聲：左上角放一個小喇叭，點下去才取消靜音（官方也是小喇叭）
    var b = document.createElement("button");
    b.type = "button"; b.title = "點擊以開啟聲音"; b.textContent = "🔇";
    b.style.cssText = "position:absolute;left:4px;top:4px;z-index:4;background:rgba(0,0,0,.45);color:#fff;border:0;border-radius:3px;font-size:16px;line-height:1;padding:3px 5px;cursor:pointer";
    b.onclick = function () { try { p.play(); } catch (e) {} b.remove(); };
    d.appendChild(b);
  });
});
</script>"""


def load_sources(path):
    import csv
    if not path.exists():
        return {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        return {int(r["official"]): r for r in csv.DictReader(f) if r.get("official", "").isdigit()}


def load_json(path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


_tf = ROOT / "title_fix.json"
TITLE_FIX = json.loads(_tf.read_text(encoding="utf-8")) if _tf.exists() else {}


def parse_page(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n?(.*)", text, re.S)
    if not m:
        raise ValueError(f"{path.name}: 缺少開頭的 front matter（--- 區塊）")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    if "page" not in meta:
        raise ValueError(f"{path.name}: front matter 缺少 page")
    meta["page"] = int(meta["page"])
    meta.setdefault("title", f"第 {meta['page']} 頁")
    meta.setdefault("status", "converted")
    if meta["status"] not in STATUS_LABEL:
        raise ValueError(f"{path.name}: status 必須是 {sorted(STATUS_LABEL)} 其中之一")
    if meta["status"] == "converted" and str(meta["page"]) in TITLE_FIX:
        meta["title"] = TITLE_FIX[str(meta["page"])]  # 簡中標題缺漏或和官方不同的頁，改用官方標題
    meta["body"] = m.group(2).strip("\n")
    return meta


def esc(s):
    return html.escape(s, quote=True)


def layout(site, title, inner, base, raw=False, body_class="", sep_img=""):
    credits = "".join(
        f'<li><a href="{esc(c["url"])}">{esc(c["name"])}</a>：{esc(c.get("note", ""))}</li>'
        for c in site.get("credits", [])
    )
    sep = f'<img class="tooth" src="{esc(sep_img)}" alt="|">' if (sep_img and "a6a6" in body_class) else "|"
    body = inner if raw else f'<article class="story pagebox">{inner}</article>'
    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<link rel="stylesheet" href="{base}/style.css">
</head>
<body class="{body_class}">
<header class="site">
<a class="name" href="{base}/">{esc(site["title"])}</a> {sep}
<a href="{base}/progress.html">翻譯進度</a>
</header>
<main class="wrap">
{body}
</main>
<footer class="site">
<p>{esc(site.get("copyright", ""))}</p>
<ul>{credits}</ul>
</footer>
</body>
</html>
"""


SPEAKER_RE = re.compile(r"^\s*([^：:]{1,40}?)\s*[：:]")
FLASHWIN_JS = """<script>
(function(){
  function fit(){
    document.querySelectorAll(".flashwin").forEach(function(w){
      var f=w.querySelector("iframe"), s=w.clientWidth/(+w.dataset.w);
      f.style.transform="scale("+s+") translate(-"+w.dataset.left+"px,-"+w.dataset.top+"px)";
    });
  }
  fit(); window.addEventListener("resize",fit);
})();
</script>"""
FIREFLY_JS = """<script>
(function(){
  var ff=document.querySelector(".assets.ff"); if(!ff) return;
  var base=ff.getAttribute("data-sprite")||"";
  var box=ff.closest("article")||ff; box.style.position="relative"; // 官方是蓋在整個內容框上，位置百分比以內容框計算
  var R=new Image(), L=new Image(); R.src=base+"firefly_sprite_opt.png"; L.src=base+"firefly_sprite_left_opt.png";
  function rnd(a,b){return Math.floor(Math.random()*(b-a+1))+a;}
  var flies=[0,1,2,3].map(function(){
    var c=document.createElement("canvas"); c.width=140; c.height=140;
    c.style.cssText="position:absolute;pointer-events:none;z-index:2;top:"+rnd(0,100)+"%;left:"+rnd(15,65)+"%";
    box.appendChild(c);
    return {c:c.getContext("2d"),dir:rnd(0,1),x:rnd(0,80),y:rnd(0,80),vx:rnd(1,3),vy:rnd(1,3),f:rnd(0,12),wait:0,w:0};
  });
  // 每格 60x60，0~12 格是翅膀拍動加白圈閃光，播完停一小段再重來；15 格/秒
  setInterval(function(){
    flies.forEach(function(o){
      var x=o.c; x.clearRect(0,0,140,140);
      var img=o.dir?R:L;
      if(img.complete&&img.naturalWidth) x.drawImage(img,o.f*60,0,60,60,o.x,o.y,60,60);
      if(o.wait){ if(++o.w>15){o.wait=0;o.w=0;} } else if(++o.f>12){o.f=0;o.wait=1;o.w=0;}
      o.x+=o.dir?o.vx:-o.vx; o.y+=o.vy;
      if(o.y>80){o.y=80;o.vy=-rnd(1,2);} if(o.y<0){o.y=0;o.vy=rnd(1,2);}
      if(o.x>80){o.x=80;o.dir=0;o.vx=rnd(1,2);} if(o.x<0){o.x=0;o.dir=1;o.vx=rnd(1,2);}
    });
  },1000/15);
})();
</script>"""
DIALOG_JS = """<script>
document.querySelectorAll(".dialog button").forEach(function(b){
  b.addEventListener("click",function(){
    var l=b.parentNode.querySelector(".log"), off=l.classList.toggle("off");
    b.textContent=off?"顯示對話記錄":"隱藏對話記錄";
  });
});
</script>"""


def body_html(body, colors):
    lines = [l.strip() for l in body.splitlines() if l.strip()]
    if not lines:
        return ""
    speakers = [SPEAKER_RE.match(l) for l in lines]
    if not any(speakers):
        return '<div class="plain">' + "".join(f"<p>{esc(l)}</p>" for l in lines) + "</div>"
    out, last = [], None
    for l, m in zip(lines, speakers):
        who = m.group(1).strip() if m else None
        color = colors.get(who.upper()) if who else None
        style = f' style="color:{color}"' if color else ""
        cls = ' class="gap"' if (last is not None and who != last and out) else ""
        out.append(f"<p{cls}{style}>{esc(l)}</p>")
        last = who
    return (
        '<div class="dialog"><button type="button">隱藏對話記錄</button>'
        '<div class="log">' + "".join(out) + "</div></div>"
    )


def local_swf(item):
    """assets/ 底下有放這個 SWF 就回傳相對路徑（優先 assets/<manifest 路徑>，其次 assets/flashes/<檔名>），否則回傳 None"""
    f = item.get("file", "")
    for rel in (f, "flashes/" + f.rsplit("/", 1)[-1]):
        if rel and (ROOT / "assets" / rel).exists():
            return rel
    return None


def asset_html(page, manifest, asset_base, fallback_base="", flash_mode="iframe", official_page_url="", flash_box=None):
    items = manifest.get(str(page), [])
    if not items:
        return '<p class="noasset">（本頁的圖片／影片尚未補上）</p>'
    parts = []
    for it in items:
        kind = it.get("type", "image")
        if kind == "youtube":
            # 官方放在 YouTube 的頁面（例如最後的 Credits），manifest 只要寫 {"type":"youtube","id":"影片ID"}
            vid = esc(it["id"])
            parts.append(
                '<div class="yt"><iframe src="https://www.youtube-nocookie.com/embed/'
                f'{vid}" title="YouTube" loading="lazy" allowfullscreen></iframe></div>'
            )
            continue
        url = esc(asset_base + it["file"])
        # 官方網址載入失敗時，自動換成自己的鏡像（asset_fallback_base 不為空才啟用）
        onerr = ""
        if fallback_base:
            fb = esc(fallback_base + it["file"])
            onerr = f""" onerror="this.onerror=null;this.src='{fb}'" """
        if kind == "image":
            parts.append(f'<img src="{url}"{onerr} alt="{esc(it.get("alt", ""))}" loading="lazy">')
        elif kind == "video":
            parts.append(f'<video src="{url}"{onerr} controls preload="none"></video>')
        elif kind == "flash" and local_swf(it):
            # 本站自己放的 SWF：用 Ruffle 直接播，滑鼠可以互動；沒放檔案的頁面維持下面的嵌入官方頁面
            _l, _t, fw, fh = flash_box or (175, 94, 650, 450)
            parts.append(f'<div class="flash" data-swf="../assets/{local_swf(it)}" data-w="{fw}" data-h="{fh}" style="max-width:{fw}px"></div>')
        elif kind == "flash":
            # flash_mode（site.json）：
            #   iframe：直接嵌入官方頁面，由官方站播放（官方的 SWF 只允許 www.homestuck.com 讀取，
            #           實測 2026-10-29 自己用 Ruffle 讀會被 CORS 擋住）
            #   ruffle：用 Ruffle 播放 asset_base 底下的 SWF（asset_base 要能讓你的網站讀取）
            #   link ：只顯示「請到官方頁面觀看」
            if flash_mode == "ruffle":
                _l, _t, fw, fh = flash_box or (175, 94, 650, 450)
                parts.append(f'<div class="flash" data-swf="{url}" data-w="{fw}" data-h="{fh}"></div>')
            elif flash_mode == "iframe" and official_page_url:
                # 只露出官方頁面中間的 Flash 區塊（650x450），不顯示官方的導覽列和標題，也沒有捲軸。
                # 做法：iframe 固定 1000px 寬（官方版面在這個寬度下，內容框左邊距是 175px），
                # 再往左上平移到 Flash 的位置；flash_top 依標題佔幾行（每行 36px）算出。
                if not any('class="flashwin"' in p for p in parts):
                    left, top, fw, fh = flash_box or (175, 94, 650, 450)
                    parts.append(
                        f'<div class="flashwin" data-left="{left}" data-top="{top}" data-w="{fw}" '
                        f'style="max-width:{fw}px;aspect-ratio:{fw}/{fh}">'
                        f'<iframe src="{esc(official_page_url)}" title="官方頁面的動畫" scrolling="no" '
                        'loading="lazy" allow="autoplay"></iframe></div>'
                    )
            else:
                parts.append('<p class="noasset">這頁是 Flash 動畫，請到上方「官方原文」連結觀看。</p>')
        else:
            parts.append(f'<p class="noasset">（尚未支援的素材類型：{esc(kind)}）</p>')
    return '<div class="assets">' + "\n".join(parts) + "</div>"


def build():
    site = load_json(ROOT / "site.json", {})
    manifest = load_json(ROOT / "manifest.json", {})
    colors = load_json(ROOT / "speaker_colors.json", {})
    flags = load_json(ROOT / "flags.json", {})
    flash_layout = load_json(ROOT / "flash_layout.json", {})
    navg = load_json(ROOT / "nav.json", {})
    pwhash = load_json(ROOT / "passwords.json", {})
    sources = load_sources(ROOT / "sources.csv")
    base =site.get("base_url", "").rstrip("/")
    asset_base = site.get("asset_base", "")
    if asset_base and not asset_base.endswith("/"):
        asset_base += "/"
    fallback_base = site.get("asset_fallback_base", "")
    if fallback_base and not fallback_base.endswith("/"):
        fallback_base += "/"
    tooth = asset_base.rsplit("media/", 1)[0] + "assets/a6a6_tooth2.gif" if "media/" in asset_base else ""
    official_tpl = site.get("official_url", "")
    flash_mode = site.get("flash_mode", "iframe")

    all_pages = sorted(
        (parse_page(p) for p in CONTENT.glob("*.md")), key=lambda d: d["page"]
    )
    # 隱藏頁（front matter 寫 hidden: true）：有網址，但不在上一頁／下一頁的路徑上，也不算進度
    pages = [p for p in all_pages if p.get("hidden", "").lower() != "true"]
    hidden_pages = [p for p in all_pages if p.get("hidden", "").lower() == "true"]
    by_num = {p["page"]: p for p in all_pages}
    nums = [p["page"] for p in all_pages]
    if len(nums) != len(set(nums)):
        dup = [n for n, c in Counter(nums).items() if c > 1]
        raise SystemExit(f"頁碼重複：{dup}")

    # 重新產生輸出（保留 CNAME）
    OUT.mkdir(exist_ok=True)
    for child in OUT.iterdir():
        if child.name == "CNAME":
            continue
        shutil.rmtree(child) if child.is_dir() else child.unlink()
    (OUT / "p").mkdir()
    (OUT / "style.css").write_text(CSS, encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    if (ROOT / "assets").is_dir():  # 自己放的素材（collect_assets.py 產生），site.json 的 asset_base 指到 /你的base/assets/
        shutil.copytree(ROOT / "assets", OUT / "assets")

    # 各頁
    for pg in all_pages:
        n = pg["page"]
        before = [p for p in pages if p["page"] < n]
        after = [p for p in pages if p["page"] > n]
        # 上一頁／下一頁：優先照官方的連結關係（nav.json，來自 UHC 資料，只有頁碼），
        # 沒有資料或是隱藏頁才退回用頁碼前後頁
        g = None if "hidden" in pg and pg["hidden"].lower() == "true" else navg.get(str(n))

        def tlink(t, label=None):
            if t in by_num:
                return f'{base}/p/{t:06d}.html', label or by_num[t]["title"]
            if t < 7959:
                return f"https://zhhomestuck.github.io/p/{t:06d}", label or f"繁中站第 {t} 頁 ↗"
            return None, None

        targets = g["n"] if g else ([after[0]["page"]] if after else [])
        nl = []
        for t in targets:
            u, lab = tlink(t)
            if u:
                nl.append(f'<div class="nextlink"><span>&gt;</span> <a href="{u}">{esc(lab)}</a></div>')
        next_html = "".join(nl)
        pv = g["p"] if g and g.get("p") else (before[-1]["page"] if before else None)
        pu, _ = tlink(pv) if pv else (None, None)
        foot = (
            (f'<a href="{pu}">← 上一頁</a>' if pu else '<span class="gone">← 上一頁</span>')
            + f'<a href="{base}/">回首頁</a>'
        )
        text = body_html(pg["body"], colors)
        # 來源連結：優先用 sources.csv（gen_mapping.py 產生），
        # 沒有的話只有 front matter 寫了 official: 官方頁碼 才顯示官方連結，避免頁碼對錯
        key = int(pg["official"]) if pg.get("official", "").isdigit() else n
        src = sources.get(key)
        links = []
        if src:
            for label, col in (("官方原文", "official_url"), ("簡中來源", "sc_url"), ("繁中來源", "tc_url")):
                if src.get(col):
                    links.append((label, src[col]))
        elif official_tpl and pg.get("official", "").isdigit():
            links.append(("官方原文", official_tpl.format(page=int(pg["official"]))))
        official = "".join(f' · <a href="{esc(u)}">{esc(t)}</a>' for t, u in links)
        official_link = next((u for t, u in links if t == "官方原文"), "")
        # Flash 在官方頁面裡的位置和大小（flash_layout.json，用 measure_flash.js 在官方站量出來的；
        # 沒量到的頁面用 650x450、標題一行的預設值）
        fb = flash_layout.get(str(n))
        assets = asset_html(n, manifest, asset_base, fallback_base, flash_mode, official_link, fb)
        ruffle = RUFFLE_JS if 'class="flash"' in assets else ""
        pflags = flags.get(str(n), [])
        if "FIREFLY" in pflags:
            text = ""  # 螢火蟲頁只留圖／動畫和下一頁連結，不放文字
        # 三選一動畫頁：官方只有其中一張圖點得動（其餘沒反應），在該張圖上蓋一個透明連結
        PICK = {8282: ("l", 8283), 8297: ("m", 8298), 8301: ("l", 8302), 8305: ("r", 8306), 8316: ("l", 8317)}
        if n in PICK and 'class="flash"' in assets:
            side, tgt = PICK[n]
            x = {"l": (4.2, 25.8), "m": (37.2, 25.7), "r": (70.2, 25.7)}[side]
            assets = assets.replace('class="flash" ', 'class="flash" data-pick="1" ', 1).replace("></div>",
                f'><a class="pick" href="{base}/p/{tgt:06d}.html" title="下一頁" '
                f'style="left:{x[0]}%;width:{x[1]}%"></a></div>', 1)
        elif n in PICK and 'class="flashwin"' in assets:
            side, tgt = PICK[n]
            x = {"l": (4.2, 25.8), "m": (37.2, 25.7), "r": (70.2, 25.7)}[side]
            assets = assets.replace("</iframe></div>",
                f'</iframe><a class="pick" href="{base}/p/{tgt:06d}.html" title="下一頁" '
                f'style="left:{x[0]}%;width:{x[1]}%"></a></div>', 1)
        js = DIALOG_JS if 'class="dialog"' in text else ""
        if 'class="flashwin"' in assets:
            js += FLASHWIN_JS
        body_class = ""
        extra = ""
        if "HSCROLL" in pflags:
            # 橫向捲動頁：圖片比版面寬，放在可左右捲動的容器裡
            # 官方：整個內容框拉到跟版面一樣寬，圖片在可橫向捲動的容器裡，圖下方有一個 ==> 小箭頭
            arrow = esc(asset_base + "images/inline-text/hscrollarrow.gif")
            assets = (f'<div class="hscroll">{assets}'
                      f'<img class="hs-arrow" src="{arrow}" alt="==&gt;"></div>')
            body_class = "wide"
        if fb and fb[2] > 650 and ('class="flashwin"' in assets or 'class="flash"' in assets):
            body_class = "wide"  # 官方這幾頁的動畫比內容框寬（950px），整個內容框跟著拉寬
        if "WIDE950" in pflags and not body_class:
            body_class = "wide950"  # 官方這些頁的圖／動畫是 950 寬，內容框 950、文字區仍 650 置中
        if "FIREFLY" in pflags:
            if 'class="flashwin"' not in assets:  # Flash 頁的螢火蟲由官方動畫自己畫
                assets = assets.replace('<div class="assets">', f'<div class="assets ff" data-sprite="{esc(asset_base.rsplit("media/",1)[0] + "assets/")}">', 1)
                js += FIREFLY_JS
        if "ACT7" in pflags:
            banner = esc(asset_base + "images/banners/act7_header.gif")
            assets = f'<img class="banner" src="{banner}" alt="ACT 7">' + assets
            body_class = "act7"
        if "ENDCREDITS" in pflags:
            body_class = "endcredits"
            # 官方最後一頁的「==>」連回第一頁；我們的第一頁在繁中站
            next_html += ('<div class="nextlink"><span>&gt;</span> '
                          '<a href="https://zhhomestuck.github.io/p/001901">==&gt;</a></div>')
        if "COLLIDE" in pflags:
            banner = esc(asset_base + "images/banners/collide_header.gif")
            assets = f'<img class="banner" src="{banner}" alt="ACT 6 ACT 6 ACT 6">' + assets
            body_class = "collide"
        if "TZPASSWORD" in pflags:
            # 密碼頁：輸入正確密碼 → 下一頁；錯誤 → 顯示訊息；「回上一頁」→ 上一頁。
            # passwords.json 只存密碼的 SHA-256（大寫、去空白後），用 add_password.py 新增；
            # 還沒有密碼的頁面，改成連到官方頁面輸入。
            back = f'<a href="{pu}">← 或是回上一頁</a>' if pu else ""
            # 官方的「PASSWORD HINT」：按下去只會顯示同一句話（每個密碼頁都一樣）
            hintbox = (
                '<div class="hintbox"><button type="button" id="hintbtn">密碼提示</button>'
                '<p id="hinttext" hidden>如果你還不知道密碼，就代表你還不該知道，笨蛋！回去！！！</p></div>'
                '<script>document.getElementById("hintbtn").addEventListener("click",function(){'
                'var t=document.getElementById("hinttext");t.hidden=!t.hidden;});</script>'
            )
            h = pwhash.get(str(n))
            nu = (tlink(targets[0])[0] if targets else None)
            if h and nu:
                extra = (
                    '<div class="pw"><form id="pwform"><label>請輸入密碼：<br>'
                    '<input id="pwin" type="text" autocomplete="off" spellcheck="false"> '
                    '<button type="submit">送出</button></label></form>'
                    '<p id="pwmsg" class="hint2"></p>'
                    f"<p>{back}</p></div>" + hintbox +
                    '<script>(function(){var H="%s",U="%s";'
                    'document.getElementById("pwform").addEventListener("submit",function(e){'
                    'e.preventDefault();var v=document.getElementById("pwin").value.toUpperCase().replace(/\\s+/g,"");'
                    'crypto.subtle.digest("SHA-256",new TextEncoder().encode(v)).then(function(b){'
                    'var x=Array.from(new Uint8Array(b)).map(function(c){return c.toString(16).padStart(2,"0")}).join("");'
                    'if(x===H){location.href=U}else{document.getElementById("pwmsg").textContent="密碼不對。"}});});})();</script>'
                    % (h, nu)
                )
            else:
                extra = (
                    '<div class="pw"><p>請輸入密碼才能繼續。</p>'
                    f'<p class="box"><a href="{esc(official_link)}">到官方頁面輸入密碼</a></p>'
                    f"<p>{back}</p></div>" + hintbox
                )
        if "A6A6" in pflags:  # 官方 Act 6 Act 6 的綠色配色（body/外框/內容框 = #042300/#168500/#073c00，字 #2ed73a）
            body_class = (body_class + " a6a6").strip()
        top950 = ""
        h1 = f'<h1>{esc(pg["title"])}</h1>\n'
        if "wide950" in body_class.split() and 'class="flashwin"' not in assets:
            # 官方：圖貼在內容框最上面（沒有標題），文字區 650px 在圖的下面
            top950 = assets.replace('<div class="assets">', '<div class="assets top950">', 1) + "\n"
            assets = ""
            h1 = ""
        inner = f"""{top950}<article class="story">
{h1}{assets}{ruffle}
{extra}
{text}
{next_html}
<div class="story-foot">{foot}</div>
</article>
<div class="page-info">第 {n} 頁 ·
<span class="badge {pg["status"]}">{STATUS_LABEL[pg["status"]]}</span>{official}</div>
{js}"""
        (OUT / "p" / f"{n:06d}.html").write_text(
            layout(site, f'{pg["title"]} - {site["title"]}', inner, base, raw=True, body_class=body_class, sep_img=tooth),
            encoding="utf-8",
        )

    # 進度頁
    counts = Counter(p["status"] for p in pages)
    total = max(len(pages), 1)
    bar = "".join(
        f'<span style="width:{counts[s] / total * 100:.2f}%;background:var(--c-{s})"></span>'
        for s in STATUS_LABEL
    )
    summary = " ".join(
        f'<span class="badge {s}">{STATUS_LABEL[s]} {counts[s]}</span>' for s in STATUS_LABEL
    )
    buckets = {}
    for p in pages:
        key = p["page"] // 100 * 100
        buckets.setdefault(key, Counter())[p["status"]] += 1
    rows = "".join(
        f"<tr><td>{k}–{k + 99}</td>"
        + "".join(f"<td>{c[s]}</td>" for s in STATUS_LABEL)
        + f"<td>{sum(c.values())}</td></tr>"
        for k, c in sorted(buckets.items())
    )
    head = "".join(f"<th>{STATUS_LABEL[s]}</th>" for s in STATUS_LABEL)
    inner = f"""<h1>翻譯進度</h1>
<p>目前共收錄 {len(pages)} 頁。</p>
<div class="bar">{bar}</div>
<p>{summary}</p>
<table><tr><th>頁碼範圍</th>{head}<th>合計</th></tr>{rows}</table>"""
    (OUT / "progress.html").write_text(
        layout(site, f"翻譯進度 - {site['title']}", inner, base), encoding="utf-8"
    )

    # 首頁
    start = (
        f'<p><a href="{base}/p/{pages[0]["page"]:06d}.html">從第 {pages[0]["page"]} 頁開始閱讀 →</a></p>'
        if pages else "<p>目前還沒有內容。</p>"
    )
    inner = f"""<h1>{esc(site["title"])}</h1>
<p>{esc(site.get("subtitle", ""))}</p>
{start}
<p><a href="{base}/progress.html">查看翻譯進度</a></p>"""
    (OUT / "index.html").write_text(
        layout(site, site["title"], inner, base), encoding="utf-8"
    )

    print(f"完成：{len(pages)} 頁（另有隱藏頁 {len(hidden_pages)}）→ {OUT}")


if __name__ == "__main__":
    build()
