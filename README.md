# Homestuck 繁體中文整合站

非官方、非營利的 Homestuck 繁體中文整合站，目標是在 HTML／CSS／行為上盡量貼近官方站 https://www.homestuck.com 。
靜態網站，用 GitHub Pages 發佈：https://zvafqr8877.github.io/homestuck-zh/

譯文來源：繁中站（zhhomestuck.github.io）＋簡中站（簡轉繁）。Homestuck 的著作權屬於 Andrew Hussie。

## 資料夾與主要檔案

| 路徑 | 用途 |
| --- | --- |
| `site.json` | 站名、致謝名單、著作權聲明、`asset_base`（素材網址前綴）、`base_url`、`flash_mode` |
| `content/` | 每頁一個 `.md`（`NNNNNN.md`），front matter 有 `page`、`title`、`status`（可有 `source`、`hidden`） |
| `src_sc/` | 簡體來源純文字，**不進 git**（已在 `.gitignore`） |
| `glossary.csv` | 術語覆蓋表，OpenCC 轉完後做取代（長詞優先） |
| `manifest.json` | 頁碼對應圖片／影片／Flash 檔 |
| `build.py` | 產生 `docs/`（`docs/` 不進 git，由 GitHub Actions 建置） |
| `convert.py` | 簡轉繁並寫入 `content/` |
| `check_assets.py` | 檢查哪些頁缺素材、哪些檔案不存在 |
| `assets/` | 自己放的素材，**要進 git**；其中 `assets/flashes/` 是原版 SWF、`assets/zh/` 是翻譯版、`assets/ruffle/` 是字型 |
| `tc_special.json` | 繁中站 11 個「文字版」頁的內容（由 `fetch_tc_special.py` 產生），`build.py` 用它產生 `p/NNNNNNtc.html` |
| `search_chars.json` | 官方搜尋的角色別名表（由 `fetch_search_chars.py` 產生） |
| `log_official.json`、`log_zh.csv` | 官方「冒險紀錄」頁的標題與日期資料、繁中標題 |
| `swf_zh/`、`tools/` | 簡中字幕翻譯 Flash 的工具（見下方 Flash 一節） |
| `.github/workflows/pages.yml` | push 到 main 就自動建置並發佈 |

## 狀態欄位

`status` 有三種：`converted`（機器轉換，待校對）、`proofreading`（校對中）、`done`（已校對）。
`convert.py` 不會覆蓋 `proofreading` 和 `done` 的頁面，重跑是安全的。進度頁會自動統計。
內容和標題都是空的占位頁不會輸出。

## 流程

1. 參考網站：
   * 繁中站：https://zhhomestuck.github.io/
      * 使用範圍：官方第 1901 頁到第 7964 頁
      * 原始碼：https://github.com/zhhomestuck/zhhomestuck.github.io
   * 簡中站：https://linzhiyi622.github.io/
      * 使用範圍：官方第 7965 頁到第 10030 頁
      * 第 7965 頁（簡中第 6065 頁）連結：https://linzhiyi622.github.io/homestuckjz.GitHub.io/6065.html
      * 第 10030 頁（簡中第 8130 頁）連結：https://linzhiyi622.github.io/homestuckjz.GitHub.io/8130.html
      * 原始碼：https://github.com/linzhiyi622/homestuckjz.GitHub.io
   * The Unofficial Homestuck Collection：https://uhca.carrd.co/
2. 在你自己的電腦上：

   ```
   pip install opencc-python-reimplemented
   # 方法 A（建議）：git clone 簡中站的 repo，再 python fetch_sc.py --from-dir <repo資料夾>
   # 方法 B：python fetch_sc.py，從網站抓（約 40 分鐘，可中斷續跑）
   python convert.py src_sc content  # 簡轉繁，檔名自動 +1900 變官方頁碼
   python build.py
   python check_assets.py
   ```

   注意：簡中站只翻譯「對話記錄」和少數內文頁；圖片裡的英文沒有翻譯。
   沒有任何中文的頁面，轉出來的 `.md` 只有標題，圖片照常顯示。

