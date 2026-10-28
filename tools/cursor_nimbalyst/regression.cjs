'use strict';
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const bridge = process.argv[2] || path.join(process.env.LOCALAPPDATA, 'NimbalystMcpBridge', 'bridge.cjs');
const source = fs.readFileSync(bridge, 'utf8');
const results = [];
async function test(name, fn) { try { await fn(); results.push({ name, pass: true }); } catch (error) { results.push({ name, pass: false, error: error.message }); } }
(async () => {
  const boundary = source.indexOf('const input = readline.createInterface(');
  assert.ok(boundary > 0);
  const context = vm.createContext({ require, process, URL, AbortSignal, observed: [] });
  vm.runInContext(source.slice(0, boundary) + `
    resolveSession = explicit => { if (explicit !== 'test-session') throw Error('invalid identity'); return explicit; };
    connect = async (session, targetRoute) => ({ request: async message => {
      if (message.method === 'tools/list') return {result:{tools:[{name:'get_session_result',inputSchema:{type:'object',properties:{includeFullResponse:{type:'boolean'},sessionId:{type:'string'}}}},{name:'memory_recall',inputSchema:{type:'object',properties:{limit:{type:'number'}}}}]}};
      observed.push({session, targetRoute, message});
      return {jsonrpc:'2.0', id:message.id, result:{content:[{type:'text',text:'upstream mock'}]}};
    }});
    globalThis.call = handle;
    globalThis.routes = compositeToolRoutes;
  `, context);
  const expected = { spawn_session: '/mcp/host', create_session: '/mcp/host', send_prompt: '/mcp/host', get_session_status: '/mcp/host', get_session_result: '/mcp/host', list_recent_sessions: '/mcp/host', memory_recall: '/mcp/ext/memory', memory_status: '/mcp/ext/memory', memory_search_project_knowledge: '/mcp/ext/memory', update_session_meta: '/mcp/core', readCollabDoc: '/mcp/situational' };
  for (const [name, route] of Object.entries(expected)) await test(`${name} routes with caller identity`, async () => {
    const before = context.observed.length;
    const response = await context.call({ jsonrpc: '2.0', id: 1, method: 'tools/call', params: { name, arguments: { nimbalyst_session_id: 'test-session' } } });
    assert.equal(response.error, undefined);
    assert.equal(context.observed.length, before + 1);
    const actual = context.observed.at(-1);
    assert.equal(actual.targetRoute, route);
    assert.equal(actual.session, 'test-session');
    assert.equal('nimbalyst_session_id' in actual.message.params.arguments, false);
  });
  await test('invalid caller identity never reaches upstream', async () => {
    const before = context.observed.length;
    const response = await context.call({id: 2, method:'tools/call', params:{name:'spawn_session',arguments:{nimbalyst_session_id:'wrong-session'}}});
    assert.ok(response.error);
    assert.equal(context.observed.length, before);
  });
  await test('read-only memory boundary retained', async () => {
    for (const name of ['memory_remember', 'memory_delete_fact', 'memory_set_local_embeddings', 'memory_rebuild']) assert.equal(context.routes.has(name), false);
  });
  await test('session metadata rejects invalid phase', async () => {
    const before = context.observed.length;
    const response = await context.call({id:3,method:'tools/call',params:{name:'update_session_meta',arguments:{nimbalyst_session_id:'test-session',phase:'implementation'}}});
    assert.equal(response.result.isError, true);
    assert.equal(context.observed.length, before);
  });
  await test('Cursor string false remains false at upstream', async () => {
    await context.call({id:4,method:'tools/call',params:{name:'get_session_result',arguments:{nimbalyst_session_id:'test-session',includeFullResponse:'false'}}});
    assert.equal(context.observed.at(-1).message.params.arguments.includeFullResponse, false);
  });
  await test('Cursor numeric limit reaches upstream as a number', async () => {
    await context.call({id:5,method:'tools/call',params:{name:'memory_recall',arguments:{nimbalyst_session_id:'test-session',limit:'1'}}});
    assert.equal(context.observed.at(-1).message.params.arguments.limit, 1);
  });
  await test('string fields are not coerced', async () => {
    await context.call({id:6,method:'tools/call',params:{name:'get_session_result',arguments:{nimbalyst_session_id:'test-session',sessionId:'false'}}});
    assert.equal(context.observed.at(-1).message.params.arguments.sessionId, 'false');
  });
  await test('native false stays false', async () => {
    await context.call({id:7,method:'tools/call',params:{name:'get_session_result',arguments:{nimbalyst_session_id:'test-session',includeFullResponse:false}}});
    assert.equal(context.observed.at(-1).message.params.arguments.includeFullResponse, false);
  });
  await test('nonfinite and noncanonical numeric strings are not guessed', async () => {
    for (const value of ['NaN', 'Infinity', ' 1 ', '1abc']) {
      await context.call({id:8,method:'tools/call',params:{name:'memory_recall',arguments:{nimbalyst_session_id:'test-session',limit:value}}});
      assert.equal(context.observed.at(-1).message.params.arguments.limit, value);
    }
  });
  const report = { at: new Date().toISOString(), bridge, failed: results.filter(r=>!r.pass).length, results };
  console.log(JSON.stringify(report, null, 2));
  process.exitCode = report.failed ? 1 : 0;
})().catch(e => { console.error(e); process.exitCode=1; });
