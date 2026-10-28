'use strict';
// Apply only the verified catalog/routing changes; preserve the installed bridge.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const target = path.join(process.env.LOCALAPPDATA, 'NimbalystMcpBridge', 'bridge.cjs');
const before = fs.readFileSync(target, 'utf8');
const oldHost = "'/mcp/host': new Set(['get_session_summary','get_session_coaching_signals','get_workstream_overview','get_workstream_edited_files','list_citable_inputs'])";
const newHost = "'/mcp/host': new Set(['spawn_session','create_session','send_prompt','get_session_status','get_session_result','list_recent_sessions','list_spawned_sessions','consume_session_inbox','get_session_summary','get_session_coaching_signals','get_workstream_overview','get_workstream_edited_files','list_citable_inputs'])";
const oldRoutes = "? ['/mcp/core', '/mcp/host', '/mcp/trackers', '/mcp/situational']";
const newRoutes = "? ['/mcp/core', '/mcp/host', '/mcp/trackers', '/mcp/situational', '/mcp/ext/memory']";
function normalizeSchemaScalars(value, schema) {
  // Convert only unambiguous primitive types declared by the upstream schema.
  if (!schema || typeof schema !== 'object') return value;
  if (schema.type === 'boolean' && (value === 'true' || value === 'false')) return value === 'true';
  if ((schema.type === 'number' || schema.type === 'integer') && typeof value === 'string' && /^-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?$/.test(value)) {
    const number = Number(value);
    if (Number.isFinite(number) && (schema.type !== 'integer' || Number.isSafeInteger(number))) return number;
  }
  if (schema.type === 'array' && Array.isArray(value)) return value.map(item => normalizeSchemaScalars(item, schema.items));
  if (schema.type === 'object' && value && typeof value === 'object' && !Array.isArray(value)) {
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, normalizeSchemaScalars(item, schema.properties?.[key])]));
  }
  return value;
}
const scalarMarker = 'const toolSchemas = new Map();';
const scalarLookup = "if (msg.params.name !== 'update_session_meta' && !toolSchemas.has(msg.params.name))";
if (before.includes(newHost) && before.includes(newRoutes) && before.includes(scalarMarker) && before.includes(scalarLookup)) { console.log('Already patched.'); process.exit(0); }
if (!(before.includes(oldHost) || before.includes(newHost)) || !(before.includes(oldRoutes) || before.includes(newRoutes))) throw Error('Installed bridge differs from audited source; refusing patch.');
let after = before.replace(oldHost, newHost).replace(oldRoutes, newRoutes);
if (!before.includes(scalarMarker)) {
  const oldCall = 'return await c.request({ ...msg, params: { ...msg.params, arguments: args } });';
  const newCall = `if (!toolSchemas.has(msg.params.name)) {
        const catalog = await c.request({ jsonrpc: '2.0', id: msg.id, method: 'tools/list', params: {} });
        if (catalog.error) throw new Error(catalog.error.message);
        for (const tool of catalog.result?.tools || []) toolSchemas.set(tool.name, tool.inputSchema);
      }
      args = normalizeSchemaScalars(args, toolSchemas.get(msg.params.name));
      return await c.request({ ...msg, params: { ...msg.params, arguments: args } });`;
  for (const fragment of ['const connections = new Map();', 'tools.push({ ...tool, inputSchema: schema });', oldCall]) if (!after.includes(fragment)) throw Error('Missing audited schema normalization anchor.');
  after = after.replace('const connections = new Map();', 'const connections = new Map();\n' + scalarMarker + '\n' + normalizeSchemaScalars.toString());
  after = after.replace('tools.push({ ...tool, inputSchema: schema });', 'toolSchemas.set(tool.name, tool.inputSchema);\n          tools.push({ ...tool, inputSchema: schema });');
  after = after.replace(oldCall, newCall);
}
// Metadata already has its own strict validator and has no scalar coercions.
after = after.replace('if (!toolSchemas.has(msg.params.name))', scalarLookup);
const stamp = new Date().toISOString().replace(/[:.]/g, '-');
const backupDir = path.join(path.dirname(target), 'repairs', stamp + '-session-memory');
fs.mkdirSync(backupDir, { recursive: true });
fs.writeFileSync(path.join(backupDir, 'bridge.cjs.bak'), before);
const hash = s => crypto.createHash('sha256').update(s).digest('hex');
const manifest = { at: new Date().toISOString(), target, backupDir, beforeSha256: hash(before), afterSha256: hash(after), changes: ['Expose child-session creation, follow-up and inspection tools', 'Include existing read-only memory route in default catalog', 'Normalize Cursor string boolean/number arguments only where upstream schema declares those types'] };
fs.writeFileSync(path.join(backupDir, 'manifest.json'), JSON.stringify(manifest, null, 2) + '\n');
fs.writeFileSync(target + '.tmp', after);
fs.renameSync(target + '.tmp', target);
console.log(JSON.stringify(manifest, null, 2));
