'use strict';
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { DatabaseSync } = require('node:sqlite');
const root = path.join(process.env.APPDATA, '@nimbalyst/electron');
const out = 'artifacts/cursor_nimbalyst_inbox_debug/';
function parseResponse(text) {
  if (!text.trim()) return null;
  if (text.trimStart().startsWith('{')) return JSON.parse(text);
  const data = text.split(/\r?\n\r?\n/).flatMap(block => block.split(/\r?\n/).filter(l=>l.startsWith('data:')).map(l=>l.slice(5).trimStart()));
  return JSON.parse(data.at(-1));
}
async function launch(callerId,compatibility=false) {
  const endpoint = JSON.parse(fs.readFileSync(path.join(root, 'mcp-endpoint.json'), 'utf8'));
  const url = new URL(`http://127.0.0.1:${endpoint.port}/mcp/host`);
  url.searchParams.set('workspacePath', process.cwd()); url.searchParams.set('sessionId', callerId);
  const headers = {Authorization:`Bearer ${endpoint.token}`,'Content-Type':'application/json',Accept:'application/json, text/event-stream'};
  let id=0;
  async function rpc(method, params) {
    const response = await fetch(url,{method:'POST',headers,body:JSON.stringify({jsonrpc:'2.0',id:++id,method,params}),signal:AbortSignal.timeout(45000)});
    if (!response.ok) throw Error(`Local MCP HTTP ${response.status}`);
    if (response.headers.get('mcp-session-id')) headers['mcp-session-id']=response.headers.get('mcp-session-id');
    const value=parseResponse(await response.text()); if(value?.error)throw Error(value.error.message); return value?.result;
  }
  await rpc('initialize',{protocolVersion:'2024-11-05',capabilities:{},clientInfo:{name:'active-inbox-verifier',version:'1'}});
  const notified = await fetch(url,{method:'POST',headers,body:JSON.stringify({jsonrpc:'2.0',method:'notifications/initialized'}),signal:AbortSignal.timeout(45000)});
  if (!notified.ok) throw Error(`Local MCP initialization HTTP ${notified.status}`);
  const catalog=await rpc('tools/list',{});
  assert.ok(catalog.tools.some(t=>t.name==='consume_session_inbox'),'Inbox is still missing from running host catalog');
  let prompt=`真实 Cursor 运行中收件验收。不要修改文件、依赖、记忆；不得使用 computer use。不要重命名本会话。先用 update_session_meta 设置 phase=validating、add=["inbox-live-test"]。按你当前上下文的准确 Nimbalyst session ID 调用所有工具。
1. 实际调用 spawn_session，inheritModel=true，notifyOnComplete=true，title="Inbox 单次报告探针"，prompt="这是一次子消息消费验收。禁止创建子会话、shell、computer use、文件读写、写记忆或发消息。不要重命名。仅按宿主要求调用 update_session_meta 设置 phase 为 validating、用 add 添加 inbox-probe 标签，然后最终只回复 INBOX_CHILD_READY_20261028。只完成一次，不等待其它消息。"。保存真实 child session ID，之后绝不再创建其它子会话。
2. 保持本回合运行，通过原生 Shell 工具执行唯一一次只读同步命令（禁止用 MCP 重复轮询）：在工作目录 D:\\Library\\10-16-handcrafted 用 powershell -NoProfile -Command 调用 & 'C:\\Program Files\\nodejs\\node.exe' 'D:\\Library\\10-16-handcrafted\\tools\\cursor_nimbalyst\\wait-inbox-report.cjs' '<你的准确session ID>' '<刚创建的child session ID>'。该脚本等待实际报告到达，最多45秒，没有数据库写入。如果超时直接报告失败并结束。
3. 脚本返回 reportReady=true 后，在同一回合实际调用 consume_session_inbox，checkpointId="live_received"（并提供桥接器要求的你自己的 nimbalyst_session_id）。读取整个批次，确认其中有 INBOX_CHILD_READY_20261028。不得发送确认消息，不得向子会话再发任何 prompt。
4. 最终只报告 INBOX_TEST_PASS、receipt 的 deliveryId、收到的 report ID 和 child ID；若工具错误或报告缺失则 INBOX_TEST_FAIL 加真实错误。收到消息后直接结束，不轮询空 inbox。
这项验收必须发生在父回合未结束时；不得先结束再由通知开新回合完成。`;
  if(compatibility)prompt=prompt.replace('在同一回合实际调用 consume_session_inbox，checkpointId="live_received"（并提供桥接器要求的你自己的 nimbalyst_session_id）。','在同一回合必须通过旧兼容入口 CallMcpTool 调用 server="nimbalyst"、toolName="consume_session_inbox"，arguments={checkpointId:"live_received",nimbalyst_session_id:"你的准确父session ID"}。这是针对 cursor-byok-compat 包装路径的定向验收，不能用原始 consume_session_inbox 直接调用代替。若工具报错，直接报告 INBOX_TEST_FAIL 并结束，禁止排查、重试或读取其它文件。');
  const result=await rpc('tools/call',{name:'spawn_session',arguments:{model:'cursor-agent:auto',title:compatibility?'Cursor 兼容入口收件验收':'Cursor 运行中收件验收',notifyOnComplete:false,prompt}});
  assert.ok(!result.isError,JSON.stringify(result));
  const text=result.content.filter(c=>c.type==='text').map(c=>c.text).join('\n');
  const created=JSON.parse(text);
  fs.writeFileSync(out+(compatibility?'compat-live-launch.json':'live-launch.json'),JSON.stringify({at:new Date().toISOString(),callerId,endpointPid:endpoint.pid,created},null,2)+'\n');
  console.log(JSON.stringify(created));
}
function audit(parentId,compatibility=false) {
  const db=new DatabaseSync(path.join(root,'sqlite-db/nimbalyst.sqlite'),{readOnly:true});
  try {
    const parent=db.prepare('SELECT id,provider,status,parent_session_id FROM ai_sessions WHERE id=?').get(parentId);
    assert.equal(parent?.provider,'cursor-agent'); assert.equal(parent.status,'idle','Wait for the test parent to finish before auditing');
    const messages=db.prepare('SELECT id,source,direction,content,created_at FROM ai_agent_messages WHERE session_id=? ORDER BY id').all(parentId);
    const inputs=messages.filter(r=>r.direction==='input'); assert.equal(inputs.length,1,'Report was replayed as an extra parent turn');
    const receipts=messages.filter(r=>r.source==='session-inbox').map(r=>({...r,parsed:JSON.parse(r.content)}));
    assert.equal(receipts.length,1,'Expected one in-turn receipt');
    const payload=JSON.parse(receipts[0].parsed.result); assert.equal(payload.messages.length,1);
    assert.ok(payload.messages[0].text.includes('INBOX_CHILD_READY_20261028'));
    const rows=db.prepare('SELECT id,status,document_context,prompt FROM queued_prompts WHERE session_id=? ORDER BY created_at,id').all(parentId);
    const consumed=rows.find(r=>r.id===payload.messages[0].id); assert.equal(consumed?.status,'completed');
    const delivery=JSON.parse(consumed.document_context).inboxDelivery;
    assert.equal(delivery.inputId,inputs[0].id); assert.equal(delivery.turnId,payload.turnId);
    assert.ok(receipts[0].id>inputs[0].id);
    const toolEvents=messages.flatMap(r=>{try{const event=JSON.parse(r.content);return event.type==='tool_call'&&event.subtype==='completed'?[{messageId:r.id,event}]:[];}catch{return[];}});
    function consumeArguments(event) {
      const a=event.tool_call?.mcpToolCall?.args;
      if(a?.toolName==='consume_session_inbox'&&a.serverIdentifier==='nimbalyst')return a.args;
      if(a?.toolName==='CallMcpTool'&&a.serverIdentifier==='cursor-byok-compat'&&a.args?.server==='nimbalyst'&&a.args?.toolName==='consume_session_inbox')return a.args.arguments;
      return null;
    }
    const consume=toolEvents.find(r=>consumeArguments(r.event)&&r.event.tool_call.mcpToolCall.result?.success?.isError===false); assert.ok(consume);
    if(compatibility)assert.ok(rows.some(r=>r.prompt.includes('必须通过旧兼容入口 CallMcpTool')),'Compatibility form was not requested in the actual queued prompt');
    assert.equal(consume.event.tool_call.mcpToolCall.result.success.isError,false);
    // A retried checkpoint intentionally returns the original receipt, including
    // its original invocation ID; the successful retry can have a new call ID.
    let originalInvocation=null;
    const successfulArgs=consumeArguments(consume.event);
    assert.equal(successfulArgs.nimbalyst_session_id,parentId);
    assert.equal(successfulArgs.checkpointId,delivery.requestKey.split(':').at(-1));
    if(delivery.identityKind==='authenticated-mcp-request') {
      assert.match(delivery.toolCallId,/^mcp:[a-f0-9-]{36}:.{1,200}$/);
      assert.ok(receipts[0].id<consume.messageId,'Receipt must precede successful tool completion');
    } else {
      originalInvocation=messages.flatMap(r=>{try{const event=JSON.parse(r.content);return event.type==='tool_call'&&event.subtype==='started'&&event.call_id===delivery.toolCallId?[{messageId:r.id,event}]:[];}catch{return[];}})[0];
      assert.ok(originalInvocation,'Receipt has no original provider invocation');
      const originalArgs=originalInvocation.event.tool_call?.mcpToolCall?.args;
      assert.equal(originalArgs?.toolName,'consume_session_inbox');
      assert.equal(originalArgs?.serverIdentifier,'nimbalyst');
      assert.equal(originalArgs?.args?.nimbalyst_session_id,parentId);
      assert.equal(originalArgs?.args?.checkpointId,successfulArgs.checkpointId);
      assert.ok(originalInvocation.messageId>inputs[0].id && originalInvocation.messageId<receipts[0].id);
    }
    const content=consume.event.tool_call.mcpToolCall.result.success.content;
    const returned=typeof content==='string'?content:content.map(c=>typeof c.text==='string'?c.text:c.text?.text||'').join('\n');
    assert.deepEqual(JSON.parse(returned),payload,'Successful invocation did not return the recorded delivery');
    assert.ok(messages.some(r=>{try{const e=JSON.parse(r.content);return e.type==='assistant'&&JSON.stringify(e.message?.content).includes('INBOX_TEST_PASS');}catch{return false;}}));
    assert.ok(!rows.some(r=>['pending','executing'].includes(r.status)),'Queue has unconsumed messages');
    const providerStart=messages.flatMap(r=>{try{const e=JSON.parse(r.content);return e.type==='tool_call'&&e.subtype==='started'&&e.call_id===consume.event.call_id?[r]:[];}catch{return[];}})[0];
    assert.ok(providerStart);
    const traceObservation={requestedCompatibility:compatibility,observedServerIdentifier:consume.event.tool_call.mcpToolCall.args.serverIdentifier,observedToolName:consume.event.tool_call.mcpToolCall.args.toolName,providerStartMessageId:providerStart.id,receiptBeforeProviderTrace:receipts[0].id<providerStart.id,providerTraceDelayMs:Date.parse(providerStart.created_at)-Date.parse(receipts[0].created_at)};
    const result={at:new Date().toISOString(),status:'PASS',parent,inputMessageId:inputs[0].id,receiptMessageId:receipts[0].id,identityKind:delivery.identityKind||'provider-trace',receiptInvocationId:delivery.toolCallId,originalInvocation,successfulProviderCallId:consume.event.call_id,traceObservation,payload,queue:rows,toolEvents};
    fs.writeFileSync(out+(compatibility?'compat-live-evidence.json':'live-evidence.json'),JSON.stringify(result,null,2)+'\n');
    console.log(JSON.stringify({status:'PASS',parentId,inputTurns:inputs.length,reports:payload.messages.length,queueStatus:consumed.status,deliveryId:payload.deliveryId,traceObservation}));
  } finally {db.close();}
}
(async()=>{if(process.argv[2]==='--launch')await launch(process.argv[3]);else if(process.argv[2]==='--launch-compat')await launch(process.argv[3],true);else if(process.argv[2]==='--audit')audit(process.argv[3]);else if(process.argv[2]==='--audit-compat')audit(process.argv[3],true);else throw Error('Usage: live-inbox.cjs --launch[-compat] caller-session | --audit[-compat] test-parent-session');})().catch(e=>{console.error(e.message);process.exitCode=1;});
