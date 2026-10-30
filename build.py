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
.story .assets img,.story .assets video{width:650px;max-width:100%;height:auto;display:block;margin:0 auto}
.flash{margin:0 auto;max-width:650px}
.official-frame{margin:0 auto}
.official-frame iframe{width:100%;height:700px;border:0;background:#fff;display:block}
.hscroll{overflow-x:auto;margin:0}
.story .hscroll img{width:auto;max-width:none;margin:0}
.hint{color:#555;font-size:12px;text-align:center;margin:6px 16px}
.pw{margin:16px 28px 0;text-align:center;font:14px/1.8 Verdana,"Microsoft JhengHei",sans-serif}
.pw .box{display:inline-block;margin:6px 0;padding:6px 14px;border:1px dashed #888}
.assets.ff{position:relative}
.assets.ff canvas{position:absolute;left:0;top:0;width:100%;height:100%;pointer-events:none}
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
<script src="https://unpkg.com/@ruffle-rs/ruffle"></script>
<script>
window.addEventListener("load", function () {
  var R = window.RufflePlayer && window.RufflePlayer.newest();
  if (!R) return;
  document.querySelectorAll(".flash").forEach(function (d) {
    var p = R.createPlayer();
    p.style.width = "650px"; p.style.maxWidth = "100%"; p.style.height = "450px";
    d.appendChild(p);
    p.load(d.dataset.swf);
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
    meta["body"] = m.group(2).strip("\n")
    return meta


def esc(s):
    return html.escape(s, quote=True)


def layout(site, title, inner, base, raw=False, body_class=""):
    credits = "".join(
        f'<li><a href="{esc(c["url"])}">{esc(c["name"])}</a>：{esc(c.get("note", ""))}</li>'
        for c in site.get("credits", [])
    )
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
<a class="name" href="{base}/">{esc(site["title"])}</a> |
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
FIREFLY_JS = """<script>
(function(){
  var box=document.querySelector(".assets.ff"); if(!box) return;
  var c=document.createElement("canvas"); box.appendChild(c);
  var x=c.getContext("2d"), flies=[], i;
  function size(){c.width=box.clientWidth; c.height=box.clientHeight;}
  size(); window.addEventListener("resize",size);
  for(i=0;i<4;i++) flies.push({x:Math.random(),y:Math.random(),a:Math.random()*6.28});
  function tick(){
    x.clearRect(0,0,c.width,c.height);
    flies.forEach(function(f){
      f.a+=(Math.random()-.5)*.6;
      f.x=(f.x+Math.cos(f.a)*.002+1)%1; f.y=(f.y+Math.sin(f.a)*.002+1)%1;
      var px=f.x*c.width, py=f.y*c.height;
      x.fillStyle="#000"; x.fillRect(px-2,py-2,4,4);
      x.fillStyle="rgba(255,255,160,.9)"; x.fillRect(px+(Math.random()<.5?2:-4),py+2,2,2);
    });
    requestAnimationFrame(tick);
  }
  tick();
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


def asset_html(page, manifest, asset_base, fallback_base="", flash_mode="iframe", official_page_url=""):
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
        elif kind == "flash":
            # flash_mode（site.json）：
            #   iframe：直接嵌入官方頁面，由官方站播放（官方的 SWF 只允許 www.homestuck.com 讀取，
            #           實測 2026-10-29 自己用 Ruffle 讀會被 CORS 擋住）
            #   ruffle：用 Ruffle 播放 asset_base 底下的 SWF（asset_base 要能讓你的網站讀取）
            #   link ：只顯示「請到官方頁面觀看」
            if flash_mode == "ruffle":
                parts.append(f'<div class="flash" data-swf="{url}"></div>')
            elif flash_mode == "iframe" and official_page_url:
                if not any('class="official-frame"' in p for p in parts):
                    parts.append(
                        f'<div class="official-frame"><iframe src="{esc(official_page_url)}" '
                        'title="官方頁面" loading="lazy"></iframe>'
                        '<p class="noasset">這頁是 Flash 動畫，畫面直接來自官方站。</p></div>'
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
    sources = load_sources(ROOT / "sources.csv")
    base =site.get("base_url", "").rstrip("/")
    asset_base = site.get("asset_base", "")
    if asset_base and not asset_base.endswith("/"):
        asset_base += "/"
    fallback_base = site.get("asset_fallback_base", "")
    if fallback_base and not fallback_base.endswith("/"):
        fallback_base += "/"
    official_tpl = site.get("official_url", "")
    flash_mode = site.get("flash_mode", "iframe")

    all_pages = sorted(
        (parse_page(p) for p in CONTENT.glob("*.md")), key=lambda d: d["page"]
    )
    # 隱藏頁（front matter 寫 hidden: true）：有網址，但不在上一頁／下一頁的路徑上，也不算進度
    pages = [p for p in all_pages if p.get("hidden", "").lower() != "true"]
    hidden_pages = [p for p in all_pages if p.get("hidden", "").lower() == "true"]
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

    # 各頁
    for pg in all_pages:
        n = pg["page"]
        before = [p for p in pages if p["page"] < n]
        after = [p for p in pages if p["page"] > n]
        next_html = (
            f'<div class="nextlink"><span>&gt;</span> <a href="{base}/p/{after[0]["page"]:06d}.html">'
            f'{esc(after[0]["title"])}</a></div>'
            if after else ""
        )
        foot = (
            (f'<a href="{base}/p/{before[-1]["page"]:06d}.html">← 上一頁</a>' if before
             else '<span class="gone">← 上一頁</span>')
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
        assets = asset_html(n, manifest, asset_base, fallback_base, flash_mode, official_link)
        ruffle = RUFFLE_JS if 'class="flash"' in assets else ""
        js = DIALOG_JS if 'class="dialog"' in text else ""
        pflags = flags.get(str(n), [])
        body_class = ""
        extra = ""
        if "HSCROLL" in pflags:
            # 橫向捲動頁：圖片比版面寬，放在可左右捲動的容器裡
            assets = f'<div class="hscroll">{assets}</div><p class="hint">← 這頁的圖片很寬，請用左右捲動查看 →</p>'
        if "FIREFLY" in pflags:
            assets = assets.replace('<div class="assets">', '<div class="assets ff">', 1)
            js += FIREFLY_JS
        if "COLLIDE" in pflags:
            banner = esc(asset_base + "images/banners/collide_header.gif")
            assets = f'<img class="banner" src="{banner}" alt="ACT 6 ACT 6 ACT 6">' + assets
            body_class = "collide"
        if "TZPASSWORD" in pflags:
            # 密碼頁：官方要輸入密碼才能繼續；密碼不在我們手上，輸入請到官方頁面
            back = (f'<a href="{base}/p/{before[-1]["page"]:06d}.html">← 回上一頁</a>' if before else "")
            extra = (
                '<div class="pw"><p>請輸入密碼才能繼續。</p>'
                f'<p class="box"><a href="{esc(official_link)}">到官方頁面輸入密碼</a></p>'
                f"<p>{back}</p></div>"
            )
        inner = f"""<article class="story">
<h1>{esc(pg["title"])}</h1>
{assets}{ruffle}
{extra}
{text}
{next_html}
<div class="story-foot">{foot}</div>
</article>
<div class="page-info">第 {n} 頁 ·
<span class="badge {pg["status"]}">{STATUS_LABEL[pg["status"]]}</span>{official}</div>
{js}"""
        (OUT / "p" / f"{n:06d}.html").write_text(
            layout(site, f'{pg["title"]} - {site["title"]}', inner, base, raw=True, body_class=body_class),
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
