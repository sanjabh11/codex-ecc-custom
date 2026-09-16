#!/usr/bin/env node
'use strict';

const fs = require('fs');
const crypto = require('crypto');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');

const VALID_DECISIONS = new Set(['continue', 'change-plan', 'stop-and-ask']);
const VALID_DIRECTIONS = new Set(['lower', 'higher']);
const VALID_TRACE_STATUSES = new Set(['pass', 'fail', 'blocked', 'info']);

function usage() {
  return [
    'Usage:',
    '  phase-loop-ledger.js init --task <text> [--tier <0-3>] [--root <path>]',
    '  phase-loop-ledger.js classify --task <text> [--json] [--root <path>]',
    '  phase-loop-ledger.js record --phase <id> --objective <text> --baseline <text> --delta <text> --reflection <text> --decision <continue|change-plan|stop-and-ask> --next-adjustment <text> [--metric name=value:lower|higher:thresholdPct] [--check command|pass|durationMs]',
    '  phase-loop-ledger.js trace-step --phase <id> --name <text> --status <pass|fail|blocked|info> [--kind <text>] [--evidence <text>] [--failure-category <text>] [--duration-ms <number>] [--root <path>]',
    '  phase-loop-ledger.js queue-improvement --note <text> [--source <text>] [--root <path>]',
    '  phase-loop-ledger.js health [--json] [--root <path>]',
    '  phase-loop-ledger.js next [--json] [--root <path>]',
    '  phase-loop-ledger.js audit [--json] [--root <path>]',
    '  phase-loop-ledger.js pack --name <text> [--json] [--root <path>]',
    '  phase-loop-ledger.js import-bench --file <path> [--metric-prefix <text>] [--threshold-pct <number>] [--root <path>]',
    '  phase-loop-ledger.js map-beads [--phase <id> --bead <id>] [--json] [--root <path>]',
    '  phase-loop-ledger.js status [--json] [--root <path>]',
  ].join('\n');
}

function parseArgv(argv) {
  const [command, ...rest] = argv;
  const flags = {};
  const positional = [];

  for (let index = 0; index < rest.length; index += 1) {
    const token = rest[index];
    if (!token.startsWith('--')) {
      positional.push(token);
      continue;
    }

    const key = token.slice(2);
    const next = rest[index + 1];
    const value = !next || next.startsWith('--') ? true : next;
    if (value !== true) {
      index += 1;
    }

    if (Object.prototype.hasOwnProperty.call(flags, key)) {
      flags[key] = Array.isArray(flags[key]) ? [...flags[key], value] : [flags[key], value];
    } else {
      flags[key] = value;
    }
  }

  return { command, flags, positional };
}

function flag(flags, key, fallback = null) {
  const value = flags[key];
  if (Array.isArray(value)) {
    return value[value.length - 1];
  }
  return value === undefined ? fallback : value;
}

function flagList(flags, key) {
  const value = flags[key];
  if (value === undefined) {
    return [];
  }
  return Array.isArray(value) ? value : [value];
}

function nowIso() {
  return new Date().toISOString();
}

function resolveRoot(flags) {
  return path.resolve(String(flag(flags, 'root', process.cwd())));
}

function ensureDir(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
}

function artifactPaths(root) {
  const dir = path.join(root, '.phase-loop');
  return {
    dir,
    masterPlan: path.join(dir, 'master-plan.md'),
    ledger: path.join(dir, 'phase-ledger.jsonl'),
    ratchets: path.join(dir, 'ratchets.json'),
    improvements: path.join(dir, 'improvements.jsonl'),
    health: path.join(dir, 'session-health.jsonl'),
    traceSpans: path.join(dir, 'trace-spans.jsonl'),
    beadMap: path.join(dir, 'bead-map.json'),
    evidencePacksDir: path.join(dir, 'evidence-packs'),
  };
}

