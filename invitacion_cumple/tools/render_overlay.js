// Renderiza la capa del personaje (PNG con transparencia) cuadro a cuadro con Chromium + GSAP.
// Uso: node render_overlay.js <overlay_dir> <out_dir> [lista de cuadros "a-b,c,d-e" | all]
const fs = require('fs'); const path = require('path');
const { chromium } = require('playwright');
(async () => {
  const [dir, outDir, spec] = process.argv.slice(2);
  const total = 825;
  let frames = [];
  if (!spec || spec === 'all') frames = Array.from({ length: total }, (_, i) => i);
  else for (const part of spec.split(',')) { const [a, b] = part.split('-').map(Number); for (let i = a; i <= (b === undefined ? a : b); i++) frames.push(i); }
  const read = f => JSON.parse(fs.readFileSync(f, 'utf-8'));
  const data = { meta: read(path.join(dir, 'assets/meta.json')), wipes: read(path.join(dir, 'data/wipes.json')), circles: read(path.join(dir, 'data/circles.json')), card: read(path.join(dir, 'data/card.json')), cfg: read(path.join(dir, 'config.json')) };
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ headless: true, args: ['--allow-file-access-from-files', '--force-color-profile=srgb'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  page.on('console', m => console.log('[page]', m.text())); page.on('pageerror', e => { console.error('[pageerror]', e.message); process.exitCode = 1; });
  await page.addInitScript(d => { window.DATA = d; }, data);
  await page.goto('file://' + path.resolve(dir, 'index.html'));
  await page.evaluate(() => window.ready);
  let blank = null, shots = 0;
  for (const n of frames) {
    const file = path.join(outDir, `ov_${String(n).padStart(4, '0')}.png`);
    const any = await page.evaluate(k => window.seekFrame(k), n);
    if (!any && blank) { fs.copyFileSync(blank, file); continue; }
    await page.screenshot({ path: file, type: 'png', omitBackground: true }); shots++;
    if (!any) blank = file;
  }
  await browser.close();
  console.log(`frames: ${frames.length}, screenshots: ${shots}`);
})().catch(e => { console.error(e); process.exit(1); });
