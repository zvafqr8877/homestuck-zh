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
header.site{background:#535353;padding:0 8px;font:10px/1 Verdana,"Microsoft JhengHei",sans-serif}
header.site .navin{display:flex;flex-wrap:wrap;justify-content:center;align-items:center;max-width:896px;margin:0 auto;padding:2px 0;white-space:nowrap}
header.site .grp{display:block}
header.site ul{display:flex;margin:0;padding:0;list-style:none}
header.site li{position:relative}
header.site li+li:before{content:"|";color:#fff;margin:0 2px}
header.site a{color:#fff;font-weight:700;text-decoration:underline}
header.site .g1 a{color:#fff}
header.site .g2 a{color:#29ff4a}
header.site .g3 a{color:#39d5f6}
header.site .g4 a{color:#f7f72a}
header.site .g5 a{color:#ffb529}
header.site img{margin:2px 6px 0;height:16px;vertical-align:top}
header.site .menu{position:absolute;left:0;top:100%;width:220px;background:#c6c6c6;box-shadow:4px 4px rgba(0,0,0,.3);font-size:16px;line-height:24px;opacity:0;pointer-events:none;transition:opacity 1s;z-index:50;text-align:left}
header.site li:hover>.menu,header.site li:focus-within>.menu{opacity:1;pointer-events:auto}
header.site .menu ul{display:block}
header.site .menu li{border-bottom:1px solid #000}
header.site .menu li+li:before{content:none}
header.site .menu a{display:flex;padding-left:4px;color:#00f;font-weight:700;text-decoration:underline}
header.site .menu a:hover,header.site .menu a:focus{color:#fff;background:#61d8ff}
header.site .dd>a{cursor:pointer}
.logbox{padding:8px 12px;font-size:12px}
.logbox h1{text-align:center;font-size:24px;margin:4px 0}
.logbox ul{list-style:none;margin:0;padding:0}
.newreader p{font-size:14px;margin:.7em 0}.newreader h2{text-align:center;font-size:18px;margin:4px 0 10px}.archive{font-weight:700;font-size:16px;padding:8px;font-family:Verdana,"Microsoft JhengHei",sans-serif}.archive header{display:flex;flex-direction:column;align-items:center;gap:16px;margin:16px 0}.logbox.archive h1{font:700 36px/40px "Courier New",CourierPrime,courier,"Microsoft JhengHei",monospace;margin:0}.archive header p{font-weight:400;text-align:center;margin:0;line-height:24px}.arch{display:flex;align-items:center;align-self:center;width:100%;max-width:650px;margin:0 auto;padding:16px 0}.arch>a{display:contents}.arch img{display:block;width:164px;height:164px;max-width:100%;flex:none}.arch>div{display:flex;flex-direction:column;align-items:center;flex:1 1 0;min-width:0;padding:16px 24px}.arch h2{font:700 36px/40px "Courier New",CourierPrime,courier,"Microsoft JhengHei",monospace;text-align:center;padding:0 0 16px;margin:0}.arch p{font-weight:400;text-align:center;line-height:24px;padding:0 0 16px;margin:0}.arch p span{font-weight:700}.arch li span.off{text-decoration:line-through}.arch ul{display:flex;gap:12px;margin:0;padding:0;font-weight:400;list-style:none;line-height:24px}.arch li{padding-left:4px}.arch li+li{list-style:"|" outside;margin-left:0}@media (max-width:649px){.arch{flex-direction:column}}body.offi main.wrap{max-width:940px;padding:0;display:flow-root}.logbox.archive{margin:8px;background:#eee;padding:8px}body.owhite main.wrap{max-width:650px;padding:0;background:#fff;display:flow-root;margin:0 auto 40px}.oc{margin:8px;background:#eee;padding:8px;display:flex;flex-direction:column;font:700 16px/24px Verdana,"Microsoft JhengHei",sans-serif;color:#000}.oc.ocsearch h1{font:700 36px/40px "Courier New",CourierPrime,courier,"Microsoft JhengHei",monospace;margin:8px 0 0;align-self:center}
.ocsearch .sbox{display:flex;align-self:center;width:775px;max-width:100%;padding:16px 0}
.ocsearch .scard{display:flex;flex-direction:column;gap:16px;padding:12px 0;margin:8px 0 24px;width:100%;background:#eee;font-weight:400}
.ocsearch input[type=text]{display:block;width:100%;box-sizing:border-box;background:#fff;color:#000;padding:4px;font:400 16px/24px Verdana,"Microsoft JhengHei",sans-serif;border-radius:0}
.ocsearch .sq1{border:0;border-bottom:1px solid #000}
.ocsearch .sq2{border:1px solid #000}
.ocsearch .sexact{display:flex;align-items:center;gap:5px;height:24px;font-weight:400}
.ocsearch .sexact input{margin:0;width:13px;height:13px}
.ocsearch h2{font:700 36px/40px "Courier New",CourierPrime,courier,"Microsoft JhengHei",monospace;align-self:center;margin:8px 0 0}
.ocsearch .sempty{align-self:center;font:400 16px/24px "Courier New",CourierPrime,courier,"Microsoft JhengHei",monospace}
.ocsearch ul{list-style:none;margin:0;padding:0}
.ocsearch .sres{display:flex;flex-direction:column;align-items:center;margin:16px}
.ocsearch .sres h3{margin:0;font:700 18px/28px Verdana,"Microsoft JhengHei",sans-serif;color:#00f;text-decoration:underline}
.ocsearch .sres p{margin:16px;font-weight:400;word-break:break-all}
.ocsearch .sres p b{font-weight:700}
.ocsearch .sline{border-bottom:1px solid #000;width:40%}
.ocsearch .spg{display:flex;align-self:center}
.ocsearch .spg button{font:400 16px/24px Verdana,"Microsoft JhengHei",sans-serif;gap:8px;padding:16px;background:none;border:0;color:#000;cursor:pointer}
.ocsearch .spg button.cur{font-weight:700}
.ocsearch .spg button:disabled{cursor:not-allowed;opacity:.5}
.oc h1{font:700 30px/36px "Courier New",CourierPrime,courier,"Microsoft JhengHei",monospace;align-self:center;margin:0}.oc ul{list-style:none;margin:0;padding:0}.oclog .tg{display:block;font:700 10px/15px Verdana,"Microsoft JhengHei",sans-serif;padding:0 0 8px;color:#00f;text-decoration:underline}.oclog li span{font-size:12px;line-height:16px}.ocmap h1{padding:16px 0 40px}.mbox{display:flex;background:#fff;width:100%}.mleft{display:flex;flex-direction:column;min-width:0}.mrw{display:flex;justify-content:center;padding:8px}.mflex{display:flex}.msb{display:none;flex-direction:column;align-items:flex-end;border-right:8px solid}.msb.l{align-items:flex-start;border-right:0;border-left:8px solid}.mlab{width:fit-content;min-width:30px;height:fit-content;margin-top:32px;padding-top:4px;color:#fff}.upright{writing-mode:vertical-lr;text-orientation:upright;font:400 16px/24px Homestuck,monospace;margin:0;color:#fff}.upright .a{font-size:14px;line-height:20px;padding-bottom:8px}.upright .b{font-size:30px;line-height:36px}.msb img{margin-top:4px;max-width:100%;height:auto}.msb img.mi{margin-top:4px}.mside>.mflex>.msb img{margin-top:8px}.mbr{display:none;width:16px;border-top:8px solid;border-bottom:8px solid;margin-right:12px}.mbr.l{margin-right:0;margin-left:12px}.mcont{min-width:0}.mpc{display:flex;flex-direction:column;align-items:center;min-width:0}.mpc a{display:block;max-width:100%}.mpc img{display:block;max-width:100%;height:auto}.mrow{display:flex}.mrow a{flex:0 1 auto}.mcode{text-align:center;font:400 20px/28px Verdana,"Microsoft JhengHei",sans-serif;margin:20px 0}.mright{display:flex;flex-direction:column;padding:8px;flex-grow:1}.mrt{display:flex}@media (min-width:650px){.msb{display:flex}.mcode.m0{margin-left:60px}.mcode.m1{margin-left:200px}.mcode.m2{margin-left:70px}}@media (min-width:950px){.mbr{display:block}.mbr.l{display:block}}.ocnr{flex-direction:row;justify-content:center}.ocnr>div{max-width:750px;width:100%;display:flex;flex-direction:column;gap:28px;margin:32px 0;font-weight:400}.ocnr p{text-align:center;margin:0}.ocnr h2{font-size:16px;font-weight:400;align-self:center;margin:0}.ocnr button{font:400 48px/48px Homestuck,"Microsoft JhengHei",monospace;border:5px solid #000;background:#fff;color:#000;padding:16px 24px;cursor:pointer;max-width:100%}.ocnr button:hover{background:#000;color:#fff}.ocnr section{display:flex;flex-direction:column;gap:32px}.ocnr section p{text-align:left}.ocnr section ul{list-style:disc;margin:0 0 0 40px;padding:0;display:flex;flex-direction:column}.ow{font:400 16px/24px Verdana,"Microsoft JhengHei",sans-serif;color:#000;background:#fff}.ow header{display:flex;flex-direction:column;gap:16px;margin:16px 0}.ow h1{font:700 36px/40px "Courier New",CourierPrime,courier,"Microsoft JhengHei",monospace;text-align:center;margin:0}.ow section{display:flex;flex-direction:column;align-items:center;gap:16px;padding:16px;text-align:center}.ow h2{font:700 16px/24px Verdana,"Microsoft JhengHei",sans-serif;margin:16px 0 0}.ow p{margin:0}.ow ul{list-style:none;padding:0;margin:0}.ow ol{display:flex;flex-direction:column;gap:16px;margin:0;padding:0;list-style-position:inside}.ow ul.left,.ow .left{text-align:left}.logbox>a{font-size:10px;font-weight:700;display:block;padding-bottom:8px}
main.wrap{max-width:940px;margin:0 auto;background:#c6c6c6;padding:0;display:flex;flex-direction:column;align-items:center}
article.story{width:100%;max-width:650px;margin:8px 0 24px;background:#eee;padding:12px 0;display:flex;flex-direction:column;gap:16px}
.story h1{font:700 30px/36px "Courier New",CourierPrime,courier,"Microsoft JhengHei",monospace;text-align:center;margin:0 32px}
.story .assets{margin:0 0 16px}
.story .assets>*+*{margin-top:32px}
.story .assets img,.story .assets video{width:650px;max-width:100%;height:auto;display:block;margin:0 auto}
.flash{margin:0 auto;max-width:650px;position:relative}
.flash a.pick{pointer-events:none;position:absolute;z-index:3;top:34.7%;height:40.5%;display:block;background:transparent;cursor:pointer}
.flash a.pick.late{visibility:hidden;animation:pickshow 0s linear forwards}
@keyframes pickshow{to{visibility:visible}}
.flashwin{position:relative;width:100%;overflow:hidden;margin:0 auto;background:#fff}
.flashwin a.pick{position:absolute;z-index:3;top:34.7%;height:40.5%;display:block;background:transparent;cursor:pointer}
.flashwin iframe{position:absolute;left:0;top:0;width:1000px;height:1600px;border:0;transform-origin:0 0}
.hscroll{overflow-x:scroll;margin:0 0 16px}
.story .hscroll .assets img{width:auto;max-width:none;margin:0}
.story .hscroll>img.hs-arrow{width:82px;height:32px;margin:0}
body.wide950 main.wrap{max-width:950px;padding:0}
body.wide950 .assets.top950{margin:0}
body.wide950 .assets.top950 .flashwin,body.wide950 .assets.top950 .flash{max-width:950px}
body.wide950 .assets.top950 img,body.wide950 .assets.top950 video{width:950px;max-width:none;margin:0;display:block}
body.wide950 article.story{margin:0 auto 14px}
body.bare,body.bare main.wrap{background:#fff}
body.bare header.site{display:none}
body.gameover header.site,body.gameover article.story,body.gameover .page-info,body.gameover footer{display:none}
body.gameover main.wrap{margin-bottom:0}
body.bare article.story{background:#fff}
body.wide main.wrap{max-width:none;margin:0 12px}
body.wide article.story{max-width:none}
.branchrow{margin:14px 28px;text-align:center;font:16px/1.8 "Courier New",monospace}
.pw{margin:16px 28px 0;text-align:center;font:14px/1.8 Verdana,"Microsoft JhengHei",sans-serif}
@font-face{font-family:Homestuck;src:url("assets/fonts/homestuck.woff2") format("woff2");font-display:swap}
.pw input{text-transform:uppercase;font:16px/24px Homestuck,monospace;padding:2px 6px;width:200px}
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
.plain{margin:0 24px;text-align:center;font:400 16px/1.55 "Courier New",CourierPrime,courier,"Microsoft JhengHei","Noto Sans TC",monospace}
.plain p{margin:0 0 16px}.plain p:last-child{margin-bottom:0}
.nextlink{margin:16px 24px;font:24px/32px Verdana,"Microsoft JhengHei",sans-serif}
.nextlink span{color:#000}
.story-foot{margin:0 28px;font:12px/1.6 Verdana,"Microsoft JhengHei",sans-serif}
.footrow{display:flex;align-items:flex-end;justify-content:space-between;margin:0 -4px}.footrow .startover{list-style:"|" outside;margin:0;padding:0;display:flex;font:700 10px/12px Verdana,"Microsoft JhengHei",sans-serif}.footrow .startover li{padding:0 4px;margin-right:4px}.footrow .startover li:first-child,.savebar li:first-child{list-style:none}.footrow a{color:#0000ee;text-decoration:underline}
.savebar{display:flex;justify-content:flex-end;position:relative;margin:0 0 0 auto;font:700 10px/12px Verdana,"Microsoft JhengHei",sans-serif}
.savebar.first{justify-content:flex-start;margin:0}
.savebar ul{list-style:"|" outside;margin:0;padding:0;display:flex;flex-wrap:wrap}
.savebar li{padding:0 4px;margin-right:4px}

.savebar button{font:inherit;background:none;border:0;padding:0;margin:0;color:#0000ee;text-decoration:underline;cursor:pointer}
.savebar .tip{margin-left:3px;color:#0000ee;text-decoration:underline;cursor:pointer;position:relative}
.savebar .tipbox{position:absolute;bottom:100%;right:0;width:260px;background:#eee;border:4px solid #ccc;padding:8px 10px;margin-bottom:6px;font:400 12px/1.6 Verdana,"Microsoft JhengHei",sans-serif;color:#000;text-align:left;z-index:20}
.savebar .toast{position:absolute;bottom:100%;right:0;background:#eee;border:4px solid #ccc;padding:6px 14px;margin-bottom:6px;font:400 14px/1.6 Verdana,"Microsoft JhengHei",sans-serif;color:#000;z-index:21}
.a6a6 .savebar button,.a6a6 .savebar .tip{color:#2ed73a}
.collide .savebar button,.collide .savebar .tip,.endcredits .savebar button,.endcredits .savebar .tip{color:#8cf}
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
footer.site{max-width:940px;margin:12px auto 0;padding:14px 20px 24px;background:#ececec;color:#000;font:12px/1.7 Verdana,"Microsoft JhengHei",sans-serif}
footer.site a{color:#00f}
footer.site .line{font-weight:700;margin:0 0 6px}
footer.site p{margin:.4em 0}
footer.site ul{margin:.4em 0;padding-left:1.2em}
footer.site h2{font:700 13px/1.6 Verdana,"Microsoft JhengHei",sans-serif;margin:10px 0 2px}
@media (max-width:560px){.story h1{font-size:22px}.dialog{margin:12px 8px 0;padding:6px 10px 12px}.nextlink,.story-foot,.plain{margin-left:12px;margin-right:12px}.nextlink{font-size:20px}main.wrap{padding:0}}
"""


RUFFLE_JS = r"""
<script>window.RufflePlayer=window.RufflePlayer||{};window.RufflePlayer.config={autoplay:"on",unmuteOverlay:"hidden",splashScreen:false,letterbox:"on",contextMenu:"off"};</script>
<script>
// Ruffle 設定（照官方站實測的設定：腳本權限、透明、字型、舊 MSPA 連結改寫）。
// Flash 裡的連結是舊網址 http://www.mspaintadventures.com/?s=6&p=008106，這裡改成本站頁面。
(function () {
  var base = location.pathname.replace(/\/p\/[^\/]*$/, "");
  window.RufflePlayer = window.RufflePlayer || {};
  window.RufflePlayer.config = {
    allowScriptAccess: true, wmode: "transparent", letterbox: "on", autoplay: "on", splashScreen: false,
    unmuteOverlay: "visible", scale: "showall", upgradeToHttps: true,
    fontSources: [base + "/assets/ruffle/homestuck-fonts.swf", base + "/assets/ruffle/courier-new-pixel.swf"],
    defaultFonts: {sans: ["Arial"], serif: ["Times New Roman"], typewriter: ["Courier New"]},
    // 格式和官方站一致：[ "/正規表示式/", "取代成" ]
    urlRewriteRules: [
      ["/^http:\\/\\/www\\.mspaintadventures\\.com\\/\\?s=6&p=(\\d+)/", base + "/p/$1.html"],
      ["/^http:\\/\\/www\\.mspaintadventures\\.com\\/\\?s=4/", "https://zhhomestuck.github.io/"],
      // 繁中站翻譯過的 Flash 裡的連結（https://zhhomestuck.github.io/p/005786 或相對的 /p/005786）改成本站頁面
      ["/^https?:\\/\\/zhhomestuck\\.github\\.io\\/p\\/+(\\d+)(?:\\.html)?/", base + "/p/$1.html"],
      ["/^https?:\\/\\/[^\\/]*github\\.io\\/p\\/+(\\d+)(?:\\.html)?/", base + "/p/$1.html"],
      ["/^http:\\/\\/www\\.mspaintadventures\\.com\\/(soundcredits|artcredits)\\.html/", base + "/"],
      ["/^http:\\/\\/www\\.mspaintadventures\\.com\\/storyfiles\\/hs2\\/(\\d+)\\/([^\\/]+)\\.(\\w+)/", "https://storage.homestuck.com/story/homestuck/media/audio/$1/$2.$3"],
      ["/^http:\\/\\/www\\.mspaintadventures\\.com\\/storyfiles\\/hs2\\/songs\\/alterniaboundsongs\\/([^\\/]+)\\.(\\w+)/", "https://storage.homestuck.com/story/homestuck/media/audio/004692/$1.$2"],
      ["/^http:\\/\\/www\\.timelesschaos\\.com\\/transferFiles\\/618heircut.mp3/", "https://storage.homestuck.com/story/homestuck/media/audio/005221/618heircut.mp3"]
    ]
  };
})();
</script>
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
  });
  // 動畫上的換頁連結：連結本身不擋滑鼠（動畫的滑過效果才看得到），改成監聽點擊，點在連結範圍內就換頁
  document.querySelectorAll(".flash[data-pick]").forEach(function (d) {
    var links = d.querySelectorAll("a.pick");
    // 「點擊以取消靜音」遮罩還在時不啟用連結（那一下點擊只用來取消靜音）
    // 找得到遮罩就看它有沒有顯示；找不到（版本不同）就當作第一下點擊是取消靜音
    var unlocked = false;
    function muted() {
      var p = d.querySelector("ruffle-player"), sr = p && p.shadowRoot;
      var o = sr && sr.querySelector('#unmute-overlay,[id*="unmute"],[class*="unmute"]');
      if (unlocked) return false;
      if (!o) return true;
      var cs = getComputedStyle(o);
      return cs.display !== "none" && cs.visibility !== "hidden" && o.getBoundingClientRect().width > 0;
    }
    function hit(e) {
      if (muted()) return null;
      for (var i = 0; i < links.length; i++) {
        var a = links[i], r = a.getBoundingClientRect();
        if (getComputedStyle(a).visibility === "hidden") continue;
        if (e.clientX >= r.left && e.clientX <= r.right && e.clientY >= r.top && e.clientY <= r.bottom) return a;
      }
      return null;
    }
    // 點在連結範圍內時，不讓滑鼠按下/放開/點擊傳給動畫（否則動畫自己的 getURL 會另外開官方舊網址 mspaintadventures.com）
    ["pointerdown", "mousedown", "pointerup", "mouseup", "touchstart", "touchend"].forEach(function (t) {
      d.addEventListener(t, function (e) {
        var x = e.touches && e.touches[0] || e.changedTouches && e.changedTouches[0] || e;
        if (hit({clientX: x.clientX, clientY: x.clientY})) { e.stopImmediatePropagation(); e.stopPropagation(); }
      }, true);
    });
    d.addEventListener("click", function (e) {
      var a = hit(e); unlocked = true;
      if (a) { e.preventDefault(); e.stopImmediatePropagation(); e.stopPropagation(); location.href = a.href; }
    }, true);
    d.addEventListener("mousemove", function (e) { d.style.cursor = hit(e) ? "pointer" : ""; });
  });
});
</script>"""


SEARCH_JS = r"""<script>(function(){
var D=null,q=document.getElementById('sq'),a=document.getElementById('sa'),x=document.getElementById('sx'),
    sm=document.getElementById('sm'),sr=document.getElementById('sr'),sp=document.getElementById('sp'),res=[],cur=1,PER=10;
function E(s){return String(s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
var ACTS=ACTS_JSON;
function parseAdv(v){var o={rng:[],chars:[],on:false},p=v.toLowerCase().trim().split(/\b(acts|pages|chars):/),k,key,val;
  for(k=1;k<p.length;k+=2){key=p[k];val=p[k+1].trim().replace(/,$/,'');
    if(key==='acts'){val.split(',').forEach(function(t){t=t.trim();if(ACTS[t]){o.rng.push(ACTS[t]);o.on=true}})}
    else if(key==='pages'){val.split(',').forEach(function(t){var m=t.trim().match(/^(\d+)(?:-(\d+))?$/);if(m){o.rng.push([+m[1],m[2]?+m[2]:+m[1]]);o.on=true}})}
    else if(key==='chars'){o.chars=val.split(',').map(function(t){return t.trim()}).filter(Boolean);if(o.chars.length)o.on=true}}
  return o}
function inRng(r,n){for(var i=0;i<r.length;i++)if(n>=r[i][0]&&n<=r[i][1])return true;return false}
function load(cb){if(D)return cb();fetch('BASE/search_index.json').then(function(r){return r.json()}).then(function(d){D=d;cb()}).catch(function(){sm.innerHTML='<i>索引載入失敗。</i>'})}
function run(){var v=q.value.toLowerCase().trim(),w=x.checked?(v?[v]:[]):v.split(/\s+/).filter(Boolean),ad=parseAdv(a.value);
  cur=1;res=[];if(!w.length&&!ad.on){draw();return}
  load(function(){var i,r,h,lab;
    for(i=0;i<D.length&&res.length<2000;i++){r=D[i];if(ad.rng.length&&!inRng(ad.rng,r[0]))continue;h=(r[1]+' '+r[2]).toLowerCase();
      if(!w.every(function(t){return h.indexOf(t)>=0}))continue;
      if(ad.chars.length&&!ad.chars.some(function(c){return h.indexOf(c+'：')>=0||h.indexOf(c+':')>=0}))continue;
      res.push(r)}
    draw()})}
function label(t){var m=t.match(/^((?:\s*\[[^\]]*\])*\s*)([^：:]{1,16})([：:])([\s\S]*)$/);
  return m?E(m[1])+'<b>'+E(m[2])+'</b>'+E(m[3]+m[4]):E(t)}
function draw(){sm.style.display=res.length?'none':'';
  sr.innerHTML=res.slice((cur-1)*PER,cur*PER).map(function(r){return '<li><section class="sres"><a href="BASE/p/'+('00000'+r[0]).slice(-6)+'.html" target="_blank"><h3>第 '+('00000'+r[0]).slice(-6)+' 頁</h3></a><p>'+label(r[1])+'</p><div class="sline"></div></section></li>'}).join('');
  var tot=Math.ceil(res.length/PER);if(tot<=1){sp.innerHTML='';return}
  var st=Math.max(1,Math.min(cur-4,tot-9)),en=Math.min(tot,st+9),h='<div><button type="button"'+(cur<=1?' disabled':'')+' data-p="'+(cur-1)+'">上一頁</button>',k;
  for(k=st;k<=en;k++)h+='<button type="button"'+(k===cur?' class="cur"':'')+' data-p="'+k+'">'+k+'</button>';
  sp.innerHTML=h+'<button type="button"'+(cur>=tot?' disabled':'')+' data-p="'+(cur+1)+'">下一頁</button></div>'}
sp.addEventListener('click',function(e){var b=e.target.closest('button');if(!b||b.disabled)return;cur=+b.dataset.p;draw();window.scrollTo(0,0)});
[q,a].forEach(function(el){el.addEventListener('keydown',function(e){if(e.key==='Enter'){e.preventDefault();run()}})});
x.addEventListener('change',run);
})();</script>"""


# 官方故事頁按 F5 重新整理會回到最上面（不還原捲動位置）；上一頁／下一頁（back_forward）仍由瀏覽器還原
RELOAD_JS = r"""<script>(function(){try{var n=performance.getEntriesByType("navigation")[0];if(n&&n.type==="reload"){history.scrollRestoration="manual";window.scrollTo(0,0);window.addEventListener("load",function(){window.scrollTo(0,0);setTimeout(function(){window.scrollTo(0,0)},60)});}}catch(e){}})();</script>"""


SAVE_JS = r"""<script>
(function () {
  var bar = document.querySelector(".savebar"); if (!bar) return;
  var P = bar.dataset.page, base = bar.dataset.base, K = "homestuck-zh-current-page", A = "homestuck-zh-autosave";
  function get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function set(k, v) { try { localStorage.setItem(k, v); return true; } catch (e) { return false; } }
  function del(k) { try { localStorage.removeItem(k); } catch (e) {} }
  var box = null, timer = null;
  function say(t, ms) { clear(); box = document.createElement("div"); box.className = "toast"; box.textContent = t; bar.appendChild(box); timer = setTimeout(clear, ms || 1500); }
  function tip(t) { clear(); box = document.createElement("div"); box.className = "tipbox"; box.innerHTML = t; bar.appendChild(box); }
  function clear() { if (timer) { clearTimeout(timer); timer = null; } if (box) { box.remove(); box = null; } }
  var TIPS = {
    1: "如果瀏覽器允許儲存資料，你可以記下目前讀到的位置。按「存檔」，下次回到本站時按「讀檔」就會回到這一頁。",
    2: "按下後，無論你讀到哪一頁都會自動記錄位置！下次回到本站首頁時，會自動帶你回到上次讀到的地方。如果覺得煩，按「刪除遊戲資料」就能清掉。"
  };
  function refresh() { var t = document.getElementById("autotip"); if (t) t.textContent = get(A) === "1" ? "(✓)" : "(?)"; }
  bar.addEventListener("click", function (e) {
    var b = e.target.closest("button"); if (!b) return;
    var a = b.dataset.act;
    if (a === "save") { say(set(K, P) ? "已存檔！" : "無法存檔（瀏覽器擋住了儲存功能）。"); }
    else if (a === "auto") { var on = get(A) !== "1"; if (on) { set(A, "1"); set(K, P); } else del(A); refresh(); say(on ? "自動存檔已開啟。" : "自動存檔已關閉。"); }
    else if (a === "load") { var p = get(K); if (p) location.href = base + "/p/" + ("000000" + p).slice(-6) + ".html"; else say("找不到存檔。"); }
    else if (a === "del") { del(K); del(A); refresh(); say("遊戲資料已刪除。"); }
  });
  bar.querySelectorAll(".tip").forEach(function (t) {
    t.addEventListener("mouseenter", function () { tip(TIPS[t.dataset.tip]); });
    t.addEventListener("mouseleave", clear);
  });
  if (get(A) === "1") set(K, P);
  refresh();
})();
</script>"""


INDEX_JS = r"""<script>(function(){var K="homestuck-zh-current-page",A="homestuck-zh-autosave",p=null,a=null;try{p=localStorage.getItem(K);a=localStorage.getItem(A);}catch(e){}
if(!p)return;var u="BASE/p/"+("000000"+p).slice(-6)+".html";var r=document.getElementById("resume");r.hidden=false;r.firstChild.href=u;if(a==="1")location.replace(u);})();</script>"""


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
    candy = esc(sep_img) if (sep_img and "a6a6" in body_class) else "https://storage.homestuck.com/media/assets/candycorn.gif"
    sep = f'<img class="{"tooth" if (sep_img and "a6a6" in body_class) else "candy"}" src="{candy}" alt="|">'
    HS = "https://www.homestuck.com"
    nav_groups = [
        [("Homestuck 繁中", base + "/", "c1"), ("翻譯進度", base + "/progress.html", "c1")],
        [("目錄", base + "/archive.html", "c2"), ("新讀者？", base + "/newreader.html", "c2")],
        [("地圖", base + "/map.html", "c3"), ("紀錄", base + "/log.html", "c3"), ("搜尋", base + "/search.html", "c3")],
        [("商店", "https://homestuckofficial.store/", "c4", [("官方商店", "https://homestuckofficial.store/"), ("Topatoco", "https://topatoco.com/collections/hussie"), ("粉絲周邊", "https://shop.fruityrumpus.com/")]), ("音樂", "https://homestuck.bandcamp.com", "c4")],
        [("論壇", "https://www.fruityrumpus.com/forums", "c5", [("論壇", "https://www.fruityrumpus.com/forums"), ("Discord", "https://discord.com/invite/homestuck")]), ("秘密", base + "/secrets.html", "c5"), ("致謝", base + "/credits.html", "c5")],
    ]
    def li(it):
        if len(it) > 3:
            return (f'<li class="dd"><a class="{it[2]}" href="{esc(it[1])}">{esc(it[0])}</a><div class="menu"><ul>'
                    + "".join(f'<li><a href="{esc(mu)}">{esc(mt)}</a></li>' for mt, mu in it[3]) + '</ul></div></li>')
        return f'<li><a class="{it[2]}" href="{esc(it[1])}">{esc(it[0])}</a></li>'
    nav = f"{sep}".join(f'<div class="grp g{gi + 1}"><ul>' + "".join(li(it) for it in g) + '</ul></div>' for gi, g in enumerate(nav_groups))
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
<header class="site"><nav class="navin">
{nav}
</nav></header>
<main class="wrap">
{body}
</main>
<footer class="site">
<p class="line">Homestuck © Andrew Hussie ｜ 本站為非官方、非營利的讀者翻譯整合站 ｜ <a href="https://www.homestuck.com">官方網站</a></p>
<p>{esc(site.get("copyright", ""))}</p>
<h2 id="credits">致謝與來源</h2>
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
    lines = [l for l in lines if not re.match(r"^原[網网]址\s*[：:]", l)]  # 簡中頁面開頭的「原網址：舊 MSPA 網址」是來源紀錄，不是內文
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
    # 有翻譯過的版本（tools/swf_zh.py 產生）就優先用 assets/zh/ 底下的
    for rel in ("zh/" + f, "zh/flashes/" + f.rsplit("/", 1)[-1], f, "flashes/" + f.rsplit("/", 1)[-1]):
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

    # 官方紀錄資料（fetch_log.py 產生）：紀錄頁與各頁「> 下一頁」連結共用同一套文字規則
    LOGV = {}
    LOG_SPECIAL = {"/GAMEOVER": 8801, "/shes8ack": 9305}
    log_tags = re.compile(r"^(?:\s*\[[^\]]*\])*\s*")
    lo = ROOT / "log_official.json"
    if lo.exists():
        for _id, d, v, link in json.loads(lo.read_text(encoding="utf-8")):
            mm = re.fullmatch(r"/(\d{6})", link)
            num = int(mm.group(1)) if mm else LOG_SPECIAL.get(link)
            if num is not None:
                LOGV[num] = (d, v, link)

    # log_zh.csv：手動指定某些頁在紀錄頁與「> 下一頁」連結顯示的完整文字（含 [S] 標記），優先於自動規則
    LOG_ZH = {}
    lz = ROOT / "log_zh.csv"
    if lz.exists():
        import csv
        for row in csv.DictReader(lz.open(encoding="utf-8-sig", newline="")):
            if (row.get("page") or "").strip().isdigit():
                LOG_ZH[int(row["page"])] = row["text"]

    def log_label(num):
        """標記（[S]、[A6A6I5]）與 ==> 箭頭照官方；英文句子換成本站的繁中標題。沒有官方資料時回傳 None。"""
        if num in LOG_ZH:
            return LOG_ZH[num]
        if num not in LOGV:
            return None
        v = LOGV[num][1]
        inner_v = v[1:-1] if len(v) >= 2 and v[0] == '"' and v[-1] == '"' else v
        prefix = log_tags.match(inner_v).group(0)
        rest = inner_v[len(prefix):]
        if re.search(r"[A-Za-z0-9\u4e00-\u9fff]", rest) and num in by_num:
            zh = re.sub(r"<[^>]+>", "", by_num[num]["title"])  # 標題裡的 <b>、<span>※</span> 等標籤在紀錄頁不用
            for _ in range(3):  # 有些標題的 &gt; 被轉了兩三次，還原到穩定為止
                z2 = html.unescape(zh)
                if z2 == zh:
                    break
                zh = z2
            zh = log_tags.sub("", zh).strip()
            if zh and not re.match(r"^(第\s*\d+\s*頁|測試頁)", zh):
                rest = zh
        return prefix + rest
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
                return f'{base}/p/{t:06d}.html', label or log_label(t) or by_num[t]["title"]
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
        # 官方的存檔列（Save Game／Auto-Save!／Load Game／Delete Game Data）：放在內容框最下面，
        # 第一頁靠左，其他頁靠右（和官方一樣）；存檔記在這台瀏覽器的 localStorage，不用登入
        first_cls = " first" if pages and n == pages[0]["page"] else ""
        foot = (
            f'<div class="savebar{first_cls}" data-page="{n}" data-base="{base}"><ul>'
            '<li><button type="button" data-act="save">存檔</button><span class="tip" data-tip="1">(?)</span></li>'
            '<li><button type="button" data-act="auto">自動存檔！</button><span class="tip" data-tip="2" id="autotip">(?)</span></li>'
            '<li><button type="button" data-act="load">讀檔</button></li>'
            '<li><button type="button" data-act="del">刪除遊戲資料</button></li>'
            '</ul></div>'
        )
        left = ""
        if not first_cls:
            li = f'<li><a href="{base}/p/{pages[0]["page"]:06d}.html">首頁</a></li>' if pages else ""
            if pu:
                li += f'<li><a href="{pu}">上一頁</a></li>'
            left = f'<ul class="startover">{li}</ul>' if li else ""
        foot = '<div class="footrow">' + left + foot + '</div>' + SAVE_JS
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
            # 各頁微調 (左, 上, 寬, 高)：依使用者截圖，讓黃框貼齊那張圖
            ADJ = {8282: (0.5, 0.7, -1.0, -1.4), 8316: (0.3, 0.5, -1.4, -1.2)}.get(n, (0, 0, 0, 0))
            assets = assets.replace('class="flash" ', 'class="flash" data-pick="1" ', 1).replace("></div>",
                f'><a class="pick" href="{base}/p/{tgt:06d}.html" title="下一頁" '
                f'style="left:{x[0]+ADJ[0]:.1f}%;top:{34.7+ADJ[1]:.1f}%;width:{x[1]+ADJ[2]:.1f}%;height:{40.5+ADJ[3]:.1f}%"></a></div>', 1)
        # 角色選擇頁：Flash 裡三個星球各自連到不同的頁面（8199：左 Dave→8200、中 Jade→8224、右 Rose→8243）
        # 頁碼: [(目標頁, 左%, 上%, 寬%, 高%), ...]，百分比是相對 650x450 的動畫
        MULTI = {8199: [(8200, 15.1, 23.6, 22.6, 32.7), (8224, 38.9, 23.6, 22.6, 32.7), (8243, 62.8, 23.6, 22.6, 32.7)], 9386: [(9387, 2.5, 3.5, 22.8, 22.6), (9393, 26.3, 3.5, 22.8, 22.6), (9397, 50.2, 3.5, 22.8, 22.6), (9400, 74.0, 3.5, 22.8, 22.6), (9402, 2.5, 74.3, 22.8, 22.6), (9408, 26.3, 74.3, 22.8, 22.6), (9410, 50.2, 74.3, 22.8, 22.6), (9413, 74.0, 74.3, 22.8, 22.6)]}
        if n in MULTI and ('class="flash"' in assets or 'class="flashwin"' in assets):
            links = "".join(
                f'<a class="pick" href="{base}/p/{t:06d}.html" title="第 {t} 頁" '
                f'style="left:{l}%;top:{tp}%;width:{w}%;height:{h}%"></a>'
                for t, l, tp, w, h in MULTI[n])
            if 'class="flashwin"' in assets:
                assets = assets.replace("</iframe></div>", "</iframe>" + links + "</div>", 1)
            else:
                assets = assets.replace('class="flash" ', 'class="flash" data-pick="1" ', 1).replace("></div>", ">" + links + "</div>", 1)
        # 官方文字區的分支連結列（例如 9386 的 ONE | TWO | ... | EIGHT，分別連到八條故事線的起點）
        BRANCH = {9386: [("一", 9387), ("二", 9393), ("三", 9397), ("四", 9400), ("五", 9402), ("六", 9408), ("七", 9410), ("八", 9413)]}
        branch = ""
        if n in BRANCH:
            branch = '<p class="branchrow">' + " | ".join(f'<a href="{base}/p/{t:06d}.html">{lab}</a>' for lab, t in BRANCH[n]) + "</p>"
        # 動畫裡自己帶連結的頁（官方是動畫內的連結換頁）：本站播放時在連結位置蓋透明連結，並拿掉下方的「下一頁」按鈕
        # 頁碼: (下一頁, 左%, 上%, 寬%, 高%)
        INLINK = {8105: (8106, 3, 92, 92, 8, 0), 8143: (8144, 3, 89, 42, 8, 108), 9305: (9306, 41.5, 46.0, 17.6, 12.2, 80), 8801: (8802, 21.5, 71.5, 56.4, 9.7, 260), 10029: (10030, 42.6, 68.7, 7.7, 12.3, 46)}  # 最後一項：幾秒後才可點（0=馬上）
        if n in INLINK and 'class="flash"' in assets:
            tgt, il, it_, iw, ih, delay = INLINK[n]
            late = f' class="pick late" style="animation-delay:{delay}s;' if delay else ' class="pick" style="'
            assets = assets.replace('class="flash" ', 'class="flash" data-pick="1" ', 1).replace("></div>",
                f'><a{late}left:{il}%;top:{it_}%;width:{iw}%;height:{ih}%" href="{base}/p/{tgt:06d}.html" title="下一頁"></a></div>', 1)
            next_html = ""
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
            body_class = "wide950"  # 官方這幾頁的動畫是 950 寬、貼在內容框最上面（標題在動畫裡面），下面才是 650 的文字區
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
                    '<input id="pwin" type="text" autocomplete="off" autocapitalize="characters" spellcheck="false"> '
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
        if n == 8801:  # 官方 /GAMEOVER：整頁只有一個 950x786 的動畫（沒有標題、導覽列、文字、下一頁），背景是 Act 6 Act 6 綠色
            body_class = (body_class + " gameover").strip()
        if n == 9305:  # 官方 /shes8ack：整頁純白，只有一個 950x650 的動畫（沒有標題、外框、連結），動畫自己播完換頁
            body_class = (body_class + " bare").strip()
        if "A6A6" in pflags:  # 官方 Act 6 Act 6 的綠色配色（body/外框/內容框 = #042300/#168500/#073c00，字 #2ed73a）
            body_class = (body_class + " a6a6").strip()
        top950 = ""
        h1 = f'<h1>{esc(pg["title"])}</h1>\n'
        if "wide950" in body_class.split():
            # 官方：圖貼在內容框最上面（沒有標題），文字區 650px 在圖的下面
            top950 = assets.replace('<div class="assets">', '<div class="assets top950">', 1) + "\n"
            assets = ""
            h1 = ""
        inner = f"""{top950}<article class="story">
{h1}{assets}{ruffle}
{extra}
{text}
{branch}
{next_html}
<div class="story-foot">{foot}</div>
</article>
<div class="page-info">第 {n} 頁 ·
<span class="badge {pg["status"]}">{STATUS_LABEL[pg["status"]]}</span>{official}</div>
{js}{RELOAD_JS}"""
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

    # 紀錄（對應官方 /viewlog）：日期資料 log_dates.txt 取自官方，格式 起始頁:YYMMDD:頁數
    dates = {}
    lf = ROOT / "log_dates.txt"
    if lf.exists():
        for run in lf.read_text(encoding="utf-8").strip().split(","):
            st, d, c = run.split(":")
            for k in range(int(c)):
                dates[int(st) + k] = f"{d[2:4]}/{d[4:6]}/{d[0:2]}"
    items = []
    if LOGV:
        # 日期照官方；文字規則見 log_label；全部連到本站，引號改為「」
        for _id, d, v, link in json.loads(lo.read_text(encoding="utf-8")):
            mm = re.fullmatch(r"/(\d{6})", link)
            num = int(mm.group(1)) if mm else LOG_SPECIAL.get(link)
            href = f"{base}/p/{num:06d}.html" if num in by_num else "https://www.homestuck.com" + link
            txt = log_label(num) if num is not None else v[1:-1]
            items.append(f'<li><span>{d} - <a href="{esc(href)}">「{esc(txt)}」</a></span></li>')
    for p in ([] if items else pages):
        d = dates.get(p["page"], "")
        items.append(
            f'<li><span>{d + " - " if d else ""}<a href="{base}/p/{p["page"]:06d}.html">'
            f'「{esc(p["title"])}」</a></span></li>'
        )
    inner = (
        '<nav class="oc oclog"><h1>冒險紀錄</h1>'
        '<a href="#" id="logtoggle" class="tg">由舊到新排列</a><ul id="loglist">' + "".join(items) + "</ul></nav>"
        "<script>(function(){var u=document.getElementById('loglist'),t=document.getElementById('logtoggle'),"
        "n=false;u.style.display='flex';u.style.flexDirection='column-reverse';"
        "t.onclick=function(e){e.preventDefault();n=!n;u.style.flexDirection=n?'column':'column-reverse';"
        "t.textContent=n?'由新到舊排列':'由舊到新排列'}})();</script>"
    )
    (OUT / "log.html").write_text(
        layout(site, f"紀錄 - {site['title']}", inner, base, raw=True, body_class="offi"), encoding="utf-8"
    )

    # 搜尋（對應官方 /search）：把全站文字做成 search_index.json，在瀏覽器裡搜尋，不需要伺服器
    idx = []
    for p in pages:
        txt = re.sub(r"\s*\n\s*", " ", re.sub(r"[ \t]+", " ", p["body"])).strip()
        idx.append([p["page"], log_label(p["page"]) or p["title"], p["title"] + " " + txt])
    (OUT / "search_index.json").write_text(
        json.dumps(idx, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    # acts: 篩選依地圖頁（map_data.txt 的 A 行）的分配：5.1、6.1、6.1i、6.6.1…；5、6、6.6 為合併範圍
    acts_rng = {}
    starts = []
    if (ROOT / "map_data.txt").exists():
        for ln in (ROOT / "map_data.txt").read_text(encoding="utf-8").splitlines():
            t = ln.split()
            if len(t) >= 3 and t[0] == "A" and t[1].isdigit():
                c, pg_ = t[2], int(t[1])
                al = None
                if re.fullmatch(r"06_0[1-4]", c):
                    al = str(int(c[-1]))
                elif c == "06_int":
                    al = "1i"
                elif c in ("06_051", "06_052"):
                    al = "5." + c[-1]
                elif c == "06_int2":
                    al = "6.1"
                elif re.fullmatch(r"06_I[1-5]", c):
                    al = "6." + c[-1] + "i"
                elif re.fullmatch(r"06_06[2-5]", c):
                    al = "6." + c[-1]
                elif re.fullmatch(r"06_0661_I1|06_066[1-6]_I\d|06_066[1-6]", c):
                    m6 = re.fullmatch(r"06_066(\d)(_I\d)?", c)
                    al = "6.6." + m6.group(1) + ("i" if m6.group(2) else "")
                elif c == "06_07_01":
                    al = "7"
                if al:
                    starts.append((pg_, al))
        starts.sort()
        last_pg = max((p["page"] for p in all_pages), default=10030)
        for k, (st, al) in enumerate(starts):
            hi = starts[k + 1][0] - 1 if k + 1 < len(starts) else max(last_pg, st)
            acts_rng[al] = [st, hi]
        def grp(name, lo_al, hi_al):
            if lo_al in acts_rng and hi_al in acts_rng:
                acts_rng[name] = [acts_rng[lo_al][0], acts_rng[hi_al][1]]
        grp("5", "5.1", "5.2")
        grp("6", "6.1", "7")
        grp("6.6", "6.6.1", "7")
        if "1i" in acts_rng:
            acts_rng["i"] = acts_rng["intermission"] = acts_rng["1i"]
    inner = (
        '<nav class="oc ocsearch"><h1>搜尋</h1>'
        '<section class="sbox"><article class="scard">'
        '<input id="sq" class="sq1" type="text" placeholder="搜尋 Homestuck" autocomplete="off">'
        '<label class="sexact"><input id="sx" type="checkbox"><span>完全符合</span></label>'
        '<input id="sa" class="sq2" type="text" placeholder="chars:john,gt acts:6.1i pages:3000-5000" autocomplete="off">'
        '<h2>結果</h2><div class="sempty" id="sm"><i>找不到結果。</i></div><ul id="sr"></ul>'
        '</article></section><div class="spg" id="sp"></div></nav>'
    ) + SEARCH_JS.replace("BASE", base).replace("ACTS_JSON", json.dumps(acts_rng))
    (OUT / "search.html").write_text(
        layout(site, f"搜尋 - {site['title']}", inner, base, raw=True, body_class="offi"), encoding="utf-8"
    )

    # 新讀者（對應官方 /newreader）：中文翻譯
    first = pages[0]["page"] if pages else 1901
    inner = f"""<article class="oc ocnr"><div><h1>嘿！</h1><h2>歡迎來到 MSPA！</h2>
<p>Homestuck.com（前身為 MSPaintAdventures.com）是安德魯・赫西（Andrew Hussie）創作的各部冒險作品的存檔。這些網路漫畫是為了展現那個年代敘事與技術的結合而做的——那時網路上滿是 Flash 和 Shockwave 遊戲，螢幕是橫向的，解析度高達 1024 像素，網路的蠻荒西部可以用無窮無盡、令人驚嘆的方式玩壞。這個存檔盡力重現當時的體驗，不過 Homestuck「作者原本的意圖」，用電腦讀會比用手機讀好得多。</p>
<p>在開始讀 Homestuck（或任何一部冒險）之前，有兩件事要先知道。</p>
<p><b>1) MSPA 的故事是以「模擬遊戲」的形式呈現</b>，更準確地說，是文字冒險遊戲。你要點擊一些聽起來像是在文字提示列輸入的指令的連結，來推進故事的頁面，讓角色去做某件事。通常，角色會在下一頁回應那個指令。</p>
<p><b>2) MSPA 的故事大多是「讀者驅動」的</b>，也就是大部分的文字指令都是讀者透過建議箱提供的。安德魯會從清單中選一個指令，然後把執行的結果畫出來。對 Homestuck 來說，這個功能用得不多，但被拿來做了許多有趣的變化。</p>
<p>不過話說回來，歸根結底，Homestuck 只是一個關於四個朋友和他們一起玩的遊戲的簡單故事。</p>
<p>那是瓶中的閃電。再也沒有別的作品像它。它會毀掉你的人生。</p>
<a href="{base}/p/{first:06d}.html" style="align-self:center"><button type="button">開始讀 HOMESTUCK</button></a>
<section>
<p>想繼續看的話，可以到<a href="{base}/archive.html">目錄</a>頁，查看 Homestuck.com 目前收錄的各部冒險。</p>
<p>想看安德魯・赫西的另一部作品，可以試試 <a href="https://store.steampowered.com/app/1529810/Psycholonials/">Psycholonials</a>，這是一款講述疫情時代的網紅如何建立小丑邪教的遊戲。</p>
<p>如果你是 Homestuck 食人魔（trolls）的忠實粉絲，可以看看 <a href="https://www.hiveswap.com/">Hiveswap 遊戲與延伸宇宙</a>，包括 <a href="https://store.steampowered.com/agecheck/app/833040/">Friendsim 視覺小說</a>。</p>
<p>想和 Homestuck 的一些角色一起玩，Steam 上有視覺小說 <a href="https://store.steampowered.com/app/1144030/Pesterquest/">Pesterquest</a>。</p>
<p>如果你是老讀者（你來這一頁做什麼？？），可以看看 <a href="https://beyondcanon.com/">Homestuck: Beyond Canon</a>，這是接續 Homestuck 後記的故事續作，持續更新中！</p>
<p>2017 年左右的舊版「新讀者」頁面，請<a href="https://www.homestuck.com/oldreader">點這裡</a>（官方英文）。</p>
<section>當然，還有 Homestuck 目前的社群連結：<ul><li><a href="https://discord.com/invite/homestuck">Discord</a></li><li><a href="https://x.com/homestuck">Twitter</a></li><li><a href="https://bsky.app/profile/homestuck.com">Bluesky</a></li></ul></section>
<p style="font-size:10px">以上為本站讀者翻譯，原文見<a href="https://www.homestuck.com/newreader">官方新讀者頁</a>。</p>
</section></div></article>"""
    (OUT / "newreader.html").write_text(
        layout(site, f"新讀者 - {site['title']}", inner, base, raw=True, body_class="offi"), encoding="utf-8"
    )

    # 目錄（對應官方 /archive）：Homestuck 連本站頁面，其他作品連官方英文站
    O = "https://www.homestuck.com"
    IM = "https://storage.homestuck.com/media/images/"
    arch = [
        ("PSYCHOLONIALS", O + "/psycholonials", "archive_psy.gif", "在與超自然力量溝通的過程中，兩位網紅推出了大膽的全新社群媒體品牌。", "已完結", []),
        ("THE HOMESTUCK EPILOGUES", O + "/epilogues/prologue", "archive_ep.gif", "真實性有待商榷的故事。", "已完結", [("紀錄", O + "/epilogues/viewlog"), ("搜尋", None)]),
        ("HOMESTUCK", f"{base}/p/{first:06d}.html", "archive_hs.gif", "一個關於男孩與朋友們，以及他們一起玩的電子遊戲的故事。約 8,000 頁。", "已完結",
         [("地圖", base + "/map.html"), ("紀錄", base + "/log.html"), ("搜尋", base + "/search.html"), ("致謝", base + "/credits.html")]),
        ("PROBLEM SLEUTH", O + "/problemsleuth/000219", "archive_ps.gif", "一場關於硬漢偵探在他辦公室裡的冒險。共22 章，約 1700 頁。", "已完結",
         [("地圖", O + "/problemsleuth/viewmap"), ("紀錄", O + "/problemsleuth/viewlog"), ("搜尋", O + "/problemsleuth/search"), ("科學問答", O + "/faqs/science")]),
        ("JESTER QUEST", O + "/jesterquest/000001", "archive_jq.gif", "一個普通的小丑，自 2007 年以來就一直熱切地等待著《[[BARD QUEST]]》更新。共30,000 頁。", "已完結",
         [("紀錄", O + "/jesterquest/viewlog"), ("搜尋", O + "/jesterquest/search")]),
        ("BARD QUEST", O + "/bardquest/000136", "archive_bq.gif", "一個年輕吟遊詩人試圖殺掉幾隻龍。分支式風格「做出你冒險的選擇」。共47 頁。", "已完結？",
         [("紀錄", O + "/bardquest/viewlog"), ("搜尋", O + "/bardquest/search")]),
        ("JAILBREAK", O + "/jailbreak/000002", "archive_jb.gif", "一個人試圖越獄。共134 頁。", "已完結？",
         [("紀錄", O + "/jailbreak/viewlog"), ("搜尋", O + "/jailbreak/search")]),
        ("SWEET BRO AND HELLA JEFF", O + "/sweetbroandhellajeff/001", "archive_sbahj.gif", "它還正在進行中。共???頁。", "",
         [("紀錄", O + "/sweetbroandhellajeff/001#log")]),
    ]
    secs = ""
    for name, url, img, desc, st, links in arch:
        lk = "".join((f'<li><a href="{esc(u)}">{esc(t)}</a></li>' if u else f'<li><span class="off">{esc(t)}</span></li>') for t, u in links)
        desc_html = esc(desc).replace("[[BARD QUEST]]", '<a href="' + O + '/bardquest/000136">BARD QUEST</a>')
        st_html = ("<span>【" + st + "】</span>") if st else ""
        secs += (
            f'<section class="arch"><a href="{esc(url)}"><img src="{IM}{img}" alt="{esc(name)}"></a>'
            f'<div><h2><a href="{esc(url)}">{esc(name)}</a></h2><p>{desc_html} {st_html}</p>'
            + (f"<ul>{lk}</ul>" if lk else "") + "</div></section>"
        )
    inner = (
        '<nav class="logbox archive"><header><h1>目錄</h1><p>冒險作品依我們高興的順序排列。</p><p>※本頁連結皆連至原英文官方頁面，本站並無翻譯</p></header>'
        + secs + '</nav>'
    )
    (OUT / "archive.html").write_text(
        layout(site, f"目錄 - {site['title']}", inner, base, raw=True, body_class="offi"), encoding="utf-8"
    )

    # 地圖（對應官方 /viewmap）：map_data.txt 取自官方（S/T=側欄標籤、A/R=地圖圖片連結、P=程式碼文字、H=光碟圖）
    MAPB = "https://storage.homestuck.com/story/homestuck/assets/map/"
    SIDEC = {"1": "#b7b7b7", "2": "#4be24f", "3": "#7638e7", "4": "#f40c0c", "5": "#0b4100"}
    mp = ROOT / "map_data.txt"
    mapcode = [
        "bifurcate Act_5[Act_1, Act_2];",
        "split Act_6[Act_1, Act_2, Act_3, Act_4, Act_5, Act_6];",
        "split Act_6_6[Act_1, Act_2, Act_3, Act_4, Act_5, Act_6];",
    ]

    MAPFIX = {"part-1": (29, 109), "part-2": (28, 342), "part-3": (31, 168), "part-4": (31, 64), "side-1": (73, 53), "side-2": (73, 51),
              "disc-1": (30, 30), "disc-2": (28, 28), "supercartridge": (29, 34)}

    def imgdim(fn):
        b = fn[:-4] if fn.endswith(".gif") else fn
        if b in MAPFIX:
            w, h = MAPFIX[b]
        elif re.match(r"^map_06_(0\d{1,3}|int2?|cascade|I\d|0\d{3}_I\d|07_01)$", b):
            w, h = (610, 128) if (re.search(r"I\d$", b) or b.endswith("07_01")) else (610, 180)
        else:
            w, h = 102, 102
        return f' width="{w}" height="{h}"'

    def mlink(pg_, img):
        im = f'<img src="{MAPB}map_{img}.gif"{imgdim("map_" + img + ".gif")} alt="第 {pg_} 頁" loading="lazy">'
        if pg_ == "-":
            return im
        u = f"{base}/p/{int(pg_):06d}.html" if int(pg_) in by_num else f"https://www.homestuck.com/{int(pg_):06d}"
        return f'<a href="{u}">{im}</a>'

    def mlabel(kind, num, col, img, cls):
        c = SIDEC.get(col, "#b7b7b7")
        return (
            f'<div class="msb" style="border-right:8px solid {c}"><div class="mlab" style="background:{c}">'
            f'<span class="a">{kind}</span><span class="b">{num}</span></div><img src="{MAPB}{img}"{imgdim(img)} alt=""></div>'
            f'<div class="mbar" style="border-color:{c}"></div>'
        )

    def msb(kind, num, col, img, cls, right=False):
        c = SIDEC.get(col, "#b7b7b7")
        hx = "h2" if kind == "SIDE" else "h3"
        lab = f'<span class="a">{kind}</span>' + (f'<span class="b">{num}</span>' if num else "")
        return (
            f'<div class="msb{" mr" if right else ""}" style="border-color:{c}"><div class="mlab" style="background:{c}">'
            f'<{hx} class="upright">{lab}</{hx}></div><img class="{cls}" src="{MAPB}{img}"{imgdim(img)} alt=""></div>'
            f'<div class="mbr{" mr" if right else ""}" style="border-color:{c}"></div>'
        )

    def mcode(idx, names):
        cols = ["", "", ""]
        head = ["bifurcate Act_5", "split Act_6", "split Act_6_6"][idx]
        colr = ["#ff0000,#0000ff", "#2ed73a", "#007800"][idx].split(",")
        sp = ", ".join(f'<span style="color:{colr[k] if k < len(colr) else colr[-1]}">{n}</span>' for k, n in enumerate(names))
        return f'<p class="mcode m{idx}">{head}[{sp}];</p>'

    mh = ""
    if mp.exists():
        lines = [ln.split() for ln in mp.read_text(encoding="utf-8").splitlines() if ln.strip()]
        pi = 0
        in_side = in_part = False

        def close_part():
            return "</div></div>" if in_part else ""

        for n, t in enumerate(lines):
            k = t[0]
            if k == "S":
                mh += close_part() + ("</div></div></div></div>" if in_side else "")
                in_part = False
                mh += '<div class="mrw"><div class="mside"><div class="mflex">' + msb("SIDE", t[1], t[2], t[3], "mi") + '<div class="mcont">'
                in_side = True
            elif k == "T":
                mh += close_part()
                mh += '<div class="mflex">' + msb("PART", t[1], t[2], t[3], "mi") + '<div class="mpc">'
                in_part = True
            elif k == "A":
                mh += mlink(t[1], t[2])
            elif k == "R":
                mh += '<div class="mrow">' + "".join(mlink(t[i], t[i + 1]) for i in range(1, len(t), 2)) + "</div>"
            elif k == "P":
                nxt = next((u[0] for u in lines[n + 1:] if u[0] != "P"), "")
                names = t[1].split("|")
                if nxt in ("S", "H"):
                    mh += close_part() + "</div></div></div></div>"
                    in_part = in_side = False
                    mh += mcode(pi, names).replace('class="mcode', 'class="mcode mout')
                else:
                    mh += close_part()
                    in_part = False
                    mh += mcode(pi, names)
                pi += 1
            elif k == "H":
                break
        mh += close_part() + ("</div></div></div></div>" if in_side else "")
        # 右側欄（DISC 1、DISC 2、SUPERCARTRIDGE）
        hs = [u for u in lines if u[0] == "H"]
        rc = ""
        specs = [("DISC", "1", "height:3070px"), ("", "", "height:252px"), ("DISC", "2", "height:3560px"), ("", "", "height:310px"), ("SUPERCARTRIDGE", "", "flex:1")]
        hi = 0
        for kind, num, st in specs:
            if not kind:
                rc += f'<div style="{st}"></div>'
                continue
            u = hs[hi]; hi += 1
            c = SIDEC["1"]
            lab = f'<span class="a">{kind}</span>' + (f'<span class="b">{num}</span>' if num else "")
            rc += (
                f'<div class="mrt" style="{st}"><div class="mbr l" style="border-color:{c}"></div>'
                f'<div class="msb l" style="border-color:{c}"><div class="mlab" style="background:{c}"><h2 class="upright">{lab}</h2></div>'
                f'<img class="mi" src="{MAPB}{u[-1]}"{imgdim(u[-1])} alt=""></div></div>'
            )
        mh = f'<div class="mbox"><div class="mleft">{mh}</div><div class="mright">{rc}</div></div>'
    inner = '<nav class="oc ocmap mapbox"><h1>冒險地圖</h1>' + mh + "</nav>"
    (OUT / "map.html").write_text(
        layout(site, f"地圖 - {site['title']}", inner, base, raw=True, body_class="offi"), encoding="utf-8"
    )

    # 致謝（對應官方 /credits）：官方的音樂／美術／程式致謝有近千條外部連結，這裡先連到官方；本站自己的致謝列在下面
    credits_li = "".join(
        '<li><a href="%s">%s</a>：%s</li>' % (esc(c["url"]), esc(c["name"]), esc(c.get("note", "")))
        for c in site.get("credits", [])
    )
    inner = (
        '<article class="ow"><header><h1>致謝</h1></header><section>'
        "<h2>官方致謝</h2>"
        "<p>Homestuck 的音樂與音效、美術、程式的完整致謝名單（逐頁列出曲目、作者與連結），請見官方英文頁面：</p>"
        '<ul><li><a href="https://www.homestuck.com/credits">音效致謝／美術致謝／程式致謝（官方 Credits）</a></li></ul>'
        "<h2>本站致謝</h2>"
        f"<p>{esc(site.get('copyright', ''))}</p>"
        f"<ul>{credits_li}</ul></section></article>"
    )
    (OUT / "credits.html").write_text(
        layout(site, f"致謝 - {site['title']}", inner, base, raw=True, body_class="owhite"), encoding="utf-8"
    )

    # 秘密（對應官方 /unlock）：中文翻譯；各條指令的圖畫頁仍連官方英文站
    SECRET_CMDS = ['FAD+ZAD+AD：憤怒地把帽子摔在地上。', 'PI：以令人震驚的不得體方式跌倒。', 'PI：以硬派黑色反英雄的方式跌倒。', 'PS：GAMBIT SCHEMA -> 帶著 :3 臉的糖果玉米老虎！', 'MK：和兇惡的打手們擺出反派姿勢。', 'PI：邀請你意想不到的客人進來，痛快地玩一場龍與地下城。', 'PI：令人不安地盯著阿曼達（Amanda）看。', 'PS：騎著死神的鐮刀像騎機械公牛一樣，同時死神用小提琴拉出一曲激昂的〈魔鬼下到喬治亞〉。', 'FAD：GAMBIT SCHEMA -> 辣玉米粽卓柏卡布拉！', 'FPI：帶著未來版的《終極警探》傳送到電影院，讓 FAD 和 MK 放鬆一下，「看場電影！」。', 'FPI - 離開之前，把妓院改造成可愛的賭場。', 'GPI：深情地看著捐款。', 'PS：召喚（順便雇用）午夜天團，讓這個邋遢的小角色見識誰才是真正的王牌。', 'MC：被激怒，猛烈地加入戰鬥，改為替 DMK 效力。', 'MC 和 SMK：向主角們發動無情、由捐款資助的戰爭，雖非正史，卻是宏大的劇情線。', '無墨鏡的斯蒂勒半身像：從時空裂縫中現身，緩慢而詭異地朝觀眾飄去。', 'PS + AD + PI + ZAD + FAD + 4 名冒險者 + HD + NB + candymecha + GPI + PPI + FPI 對上 MK + LoathsomeBeast + MM + DMK + MonsterPI + Fluthulu + SurlyThugs + FrighteningBeast + MortholDryax + BowenStilsonDogg：正面對決！', 'MC：讓勞工黃蜂從主角們身上採集影子花蜜。然後，HIVE RAGTIME：用午夜把牠們灌滿。', '所有人：暫停拍一輯十二個月的月曆寫真，因為事情變得令人不安地真實了。', '用酷炫的骰子科技反擊午夜天團。', '開始約會模擬小遊戲。', 'MC：SHADOW COMB RAVE -> MIDNIGHT GOSPEL ACT', '把機率論黃蜂教授的「干涉等級」從中調到高。', '死神：不小心在你的《遊魂之書》上撕開一個劇情漏洞。', 'PS：戰鬥手法：召喚 ZILLYHOO 戰錘！', '玩一場(興)奮的(興)奮的《猛男翹臀：萬智牌》。', '蜜蜂教授：一勞永逸地結束機率論黃蜂教授那些惱人的干涉。', '午夜天團：繼續你們的戰鬥，對黃蜂教授干涉時間所造成的種種怪異改變渾然不覺。', 'MC：嘗試用更高明的影子魔法，終結機率論黃蜂的干涉。', '顯示玩家目前為止見過的所有地點的地圖。', 'PI：召喚一隊殭屍太空人來幫忙！', 'PS：和一隻小白貓合影，因為事情變得好可愛了。', '糖果機甲駕駛員 PI：成為總統，用糖果機甲拯救美國。', '一邊曖昧地朝玩家眨眼，一邊點起小小的鬍子火。', 'PS：召喚微波爐觸手怪。LVL 150 CODDLETECH：滑溜溜的拍打吸盤觸鬚', 'FMB：深情地看著莎拉（Sarah）', '死神：用你的《遊魂之書》，召集 PS、PI、AD 以及 ZAD 先前的骸骨。事情真實到你們組成了一個樂團去巡迴演出，演奏〈顫慄〉和其他與不死有關的音樂曲目。', 'Dapper Swain：像騎真正的公牛一樣騎機械公牛。', 'Cooper：「借用」戴夫（Dave）的酷炫裝備，對一些老鼠和其他森林動物發狂，同時說出機智的單句台詞。', 'Richard：向塔夫羅斯（Tavros）挑戰輪椅比武。']
    cmd_li = "".join(
        '<li><a href="https://www.homestuck.com/old-secrets/ps%06d">%s</a></li>' % (i + 1, esc(t))
        for i, t in enumerate(SECRET_CMDS)
    )
    inner = (
        '<article class="ow"><header><h1>隱藏內容</h1></header><section>'
        '<img src="https://storage.homestuck.com/secrets/old-secrets/images/unlock_gamecode.gif" alt="輸入了一組神秘的遊戲代碼">'
        '<p>恭喜！！！</p>'
        '<p>你輸入了有效的遊戲代碼（GAME CODE），解鎖了令人興奮的秘密！其中包括：</p>'
        '<h2>安德魯的東西</h2><ul><li><a href="https://linktr.ee/andrewhussie">Linktree</a></li>'
        '<li><a href="https://mspaintadventures.itch.io/troubled-cosmos">Troubled Cosmos</a></li></ul>'
        '<h2>冷門連結</h2><ul><li><a href="https://www.homestuck.com/faqs">極度過時的常見問答</a></li>'
        '<li><a href="https://www.homestuck.com/ryanquest">Ryanquest</a></li>'
        '<li><a href="https://www.homestuck.com/old-secrets/vigilprince">The Vigil Prince</a></li></ul>'
        '</section><section>'
        '<p>你還解鎖了一些<b>粉絲點播的遊戲指令</b>。如果你在 2010 年以前捐過款，這些指令就會被畫出來並貼在這裡。</p>'
        '<ol>' + cmd_li + '</ol>'
        '<p style="font-size:10px">以上為本站讀者翻譯，原文見<a href="https://www.homestuck.com/unlock">官方頁面</a>；各條指令的圖畫頁為官方英文站。</p></section></article>'
    )
    (OUT / "secrets.html").write_text(
        layout(site, f"秘密 - {site['title']}", inner, base, raw=True, body_class="owhite"), encoding="utf-8"
    )

    # 首頁
    start = (
        f'<p><a href="{base}/p/{pages[0]["page"]:06d}.html">從第 {pages[0]["page"]} 頁開始閱讀 →</a></p>'
        if pages else "<p>目前還沒有內容。</p>"
    )
    inner = f"""<h1>{esc(site["title"])}</h1>
<p>{esc(site.get("subtitle", ""))}</p>
{start}
<p id="resume" hidden><a href="#">繼續上次讀到的地方 →</a></p>
<p><a href="{base}/progress.html">查看翻譯進度</a></p>""" + INDEX_JS.replace("BASE", base)
    (OUT / "index.html").write_text(
        layout(site, site["title"], inner, base), encoding="utf-8"
    )

    print(f"完成：{len(pages)} 頁（另有隱藏頁 {len(hidden_pages)}）→ {OUT}")


if __name__ == "__main__":
    build()