function readJson(filePath, fallback) {
  if (!fs.existsSync(filePath)) {
    return fallback;
  }
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function writeJson(filePath, value) {
  ensureDir(path.dirname(filePath));
  fs.writeFileSync(filePath, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
}

function appendJsonl(filePath, value) {
  ensureDir(path.dirname(filePath));
  fs.appendFileSync(filePath, `${JSON.stringify(value)}\n`, 'utf8');
}

function readJsonl(filePath) {
  if (!fs.existsSync(filePath)) {
    return [];
  }
  return fs.readFileSync(filePath, 'utf8')
    .split('\n')
    .map(line => line.trim())
    .filter(Boolean)
    .map(line => JSON.parse(line));
}

function fileExists(filePath) {
  try {
    return fs.existsSync(filePath) && fs.statSync(filePath).isFile();
  } catch (_error) {
    return false;
  }
}

function commandExists(command) {
  try {
    execFileSync('sh', ['-c', `command -v ${JSON.stringify(command)} >/dev/null 2>&1`], {
      stdio: ['ignore', 'ignore', 'ignore'],
    });
    return true;
  } catch (_error) {
    return false;
  }
}

function isInsideRoot(root, candidatePath) {
  const relative = path.relative(root, candidatePath);
  return relative === '' || (!relative.startsWith('..') && !path.isAbsolute(relative));
}

function sha256File(filePath) {
  const hash = crypto.createHash('sha256');
  hash.update(fs.readFileSync(filePath));
  return hash.digest('hex');
}

function requireText(flags, key) {
  const value = flag(flags, key);
  if (typeof value !== 'string' || value.trim() === '') {
    throw new Error(`Missing required --${key}`);
  }
  return value.trim();
}

function parseTier(value) {
  if (value === null || value === true) {
    return null;
  }
  const tier = Number(value);
  if (!Number.isInteger(tier) || tier < 0 || tier > 3) {
    throw new Error('--tier must be an integer from 0 to 3');
  }
  return tier;
}

function matchAny(text, patterns) {
  return patterns.some(pattern => pattern.test(text));
}

function uniq(values) {
  return [...new Set(values)];
}

function classifyTask(task, root) {
  const text = task.toLowerCase();
  const reasons = [];
  const subskills = [];
  let tier = 0;

  const highRisk = matchAny(text, [
    /\bproduction\b/,
    /\bprod\b/,
    /\bdeploy(?:ment)?\b/,
    /\bsecurity\b/,
    /\bsecrets?\b/,
    /\bcompliance\b/,
    /\blegal\b/,
    /\bmedical\b/,
    /\bfinancial?\b/,
    /\bpayments?\b/,
    /\bdestructive\b/,
    /\bdelete\b/,
    /\breset\b/,
    /\bforce[- ]?push\b/,
    /\bglobal\b/,
    /\bplugin\b/,
    /\bruntime cache\b/,
    /\bperformance\b/,
    /\bbenchmark\b/,
    /\bratchet\b/,
  ]);
  const multiPhase = matchAny(text, [
    /\bmulti[- ]?phase\b/,
    /\bdeep research\b/,
    /\bplan\b.*\bproceed\b/,
    /\bimplement(?:ation)?\b/,
    /\brefactor\b/,
    /\bmigration\b/,
    /\barchitecture\b/,
    /\bflywheel\b/,
    /\bagent\b/,
    /\beval\b/,
  ]);
  const nonTrivial = matchAny(text, [
    /\bfix\b/,
    /\bdebug\b/,
    /\badd\b/,
    /\bupdate\b/,
    /\bmodify\b/,
    /\btest\b/,
    /\breview\b/,
    /\bdesign\b/,
  ]);

  if (highRisk) {
    tier = 3;
    reasons.push('high-risk/global/performance/deployment/security keyword detected');
  } else if (multiPhase) {
    tier = 2;
    reasons.push('multi-phase, implementation, architecture, eval, or flywheel keyword detected');
  } else if (nonTrivial || task.trim().split(/\s+/).length > 12) {
    tier = 1;
    reasons.push('non-trivial change or analysis keyword detected');
  } else {
    reasons.push('short/simple task with no high-risk signal');
  }

  if (matchAny(text, [/\bperformance\b/, /\bbenchmark\b/, /\blatency\b/, /\bthroughput\b/, /\bmemory\b/, /\bbundle\b/, /\bratchet\b/])) {
    subskills.push('perf-ratchet');
  }
  if (matchAny(text, [/\bcorrectness\b/, /\bconformance\b/, /\brelease\b/, /\bapi\b/, /\bcontract\b/, /\bproof\b/, /\bverification\b/, /\bglobal\b/, /\bplugin\b/])) {
    subskills.push('conformance-gate');
  }
  if (matchAny(text, [/\bfuzz\b/, /\bmalformed\b/, /\badversarial\b/, /\bedge[- ]?case\b/, /\bparser\b/, /\bregression\b/])) {
    subskills.push('fuzz-regression');
  }
  if (fs.existsSync(path.join(root, '.beads')) || matchAny(text, [/\bbeads?\b/, /\bbv\b/, /\bbr\b/, /\btriage\b/])) {
    subskills.push('beads-triage');
  }
  if (matchAny(text, [/\bagent\b/, /\beval\b/, /\bgrader\b/, /\btrace\b/, /\btrajectory\b/, /\bflywheel\b/])) {
    subskills.push('eval-harness');
  }
  if (tier >= 1) {
    subskills.push('verification-loop');
  }

  const researchDepth = tier === 3
    ? 'high-risk'
    : (tier === 2 ? 'deep' : (tier === 1 ? 'standard' : 'light'));

  const stopAndAskThresholds = tier === 3
    ? [
      'destructive action requested or required',
      'production, security, secret, compliance, legal, medical, or financial ambiguity',
      'critical verification gate fails',
      'tool health contradicts the planned route',
      'strategic drift from the user objective',
    ]
    : [];

  return {
    type: 'classification',
    timestamp: nowIso(),
    task,
    root,
    tier,
    research_depth: researchDepth,
    persistent_artifacts_required: tier >= 2,
    subskills: uniq(subskills),
    reasons,
    stop_and_ask_thresholds: stopAndAskThresholds,
  };
}

function commandClassify(flags) {
  const root = resolveRoot(flags);
  return classifyTask(requireText(flags, 'task'), root);
}

function parseCheck(value) {
  if (typeof value !== 'string') {
    throw new Error('--check must be command|status|durationMs');
  }
  const parts = value.split('|');
  if (parts.length < 2 || parts.length > 3) {
    throw new Error('--check must be command|status|durationMs');
  }
  const [command, status, durationText] = parts;
  const check = {
    command: command.trim(),
    status: status.trim(),
  };
  if (durationText !== undefined && durationText.trim() !== '') {
    const durationMs = Number(durationText);
    if (!Number.isFinite(durationMs) || durationMs < 0) {
      throw new Error('--check durationMs must be a non-negative number');
    }
    check.duration_ms = durationMs;
  }
  return check;
}

function parseMetric(value) {
  if (typeof value !== 'string') {
    throw new Error('--metric must be name=value:direction:thresholdPct');
  }
  const [nameAndValue, direction = 'lower', thresholdText = '0'] = value.split(':');
  const equalsIndex = nameAndValue.indexOf('=');
  if (equalsIndex <= 0) {
    throw new Error('--metric must be name=value:direction:thresholdPct');
  }
  const name = nameAndValue.slice(0, equalsIndex).trim();
  const metricValue = Number(nameAndValue.slice(equalsIndex + 1));
  const thresholdPct = Number(thresholdText);
  if (!name) {
    throw new Error('--metric name is required');
  }
  if (!Number.isFinite(metricValue)) {
    throw new Error('--metric value must be numeric');
  }
  if (!VALID_DIRECTIONS.has(direction)) {
    throw new Error('--metric direction must be lower or higher');
  }
  if (!Number.isFinite(thresholdPct) || thresholdPct < 0) {
    throw new Error('--metric thresholdPct must be a non-negative number');
  }
  return {
    name,
    value: metricValue,
    direction,
    threshold_pct: thresholdPct,
  };
}

function compareMetric(previous, metric) {
  if (!previous || previous.value === 0) {
    return {
      metric: metric.name,
      status: 'baseline-created',
      previous: previous || null,
      current: metric,
      regression_pct: 0,
    };
  }

  const rawChangePct = ((metric.value - previous.value) / Math.abs(previous.value)) * 100;
  const regressionPct = metric.direction === 'lower' ? rawChangePct : -rawChangePct;
  const status = regressionPct > metric.threshold_pct ? 'fail' : 'pass';
  return {
    metric: metric.name,
    status,
    previous,
    current: metric,
    regression_pct: Number(regressionPct.toFixed(4)),
  };
}

function commandInit(flags) {
  const root = resolveRoot(flags);
  const paths = artifactPaths(root);
  const task = requireText(flags, 'task');
  const tier = parseTier(flag(flags, 'tier', null));
  ensureDir(paths.dir);

  if (!fs.existsSync(paths.masterPlan)) {
    const lines = [
      '# PhaseLoop_v2 Master Plan',
      '',
      `Created: ${nowIso()}`,
      `Task: ${task}`,
      `Tier: ${tier === null ? 'unclassified' : tier}`,
      '',
      '## Operating Pattern',
      '',
      'research -> baseline -> one focused lever -> verify -> reflect -> ratchet -> next-phase adjustment',
      '',
      '## Persistent Artifacts',
      '',
      '- `phase-ledger.jsonl`: per-phase baseline, checks, deltas, reflection, decision, and next adjustment.',
      '- `ratchets.json`: latest metric baselines and regression thresholds.',
      '- `improvements.jsonl`: queued self-improvement notes that require explicit approval before mutating global skills or prompts.',
      '- `session-health.jsonl`: disk, memory, load, and zombie-process snapshots for long-running work.',
      '',
      '## Phase Plan',
      '',
      '- P1: Define baseline and first focused lever.',
      '- P2: Verify, reflect, and update next adjustment from evidence.',
      '- P-polish: Optional optimization/de-slopify round after core acceptance criteria pass.',
      '',
    ];
    fs.writeFileSync(paths.masterPlan, `${lines.join('\n')}\n`, 'utf8');
  }

  const event = {
    type: 'init',
    timestamp: nowIso(),
    task,
    tier,
    root,
    artifacts: paths,
  };
  appendJsonl(paths.ledger, event);
  return event;
}

function commandRecord(flags) {
  const root = resolveRoot(flags);
  const paths = artifactPaths(root);
  const phaseId = requireText(flags, 'phase');
  const decision = requireText(flags, 'decision');
  if (!VALID_DECISIONS.has(decision)) {
    throw new Error('--decision must be continue, change-plan, or stop-and-ask');
  }

  const checks = flagList(flags, 'check').map(parseCheck);
  const metrics = flagList(flags, 'metric').map(parseMetric);
  const ratchets = readJson(paths.ratchets, { version: 1, metrics: {} });
  const ratchetDecisions = [];

  for (const metric of metrics) {
    const previous = ratchets.metrics[metric.name] || null;
    const ratchetDecision = compareMetric(previous, metric);
    ratchetDecisions.push(ratchetDecision);
    if (ratchetDecision.status !== 'fail') {
      ratchets.metrics[metric.name] = {
        value: metric.value,
        direction: metric.direction,
        threshold_pct: metric.threshold_pct,
        updated_at: nowIso(),
        phase_id: phaseId,
      };
    }
  }
  writeJson(paths.ratchets, ratchets);

  const entry = {
    type: 'phase',
    timestamp: nowIso(),
    phase_id: phaseId,
    objective: requireText(flags, 'objective'),
    baseline: requireText(flags, 'baseline'),
    research_delta: String(flag(flags, 'research-delta', 'not needed')),
    checks,
    delta: requireText(flags, 'delta'),
    reflection: requireText(flags, 'reflection'),
    decision,
    next_adjustment: requireText(flags, 'next-adjustment'),
    bead_id: flag(flags, 'bead', null),
    artifacts: flagList(flags, 'artifact'),
    ratchet_decisions: ratchetDecisions,
  };

  appendJsonl(paths.ledger, entry);
  return entry;
}

function commandTraceStep(flags) {
  const root = resolveRoot(flags);
  const paths = artifactPaths(root);
  const status = requireText(flags, 'status');
  if (!VALID_TRACE_STATUSES.has(status)) {
    throw new Error('--status must be pass, fail, blocked, or info');
  }

  const durationValue = flag(flags, 'duration-ms', null);
  const durationMs = durationValue === null ? null : Number(durationValue);
  if (durationValue !== null && (!Number.isFinite(durationMs) || durationMs < 0)) {
    throw new Error('--duration-ms must be a non-negative number');
  }

  const phaseId = requireText(flags, 'phase');
  const name = requireText(flags, 'name');
  const spanSeed = `${phaseId}:${name}:${nowIso()}`;
  const spanId = crypto.createHash('sha1').update(spanSeed).digest('hex').slice(0, 12);
  const entry = {
    type: 'trace-step',
    timestamp: nowIso(),
    phase_id: phaseId,
    span_id: spanId,
    parent_span_id: flag(flags, 'parent', null),
    kind: String(flag(flags, 'kind', 'work')),
    name,
    status,
    evidence: flagList(flags, 'evidence'),
    failure_category: flag(flags, 'failure-category', null),
    duration_ms: durationMs,
  };
  appendJsonl(paths.traceSpans, entry);
  appendJsonl(paths.ledger, {
    type: 'trace-step-ref',
    timestamp: entry.timestamp,
    phase_id: phaseId,
    span_id: spanId,
    status,
    name,
  });
  return entry;
}

function commandQueueImprovement(flags) {
  const root = resolveRoot(flags);
  const paths = artifactPaths(root);
  const entry = {
    type: 'queued-improvement',
    timestamp: nowIso(),
    note: requireText(flags, 'note'),
    source: String(flag(flags, 'source', 'phase-loop-reflection')),
    status: 'queued',
  };
  appendJsonl(paths.improvements, entry);
  return entry;
}

function readDiskHealth(root) {
  try {
    const output = execFileSync('df', ['-k', root], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] });
    const lines = output.trim().split('\n');
    const columns = lines[lines.length - 1].split(/\s+/);
    const totalKb = Number(columns[1]);
    const usedKb = Number(columns[2]);
    const availableKb = Number(columns[3]);
    const usePct = columns[4] || null;
    return {
      total_kb: Number.isFinite(totalKb) ? totalKb : null,
      used_kb: Number.isFinite(usedKb) ? usedKb : null,
      available_kb: Number.isFinite(availableKb) ? availableKb : null,
      use_pct: usePct,
    };
  } catch (_error) {
    return null;
  }
}

