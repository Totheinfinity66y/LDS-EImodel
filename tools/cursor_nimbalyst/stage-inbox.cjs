'use strict';
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');
const { readArchive, replaceMain, hash } = require('./asar.cjs');
const { patchMain } = require('./inbox-patch.cjs');
const target = path.join(process.env.LOCALAPPDATA, 'Programs/Nimbalyst/resources/app.asar');
function compare(before, after) {
  assert.deepEqual([...before.entries.keys()], [...after.entries.keys()]);
  const changed = [...before.entries.keys()].filter(key => !before.entries.get(key).bytes.equals(after.entries.get(key).bytes));
  assert.deepEqual(changed, ['/out/main/index.js']);
  const main = after.entries.get('/out/main/index.js');
  assert.equal(main.entry.integrity.hash, hash(main.bytes));
  return changed;
}
if (process.argv[2] === '--apply') {
  const manifestFile = process.argv[3];
  if (!manifestFile) throw Error('A staged manifest is required');
  const manifest = JSON.parse(fs.readFileSync(manifestFile, 'utf8'));
  assert.equal(path.resolve(manifest.target).toLowerCase(), path.resolve(target).toLowerCase());
  assert.equal(hash(fs.readFileSync(target)), manifest.beforeSha256, 'Installed application changed after staging');
  const staged = fs.readFileSync(manifest.stagedArchive);
  assert.equal(hash(staged), manifest.afterSha256, 'Staged archive changed');
  const before = readArchive(target), after = readArchive(manifest.stagedArchive);
  compare(before, after);
  fs.writeFileSync(target + '.inbox-tmp', staged);
  fs.renameSync(target + '.inbox-tmp', target);
  fs.writeFileSync(path.join(manifest.backupDir, 'applied.json'), JSON.stringify({ at: new Date().toISOString(), target, sha256: hash(fs.readFileSync(target)) }, null, 2));
  console.log('Staged inbox repair applied.');
} else {
  const original = readArchive(target), source = original.entries.get('/out/main/index.js').bytes.toString();
  const patched = patchMain(source);
  if (patched === source) throw Error('Inbox repair is already present; inspect the running application version.');
  assert.equal(patchMain(patched), patched, 'Patch is not idempotent');
  const backupDir = path.join(process.env.LOCALAPPDATA, 'NimbalystMcpBridge/repairs', new Date().toISOString().replace(/[:.]/g, '-') + '-active-inbox');
  fs.mkdirSync(backupDir, { recursive: true });
  fs.copyFileSync(target, path.join(backupDir, 'app.asar.bak'));
  const stagedArchive = path.join(backupDir, 'app.asar.staged');
  const mainFile = path.join(backupDir, 'main-after.js');
  fs.writeFileSync(mainFile, patched);
  execFileSync(process.execPath, ['--check', mainFile], { windowsHide: true });
  fs.writeFileSync(stagedArchive, replaceMain(original, patched));
  const changedEntries = compare(readArchive(target), readArchive(stagedArchive));
  const manifest = { at: new Date().toISOString(), target, backupDir, stagedArchive, mainFile, beforeSha256: hash(original.bytes), afterSha256: hash(fs.readFileSync(stagedArchive)), mainBeforeSha256: hash(Buffer.from(source)), mainAfterSha256: hash(Buffer.from(patched)), changedEntries, archiveEntries: original.entries.size, state: 'STAGED_NOT_LOADED' };
  fs.writeFileSync(path.join(backupDir, 'manifest.json'), JSON.stringify(manifest, null, 2) + '\n');
  fs.writeFileSync('artifacts/cursor_nimbalyst_inbox_debug/staged-manifest.json', JSON.stringify(manifest, null, 2) + '\n');
  console.log(JSON.stringify(manifest, null, 2));
}
