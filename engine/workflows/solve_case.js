// Auto-Bot deterministic orchestration of the investigation graph (engine/GRAPH.md)
// for Claude Code's Workflow tool. Part of Auto-Bot by Aditya Bhagat.
//
// Usage: invoke the Workflow tool with {scriptPath: "engine/workflows/solve_case.js",
//        args: {caseNumber: "26-01063725"}}
// The interactive /solve-case skill is the default path; use this script when you want
// the graph to run unattended (batch of cases, scheduled runs) with hard-coded routing.

export const meta = {
  name: 'autobot-solve-case',
  description: 'Auto-Bot L4 investigation graph: intake -> repro -> classify -> gated investigation -> hallucination check -> report -> writeback',
  phases: [
    { title: 'Intake' },
    { title: 'Connect' },
    { title: 'Reproduce' },
    { title: 'Classify' },
    { title: 'Investigate' },
    { title: 'Verify' },
    { title: 'Report' },
    { title: 'Writeback' },
  ],
}

const caseNumber = typeof args !== 'undefined' && args ? args.caseNumber : undefined
if (!caseNumber) throw new Error('args.caseNumber is required, e.g. {caseNumber: "26-01063725"}')

const CLASSIFY_SCHEMA = {
  type: 'object',
  properties: {
    primary_gate: { type: 'string', enum: ['G1', 'G2', 'G3', 'G4', 'G5'] },
    secondary_gate: { type: 'string' },
    batch_flag: { type: 'string', enum: ['none', 'NORMAL', 'SEGREGATED'] },
    parallel_gates: { type: 'array', items: { type: 'string' } },
    justification: { type: 'string' },
  },
  required: ['primary_gate', 'batch_flag', 'justification'],
}

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    verdict: { type: 'string', enum: ['PASS', 'FAIL'] },
    failures: { type: 'array', items: { type: 'string' } },
    drift: { type: 'string' },
  },
  required: ['verdict', 'failures'],
}

const GATE_AGENT = {
  G1: null, // expected behavior goes straight to report
  G2: 'config-investigator',
  G3: 'version-investigator',
  G4: 'data-investigator',
  G5: 'code-investigator',
}

phase('Intake')
const brief = await agent(
  `Run the intake-agent role from .claude/agents/intake-agent.md for Salesforce case ${caseNumber}. ` +
  `Follow it exactly (KB recall first, LIMIT 25, product detection). Write cases/${caseNumber}/case_brief.md. ` +
  `Return the executive summary + detected product + prior gate signal.`,
  { label: `intake:${caseNumber}`, phase: 'Intake' }
)
if (!brief) throw new Error('Intake failed — check Salesforce connector and case number.')
log(`Intake done for ${caseNumber}`)

phase('Connect')
// Headless run: the connector cannot ask the user mid-workflow. It binds to the
// running metadata server if the env matches the client, else records NOT CONNECTED
// (degraded mode). For interactive client/DB selection use /solve-case instead.
const connection = await agent(
  `Run the metadata-connector role from .claude/agents/metadata-connector.md for case ${caseNumber}. ` +
  `This is a HEADLESS run: if the environment is ambiguous or mismatched, do NOT wait for a user — ` +
  `record Status NOT CONNECTED (or MISMATCH) with the candidate environments in the brief and return that. ` +
  `Return the Metadata connection block.`,
  { label: `connect:${caseNumber}`, phase: 'Connect' }
)
const metadataConnected = !!(connection && connection.includes('CONNECTED') && !connection.includes('NOT CONNECTED'))
log(metadataConnected ? 'Metadata server bound to matching client env' : 'Metadata degraded mode — investigators emit NOT YET RUN SQL')

phase('Reproduce')
const repro = await agent(
  `Run the repro-agent role from .claude/agents/repro-agent.md for case ${caseNumber}. ` +
  `Read cases/${caseNumber}/case_brief.md, append the Reproduction section, return the verdict line.`,
  { label: `repro:${caseNumber}`, phase: 'Reproduce' }
)
if (!repro) log(`Repro agent failed for ${caseNumber} — continuing without a Reproduction verdict`)

phase('Classify')
let cls = await agent(
  `Run the classifier-agent role from .claude/agents/classifier-agent.md for case ${caseNumber}. ` +
  `Read the brief, append the Classification block, and return it as structured output.`,
  { label: `classify:${caseNumber}`, phase: 'Classify', schema: CLASSIFY_SCHEMA }
)

if (cls.batch_flag !== 'none') {
  const batch = await agent(
    `Run the batch-debugger role from .claude/agents/batch-debugger.md for case ${caseNumber} ` +
    `(${cls.batch_flag} batch suspected). Append findings to cases/${caseNumber}/evidence.md and return the underlying_gate block.`,
    { label: `batch:${caseNumber}`, phase: 'Classify' }
  )
  if (batch) {
    cls = await agent(
      `Run the classifier-agent role from .claude/agents/classifier-agent.md again for case ${caseNumber}, ` +
      `incorporating the batch-debugger finding:\n${batch}\n` +
      `Update the Classification block in the brief; return structured output.`,
      { label: `reclassify:${caseNumber}`, phase: 'Classify', schema: CLASSIFY_SCHEMA }
    )
  } else {
    log(`batch-debugger failed for ${caseNumber} — keeping original classification`)
  }
}
log(`Classified ${cls.primary_gate} (batch: ${cls.batch_flag}) — ${cls.justification}`)