function countZombieProcesses() {
  try {
    const output = execFileSync('ps', ['-axo', 'stat'], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] });
    return output.split('\n').filter(line => line.trim().startsWith('Z')).length;
  } catch (_error) {
    return null;
  }
}

function commandHealth(flags) {
  const root = resolveRoot(flags);
  const paths = artifactPaths(root);
  const entry = {
    type: 'session-health',
    timestamp: nowIso(),
    root,
    disk: readDiskHealth(root),
    memory: {
      free_bytes: os.freemem(),
      total_bytes: os.totalmem(),
    },
    loadavg: os.loadavg(),
    zombie_processes: countZombieProcesses(),
  };
  appendJsonl(paths.health, entry);
  return entry;
}

function commandStatus(flags) {
  const root = resolveRoot(flags);
  const paths = artifactPaths(root);
  const ledger = readJsonl(paths.ledger);
  const phaseEntries = ledger.filter(entry => entry.type === 'phase');
  const improvements = readJsonl(paths.improvements);
  const health = readJsonl(paths.health);
  const traceSpans = readJsonl(paths.traceSpans);
  const ratchets = readJson(paths.ratchets, { version: 1, metrics: {} });
  const beadMap = readJson(paths.beadMap, { version: 1, mappings: {} });
  const audit = buildAudit(root, paths, phaseEntries, improvements, health, traceSpans, ratchets, beadMap);

  return {
    root,
    artifacts_dir: paths.dir,
    initialized: fs.existsSync(paths.masterPlan),
    phase_count: phaseEntries.length,
    last_phase: phaseEntries[phaseEntries.length - 1] || null,
    queued_improvement_count: improvements.filter(entry => entry.status === 'queued').length,
    ratchet_metric_count: Object.keys(ratchets.metrics || {}).length,
    bead_mapping_count: Object.keys(beadMap.mappings || {}).length,
    trace_step_count: traceSpans.length,
    audit_implemented_count: audit.implemented_count,
    audit_total_count: audit.total_count,
    last_health: health[health.length - 1] || null,
  };
}

