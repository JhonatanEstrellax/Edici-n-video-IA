const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

async function main() {
  const args = process.argv.slice(2);
  if (args.length < 1) {
    console.error('Usage: node render_tutorial_desktop.js <jobs_json_path>');
    process.exit(1);
  }

  const jobsData = JSON.parse(fs.readFileSync(args[0], 'utf-8'));
  const width = jobsData.width || 1920;
  const height = jobsData.height || 1080;
  const fps = jobsData.fps || 30;
  const htmlUrl = jobsData.html_url;
  const scenes = jobsData.scenes || [];
  const subBlocks = jobsData.subtitle_blocks || [];
  const subsOutDir = jobsData.subs_out_dir || null;
  const docksOutDir = jobsData.docks_out_dir || null;

  const browser = await chromium.launch({
    headless: true,
    args: ['--allow-file-access-from-files']
  });
  const page = await browser.newPage({
    viewport: { width, height },
    deviceScaleFactor: 1
  });

  await page.goto(htmlUrl, { waitUntil: 'networkidle' });
  await page.evaluate(async () => {
    await Promise.all([
      document.fonts.load("400 24px 'Poppins'"),
      document.fonts.load("500 24px 'Poppins'"),
      document.fonts.load("600 28px 'Poppins'"),
      document.fonts.load("700 32px 'Poppins'"),
      document.fonts.load("800 36px 'Poppins'")
    ]);
    await document.fonts.ready;
  });

  // 1. Render dock-only overlays for chapters 1..4 (used when modal is closed)
  if (docksOutDir) {
    fs.mkdirSync(docksOutDir, { recursive: true });
    for (let ch = 1; ch <= 4; ch++) {
      await page.evaluate(async (c) => {
        window.renderScene({ chapter_index: c, hide_side_card: true });
        window.seekTo(1.0);
        await document.fonts.ready;
      }, ch);
      await page.screenshot({
        path: path.join(docksOutDir, `dock_ch_${ch}.png`),
        type: 'png',
        omitBackground: true
      });
    }
  }

  // 2. Render each scene's animated frames (first 21 frames = 0.70s of GSAP entry animation; frame 20 is held thereafter)
  for (const sc of scenes) {
    const outDir = sc.out_dir;
    fs.mkdirSync(outDir, { recursive: true });
    const cfg = sc.graphic_config || {};
    const animFrames = 21; // 0.70s @ 30fps covers full GSAP timeline entry

    await page.evaluate(async (c) => {
      window.renderScene(c);
      await document.fonts.ready;
    }, cfg);

    for (let f = 0; f < animFrames; f++) {
      const tSec = f / fps;
      await page.evaluate((t) => window.seekTo(t), tSec);
      const filePath = path.join(outDir, `frame_${String(f).padStart(4, '0')}.png`);
      await page.screenshot({ path: filePath, type: 'png', omitBackground: true });
    }
    console.log(`[MG SCENE ${sc.scene_id}] Rendered ${animFrames} keyframe RGBA overlays -> ${outDir}`);
  }

  // 3. Render all Subtitle Blocks in Google Fonts Poppins
  if (subsOutDir) {
    fs.mkdirSync(subsOutDir, { recursive: true });
    await page.evaluate(() => window.enterTextCaptureMode());
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
    console.log(`[SUBTITLES] Rendered ${subBlocks.length} subtitle blocks in Chromium.`);
  }

  await browser.close();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
