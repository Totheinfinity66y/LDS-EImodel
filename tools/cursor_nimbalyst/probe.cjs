'use strict';
// Dependency-free probe of the same stdio server registered with Cursor CLI.
const fs = require('node:fs');
const path = require('node:path');
const { spawn } = require('node:child_process');
const readline = require('node:readline');
const bridge = process.argv[2] || path.join(process.env.LOCALAPPDATA, 'NimbalystMcpBridge', 'bridge.cjs');
const session = process.argv[3];
const output = process.argv[4];
const child = spawn(process.execPath, [bridge], { cwd: process.cwd(), env: process.env, stdio: ['pipe', 'pipe', 'pipe'], windowsHide: true });
const pending = new Map();
let serial = 0;
const stderr = [];
child.stderr.on('data', data => stderr.push(String(data)));
readline.createInterface({ input: child.stdout }).on('line', line => {
  const msg = JSON.parse(line);
  const p = pending.get(msg.id);
  if (p) { pending.delete(msg.id); clearTimeout(p.timer); p.resolve(msg); }
});
child.on('exit', code => {
  for (const p of pending.values()) { clearTimeout(p.timer); p.reject(Error(`Bridge exited (${code})`)); }
  pending.clear();
});
function rpc(method, params) {
  const id = ++serial;
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => { pending.delete(id); reject(Error(`${method} timed out`)); }, 45000);
    pending.set(id, { resolve, reject, timer });
    child.stdin.write(JSON.stringify({ jsonrpc: '2.0', id, method, params }) + '\n');
  });
}
(async () => {
  const initialized = await rpc('initialize', { protocolVersion: '2024-11-05', capabilities: {}, clientInfo: { name: 'cursor-integration-probe', version: '1' } });
  if (initialized.error) throw Error(initialized.error.message);
  child.stdin.write(JSON.stringify({ jsonrpc: '2.0', method: 'notifications/initialized' }) + '\n');
  const catalog = await rpc('tools/list', {});
  if (catalog.error) throw Error(catalog.error.message);
  const names = catalog.result.tools.map(t => t.name);
  const required = ['spawn_session', 'create_session', 'send_prompt', 'get_session_status', 'get_session_result', 'list_recent_sessions', 'memory_status', 'memory_recall', 'memory_search_project_knowledge'];
  const missing = required.filter(name => !names.includes(name));
  const calls = {};
  if (session) for (const name of ['memory_status', 'memory_recall', 'list_recent_sessions']) {
    if (!names.includes(name)) continue;
    calls[name] = await rpc('tools/call', { name, arguments: { nimbalyst_session_id: session, ...(['memory_recall', 'list_recent_sessions'].includes(name) ? { limit: 1 } : {}) } });
  }
  const result = { at: new Date().toISOString(), bridge, initialized: initialized.result.serverInfo, count: names.length, names, missing, calls };
  if (output) fs.writeFileSync(output, JSON.stringify(result, null, 2) + '\n');
  console.log(JSON.stringify(result, null, 2));
  process.exitCode = missing.length || Object.values(calls).some(c => c.error || c.result?.isError) ? 1 : 0;
})().catch(e => { console.error(e.message); process.exitCode = 1; }).finally(() => child.kill());