function collectLedgerState(root) {
  const paths = artifactPaths(root);
  const ledger = readJsonl(paths.ledger);
  const phases = ledger.filter(entry => entry.type === 'phase');
  const improvements = readJsonl(paths.improvements);
  const health = readJsonl(paths.health);
  const traceSpans = readJsonl(paths.traceSpans);
  const ratchets = readJson(paths.ratchets, { version: 1, metrics: {} });
  const beadMap = readJson(paths.beadMap, { version: 1, mappings: {} });
  return {
    paths,
    ledger,
    phases,
    improvements,
    health,
    traceSpans,
    ratchets,
    beadMap,
    lastPhase: phases[phases.length - 1] || null,
    queuedImprovements: improvements.filter(entry => entry.status === 'queued'),
  };
}

function latestFailedRatchets(phases) {
  return phases.flatMap(phase => (
    Array.isArray(phase.ratchet_decisions)
      ? phase.ratchet_decisions
        .filter(decision => decision.status === 'fail')
        .map(decision => ({ phase_id: phase.phase_id, ...decision }))
      : []
  ));
}

function listFilesSafe(dirPath) {
  try {
    return fs.readdirSync(dirPath);
  } catch (_error) {
    return [];
  }
}

function readTextSafe(filePath) {
  try {
    return fs.readFileSync(filePath, 'utf8');
  } catch (_error) {
    return '';
  }
}

