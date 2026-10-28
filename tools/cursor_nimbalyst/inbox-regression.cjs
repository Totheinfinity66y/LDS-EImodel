'use strict';
const fs = require('node:fs');
const vm = require('node:vm');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const path = require('node:path');
const { readArchive } = require('./asar.cjs');
const file = process.argv[2];
const source = file ? fs.readFileSync(file, 'utf8') : readArchive(path.join(process.env.LOCALAPPDATA, 'Programs/Nimbalyst/resources/app.asar')).entries.get('/out/main/index.js').bytes.toString();
function extract(start, end) {
  const a = source.indexOf(start), b = source.indexOf(end, a);
  assert.ok(a >= 0 && b > a, `Source boundary absent: ${start}`);
  return source.slice(a, b);
}
const ctx = vm.createContext({ crypto$2: crypto, setTimeout: fn => { fn(); } });
vm.runInContext(extract('const parse = (value2) =>', 'const sessionInbox = new SessionInbox(') + ';globalThis.Inbox = SessionInbox;', ctx);
const session = 'test-parent', workspace = 'D:\\test';
const mcpInvocationId = 'mcp:00000000-0000-4000-8000-000000000000:1';
function cursorEvent(id, subtype = 'started', checkpointId = 'checkpoint1', overrides = {}) {
  return { type: 'tool_call', subtype, call_id: id, tool_call: { mcpToolCall: { args: { serverIdentifier: 'nimbalyst', toolName: 'consume_session_inbox', name: 'consume_session_inbox', args: { checkpointId, nimbalyst_session_id: session }, ...overrides } } } };
}
class FakeDb {
  constructor(events) { this.events = events; this.queue = []; this.receipts = new Map(); this.inputId = 10; this.running = true; }
  async query(sql, args) {
    if (sql.includes('SELECT MAX(id)')) return { rows: [{ id: 0 }] };
    if (sql.includes('SELECT id FROM ai_agent_messages')) return { rows: [{ id: this.inputId }] };
    if (sql.includes("source IN (")) {
      const includesCursor = sql.includes("'cursor-agent'");
      return { rows: this.events.filter(e => e.provider !== 'cursor-agent' || includesCursor).map(e => ({ content: JSON.stringify(e.value) })) };
    }
    if (sql.includes("source = 'session-inbox'")) return { rows: this.receipts.has(args[1]) ? [{ content: this.receipts.get(args[1]) }] : [] };
    if (sql.includes('SELECT id, prompt, document_context')) return { rows: this.queue.filter(r => r.status === 'pending').slice(0, args[1]) };
    if (sql.includes('UPDATE queued_prompts SET status = $2')) {
      for (const row of this.queue) if (row.status === 'executing' && JSON.parse(row.document_context).inboxDelivery.turnId === args[3]) row.status = args[1];
      return { rows: [] };
    }
    throw Error('Unexpected query: ' + sql.slice(0, 90));
  }
  async runTransaction(statements) {
    const queue = structuredClone(this.queue), receipts = new Map(this.receipts);
    for (const statement of statements) {
      const { sql, params: p } = statement;
      if (sql.includes('SELECT id FROM ai_agent_messages')) assert.ok(this.running && p[1] === this.inputId);
      else if (sql.includes('UPDATE queued_prompts SET status')) {
        const row = queue.find(r => r.id === p[0]);
        assert.ok(row && row.status === 'pending' && row.prompt === p[2] && row.document_context === p[4]);
        assert.equal(queue.find(r => r.status === 'pending').id, row.id);
        row.status = 'executing'; row.document_context = p[3];
      } else if (sql.includes('INSERT INTO ai_agent_messages')) receipts.set(p[3], p[1]);
      else throw Error('Unexpected transaction');
    }
    this.queue = queue; this.receipts = receipts;
  }
}
function fixture(events = [cursorEvent('cursor-call')]) {
  const db = new FakeDb(events.map(value => ({ provider: 'cursor-agent', value })));
  const inbox = new ctx.Inbox(db, () => {}, () => db.running);
  return { db, inbox };
}
function report(id, kind = 'report', originSessionId = 'test-child') {
  return { id, prompt: 'CHILD_REPORT_' + id, status: 'pending', attachments: null, document_context: JSON.stringify({ promptProvenance: { actor: 'agent', origin: 'child-session-update', messageKind: kind, originSessionId } }) };
}
const results = [];
async function test(name, fn) { try { await fn(); results.push({ name, pass: true }); } catch (e) { results.push({ name, pass: false, error: e.message }); } }
(async () => {
  await test('host endpoint advertises the inbox tool', async () => {
    const c = vm.createContext({});
    vm.runInContext(extract('const HOST_TOOLS = [', 'const TRACKER_TOOLS = [') + ';globalThis.host = HOST_TOOLS;', c);
    assert.ok(c.host.includes('consume_session_inbox'));
  });
  await test('Cursor turns begin an inbox lifecycle', async () => {
    const line = source.split('\n').find(l => l.includes('inboxTurn = [') && l.includes('sessionInbox.begin'));
    let started = false;
    const c = vm.createContext({ session: { id: session, provider: 'cursor-agent', workspacePath: workspace }, setup: { stage: async (_, fn) => fn() }, sessionInbox: { begin: async () => { started = true; } }, workspacePath: workspace });
    await vm.runInContext('(async()=>{let inboxTurn;' + line + '})()', c);
    assert.equal(started, true);
  });
  await test('host handler accepts verified Cursor invocation path', async () => {
    let caller;
    const c = vm.createContext({ AISessionsRepository: { get: async () => ({ workspacePath: workspace, provider: 'cursor-agent' }) }, getSessionStateManager: () => ({ getSessionState: () => ({ status: 'running' }) }), extractCodexTurnMetadataFromRequest: () => null, sessionInbox: { consume: async (_s, _w, value) => { caller = value; return '{}'; } } });
    vm.runInContext(extract('async function handleConsumeSessionInbox(', 'function connectMcpTransport(') + ';globalThis.call = handleConsumeSessionInbox;', c);
    await c.call(session, { params: { arguments: { checkpointId: 'checkpoint1' } } }, mcpInvocationId);
    assert.equal(caller.cursor, true);
    assert.equal(caller.cursorMcpInvocationId,mcpInvocationId);
  });
  await test('authenticated Cursor MCP request works before provider trace arrives', async () => {
    const {db,inbox}=fixture([]);db.queue.push(report('r1'));await inbox.begin(session,workspace);
    const result=JSON.parse(await inbox.consume(session,workspace,{cursor:true,cursorMcpInvocationId:mcpInvocationId,checkpointId:'checkpoint1'}));
    assert.equal(result.messages.length,1);assert.equal(JSON.parse(db.queue[0].document_context).inboxDelivery.identityKind,'authenticated-mcp-request');
  });
  await test('Cursor request proof cannot be supplied as a tool argument', async () => {
    const c=vm.createContext({});
    vm.runInContext(extract('async function handleConsumeSessionInbox(', 'function connectMcpTransport(')+';globalThis.call=handleConsumeSessionInbox;',c);
    await assert.rejects(()=>c.call(session,{params:{arguments:{checkpointId:'checkpoint1',cursorMcpInvocationId:mcpInvocationId}}},mcpInvocationId),/requires only/);
  });
  await test('invalid internal MCP proof is rejected',async()=>{
    const {db,inbox}=fixture([]);db.queue.push(report('r1'));await inbox.begin(session,workspace);
    await assert.rejects(()=>inbox.consume(session,workspace,{cursor:true,cursorMcpInvocationId:'unbound-request',checkpointId:'checkpoint1'}));
    assert.equal(db.queue[0].status,'pending');
  });
  await test('Cursor receives reports before the parent turn ends', async () => {
    const { db, inbox } = fixture(); db.queue.push(report('report1'));
    const turn = await inbox.begin(session, workspace);
    const result = JSON.parse(await inbox.consume(session, workspace, { cursor: true, checkpointId: 'checkpoint1' }));
    assert.equal(result.messages[0].text, 'CHILD_REPORT_report1');
    assert.equal(turn.active, true); assert.equal(db.running, true);
    assert.equal(db.queue[0].status, 'executing');
    await inbox.end(turn, true); assert.equal(db.queue[0].status, 'completed');
  });
  await test('retry returns the receipt and does not claim a second time', async () => {
    const { db, inbox } = fixture(); db.queue.push(report('report1'));
    await inbox.begin(session, workspace);
    const caller = { cursor: true, checkpointId: 'checkpoint1' };
    const first = await inbox.consume(session, workspace, caller);
    db.events.push({ provider:'cursor-agent',value:cursorEvent('cursor-call','completed') });
    db.events.unshift({provider:'cursor-agent',value:cursorEvent('retry-with-new-id')});
    const second = await inbox.consume(session, workspace, caller);
    assert.equal(first, second); assert.equal(db.receipts.size, 1);
  });
  await test('a later checkpoint cannot replay the same report', async () => {
    const { db, inbox } = fixture(); db.queue.push(report('report1'));
    await inbox.begin(session, workspace);
    await inbox.consume(session, workspace, { cursor: true, checkpointId: 'checkpoint1' });
    db.events.unshift({ provider: 'cursor-agent', value: cursorEvent('cursor-next', 'started', 'checkpoint2') });
    const result = JSON.parse(await inbox.consume(session, workspace, { cursor: true, checkpointId: 'checkpoint2' }));
    assert.equal(result.messages.length, 0);
  });
  await test('instruction boundary remains queued', async () => {
    const { db, inbox } = fixture(); db.queue.push(report('r1'), report('instruction', 'instruction'), report('r2'));
    await inbox.begin(session, workspace);
    const result = JSON.parse(await inbox.consume(session, workspace, { cursor: true, checkpointId: 'checkpoint1' }));
    assert.equal(result.messages.length, 1); assert.equal(result.boundary, 'instruction-or-untyped-message');
    assert.equal(db.queue[1].status, 'pending'); assert.equal(db.queue[2].status, 'pending');
  });
  await test('failed parent retires the consumed report without replay', async () => {
    const { db, inbox } = fixture(); db.queue.push(report('r1'));
    const turn = await inbox.begin(session, workspace);
    await inbox.consume(session, workspace, { cursor: true, checkpointId: 'checkpoint1' });
    await inbox.end(turn, false); assert.equal(db.queue[0].status, 'failed');
  });
  for (const [name, events] of [
    ['missing current tool invocation', []],
    ['wrong caller session', [cursorEvent('bad', 'started', 'checkpoint1', { args: { checkpointId: 'checkpoint1', nimbalyst_session_id: 'other-session' } })]],
    ['wrong MCP server', [cursorEvent('bad', 'started', 'checkpoint1', { serverIdentifier: 'untrusted' })]],
    ['completed tool invocation', [cursorEvent('done', 'started'), cursorEvent('done', 'completed')]],
    ['completed invocation with compatibility wrapper', [cursorEvent('wrapped-done'), cursorEvent('wrapped-done','completed','checkpoint1',{toolName:'CallMcpTool',serverIdentifier:'cursor-byok-compat',args:{server:'nimbalyst',toolName:'consume_session_inbox',arguments:{checkpointId:'checkpoint1',nimbalyst_session_id:session}}})]],
    ['ambiguous concurrent invocations', [cursorEvent('one'), cursorEvent('two')]]
  ]) await test('reject ' + name, async () => {
    const { db, inbox } = fixture(events); db.queue.push(report('r1'));
    await inbox.begin(session, workspace);
    await assert.rejects(() => inbox.consume(session, workspace, { cursor: true, checkpointId: 'checkpoint1' }));
    assert.equal(db.queue[0].status, 'pending'); assert.equal(db.receipts.size, 0);
  });
  await test('native Codex identity verification stays intact', async () => {
    const { db, inbox } = fixture([]);
    db.events.push({provider:'openai-codex',value:{method:'item/started',params:{turnId:'native-turn',threadId:'native-thread',item:{type:'mcpToolCall',tool:'consume_session_inbox',id:'native-call',arguments:{checkpointId:'checkpoint1'}}}}});
    db.queue.push(report('r1')); await inbox.begin(session, workspace);
    const result = JSON.parse(await inbox.consume(session, workspace, { nativeTurnId: 'native-turn', nativeThreadId: 'native-thread', checkpointId: 'checkpoint1' }));
    assert.equal(result.messages.length, 1);
  });
  await test('a retired turn cannot consume more messages', async () => {
    const { db, inbox } = fixture(); db.queue.push(report('r1'));
    const turn = await inbox.begin(session, workspace); await inbox.end(turn, true);
    await assert.rejects(() => inbox.consume(session, workspace, {cursor:true,cursorMcpInvocationId:mcpInvocationId,checkpointId:'checkpoint1'}));
    assert.equal(db.queue[0].status, 'pending');
  });
  await test('cross-workspace consumption is rejected', async () => {
    const { db, inbox } = fixture(); db.queue.push(report('r1')); await inbox.begin(session, workspace);
    await assert.rejects(() => inbox.consume(session, 'D:\\other', {cursor:true,checkpointId:'checkpoint1'}));
    assert.equal(db.queue[0].status, 'pending');
  });
  await test('unknown providers cannot opt themselves into Cursor identity', async () => {
    const c = vm.createContext({ AISessionsRepository: {get:async()=>({workspacePath:workspace,provider:'unknown'})},getSessionStateManager:()=>({getSessionState:()=>({status:'running'})}),extractCodexTurnMetadataFromRequest:()=>null,sessionInbox:{consume:async()=>{throw Error('must not reach consume')}} });
    vm.runInContext(extract('async function handleConsumeSessionInbox(', 'function connectMcpTransport(') + ';globalThis.call = handleConsumeSessionInbox;', c);
    await assert.rejects(()=>c.call(session,{params:{arguments:{checkpointId:'checkpoint1'}}},mcpInvocationId),/no verifiable/);
  });
  await test('native Claude identity verification stays intact', async () => {
    const { db, inbox } = fixture([]);
    db.events.push({provider:'claude-code',value:{message:{content:[{type:'tool_use',id:'claude-call',name:'mcp__nimbalyst-host__consume_session_inbox',input:{checkpointId:'checkpoint1'}}]}}});
    db.queue.push(report('r1')); await inbox.begin(session, workspace);
    const result = JSON.parse(await inbox.consume(session, workspace, { toolUseId:'claude-call',checkpointId:'checkpoint1' }));
    assert.equal(result.messages.length, 1);
  });
  const output = { at: new Date().toISOString(), source: file || 'installed app.asar', failed: results.filter(r=>!r.pass).length, results };
  console.log(JSON.stringify(output, null, 2)); process.exitCode = output.failed ? 1 : 0;
})().catch(e => { console.error(e); process.exitCode=1; });
