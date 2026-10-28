'use strict';
// Read-only, bounded evidence export for the integration test sessions only.
const fs = require('node:fs');
const path = require('node:path');
const { DatabaseSync } = require('node:sqlite');
const parentId = '0352f796-8588-44af-b009-8c9ac314c7cc';
const childId = 'f80cfa0f-5015-46cf-80f9-9fb815fed7f5';
const db = new DatabaseSync(path.join(process.env.APPDATA, '@nimbalyst/electron/sqlite-db/nimbalyst.sqlite'), { readOnly: true });
try {
  const sessions = [parentId, childId].map(id => db.prepare('SELECT id,workspace_id,provider,model,provider_session_id,parent_session_id,created_by_session_id,status FROM ai_sessions WHERE id=?').get(id));
  const messages = db.prepare('SELECT id,session_id,created_at,direction,content FROM ai_agent_messages WHERE session_id IN (?,?) ORDER BY id').all(parentId, childId);
  const calls = [];
  const replies = [];
  for (const row of messages) {
    let event; try { event = JSON.parse(row.content); } catch { continue; }
    if (event.type === 'tool_call' && event.subtype === 'completed') calls.push({ messageId: row.id, sessionId: row.session_id, createdAt: row.created_at, event });
    if (event.type === 'assistant') {
      const text = (event.message?.content || []).filter(c=>c.type==='text').map(c=>c.text).join('');
      if (row.session_id === childId) replies.push({ messageId: row.id, text });
    }
  }
  const evidence = { at: new Date().toISOString(), sessions, calls, replies };
  fs.writeFileSync('artifacts/cursor_nimbalyst_debug/end-to-end.json', JSON.stringify(evidence, null, 2) + '\n');
  console.log(JSON.stringify({sessions,calls:calls.map(c=>({messageId:c.messageId,sessionId:c.sessionId,tool:c.event.tool_call?.mcpToolCall?.args?.toolName,result:c.event.tool_call?.mcpToolCall?.result})),replies},null,2));
} finally { db.close(); }