phase('Investigate')
const gates = (cls.parallel_gates && cls.parallel_gates.length ? cls.parallel_gates : [cls.primary_gate])
  .filter(g => GATE_AGENT[g])
let verdicts = []
if (gates.length) {
  const investigators = gates.map(g => () => agent(
    `Run the ${GATE_AGENT[g]} role from .claude/agents/${GATE_AGENT[g]}.md for case ${caseNumber}. ` +
    `Read cases/${caseNumber}/case_brief.md and evidence.md, investigate per the agent file, ` +
    `append anchored findings to evidence.md, and return your verdict block.`,
    { label: `${GATE_AGENT[g]}:${caseNumber}`, phase: 'Investigate' }
  ))
  // table-analyst runs alongside G2/G4/G5 when the metadata server is bound to the client env
  if (metadataConnected && gates.some(g => g === 'G2' || g === 'G4' || g === 'G5')) {
    investigators.push(() => agent(
      `Run the table-analyst role from .claude/agents/table-analyst.md for case ${caseNumber}. ` +
      `Read cases/${caseNumber}/case_brief.md (note the Metadata connection env), build the module table map, ` +
      `verify objects/schemas/registered SQLs live, interrogate the data chain for the case entities (SELECT-only), ` +
      `append findings to evidence.md under "Table analysis", and return your verdict block.`,
      { label: `table-analyst:${caseNumber}`, phase: 'Investigate' }
    ))
  }
  verdicts = (await parallel(investigators)).filter(Boolean)
}

phase('Verify')
// G1 (expected behavior) has no investigator verdicts to refute — skip straight to report
let check = { verdict: 'PASS', failures: [] }
if (gates.length) {
  check = await agent(
    `Run the hallucination-checker role from .claude/agents/hallucination-checker.md for case ${caseNumber}. ` +
    `Verify all claims in cases/${caseNumber}/evidence.md and these verdict blocks:\n${verdicts.join('\n---\n')}\n` +
    `Return structured output.`,
    { label: `verify:${caseNumber}`, phase: 'Verify', schema: VERDICT_SCHEMA }
  )
  for (let i = 0; i < 2 && check.verdict === 'FAIL'; i++) {
    log(`Hallucination gate FAIL (${check.failures.length} claims) — iteration ${i + 1}`)
    verdicts = (await parallel(gates.map(g => () => agent(
      `Re-run the ${GATE_AGENT[g]} role from .claude/agents/${GATE_AGENT[g]}.md for case ${caseNumber} ` +
      `addressing ONLY these refuted claims:\n` +
      `${check.failures.join('\n')}\nFix or downgrade them in evidence.md; return the updated verdict block.`,
      { label: `fix:${GATE_AGENT[g]}:${caseNumber}`, phase: 'Verify' }
    )))).filter(Boolean)
    if (!verdicts.length) { log('All fix agents failed — aborting retry loop'); break }
    check = await agent(
      `Re-run the hallucination-checker role from .claude/agents/hallucination-checker.md for case ${caseNumber} ` +
      `on the updated evidence and these verdict blocks:\n${verdicts.join('\n---\n')}\nReturn structured output.`,
      { label: `reverify:${caseNumber}`, phase: 'Verify', schema: VERDICT_SCHEMA }
    )
  }
  if (check.verdict === 'FAIL') {
    log('Still failing after 2 iterations — downgrading weak claims to HYPOTHESIS per GRAPH.md; report ships as Investigation doc.')
  }
}

phase('Report')
const report = await agent(
  `Run the report-writer role from .claude/agents/report-writer.md for case ${caseNumber}. ` +
  `Gate outcome: ${cls.primary_gate}; hallucination verdict: ${check.verdict}` +
  `${check.verdict === 'FAIL' ? ' (ship as Investigation doc with ranked hypotheses)' : ''}. ` +
  `Write cases/${caseNumber}/report_<type>.md; return the report path + 5-line SF-paste summary.`,
  { label: `report:${caseNumber}`, phase: 'Report' }
)

phase('Writeback')
const learned = await agent(
  `Run the knowledge-curator role from .claude/agents/knowledge-curator.md for case ${caseNumber}. ` +
  `Decide index-only vs skill-update vs new-skill, update the product router if needed, ` +
  `and run kb.py remember. Return what was learned + where it was filed.`,
  { label: `writeback:${caseNumber}`, phase: 'Writeback' }
)

return { caseNumber, classification: cls, hallucination: check.verdict, report, learned }
