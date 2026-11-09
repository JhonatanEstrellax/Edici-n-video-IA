const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

async function main() {
  const args = process.argv.slice(2);
  if (args.length < 1) {
    console.error('Usage: node render_mg.js <jobs_json_path>');
    process.exit(1);
  }

  const jobsData = JSON.parse(fs.readFileSync(args[0], 'utf-8'));
  const width = jobsData.width || 1080;
  const height = jobsData.height || 1920;
  const fps = jobsData.fps || 30;
  const htmlUrl = jobsData.html_url;
  const scenes = jobsData.scenes || [];
  const subBlocks = jobsData.subtitle_blocks || [];
  const topTitle = jobsData.top_title || null;
  const subsOutDir = jobsData.subs_out_dir || null;

  const browser = await chromium.launch({
    headless: true,
    args: ['--allow-file-access-from-files']
  });
  const page = await browser.newPage({
    viewport: { width, height },
    deviceScaleFactor: 1
  });

  await page.goto(htmlUrl, { waitUntil: 'networkidle' });
  const fontsLoaded = await page.evaluate(async () => {
    await Promise.all([
      document.fonts.load("400 32px 'Poppins'"),
      document.fonts.load("500 32px 'Poppins'"),
      document.fonts.load("600 48px 'Poppins'"),
      document.fonts.load("700 64px 'Poppins'"),
      document.fonts.load("800 80px 'Poppins'")
    ]);
    await document.fonts.ready;
    return {
      w600: document.fonts.check("600 48px 'Poppins'"),
      w700: document.fonts.check("700 64px 'Poppins'"),
      w800: document.fonts.check("800 80px 'Poppins'")
    };
  });
  console.log('[GOOGLE FONTS POPPINS]', JSON.stringify(fontsLoaded));

  for (const sc of scenes) {
    const outDir = sc.out_dir;
    fs.mkdirSync(outDir, { recursive: true });
    const cfg = sc.graphic_config || {};
    const dur = Math.max(0.3, sc.edited_duration || 2.0);
    cfg.duration = dur;
    const totalFrames = Math.max(1, Math.round(dur * fps));

    await page.evaluate(async (c) => {
      window.renderScene(c);
      await document.fonts.ready;
    }, cfg);

    const swSec = Number(cfg.switch_sec || 0);
    const enterSec = Number(cfg.hook_delayed_enter_sec || 0);

    if (swSec > 0.2 || enterSec > 0.05) {
      let lastCapturedPath = null;
      for (let f = 0; f < totalFrames; f++) {
        const tSec = f / fps;
        const inIntro = tSec <= 0.65;
        const inDelayedEnter = enterSec > 0.05 && tSec >= (enterSec - 0.06) && tSec <= (enterSec + 0.45);
        const inSwitch = swSec > 0.2 && tSec >= (swSec - 0.55) && tSec <= (swSec + 0.45);
        const filePath = path.join(outDir, `frame_${String(f).padStart(4, '0')}.png`);

        if (f === 0 || inIntro || inDelayedEnter || inSwitch || !lastCapturedPath) {
          await page.evaluate((t) => window.seekTo(t), tSec);
          await page.screenshot({ path: filePath, type: 'png', omitBackground: true });
          lastCapturedPath = filePath;
        } else {
          fs.copyFileSync(lastCapturedPath, filePath);
        }
      }
    } else {
      const activeAnimFrames = Math.min(totalFrames, Math.round(1.45 * fps));
      for (let f = 0; f < activeAnimFrames; f++) {
        const tSec = f / fps;
        await page.evaluate((t) => window.seekTo(t), tSec);
        const filePath = path.join(outDir, `frame_${String(f).padStart(4, '0')}.png`);
        await page.screenshot({ path: filePath, type: 'png', omitBackground: true });
      }
    }
  }

  // Render all Subtitle Blocks & Hook Title directly in Chromium using Google Fonts Poppins
  if (subsOutDir) {
    fs.mkdirSync(subsOutDir, { recursive: true });
    await page.evaluate(() => window.enterTextCaptureMode());

    if (topTitle) {
      await page.evaluate(async (tCfg) => {
        window.renderTopTitleDOM(tCfg);
        await document.fonts.ready;
      }, topTitle);
      const titleLoc = page.locator('#gf-title-box');
      await titleLoc.screenshot({
        path: path.join(subsOutDir, 'top_title.png'),
        type: 'png',
        omitBackground: true
      });
    }

    const subLoc = page.locator('#gf-sub-box');
    for (const b of subBlocks) {
      await page.evaluate(async (blk) => {
        window.renderSubtitleBlockDOM(blk);
        await document.fonts.ready;
      }, b);
      await subLoc.screenshot({
        path: path.join(subsOutDir, `sub_${b.block_id}.png`),
        type: 'png',
        omitBackground: true
      });
    }
    console.log(`[GOOGLE FONTS POPPINS] Rendered ${subBlocks.length} subtitle blocks + hook title in Chromium.`);
  }

  await browser.close();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
