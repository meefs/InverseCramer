// Drives the Motion Canvas editor headlessly: start dev server, click Render, wait for the MP4.
import {spawn} from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import {chromium} from 'playwright-core';

const root = process.cwd();
// Launch the local vite binary directly so SIGTERM stops the dev server itself, not just a wrapper
const server = spawn(path.join(root, 'node_modules', '.bin', 'vite'), ['--port', '9000', '--strictPort', '--host', '127.0.0.1'], {cwd: root, stdio: ['ignore', fs.openSync('vite.log', 'w'), fs.openSync('vite.log', 'a')]});
const sleep = ms => new Promise(r => setTimeout(r, ms));
const findMp4 = dir => {
  if (!fs.existsSync(dir)) return null;
  for (const e of fs.readdirSync(dir, {withFileTypes: true})) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) { const f = findMp4(p); if (f) return f; }
    else if (e.name.endsWith('.mp4')) return p;
  }
  return null;
};
try {
  await sleep(6000);
  const browser = await chromium.launch({executablePath: process.env.CHROMIUM_PATH || undefined, args: ['--no-sandbox', '--disable-gpu']});
  const page = await browser.newPage({viewport: {width: 1600, height: 900}});
  await page.goto('http://127.0.0.1:9000');
  await page.waitForSelector('main', {timeout: 120000});
  await sleep(2000);
  const btn = page.getByRole('button', {name: 'Render'}).first();
  await btn.click({timeout: 60000});
  console.log('clicked Render');
  const deadline = Date.now() + 400000;
  let mp4 = null;
  while (!mp4 && Date.now() < deadline) { await sleep(3000); mp4 = findMp4(path.join(root, 'output')); }
  if (!mp4) { await page.screenshot({path: path.join(root, 'editor-debug.png')}); console.log('no mp4 produced; screenshot saved'); }
  else console.log('MP4:', mp4);
  await browser.close();
} finally {
  server.kill('SIGTERM');
}
