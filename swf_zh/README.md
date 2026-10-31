# Flash 內文字翻譯

譯文**完全取自簡中站**（src_sc/ 裡對應頁面的字幕），轉繁體的方式和 convert.py 相同（OpenCC s2twp + glossary.csv）。
簡中站沒有對應譯文的動畫文字（9386 的選角提示、9828 的音效字、9001 的商店對話…）維持英文，不自行翻譯。

| 頁 | 動畫 | 文字數 | 說明 |
|---|---|---|---|
| 8300 | 06397.swf | 25 | 商人藥水對話（編輯文字框） |
| 9001 | 07098.swf | 2 | 簡中站只有前 2 段，其餘商店對話無簡中字幕，維持英文 |
| 9305 | 07402.swf | 12 | JADE/CALLIOPE/JANE 對話（靜態文字，會改成文字框） |

## 使用（在專案根目錄）
```
pip install opencc-python-reimplemented      # 已經裝過就不用
python fetch_flash.py                        # 先把原始 SWF 下載到 assets/
python tools/swf_zh.py                       # 產生 assets/zh/ 底下的翻譯版 SWF
```
然後 `git add -A`、commit、push（`.gitignore` 裡不能有 `assets/`）。build.py 會優先使用 `assets/zh/` 裡的版本。

字型是思源黑體粗體（OFL），字形放在 `glyph_cache.json`（涵蓋 Big5 常用字），只把用到的字嵌進每個 SWF。
若出現「字型缺這些字」，把缺字告訴我，或用 `--font C:\Windows\Fonts\xxx.ttc` 指定字型檔補字。

## 修改譯文
編輯 `swf_zh/<頁碼>.json` 的 `sc`（簡體原文）。想直接改繁體，就改 glossary.csv 或在 json 裡寫繁體字也可以（繁體字經 OpenCC 轉換後不變）。
