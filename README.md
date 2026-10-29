# Homestuck 繁體中文整合站（骨架）

靜態網站，用 GitHub Pages 發佈。此資料夾只有程式、設定和假資料，沒有任何作品內容。

## 資料夾

| 路徑 | 用途 |
| --- | --- |
| `site.json` | 站名、致謝名單、著作權聲明、`asset_base`（素材網址前綴）、`base_url` |
| `content/` | 每頁一個 `.md`（`NNNNNN.md`），含 `page`、`title`、`status` |
| `src_sc/` | 簡體來源純文字（`6023.txt`），**不進 git**，取得授權後才放 |
| `glossary.csv` | 術語覆蓋表，OpenCC 轉完後做取代（長詞優先） |
| `manifest.json` | 頁碼對應圖片／影片檔 |
| `build.py` | 產生 `docs/` |
| `convert.py` | 簡轉繁並寫入 `content/` |
| `check_assets.py` | 檢查哪些頁缺素材、哪些檔案不存在 |
| `.github/workflows/pages.yml` | push 到 main 就自動建置並發佈 |

## 狀態欄位

`status` 有三種：`converted`（機器轉換，待校對）、`proofreading`（校對中）、`done`（已校對）。
`convert.py` 不會覆蓋 `proofreading` 和 `done` 的頁面，重跑是安全的。進度頁會自動統計。

## 流程

1. 先取得簡體站與繁體站管理員的同意（轉載、署名方式）。
2. 在你自己的電腦上：

   ```
   pip install opencc-python-reimplemented
   python convert.py src_sc content
   python build.py
   python check_assets.py
   ```

3. 用瀏覽器開 `docs/index.html` 預覽。
4. 校對完的頁面，把 front matter 的 `status` 改成 `proofreading` 或 `done`。

## 發佈到 GitHub Pages

1. 建一個 repo，把這個資料夾 push 上去（`main` 分支）。
2. 到 repo 的 Settings → Pages，Source 選 **GitHub Actions**。
3. 之後每次 push 都會自動執行 `build.py` 並發佈 `docs/`。
4. 如果網址是 `https://帳號.github.io/repo名/`，把 `site.json` 的 `base_url` 設成 `"/repo名"`。用自訂網域或 `帳號.github.io` 本身就留空字串。

## 素材（圖片／影片）

頁面引用的網址是 `asset_base + manifest 裡的 file`。要換儲存位置，只改 `site.json` 的 `asset_base`。

- GitHub Pages 單站建議不超過 1 GB，影片很多的話不適合放在同一個 repo。
- 你的 NAS 加網域可以當素材主機，不過要確認上傳頻寬和穩定度。
- 也可以考慮 Cloudflare R2 這類物件儲存。
- 放什麼素材、從哪裡取得，請先確認授權。

## 還沒做的事

- Flash 小遊戲（`manifest` 的 `type` 目前只支援 `image` 和 `video`），之後可以接 Ruffle。
- 全站搜尋、頁碼跳轉。
- 校對協作流程（例如用 GitHub Issues 或 Pull Request 認領頁面）。

## 目前已備好的資料（官方 7959–10030，簡中 6059–8130，共 2069 頁）

- `sources.csv`：由 `gen_mapping.py` 產生的三方頁碼與網址對照（官方 = 簡中 + 1900；跳號 4299、4938、4988、9802–9804；別名頁 8801=`/GAMEOVER`、9305=`/shes8ack`）。簡中網址格式只驗證過 6065、6066 兩頁。
- `manifest.json`：由 `gen_manifest.py` 從 UHC 素材包的 `mspa.json`（只取素材路徑）轉成官方新網址。2026-10-29 已用瀏覽器對官方站逐檔 HEAD 檢查，全部存在。Flash 用 Ruffle 播放，YouTube 頁（9987、10027、10030）用內嵌。
- `content/` 目前只有 6 個測試頁（7959、7966、8004、8143、8801、9987），內容是假文字，用來測試圖片、Flash、YouTube 能不能載入。正式使用前請刪掉。

### 還沒驗證的事

- Flash 從官方站載入，可能被跨站限制擋住，上線後要實測；被擋就把 SWF 放到自己的鏡像並改 `asset_base`。
- 官方 `storage.homestuck.com` 之後若改版，網址可能失效。
- 有 `-modified` 版 Flash 的頁面只驗證過 8801。
