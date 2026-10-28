'use strict';
const fs = require('node:fs');
const crypto = require('node:crypto');
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
function readArchive(file) {
  const bytes = fs.readFileSync(file);
  const base = 8 + bytes.readUInt32LE(4);
  const header = JSON.parse(bytes.subarray(16, 16 + bytes.readUInt32LE(12)));
  const entries = new Map();
  function walk(tree, prefix = '') {
    for (const [name, entry] of Object.entries(tree.files || {})) {
      const key = prefix + '/' + name;
      if (entry.files) walk(entry, key);
      else if (!entry.unpacked && !entry.link && entry.offset !== undefined) entries.set(key, { entry, bytes: bytes.subarray(base + Number(entry.offset), base + Number(entry.offset) + entry.size) });
    }
  }
  walk(header);
  return { bytes, header, entries };
}
function replaceMain(archive, source) {
  const blocks = [];
  let offset = 0;
  for (const [key, value] of archive.entries) {
    const bytes = key === '/out/main/index.js' ? Buffer.from(source) : value.bytes;
    value.entry.offset = String(offset);
    value.entry.size = bytes.length;
    offset += bytes.length;
    blocks.push(bytes);
    if (key === '/out/main/index.js' && value.entry.integrity) {
      const blockSize = value.entry.integrity.blockSize || 4194304;
      value.entry.integrity = { algorithm: 'SHA256', hash: hash(bytes), blockSize, blocks: Array.from({ length: Math.ceil(bytes.length / blockSize) }, (_, i) => hash(bytes.subarray(i * blockSize, (i + 1) * blockSize))) };
    }
  }
  const json = Buffer.from(JSON.stringify(archive.header));
  const padded = Math.ceil((4 + json.length) / 4) * 4;
  const headerBytes = Buffer.alloc(4 + padded);
  headerBytes.writeUInt32LE(padded, 0);
  headerBytes.writeUInt32LE(json.length, 4);
  json.copy(headerBytes, 8);
  const size = Buffer.alloc(8);
  size.writeUInt32LE(4, 0);
  size.writeUInt32LE(headerBytes.length, 4);
  return Buffer.concat([size, headerBytes, ...blocks]);
}
module.exports = { readArchive, replaceMain, hash };
