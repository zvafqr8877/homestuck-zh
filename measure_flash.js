// 重新量官方 Flash 頁的位置和大小（官方改版後用）。
// 用法：用瀏覽器打開 https://www.homestuck.com/ 任一頁，按 F12 開 Console，整段貼上執行，
// 等 1～2 分鐘，最後會印出一段 JSON，整段複製後存成 flash_layout.json（覆蓋舊檔）。
// 格式：{"頁碼":[left, top, 寬, 高]}，量的是 1000px 寬的視窗下，動畫相對於整頁左上角的位置。
(async () => {
  const pages = [/* 把 manifest.json 裡 type 是 flash 的頁碼貼在這裡，例如 7966, 7973, ... */];
  const alias = {8801: 'GAMEOVER', 9305: 'shes8ack'};
  const out = {};
  async function one(p) {
    const f = document.createElement('iframe');
    f.style.cssText = 'position:fixed;left:-2000px;top:0;width:1000px;height:1600px;border:0';
    f.src = '/' + (alias[p] || String(p).padStart(6, '0'));
    document.body.appendChild(f);
    const t0 = Date.now();
    while (Date.now() - t0 < 45000) {
      await new Promise(r => setTimeout(r, 600));
      const d = f.contentDocument; if (!d) continue;
      const el = d.querySelector('main ruffle-object, main ruffle-embed, article ruffle-object, article ruffle-embed');
      if (!el || el.getBoundingClientRect().height < 50) continue;
      await new Promise(r => setTimeout(r, 1200));
      const r = el.getBoundingClientRect(), sy = f.contentWindow.scrollY;
      out[p] = [Math.round(r.left), Math.round(r.top + sy), Math.round(r.width), Math.round(r.height)];
      break;
    }
    f.remove();
  }
  const q = [...pages];
  await Promise.all(Array.from({length: 6}, async () => { while (q.length) await one(q.shift()); }));
  console.log(JSON.stringify(out));
})();