3. 用瀏覽器開 `docs/index.html` 預覽。
4. 校對完的頁面，把 front matter 的 `status` 改成 `proofreading` 或 `done`。

## 發佈到 GitHub Pages

1. repo 的 Settings → Pages，Source 選 **GitHub Actions**。
2. 每次 push 到 `main` 都會自動執行 `build.py` 並發佈 `docs/`。
3. 網址是 `https://帳號.github.io/repo名/`，所以 `site.json` 的 `base_url` 是 `"/repo名"`。
4. `assets/` 要進 git（`.gitignore` 不能有 `assets/`）；`src_sc/`、`docs/`、`__pycache__/` 不進 git。
5. 重新整理看不到改動時，先確認 Actions 是綠色勾勾，再用 Ctrl+F5。

## 素材（圖片／影片）

頁面引用的網址是 `asset_base + manifest 裡的 file`。要換儲存位置，只改 `site.json` 的 `asset_base`。
GitHub Pages 單站建議不超過 1 GB，影片很多的話不適合放同一個 repo。放什麼素材、從哪裡取得，請先確認授權。

## Flash

### 三種顯示方式

1. **翻譯版 Flash**（`assets/zh/` 有檔案）：用 Ruffle 播放自己上傳的翻譯版 SWF。
2. **原版 Flash**（只有 `assets/flashes/` 有檔案）：用 Ruffle 播放英文原版，使用官方的像素字型設定。
3. **沒放檔案的 Flash**：由 `site.json` 的 `flash_mode` 決定：`iframe`（預設，直接嵌入官方頁面，只露出 650x450 的動畫區；官方的 SWF 只允許 `www.homestuck.com` 讀取，自己用 Ruffle 會被 CORS 擋住）、`ruffle`、`link`（只放連結）。

翻譯原則：Flash 內的文字只用繁中站已翻譯的版本（36 頁）和簡中站字幕（3 頁），其餘維持官方原版，不自己翻譯。有文字但兩邊都沒有譯文的 Flash（3049、7640、6009、2376、7626、6565、6517、9828、2038、2037、2238、2297、2655、2657、2669、2725、3307、3541、3620、3840、4478、7614、7659、7677）照舊用原版。

選檔順序在 `build.py` 的 `local_swf()`：`assets/zh/<manifest 路徑>` → `assets/zh/flashes/<檔名>` → `assets/<manifest 路徑>` → `assets/flashes/<檔名>`。

Ruffle 從 `https://unpkg.com/@ruffle-rs/ruffle` 載入（不在 repo 裡）。

### 字型設定（重要）

- 翻譯版（`assets/zh/` 底下的 SWF）：照繁中站設定，載入 `assets/ruffle/NotoSansCJKTC.swf`（Noto Sans CJK TC，約 23MB），並設定 `defaultFonts`。沒有這個字型，中文會不見，只剩英文。
- 原版 SWF：載入 `assets/ruffle/homestuck-fonts.swf`、`courier-new-pixel.swf`（官方的像素字型，沒有中文字）。
- 兩種設定由 `build.py` 依頁面有沒有用到 `assets/zh/` 自動切換。

### 繁中站翻譯版（36 頁）

繁中站（zhhomestuck.github.io）翻譯過 Flash 內的文字，檔名帶 `_ct`。
在專案資料夾執行（只用標準函式庫）：

```
python fetch_tc_flash.py          # 下載翻譯版 SWF 到 assets/zh/flashes/，並下載中文字型
python fetch_tc_flash.py --dry    # 只檢查，不下載
python build.py
git add assets
```