function feature(name, status, evidence, next) {
  return { name, status, evidence, next };
}

function buildAudit(root, paths, phases, improvements, health, traceSpans, ratchets, beadMap) {
  const skillPath = path.join(root, 'skills', 'agent-phase-ratchet', 'SKILL.md');
  const testPath = path.join(root, 'tests', 'scripts', 'phase-loop-ledger.test.js');
  const sourceText = readTextSafe(__filename);
  const skillText = readTextSafe(skillPath);
  const testText = readTextSafe(testPath);
  const evidencePacks = listFilesSafe(paths.evidencePacksDir).filter(file => file.endsWith('.json'));
  const metricCount = Object.keys((ratchets && ratchets.metrics) || {}).length;
  const failedRatchets = latestFailedRatchets(phases);
  const globalCodex = readTextSafe(path.join(os.homedir(), '.codex', 'AGENTS.md'));
  const windsurfRules = readTextSafe(path.join(os.homedir(), '.codeium', 'windsurf', 'memories', 'global_rules.md'));
  const geminiRules = readTextSafe(path.join(os.homedir(), '.gemini', 'GEMINI.md'));
  const hasGlobalRules = [globalCodex, windsurfRules, geminiRules]
    .filter(text => text.includes('PhaseLoop_v2') || text.includes('agent-phase-ratchet'))
    .length;
  const hasBeads = fs.existsSync(path.join(root, '.beads'));
  const beadMappingCount = Object.keys((beadMap && beadMap.mappings) || {}).length;

  const features = [
    feature(
      'cross_phase_compounding',
      phases.some(phase => phase.next_adjustment) && sourceText.includes('commandNext') ? 'implemented' : 'partial',
      `${phases.length} phase entries; next command present: ${sourceText.includes('commandNext')}`,
      phases.length === 0 ? 'Record at least one phase with --next-adjustment.' : 'Keep using next --json before each new phase.'
    ),
    feature(
      'global_ratchets',
      metricCount > 0 && sourceText.includes('compareMetric') ? 'implemented' : 'partial',
      `${metricCount} metric ratchets; import-bench present: ${sourceText.includes('commandImportBench')}`,
      metricCount === 0 ? 'Import or record at least one comparable metric.' : 'Add project-specific benchmark adapters only when native formats require them.'
    ),
    feature(
      'beads_integration',
      hasBeads ? (beadMappingCount > 0 ? 'implemented' : 'partial') : (sourceText.includes('commandMapBeads') ? 'implemented' : 'missing'),
      `.beads present: ${hasBeads}; mappings: ${beadMappingCount}; map-beads present: ${sourceText.includes('commandMapBeads')}`,
      hasBeads && beadMappingCount === 0 ? 'Map active phases to Beads IDs.' : 'Auto-discover br/bv candidates in a later hardening pass.'
    ),
    feature(
      'documentation_provenance',
      fs.existsSync(paths.masterPlan) && evidencePacks.length > 0 ? 'implemented' : 'partial',
      `master plan: ${fs.existsSync(paths.masterPlan)}; evidence packs: ${evidencePacks.length}`,
      evidencePacks.length === 0 ? 'Run pack --name <phase> after verification.' : 'Add signing only when a signing key/tool is configured.'
    ),
    feature(
      'ambition_polish_rounds',
      skillText.includes('P-polish') || readTextSafe(paths.masterPlan).includes('P-polish') ? 'implemented' : 'partial',
      `P-polish in skill/master plan: ${skillText.includes('P-polish') || readTextSafe(paths.masterPlan).includes('P-polish')}`,
      'Create domain-specific polish templates only after repeated friction is observed.'
    ),
    feature(
      'monitoring',
      health.length > 0 ? 'implemented' : 'partial',
      `${health.length} health snapshots`,
      health.length === 0 ? 'Run health at Tier 3 phase boundaries.' : 'Add heartbeat automation only when the runtime exposes it.'
    ),
    feature(
      'embedded_global_skill',
      fs.existsSync(skillPath) && hasGlobalRules >= 2 ? 'implemented' : 'partial',
      `skill exists: ${fs.existsSync(skillPath)}; global rule surfaces with PhaseLoop: ${hasGlobalRules}`,
      hasGlobalRules < 3 ? 'Verify all intended global runtime surfaces after install.' : 'Keep global rules compact and route to the skill.'
    ),
    feature(
      'automation_hooks',
      sourceText.includes('commandClassify') && sourceText.includes('commandAudit') ? 'implemented' : 'partial',
      `classify command: ${sourceText.includes('commandClassify')}; audit command: ${sourceText.includes('commandAudit')}`,
      'Do not claim runtime hooks until the target runtime exposes trusted hook execution.'
    ),
    feature(
      'human_oversight',
      sourceText.includes('stop_and_ask_thresholds') && skillText.includes('Stop and ask') ? 'implemented' : 'partial',
      `classification stop thresholds: ${sourceText.includes('stop_and_ask_thresholds')}; skill stop gate: ${skillText.includes('Stop and ask')}`,
      'Keep stop gates fail-closed for destructive, production, and security-sensitive work.'
    ),
    feature(
      'testing_loop',
      fs.existsSync(testPath) && ['classify', 'trace-step', 'audit', 'import-bench', 'map-beads', 'pack']
        .every(command => testText.includes(command)) ? 'implemented' : 'partial',
      `test file exists: ${fs.existsSync(testPath)}; tested advanced commands: ${['classify', 'trace-step', 'audit', 'import-bench', 'map-beads', 'pack'].filter(command => testText.includes(command)).join(', ')}`,
      'Run a real multi-phase project bead and add regression tests for observed friction.'
    ),
  ];

  const implementedCount = features.filter(item => item.status === 'implemented').length;
  return {
    type: 'flywheel-audit',
    timestamp: nowIso(),
    root,
    implemented_count: implementedCount,
    total_count: features.length,
    remaining_count: features.length - implementedCount,
    failed_ratchet_count: failedRatchets.length,
    queued_improvement_count: improvements.filter(entry => entry.status === 'queued').length,
    trace_step_count: traceSpans.length,
    features,
  };
}

