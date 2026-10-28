'use strict';
// Test-only synchronization: read a known test parent's queue, never claim it.
const path = require('node:path');
const { DatabaseSync } = require('node:sqlite');
const parent = process.argv[2], child = process.argv[3];
if (!parent || !child) throw Error('Usage: wait-inbox-report.cjs parent-session child-session');
const db = new DatabaseSync(path.join(process.env.APPDATA, '@nimbalyst/electron/sqlite-db/nimbalyst.sqlite'), { readOnly: true });
(async () => {
  const row = db.prepare('SELECT provider,workspace_id FROM ai_sessions WHERE id=?').get(parent);
  if (row?.provider !== 'cursor-agent' || path.resolve(row.workspace_id).toLowerCase() !== path.resolve(process.cwd()).toLowerCase()) throw Error('Not the current workspace Cursor test parent');
  const deadline = Date.now() + 45000;
  while (Date.now() < deadline) {
    const rows = db.prepare("SELECT id,document_context FROM queued_prompts WHERE session_id=? AND status='pending' ORDER BY created_at,id").all(parent);
    const report = rows.find(r => { const p = JSON.parse(r.document_context || '{}').promptProvenance; return p?.originSessionId === child && p?.messageKind === 'report'; });
    if (report) { console.log(JSON.stringify({reportReady:true,queueId:report.id,parent,child})); return; }
    await new Promise(resolve => setTimeout(resolve, 250));
  }
  throw Error('No child report arrived within 45 seconds; do not poll an empty inbox.');
})().catch(e => { console.error(e.message); process.exitCode=1; }).finally(()=>db.close());
