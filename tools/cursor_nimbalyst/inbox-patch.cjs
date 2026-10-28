'use strict';
// Pure source transformation: no application or database writes.
const legacyMarker = '// Nimbalyst local inbox compatibility: Cursor verified trace';
const marker = legacyMarker + ' v2';
const completedTrace = `
          // Completion envelopes can be renamed by Cursor's compatibility layer.
          // Match completion by ID; only started calls pass the identity checks below.
          if (caller.cursor && value2?.type === "tool_call" && value2.subtype === "completed" && typeof value2.call_id === "string") completed.add(value2.call_id);`;
function patchTrace(input) {
  if (input.includes(marker)) return input;
  if (input.includes(legacyMarker)) {
    if (input.split(legacyMarker).length !== 2) throw Error('Ambiguous Cursor inbox compatibility marker');
    return input.replace(legacyMarker, marker + completedTrace);
  }
  let source = input;
  function once(before, after) {
    if (source.split(before).length !== 2) throw Error('Patch anchor is absent or ambiguous: ' + before.slice(0, 100));
    source = source.replace(before, after);
  }
  const hostStart = source.indexOf('const HOST_TOOLS = [');
  const hostEnd = source.indexOf('const TRACKER_TOOLS = [', hostStart);
  if (hostStart < 0 || hostEnd < 0) throw Error('Host topology not found');
  const host = source.slice(hostStart, hostEnd);
  if (!host.includes('"consume_session_inbox"')) {
    source = source.slice(0, hostStart) + host.replace('  "list_queued_prompts",', '  "consume_session_inbox",\n  "list_queued_prompts",') + source.slice(hostEnd);
  }
  once('inboxTurn = ["claude-code", "openai-codex"].includes(session.provider)', 'inboxTurn = ["claude-code", "openai-codex", "cursor-agent"].includes(session.provider)');
  once("AND source IN ('claude-code', 'openai-codex')\n           ORDER BY id DESC LIMIT 100", "AND source IN ('claude-code', 'openai-codex', 'cursor-agent')\n           ORDER BY id DESC LIMIT 100");
  once('          const params2 = value2?.params;\n          const item = params2?.item;', `          ${marker}${completedTrace}
          const cursorTool = value2?.tool_call?.mcpToolCall?.args;
          const cursorInput = cursorTool?.args;
          if (caller.cursor && value2?.type === "tool_call" && typeof value2.call_id === "string" &&
              cursorTool?.toolName === TOOL && ["nimbalyst", "nimbalyst-host"].includes(cursorTool?.serverIdentifier) &&
              cursorInput && !Array.isArray(cursorInput) && typeof cursorInput === "object" &&
              Object.keys(cursorInput).every((key) => ["checkpointId", "nimbalyst_session_id"].includes(key)) &&
              cursorInput.nimbalyst_session_id === turn.sessionId &&
              this.matchesCheckpoint({ checkpointId: cursorInput.checkpointId }, caller.checkpointId)) {
            if (value2.subtype === "started") started2.add(value2.call_id);
            if (value2.subtype === "completed") completed.add(value2.call_id);
          }
          const params2 = value2?.params;
          const item = params2?.item;`);
  once('if (!native2?.turnId && typeof toolUseId !== "string")\n    throw new Error("This provider has no verifiable inbox tool invocation");', 'if (!native2?.turnId && typeof toolUseId !== "string" && session.provider !== "cursor-agent")\n    throw new Error("This provider has no verifiable inbox tool invocation");');
  once('checkpointId: args.checkpointId,\n    toolUseId:', 'checkpointId: args.checkpointId,\n    cursor: session.provider === "cursor-agent",\n    toolUseId:');
  once('Supports Claude Code and Codex MCP turns with verifiable tool-call identity.', 'Supports Claude Code, Codex and Cursor MCP turns with verifiable tool-call identity.');
  once('Use the tracker tools for TODO/work radar and collaborative document tools when relevant.`;', 'Use the tracker tools for TODO/work radar and collaborative document tools when relevant. When coordinating children, call consume_session_inbox with a unique checkpointId at integration boundaries, after independent work and before your final answer. Read its entire report batch and continue within this turn; do not resend completion acknowledgements to children. If it reports an instruction boundary, yield for normal queue delivery. Do not poll an empty inbox or keep a turn alive solely waiting for children.`;');
  return source;
}
const requestMarker = '// Nimbalyst Cursor inbox identity: authenticated MCP request v3';
function patchMain(input) {
  if(input.includes(requestMarker)) return input;
  let source=patchTrace(input);
  function once(before,after) {
    if(source.split(before).length!==2)throw Error('Request identity anchor absent or ambiguous: '+before.slice(0,90));
    source=source.replace(before,after);
  }
  once('  async resolveInvocation(turn, caller) {\n    for (let attempt', `  async resolveInvocation(turn, caller) {
    ${requestMarker}
    if (caller.cursorMcpInvocationId) {
      if (!/^mcp:[a-f0-9-]{36}:.{1,200}$/.test(caller.cursorMcpInvocationId)) throw new Error("Invalid internal MCP invocation proof");
      this.assertActive(turn);
      const input = await this.db.query(
        "SELECT id FROM ai_agent_messages WHERE session_id = $1 AND direction = 'input' AND id > $2 ORDER BY id DESC LIMIT 1",
        [turn.sessionId, turn.baselineId]
      );
      this.assertActive(turn);
      if (input.rows.length !== 1) throw new Error("Authenticated MCP request has no current turn input");
      return { inputId: Number(input.rows[0].id), toolCallId: caller.cursorMcpInvocationId, identityKind: "authenticated-mcp-request", completed: false, ambiguous: false };
    }
    for (let attempt`);
  once('toolCallId: identity2.toolCallId,\n        coordinatorId:', 'toolCallId: identity2.toolCallId,\n        identityKind: identity2.identityKind ?? "provider-trace",\n        coordinatorId:');
  once('async function handleConsumeSessionInbox(sessionId, request) {', 'async function handleConsumeSessionInbox(sessionId, request, cursorMcpInvocationId) {');
  once('  const native2 = extractCodexTurnMetadataFromRequest(request);\n  const toolUseId = request.params._meta?.["claudecode/toolUseId"];', '  if (session.provider === "cursor-agent" && !cursorMcpInvocationId) throw new Error("Cursor inbox requires an authenticated MCP invocation");\n  const native2 = extractCodexTurnMetadataFromRequest(request);\n  const toolUseId = request.params._meta?.["claudecode/toolUseId"];');
  once('    cursor: session.provider === "cursor-agent",\n    toolUseId:', '    cursor: session.provider === "cursor-agent",\n    cursorMcpInvocationId: session.provider === "cursor-agent" ? cursorMcpInvocationId : void 0,\n    toolUseId:');
  once('  const server = new Server(\n    { name: serverName, version: "1.0.0" },', '  const inboxRequestScope = crypto$1.randomUUID();\n  const server = new Server(\n    { name: serverName, version: "1.0.0" },');
  once('          return handleConsumeSessionInbox(sessionId, request);', '          return handleConsumeSessionInbox(sessionId, request, `mcp:${inboxRequestScope}:${String(extra.requestId)}`);');
  return source;
}
module.exports = { patchMain, marker:requestMarker };
if (require.main === module) {
  const fs = require('node:fs');
  if (!process.argv[2] || !process.argv[3]) throw Error('Usage: inbox-patch.cjs input-main.js output-main.js');
  fs.writeFileSync(process.argv[3], patchMain(fs.readFileSync(process.argv[2], 'utf8')));
}