function commandAudit(flags) {
  const root = resolveRoot(flags);
  const state = collectLedgerState(root);
  return buildAudit(
    root,
    state.paths,
    state.phases,
    state.improvements,
    state.health,
    state.traceSpans,
    state.ratchets,
    state.beadMap
  );
}

function commandNext(flags) {
  const root = resolveRoot(flags);
  const state = collectLedgerState(root);
  const failedRatchets = latestFailedRatchets(state.phases);
  const lastHealth = state.health[state.health.length - 1] || null;
  const lastDecision = state.lastPhase ? state.lastPhase.decision : 'continue';
  const recommendedDecision = failedRatchets.length > 0 || lastDecision === 'stop-and-ask'
    ? 'stop-and-ask'
    : (lastDecision === 'change-plan' ? 'change-plan' : 'continue');
  const nextObjective = state.lastPhase
    ? state.lastPhase.next_adjustment
    : 'Initialize the first focused phase with a measurable baseline.';

  const promptLines = [
    'Continue PhaseLoop_v2 from persisted evidence.',
    `Decision: ${recommendedDecision}`,
    `Next objective: ${nextObjective}`,
    '',
    'Use the prior ledger before editing:',
    `- Root: ${root}`,
    `- Last phase: ${state.lastPhase ? state.lastPhase.phase_id : 'none'}`,
    `- Queued improvements: ${state.queuedImprovements.length}`,
    `- Failed ratchets: ${failedRatchets.length}`,
    '',
    'Required next steps:',
    '1. Re-read `.phase-loop/phase-ledger.jsonl` and `.phase-loop/ratchets.json`.',
    '2. Address failed ratchets before claiming progress.',
    '3. Execute one focused lever only.',
    '4. Record the next phase with `phase-loop-ledger.js record`.',
  ];

  return {
    type: 'next-phase',
    timestamp: nowIso(),
    root,
    decision: recommendedDecision,
    next_objective: nextObjective,
    last_phase: state.lastPhase,
    failed_ratchets: failedRatchets,
    queued_improvements: state.queuedImprovements,
    last_health: lastHealth,
    prompt: promptLines.join('\n'),
  };
}

