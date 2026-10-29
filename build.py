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
:root{--bg:#fdfdfb;--fg:#222;--muted:#777;--line:#ddd;--accent:#2a6f97;
--c-converted:#d9822b;--c-proofreading:#2a6f97;--c-done:#3a8f5c}
@media (prefers-color-scheme:dark){:root{--bg:#17181a;--fg:#e6e6e6;--muted:#9a9a9a;
--line:#34363a;--accent:#7fb7d9}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:17px/1.8 -apple-system,"Noto Sans TC","PingFang TC","Microsoft JhengHei",sans-serif}
a{color:var(--accent)}
header.site,main,footer{max-width:760px;margin:0 auto;padding:0 16px}
header.site{padding-top:14px;padding-bottom:10px;border-bottom:1px solid var(--line);
display:flex;gap:16px;flex-wrap:wrap;align-items:baseline}
header.site .name{font-weight:700;margin-right:auto}
main{padding-top:20px;padding-bottom:30px}
h1{font-size:1.4rem;margin:.2em 0 .4em}
.meta{color:var(--muted);font-size:.85rem;margin-bottom:1em}
.badge{display:inline-block;padding:0 .6em;border-radius:1em;font-size:.8rem;color:#fff}
.badge.converted{background:var(--c-converted)}
.badge.proofreading{background:var(--c-proofreading)}
.badge.done{background:var(--c-done)}
.assets img,.assets video{max-width:100%;height:auto;display:block;margin:0 auto 1em}
.flash{margin:0 auto 1em;max-width:650px}
.official-frame{margin:0 auto 1em;max-width:760px}
.official-frame iframe{width:100%;height:660px;border:1px solid var(--line);background:#fff}
.yt{aspect-ratio:16/9;max-width:720px;margin:0 auto 1em}
.yt iframe{width:100%;height:100%;border:0}
.noasset{color:var(--muted);font-size:.85rem;text-align:center;margin-bottom:1em}
.text p{margin:.35em 0}
nav.pager{display:flex;justify-content:space-between;margin:2em 0;gap:12px}
nav.pager a{padding:.4em .9em;border:1px solid var(--line);border-radius:6px;text-decoration:none}
table{border-collapse:collapse;width:100%;font-size:.9rem}
th,td{border-bottom:1px solid var(--line);padding:.35em .5em;text-align:right}
th:first-child,td:first-child{text-align:left}
.bar{display:flex;height:.9em;border-radius:4px;overflow:hidden;background:var(--line);margin:.5em 0}
.bar span{display:block;height:100%}
footer{color:var(--muted);font-size:.8rem;padding-bottom:40px;border-top:1px solid var(--line);padding-top:14px}
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


def layout(site, title, inner, base):
    credits = "".join(
        f'<li><a href="{esc(c["url"])}">{esc(c["name"])}</a>：{esc(c.get("note", ""))}</li>'
        for c in site.get("credits", [])
    )
    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<link rel="stylesheet" href="{base}/style.css">
</head>
<body>
<header class="site">
<a class="name" href="{base}/">{esc(site["title"])}</a>
<a href="{base}/progress.html">翻譯進度</a>
</header>
<main>
{inner}
</main>
<footer>
<p>{esc(site.get("copyright", ""))}</p>
<ul>{credits}</ul>
</footer>
</body>
</html>
"""


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
            parts.append(f'<img src="{url}"{onerr}alt="{esc(it.get("alt", ""))}" loading="lazy">')
        elif kind == "video":
            parts.append(f'<video src="{url}"{onerr}controls preload="none"></video>')
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

    pages = sorted(
        (parse_page(p) for p in CONTENT.glob("*.md")), key=lambda d: d["page"]
    )
    nums = [p["page"] for p in pages]
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
    for i, pg in enumerate(pages):
        n = pg["page"]
        prev_a = (
            f'<a href="{base}/p/{pages[i-1]["page"]:06d}.html">← 上一頁</a>'
            if i > 0 else "<span></span>"
        )
        next_a = (
            f'<a href="{base}/p/{pages[i+1]["page"]:06d}.html">下一頁 →</a>'
            if i < len(pages) - 1 else "<span></span>"
        )
        text = "\n".join(
            f"<p>{esc(line)}</p>" for line in pg["body"].splitlines() if line.strip()
        )
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
        inner = f"""<h1>{esc(pg["title"])}</h1>
<div class="meta">第 {n} 頁 ·
<span class="badge {pg["status"]}">{STATUS_LABEL[pg["status"]]}</span>{official}</div>
{assets}{ruffle}
<div class="text">
{text}
</div>
<nav class="pager">{prev_a}{next_a}</nav>"""
        (OUT / "p" / f"{n:06d}.html").write_text(
            layout(site, f'{pg["title"]} - {site["title"]}', inner, base),
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

    print(f"完成：{len(pages)} 頁 → {OUT}")


if __name__ == "__main__":
    build()