腳本內建「繁中站頁碼 → 翻譯版檔名」對照表，並依 `manifest.json` 該頁的 Flash 檔名存檔，內容相同的會略過。
頁碼：2153、3258、4692、4979、5221、5338、5595、5617、5643、5660、5774、5795、5836、5874、5902、5919、5984、6000、6021、6062、6094、6369、6416、6441、6468、6720、6725、6934、6952、6970、6978、6984、7037、7327、7395、7680。
（繁中站的 7680 用 `05777_2_ct.swf`；6934、6952、6970、6978、6984 都用 `05031_ct.swf`。）

### 簡中字幕翻譯版（3 頁）

8300（`06397.swf`）、9001（`07098.swf`）、9305（`07402.swf`）：譯文取自簡中站字幕，用 `tools/swf_zh.py` 改寫 SWF 內的文字，字型直接嵌進 SWF。
指定 Noto Sans CJK TC 粗體重新產生：

```
pip install fonttools
python fetch_flash.py
python tools/swf_zh.py --font NotoSansCJKtc-Bold.otf
```

`NotoSansCJKtc-Bold.otf` 只是產生時用的字型來源（可從 https://github.com/notofonts/noto-cjk 下載），**不要 commit**。
簡中站沒有譯文的動畫文字維持英文。細節見 `swf_zh/README.md`。

## 繁中站的 11 個特殊頁

2153、3258、4692、4979、5221、5338、5595、5660、6720、6725、7327 是互動式 Flash 遊戲，繁中站另外做了文字版（指令與回應）。

- `fetch_tc_special.py`：下載繁中站的 `NNNNNNtc.html`，整理成 `tc_special.json`。
- `build.py` 為每頁產生本站自己的 `p/NNNNNNtc.html`，標題是「NNNNNNTC」，版面照繁中站（Courier、對白灰框、橘框指令列）。
- 這 11 頁最下面「首頁 | 上一頁」旁邊會多出「攻略/純文字版本」（連到本站的 TC 頁，開新分頁）和「官方Youtube影片」；連結清單是 `build.py` 裡的 `TC_LINKS`。3258 頁另有「地圖」。
- 這 11 頁的 `.md` 內文只有繁中站的連結文字，輸出時會被略過。

## 搜尋

- 全站搜尋在瀏覽器裡執行，逐行比對台詞，不搜尋標題；結果的 HTML／CSS 照官方。
- 進階搜尋支援 `acts:`、`pages:`、`chars:`（角色別名用 `search_chars.json`，由 `python fetch_search_chars.py` 取得）。

## 頁面下方列

「首頁 | 上一頁」和右邊的存檔列（存檔／自動存檔／讀檔／刪除遊戲資料）寫法和官方相同（清單符號「|」、項目左右內距 4px、右邊外距 4px）。存檔記在這台瀏覽器的 localStorage，不用登入。

## 還沒做的事

- 特殊故事頁（Collide 等）和官方的版面比對。
- 搜尋頁的英文標籤（Page、Previous／Next）、紀錄頁的切換文字、進階搜尋介面簡化。
- 製作人員名單頁文字、各幕邊界和官方的差異。
- Ruffle 目前依賴 `unpkg.com`，可考慮改放進 repo。
- 校對協作流程（例如用 GitHub Issues 或 Pull Request 認領頁面）。

## 備註

- 官方頁碼 = 簡中站頁碼 + 1900；官方頁碼也等於繁中站頁碼（例如 5338 ↔ homestuck.com/005338 ↔ zhhomestuck.github.io/p/005338.html）。`log_official.json` 裡的 `id` 不是頁碼。
- `sources.csv`（`gen_mapping.py` 產生）是三方頁碼與網址對照；跳號 4299、4938、4988、9802–9804；隱藏頁 8270 上一頁／下一頁會跳過；別名頁 8801=`/GAMEOVER`、9305=`/shes8ack`。
- 官方 `storage.homestuck.com` 之後若改版，網址可能失效；`iframe` 模式依賴官方站不改 `X-Frame-Options`。
- Python 相容 3.12 以前的版本：`build.py` 的 f-string 運算式裡不要放反斜線。