function defaultEvidenceFiles(paths) {
  return [
    paths.masterPlan,
    paths.ledger,
    paths.ratchets,
    paths.improvements,
    paths.health,
    paths.traceSpans,
    paths.beadMap,
  ];
}

function sanitizePackName(value) {
  const safe = String(value || '')
    .trim()
    .replace(/[^a-zA-Z0-9._-]+/g, '-')
    .replace(/^-+|-+$/g, '');
  if (!safe) {
    throw new Error('--name must contain at least one filename-safe character');
  }
  return safe;
}

function commandPack(flags) {
  const root = resolveRoot(flags);
  const paths = artifactPaths(root);
  const state = collectLedgerState(root);
  const name = sanitizePackName(requireText(flags, 'name'));
  const artifactRefs = state.phases.flatMap(phase => Array.isArray(phase.artifacts) ? phase.artifacts : []);
  const candidateFiles = [
    ...defaultEvidenceFiles(paths),
    ...artifactRefs.map(artifact => path.resolve(root, artifact)),
  ];
  const seen = new Set();
  const files = [];

  for (const candidateFile of candidateFiles) {
    const absolutePath = path.resolve(candidateFile);
    if (seen.has(absolutePath) || !isInsideRoot(root, absolutePath) || !fileExists(absolutePath)) {
      continue;
    }
    seen.add(absolutePath);
    files.push({
      path: path.relative(root, absolutePath),
      bytes: fs.statSync(absolutePath).size,
      sha256: sha256File(absolutePath),
    });
  }

  ensureDir(paths.evidencePacksDir);
  const packPath = path.join(paths.evidencePacksDir, `${name}.json`);
  const pack = {
    type: 'evidence-pack',
    version: 1,
    timestamp: nowIso(),
    root,
    phase_count: state.phases.length,
    latest_phase_id: state.lastPhase ? state.lastPhase.phase_id : null,
    failed_ratchets: latestFailedRatchets(state.phases),
    files,
  };
  writeJson(packPath, pack);

  return {
    ...pack,
    pack_path: packPath,
  };
}

function flattenNumericValues(value, prefix = '') {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return [{ name: prefix || 'value', value }];
  }

  if (Array.isArray(value)) {
    return value.flatMap((item, index) => flattenNumericValues(item, prefix ? `${prefix}.${index}` : String(index)));
  }

  if (value && typeof value === 'object') {
    return Object.entries(value).flatMap(([key, child]) => (
      flattenNumericValues(child, prefix ? `${prefix}.${key}` : key)
    ));
  }

  return [];
}

function readBenchmarkPayload(filePath) {
  const raw = fs.readFileSync(filePath, 'utf8').trim();
  if (!raw) {
    throw new Error('--file is empty');
  }

  try {
    return JSON.parse(raw);
  } catch (_error) {
    const entries = raw.split('\n')
      .map(line => line.trim())
      .filter(Boolean)
      .map(line => JSON.parse(line));
    return entries;
  }
}

function commandImportBench(flags) {
  const root = resolveRoot(flags);
  const paths = artifactPaths(root);
  const benchmarkPath = path.resolve(root, requireText(flags, 'file'));
  if (!isInsideRoot(root, benchmarkPath)) {
    throw new Error('--file must be inside --root');
  }
  if (!fileExists(benchmarkPath)) {
    throw new Error(`Benchmark file not found: ${benchmarkPath}`);
  }

  const metricPrefix = String(flag(flags, 'metric-prefix', 'bench')).trim() || 'bench';
  const thresholdPct = Number(flag(flags, 'threshold-pct', '0'));
  if (!Number.isFinite(thresholdPct) || thresholdPct < 0) {
    throw new Error('--threshold-pct must be a non-negative number');
  }

  const payload = readBenchmarkPayload(benchmarkPath);
  const metrics = flattenNumericValues(payload)
    .filter(metric => !metric.name.match(/(?:timestamp|time|date)$/i))
    .map(metric => ({
      name: `${metricPrefix}.${metric.name}`.replace(/[^a-zA-Z0-9_.-]+/g, '_'),
      value: metric.value,
      direction: 'lower',
      threshold_pct: thresholdPct,
    }));

  const ratchets = readJson(paths.ratchets, { version: 1, metrics: {} });
  const decisions = metrics.map(metric => {
    const previous = ratchets.metrics[metric.name] || null;
    const decision = compareMetric(previous, metric);
    if (decision.status !== 'fail') {
      ratchets.metrics[metric.name] = {
        value: metric.value,
        direction: metric.direction,
        threshold_pct: metric.threshold_pct,
        updated_at: nowIso(),
        phase_id: 'import-bench',
        source: path.relative(root, benchmarkPath),
      };
    }
    return decision;
  });
  writeJson(paths.ratchets, ratchets);

  const entry = {
    type: 'benchmark-import',
    timestamp: nowIso(),
    source: path.relative(root, benchmarkPath),
    metric_count: metrics.length,
    decisions,
  };
  appendJsonl(paths.ledger, entry);
  return entry;
}

function commandMapBeads(flags) {
  const root = resolveRoot(flags);
  const paths = artifactPaths(root);
  const state = collectLedgerState(root);
  const phaseId = flag(flags, 'phase', null);
  const beadId = flag(flags, 'bead', null);
  const beadsPresent = fs.existsSync(path.join(root, '.beads'));
  const beadMap = state.beadMap && typeof state.beadMap === 'object'
    ? state.beadMap
    : { version: 1, mappings: {} };
  beadMap.version = beadMap.version || 1;
  beadMap.mappings = beadMap.mappings || {};

  if ((phaseId && !beadId) || (!phaseId && beadId)) {
    throw new Error('--phase and --bead must be provided together');
  }

  if (phaseId && beadId) {
    beadMap.mappings[String(phaseId)] = {
      bead_id: String(beadId),
      updated_at: nowIso(),
    };
    writeJson(paths.beadMap, beadMap);
  }

  const unmappedPhases = state.phases
    .filter(phase => !phase.bead_id && !beadMap.mappings[phase.phase_id])
    .map(phase => phase.phase_id);

  const result = {
    type: 'beads-map',
    timestamp: nowIso(),
    root,
    beads_present: beadsPresent,
    tools: {
      br: commandExists('br'),
      bv: commandExists('bv'),
    },
    mappings: beadMap.mappings,
    unmapped_phases: unmappedPhases,
    recommendation: beadsPresent
      ? 'Use beads-triage and map active phase IDs to Beads IDs with --phase/--bead.'
      : 'No .beads found; use repo-native TODOs, issues, or the PhaseLoop master plan.',
  };
  appendJsonl(paths.ledger, result);
  return result;
}

function printResult(result, json) {
  if (json) {
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
    return;
  }

  if (result.type === 'init') {
    process.stdout.write(`Initialized PhaseLoop artifacts at ${result.artifacts.dir}\n`);
  } else if (result.type === 'classification') {
    process.stdout.write(`Tier ${result.tier} (${result.research_depth}); subskills: ${result.subskills.join(', ') || 'none'}\n`);
  } else if (result.type === 'phase') {
    process.stdout.write(`Recorded phase ${result.phase_id} with decision ${result.decision}\n`);
  } else if (result.type === 'trace-step') {
    process.stdout.write(`Recorded trace step ${result.span_id} for ${result.phase_id} with status ${result.status}\n`);
  } else if (result.type === 'queued-improvement') {
    process.stdout.write(`Queued improvement: ${result.note}\n`);
  } else if (result.type === 'session-health') {
    process.stdout.write(`Recorded session health for ${result.root}\n`);
  } else if (result.type === 'next-phase') {
    process.stdout.write(`${result.prompt}\n`);
  } else if (result.type === 'flywheel-audit') {
    process.stdout.write(`Flywheel audit: ${result.implemented_count}/${result.total_count} implemented; ${result.remaining_count} remaining\n`);
  } else if (result.type === 'evidence-pack') {
    process.stdout.write(`Wrote evidence pack: ${result.pack_path}\n`);
  } else if (result.type === 'benchmark-import') {
    process.stdout.write(`Imported ${result.metric_count} benchmark metrics from ${result.source}\n`);
  } else if (result.type === 'beads-map') {
    process.stdout.write(`${result.recommendation}\n`);
  } else {
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  }
}

function main() {
  const { command, flags } = parseArgv(process.argv.slice(2));
  const json = Boolean(flag(flags, 'json', false));

  if (!command || command === 'help' || flag(flags, 'help', false)) {
    process.stdout.write(`${usage()}\n`);
    return;
  }

  let result;
  if (command === 'init') {
    result = commandInit(flags);
  } else if (command === 'classify') {
    result = commandClassify(flags);
  } else if (command === 'record') {
    result = commandRecord(flags);
  } else if (command === 'trace-step') {
    result = commandTraceStep(flags);
  } else if (command === 'queue-improvement') {
    result = commandQueueImprovement(flags);
  } else if (command === 'health') {
    result = commandHealth(flags);
  } else if (command === 'next') {
    result = commandNext(flags);
  } else if (command === 'audit') {
    result = commandAudit(flags);
  } else if (command === 'pack') {
    result = commandPack(flags);
  } else if (command === 'import-bench') {
    result = commandImportBench(flags);
  } else if (command === 'map-beads') {
    result = commandMapBeads(flags);
  } else if (command === 'status') {
    result = commandStatus(flags);
  } else {
    throw new Error(`Unknown command: ${command}\n${usage()}`);
  }

  printResult(result, json);
}

try {
  main();
} catch (error) {
  process.stderr.write(`phase-loop-ledger: ${error.message}\n`);
  process.exit(1);
}
