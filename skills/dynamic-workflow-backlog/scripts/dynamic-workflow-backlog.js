#!/usr/bin/env node
'use strict';

const fs = require('fs');
const http = require('http');
const path = require('path');
const { spawnSync } = require('child_process');

const DEFAULT_MAX_CONCURRENCY = 4;
const HARD_MAX_CONCURRENCY = 16;
const HARD_MAX_AGENTS = 1000;
const DEFAULT_ADAPTER = 'tmux-worktree';
const DEFAULT_DASHBOARD_PORT = 8765;

function usage() {
  console.log([
    'Usage:',
    '  node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js automode --task <task> [--name <name>] [--dry-run]',
    '  node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js classify --task <task>',
    '  node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js plan --name <name> --task <task> [--force]',
    '  node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js init --name <name> --goal <goal> [--task "phase|role|title|prompt"]...',
    '  node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js add-task --run <run-dir> --task "phase|role|title|prompt"',
    '  node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js add-review --run <run-dir> --target <task-id> --role <role> --title <title> --prompt <prompt>',
    '  node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js add-reviews --run <run-dir> [--prompt <prompt>]',
    '  node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js shard --run <run-dir> --path <target>... --prompt-template <prompt>',
    '  node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js status --run <run-dir>',
    '  node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js next --run <run-dir>',
    '  node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js claim --run <run-dir> --task <task-id> --agent <agent-id>',
    '  node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js complete --run <run-dir> --task <task-id> --status pass|fail --summary <summary> [--evidence <evidence>]',
    '  node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js synthesize --run <run-dir>',
    '  node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js export-worktree-plan --run <run-dir> --out <plan.json>',
    '  node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js run-workers --run <run-dir> [--dry-run|--execute]',
    '  node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js collect-workers --run <run-dir> --wave <wave-id>',
    '  node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js pause --run <run-dir> [--task <task-id>]',
    '  node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js resume --run <run-dir> [--task <task-id>] [--approve-execution]',
    '  node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js retry --run <run-dir> --task <task-id>',
    '  node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js cancel --run <run-dir> [--task <task-id>] [--kill-active]',
    '  node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js watch --run <run-dir>',
    '  node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js dashboard --run <run-dir> [--port <port>]',
    '',
    'Task format:',
    '  "phase|role|title|prompt"',
    '',
    'The runner is intentionally file-backed and resumable. It only spawns Codex workers when run-workers --execute is explicit.'
  ].join('\n'));
}

function parseArgs(argv) {
  const [command, ...tokens] = argv.slice(2);
  const options = { _: [] };

  for (let index = 0; index < tokens.length; index += 1) {
    const token = tokens[index];
    if (!token.startsWith('--')) {
      options._.push(token);
      continue;
    }

    const key = token.slice(2);
    const next = tokens[index + 1];
    if (!next || next.startsWith('--')) {
      options[key] = true;
      continue;
    }

    if (Object.prototype.hasOwnProperty.call(options, key)) {
      if (!Array.isArray(options[key])) {
        options[key] = [options[key]];
      }
      options[key].push(next);
    } else {
      options[key] = next;
    }
    index += 1;
  }

  return { command, options };
}

function now() {
  return new Date().toISOString();
}

function slugify(value, fallback = 'workflow') {
  const slug = String(value || '')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
  return slug || fallback;
}

function defaultNameForTask(taskText) {
  return slugify(String(taskText || '').split(/\s+/).slice(0, 8).join('-'), 'dynamic-workflow');
}

function ensureLimit(value, fallback, hardMax, label) {
  const parsed = Number.parseInt(value || fallback, 10);
  if (!Number.isInteger(parsed) || parsed < 1) {
    throw new Error(`${label} must be a positive integer`);
  }
  if (parsed > hardMax) {
    throw new Error(`${label} must be <= ${hardMax}`);
  }
  return parsed;
}

function getRunDir(options, nameFallback) {
  if (options.run) {
    return path.resolve(options.run);
  }
  const root = path.resolve(options.root || path.join(process.cwd(), '.dynamic-workflows'));
  return path.join(root, slugify(options.name || nameFallback));
}

function pathsFor(runDir) {
  return {
    runDir,
    workflow: path.join(runDir, 'workflow.json'),
    workflowScript: path.join(runDir, 'workflow.js'),
    backlog: path.join(runDir, 'backlog.jsonl'),
    results: path.join(runDir, 'results.jsonl'),
    claims: path.join(runDir, 'claims.jsonl'),
    waves: path.join(runDir, 'waves'),
    readme: path.join(runDir, 'README.md')
  };
}

function readJson(filePath, fallback = null) {
  if (!fs.existsSync(filePath)) {
    return fallback;
  }
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function writeJson(filePath, value) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
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

function writeJsonl(filePath, entries) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, entries.map(entry => JSON.stringify(entry)).join('\n') + (entries.length ? '\n' : ''), 'utf8');
}

function appendJsonl(filePath, entry) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.appendFileSync(filePath, `${JSON.stringify(entry)}\n`, 'utf8');
}

function shellQuote(value) {
  return `'${String(value).replace(/'/g, `'\\''`)}'`;
}

function commandAvailable(command) {
  if (!/^[A-Za-z0-9._-]+$/.test(command)) {
    throw new Error(`Unsafe command name: ${command}`);
  }
  const result = spawnSync('/bin/sh', ['-lc', `command -v ${command}`], {
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'pipe']
  });
  return {
    available: result.status === 0 && Boolean(String(result.stdout || '').trim()),
    path: String(result.stdout || '').trim(),
    stderr: String(result.stderr || '').trim()
  };
}

function parsePositiveInteger(value, fallback, label) {
  const raw = value === undefined || value === true ? fallback : value;
  const parsed = Number.parseInt(raw, 10);
  if (!Number.isInteger(parsed) || parsed < 1) {
    throw new Error(`${label} must be a positive integer`);
  }
  return parsed;
}

function parseNonNegativeInteger(value, fallback, label) {
  const raw = value === undefined || value === true ? fallback : value;
  const parsed = Number.parseInt(raw, 10);
  if (!Number.isInteger(parsed) || parsed < 0) {
    throw new Error(`${label} must be a non-negative integer`);
  }
  return parsed;
}

function pluginRoot() {
  return path.resolve(__dirname, '..', '..', '..');
}

function waveId() {
  return `wave-${new Date().toISOString().replace(/[-:.TZ]/g, '').slice(0, 14)}`;
}

function readText(filePath) {
  if (!filePath || !fs.existsSync(filePath)) {
    return '';
  }
  return fs.readFileSync(filePath, 'utf8');
}

function parseWorkerStatusMarkdown(content) {
  const status = {
    state: null,
    updated: null,
    branch: null,
    worktree: null
  };

  for (const line of String(content || '').split('\n')) {
    const match = line.match(/^- ([A-Za-z ]+):\s*(.+)$/);
    if (!match) {
      continue;
    }
    const key = match[1].trim().toLowerCase().replace(/\s+/g, '');
    const value = match[2].trim().replace(/^`|`$/g, '');
    if (key === 'state') status.state = value;
    if (key === 'updated') status.updated = value;
    if (key === 'branch') status.branch = value;
    if (key === 'worktree') status.worktree = value;
  }

  return status;
}

function parseMarkdownSection(content, heading) {
  const lines = String(content || '').split('\n');
  const headingPatterns = new Set([`## ${heading}`, `**${heading}**`]);
  const start = lines.findIndex(line => headingPatterns.has(line.trim()));
  if (start === -1) {
    return '';
  }
  const collected = [];
  for (let index = start + 1; index < lines.length; index += 1) {
    const trimmed = lines[index].trim();
    if (trimmed.startsWith('## ') || (/^\*\*.+\*\*$/.test(trimmed) && !headingPatterns.has(trimmed))) {
      break;
    }
    collected.push(lines[index]);
  }
  return collected.join('\n').trim();
}

function summarizeHandoff(content, fallback) {
  const summary = parseMarkdownSection(content, 'Summary');
  if (summary) {
    return summary.split('\n').map(line => line.trim()).filter(Boolean).slice(0, 6).join(' ');
  }
  const nonEmpty = String(content || '').split('\n').map(line => line.trim()).filter(Boolean);
  return nonEmpty.slice(0, 4).join(' ') || fallback;
}

function parseTaskSpec(spec, index) {
  const parts = String(spec || '').split('|').map(part => part.trim());
  const [phase, role, title, ...promptParts] = parts;
  const prompt = promptParts.join('|').trim();

  if (!phase || !role || !title || !prompt) {
    throw new Error(`Task ${index + 1} must use "phase|role|title|prompt" format`);
  }

  return {
    phase,
    role,
    title,
    prompt
  };
}

function nextTaskId(tasks) {
  const max = tasks.reduce((highest, task) => {
    const match = /^T(\d+)$/.exec(task.id || '');
    return match ? Math.max(highest, Number.parseInt(match[1], 10)) : highest;
  }, 0);
  return `T${String(max + 1).padStart(3, '0')}`;
}

function normalizeTaskSpecs(value) {
  if (!value) {
    return [];
  }
  return Array.isArray(value) ? value : [value];
}

function createTask(spec, id, overrides = {}) {
  const timestamp = now();
  return {
    id,
    phase: spec.phase,
    role: spec.role,
    title: spec.title,
    prompt: spec.prompt,
    status: 'pending',
    dependsOn: overrides.dependsOn || [],
    reviewOf: overrides.reviewOf || null,
    assignedAgent: null,
    attempts: [],
    attemptCount: 0,
    lastAttempt: null,
    lastError: null,
    paused: false,
    cancelledAt: null,
    workerAdapter: null,
    waveId: null,
    durationMs: null,
    createdAt: timestamp,
    updatedAt: timestamp
  };
}

function unique(values) {
  return [...new Set(values)];
}

function classifyDynamicWorkflow(taskText) {
  const text = String(taskText || '').trim();
  if (!text) {
    throw new Error('classify requires --task');
  }

  const normalized = text.toLowerCase();
  const reasons = [];
  const cautions = [];
  let score = 0;

  const checks = [
    {
      points: 5,
      reason: 'explicit dynamic workflow or workflow backlog request',
      pattern: /\b(dynamic workflow|dynamic workflows|workflow backlog|ultracode|many-agent|multi-agent|agent swarm|subagent|subagents|spawn agents|spawn subagents|agent team|parallel agents|multi-spawning|multi-spawn)\b/
    },
    {
      points: 3,
      reason: 'large multi-surface task',
      pattern: /\b(entire|whole|all|full|complete|large-scale|large scale|repo-wide|codebase-wide|monorepo|many files|hundreds|thousands)\b/
    },
    {
      points: 2,
      reason: 'multi-phase or long-running execution',
      pattern: /\b(multi-phase|multi phase|phase|phases|migration|refactor|audit|deep research|systematic|end-to-end|e2e)\b/
    },
    {
      points: 2,
      reason: 'independent workstreams can be split safely',
      pattern: /\b(parallel|fan out|split|shard|workers|workstreams|subtasks|different modules|different packages)\b/
    },
    {
      points: 2,
      reason: 'adversarial verification or convergence is requested',
      pattern: /\b(adversarial|refute|challenge|cross-check|cross check|independent verification|converge|consensus|reviewer)\b/
    },
    {
      points: 2,
      reason: 'resumability or durable state is valuable',
      pattern: /\b(resume|resumable|interrupted|persistent|durable|checkpoint|backlog|queued|long-running|long running)\b/
    },
    {
      points: 1,
      reason: 'risk level benefits from explicit verification gates',
      pattern: /\b(security|auth|production|deploy|compliance|performance|benchmark|financial|medical|legal|destructive)\b/
    }
  ];

  for (const check of checks) {
    if (check.pattern.test(normalized)) {
      score += check.points;
      reasons.push(check.reason);
    }
  }

  const suppressors = [
    {
      points: 4,
      reason: 'small or local task should stay in normal PhaseLoop',
      pattern: /\b(trivial|one-liner|one liner|typo|single file|one file|quick fix|small fix|simple answer)\b/
    },
    {
      points: 2,
      reason: 'single answer or explanation does not need durable orchestration',
      pattern: /\b(explain only|just explain|no code|answer only)\b/
    }
  ];

  for (const suppressor of suppressors) {
    if (suppressor.pattern.test(normalized)) {
      score -= suppressor.points;
      cautions.push(suppressor.reason);
    }
  }

  if (/\b(delete|drop table|reset --hard|force push|production deploy|rotate secret|secret|credential)\b/.test(normalized)) {
    cautions.push('requires stop-and-ask before execution; use plan-only backlog until approved');
  }

  const launch = score >= 4 && !/\b(trivial|one-liner|one liner|typo)\b/.test(normalized);
  const tier = score >= 7 ? 3 : launch ? 2 : score >= 2 ? 1 : 0;
  const mode = launch
    ? cautions.some(caution => caution.includes('stop-and-ask')) ? 'plan-only' : 'backlog'
    : 'normal-phase-loop';
  const maxConcurrency = launch ? Math.min(HARD_MAX_CONCURRENCY, score >= 7 ? 8 : 4) : 1;
  const recommendedTasks = launch ? recommendTaskTemplate(normalized) : [];

  return {
    launch,
    mode,
    tier,
    score,
    primarySkill: launch ? 'dynamic-workflow-backlog' : 'agent-phase-ratchet',
    reasons: unique(reasons),
    cautions: unique(cautions),
    maxConcurrency,
    maxAgents: launch ? 64 : 1,
    recommendedTasks
  };
}

function decideAutoMode(taskText, options = {}) {
  const classification = classifyDynamicWorkflow(taskText);
  const force = Boolean(options.force);
  const dryRun = Boolean(options['dry-run']);
  const reasons = [...classification.reasons];
  const safeguards = [
    'never spawn workers automatically',
    'create durable backlog first',
    'export worker plans only after dry-run review',
    'use native Codex subagents only for read/review/research lanes unless a narrow write scope is explicit',
    'use tmux/worktree workers for write-heavy lanes that need isolated git state',
    'require synthesize ready=true before final answer'
  ];

  if (!classification.launch && !force) {
    return {
      action: 'skip',
      createBacklog: false,
      requiresApproval: false,
      reason: 'Classifier recommends normal PhaseLoop.',
      classification,
      safeguards
    };
  }

  if (classification.mode === 'plan-only') {
    return {
      action: 'plan-only',
      createBacklog: !dryRun,
      requiresApproval: true,
      reason: 'Safety-sensitive task: create a plan-only backlog and stop before execution/export.',
      classification,
      safeguards: [
        ...safeguards,
        'do not execute or export workers until user approval clears the stop gate'
      ]
    };
  }

  return {
    action: force && !classification.launch ? 'forced-backlog' : 'create-backlog',
    createBacklog: !dryRun,
    requiresApproval: false,
    reason: force && !classification.launch
      ? 'Forced by caller despite classifier recommending normal PhaseLoop.'
      : 'Predefined automode conditions indicate durable dynamic backlog is worthwhile.',
    classification: {
      ...classification,
      reasons
    },
    safeguards
  };
}

function recommendTaskTemplate(normalized) {
  if (/\b(bug|bugs|bug hunt|regression|flaky|failure|failures)\b/.test(normalized)) {
    return [
      'map|mapper|Map bug surface|List failing tests, suspicious modules, recent diffs, and known symptoms',
      'hunt|bug-hunter|Find candidate root causes|Inspect one independent area and report only evidence-backed defects',
      'verify|adversary|Disprove bug findings|Try to reproduce, falsify, or narrow every reported defect',
      'synthesize|reporter|Produce bug triage report|Return confirmed issues, false positives, fixes, and proof gaps'
    ];
  }

  if (/\b(migration|migrate|port|rewrite|framework swap|api deprecation|language port)\b/.test(normalized)) {
    return [
      'map|mapper|Map migration surface|Identify affected APIs, files, compatibility constraints, and test gates',
      'plan|planner|Shard migration work|Group independent migration slices by ownership and risk',
      'execute|migrator|Migrate one slice|Apply one bounded migration slice with local proof',
      'verify|adversary|Challenge migration slice|Find behavior changes, missed files, or invalid assumptions',
      'synthesize|reporter|Produce migration convergence report|Summarize completed slices, blockers, and remaining risks'
    ];
  }

  if (/\b(design|ui|dashboard|frontend|browser|visual)\b/.test(normalized)) {
    return [
      'map|mapper|Map UI surface|Identify routes, components, tokens, and current runtime proof',
      'design|designer|Propose visual direction|Define the design thesis and reusable component changes',
      'verify|browser-reviewer|Verify runtime UI|Check browser rendering, console errors, responsiveness, and proof artifacts',
      'verify|adversary|Challenge design claims|Find regressions, accessibility risks, or unsupported visual claims'
    ];
  }

  if (/\b(security|auth|permission|secret|compliance)\b/.test(normalized)) {
    return [
      'map|mapper|Map security surface|List routes, policies, secrets boundaries, and trust assumptions',
      'audit|auditor|Find security gaps|Inspect mapped surfaces for missing controls or risky behavior',
      'verify|adversary|Refute security findings|Try to disprove each claimed gap with source evidence',
      'synthesize|reporter|Produce risk-ranked report|Separate proven, unverified, and false-positive findings'
    ];
  }

  if (/\b(performance|benchmark|latency|throughput|memory|bundle)\b/.test(normalized)) {
    return [
      'map|mapper|Map performance surface|Identify hot paths, benchmarks, and current baselines',
      'measure|benchmark|Collect baseline evidence|Run or define comparable benchmark measurements',
      'verify|adversary|Challenge performance claims|Check for invalid comparisons or hidden regressions',
      'synthesize|reporter|Produce ratchet report|Summarize before/after metrics and next levers'
    ];
  }

  return [
    'map|mapper|Map task surface|Identify files, systems, risks, and proof requirements',
    'execute|implementer|Execute one workstream|Handle one independent slice with narrow ownership',
    'verify|adversary|Challenge workstream evidence|Try to refute claims and find missing proof',
    'synthesize|reporter|Converge final answer|Merge evidence, unresolved risks, and next actions'
  ];
}

function loadRun(runDir) {
  const runPaths = pathsFor(path.resolve(runDir));
  const workflow = readJson(runPaths.workflow);
  if (!workflow) {
    throw new Error(`No workflow found at ${runPaths.workflow}`);
  }
  return {
    paths: runPaths,
    workflow,
    tasks: readJsonl(runPaths.backlog),
    results: readJsonl(runPaths.results),
    claims: readJsonl(runPaths.claims)
  };
}

function listWaveMetadata(run) {
  if (!fs.existsSync(run.paths.waves)) {
    return [];
  }

  return fs.readdirSync(run.paths.waves, { withFileTypes: true })
    .filter(entry => entry.isDirectory())
    .map(entry => path.join(run.paths.waves, entry.name, 'wave.json'))
    .filter(filePath => fs.existsSync(filePath))
    .map(filePath => readJson(filePath))
    .filter(Boolean)
    .sort((left, right) => String(left.createdAt || '').localeCompare(String(right.createdAt || '')));
}

function saveWorkflow(run) {
  run.workflow.updatedAt = now();
  writeJson(run.paths.workflow, run.workflow);
}

function saveTasks(run) {
  writeJsonl(run.paths.backlog, run.tasks);
}

function estimateTokenRisk(taskCount, maxConcurrency) {
  const estimatedAgentRuns = Math.max(1, taskCount);
  const estimatedReviewRuns = Math.ceil(estimatedAgentRuns / 2);
  const estimatedTotalRuns = estimatedAgentRuns + estimatedReviewRuns;
  const risk = estimatedTotalRuns >= 50 || maxConcurrency >= 12
    ? 'high'
    : estimatedTotalRuns >= 12 || maxConcurrency >= 8
      ? 'medium'
      : 'low';

  return {
    risk,
    estimatedAgentRuns,
    estimatedReviewRuns,
    estimatedTotalRuns,
    warning: risk === 'low'
      ? 'Scoped run; still verify before exporting worker plans.'
      : 'Dynamic workflows can consume substantially more tokens than a normal session; start scoped and confirm before execution.'
  };
}

function renderWorkflowScript(runPaths) {
  return [
    '#!/usr/bin/env node',
    "'use strict';",
    '',
    "const { spawnSync } = require('child_process');",
    '',
    `const runner = ${JSON.stringify(__filename)};`,
    "const command = process.argv[2] || 'status';",
    "const args = process.argv.slice(3);",
    "const result = spawnSync(process.execPath, [runner, command, '--run', __dirname, ...args], {",
    "  stdio: 'inherit'",
    '});',
    'process.exit(result.status || 0);'
  ].join('\n');
}

function writeWorkflowScript(runPaths) {
  fs.writeFileSync(runPaths.workflowScript, `${renderWorkflowScript(runPaths)}\n`, 'utf8');
  fs.chmodSync(runPaths.workflowScript, 0o755);
}

function renderReadme(runPaths, workflow) {
  return [
    `# Dynamic Workflow Backlog: ${workflow.name}`,
    '',
    `Goal: ${workflow.goal}`,
    '',
    '## Commands',
    '',
    `- Status: \`node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js status --run ${runPaths.runDir}\``,
    `- Next: \`node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js next --run ${runPaths.runDir}\``,
    `- Preview workers: \`node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js run-workers --run ${runPaths.runDir} --dry-run\``,
    `- Execute workers: \`node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js run-workers --run ${runPaths.runDir} --execute\``,
    `- Dashboard: \`node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js dashboard --run ${runPaths.runDir}\``,
    `- Export worktree plan: \`node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js export-worktree-plan --run ${runPaths.runDir} --out .orchestration/${workflow.name}.json\``,
    '',
    '## Files',
    '',
    '- `workflow.json`: run metadata and safety limits',
    '- `workflow.js`: run-specific executable wrapper for status, next, synthesize, and export commands',
    '- `backlog.jsonl`: task state',
    '- `results.jsonl`: completion evidence',
    '- `claims.jsonl`: claim and review evidence',
    '- `waves/`: optional worker wave plans, status files, and handoffs'
  ].join('\n');
}

function summarize(run) {
  const counts = run.tasks.reduce((accumulator, task) => {
    accumulator[task.status] = (accumulator[task.status] || 0) + 1;
    return accumulator;
  }, {});
  const running = run.tasks.filter(task => task.status === 'running').length;
  const runnable = runnableTasks(run).slice(0, run.workflow.maxConcurrency - running);
  const waves = listWaveMetadata(run);

  return {
    name: run.workflow.name,
    goal: run.workflow.goal,
    runDir: run.paths.runDir,
    mode: run.workflow.mode || 'manual',
    paused: Boolean(run.workflow.paused),
    cancelledAt: run.workflow.cancelledAt || null,
    executionApproved: Boolean(run.workflow.executionApproved),
    maxConcurrency: run.workflow.maxConcurrency,
    maxAgents: run.workflow.maxAgents,
    tokenWarning: run.workflow.tokenWarning || estimateTokenRisk(run.tasks.length, run.workflow.maxConcurrency),
    synthesis: synthesisState(run),
    counts,
    running,
    runnable: runnable.map(task => ({
      id: task.id,
      phase: task.phase,
      role: task.role,
      title: task.title,
      prompt: task.prompt
    })),
    waves: waves.map(wave => ({
      waveId: wave.waveId,
      adapter: wave.adapter,
      status: wave.status || 'planned',
      createdAt: wave.createdAt,
      taskCount: Array.isArray(wave.tasks) ? wave.tasks.length : 0,
      planPath: wave.planPath || null,
      coordinationDir: wave.coordinationDir || null
    })),
    updatedAt: run.workflow.updatedAt
  };
}

function synthesisState(run) {
  const unfinished = run.tasks.filter(task => ['pending', 'running'].includes(task.status));
  const failed = run.tasks.filter(task => task.status === 'fail');
  const completed = run.tasks.filter(task => task.status === 'pass');
  const reviewTasks = run.tasks.filter(task => task.reviewOf);
  const passedReviews = reviewTasks.filter(task => task.status === 'pass');
  const reviewedTargets = new Set(reviewTasks.filter(task => task.status === 'pass').map(task => task.reviewOf));
  const completedNonReview = completed.filter(task => !task.reviewOf && task.phase !== 'synthesize');
  const unreviewed = completedNonReview.filter(task => !reviewedTargets.has(task.id));
  const blockers = [];

  if (unfinished.length > 0) {
    blockers.push(`${unfinished.length} task(s) still pending or running`);
  }
  if (failed.length > 0) {
    blockers.push(`${failed.length} task(s) failed`);
  }
  if (completedNonReview.length > 0 && passedReviews.length === 0) {
    blockers.push('no passed adversarial review tasks');
  }
  if (unreviewed.length > 0) {
    blockers.push(`${unreviewed.length} completed non-review task(s) lack passed adversarial review`);
  }

  return {
    ready: blockers.length === 0 && completed.length > 0,
    blockers,
    completed: completed.length,
    failed: failed.length,
    pendingOrRunning: unfinished.length,
    reviewTasks: reviewTasks.length,
    passedReviews: passedReviews.length,
    unreviewedCompletedTasks: unreviewed.map(task => task.id)
  };
}

function taskById(tasks, taskId) {
  const task = tasks.find(entry => entry.id === taskId);
  if (!task) {
    throw new Error(`Unknown task id: ${taskId}`);
  }
  return task;
}

function dependenciesComplete(tasks, task) {
  return (task.dependsOn || []).every(dependencyId => {
    const dependency = tasks.find(entry => entry.id === dependencyId);
    return dependency && dependency.status === 'pass';
  });
}

function runnableTasks(run) {
  if (run.workflow.paused || run.workflow.cancelledAt) {
    return [];
  }
  return run.tasks.filter(task => (
    task.status === 'pending' &&
    !task.paused &&
    !task.cancelledAt &&
    dependenciesComplete(run.tasks, task)
  ));
}

function createPlannedRun(options, context = {}) {
  const task = context.task || options.task || options.goal;
  const classification = context.classification || classifyDynamicWorkflow(task);
  const name = options.name || defaultNameForTask(task);
  const runOptions = { ...options, name };
  const runDir = getRunDir(runOptions, name);
  const runPaths = pathsFor(runDir);
  const taskSpecs = classification.recommendedTasks.map(parseTaskSpec);
  const maxConcurrency = ensureLimit(
    options['max-concurrency'] || classification.maxConcurrency,
    classification.maxConcurrency,
    HARD_MAX_CONCURRENCY,
    'max-concurrency'
  );
  const maxAgents = ensureLimit(
    options['max-agents'] || classification.maxAgents,
    classification.maxAgents,
    HARD_MAX_AGENTS,
    'max-agents'
  );
  const workflow = {
    schemaVersion: 1,
    name: slugify(name),
    goal: options.goal || task,
    sourceTask: task,
    repoRoot: path.resolve(options.repo || process.cwd()),
    mode: context.mode || classification.mode,
    classification,
    automode: context.automode || null,
    maxConcurrency,
    maxAgents,
    tokenWarning: estimateTokenRisk(taskSpecs.length, maxConcurrency),
    createdAt: now(),
    updatedAt: now()
  };
  const tasks = taskSpecs.map((spec, index) => createTask(spec, `T${String(index + 1).padStart(3, '0')}`));

  fs.mkdirSync(runDir, { recursive: true });
  writeJson(runPaths.workflow, workflow);
  writeJsonl(runPaths.backlog, tasks);
  writeJsonl(runPaths.results, []);
  writeJsonl(runPaths.claims, []);
  writeWorkflowScript(runPaths);
  fs.writeFileSync(runPaths.readme, `${renderReadme(runPaths, workflow)}\n`, 'utf8');

  return {
    created: true,
    classification,
    ...summarize(loadRun(runDir))
  };
}

function cmdInit(options) {
  if (!options.name) {
    throw new Error('init requires --name');
  }
  if (!options.goal) {
    throw new Error('init requires --goal');
  }

  const runDir = getRunDir(options, options.name);
  const runPaths = pathsFor(runDir);
  const maxConcurrency = ensureLimit(options['max-concurrency'], DEFAULT_MAX_CONCURRENCY, HARD_MAX_CONCURRENCY, 'max-concurrency');
  const maxAgents = ensureLimit(options['max-agents'], 64, HARD_MAX_AGENTS, 'max-agents');
  const taskSpecs = normalizeTaskSpecs(options.task).map(parseTaskSpec);
  const workflow = {
    schemaVersion: 1,
    name: slugify(options.name),
    goal: options.goal,
    repoRoot: path.resolve(options.repo || process.cwd()),
    mode: options.mode || 'manual',
    maxConcurrency,
    maxAgents,
    tokenWarning: estimateTokenRisk(taskSpecs.length, maxConcurrency),
    createdAt: now(),
    updatedAt: now()
  };
  const tasks = taskSpecs.map((spec, index) => createTask(spec, `T${String(index + 1).padStart(3, '0')}`));

  if (tasks.length > maxAgents) {
    throw new Error(`Task count exceeds max-agents (${maxAgents})`);
  }

  fs.mkdirSync(runDir, { recursive: true });
  writeJson(runPaths.workflow, workflow);
  writeJsonl(runPaths.backlog, tasks);
  writeJsonl(runPaths.results, []);
  writeJsonl(runPaths.claims, []);
  writeWorkflowScript(runPaths);
  fs.writeFileSync(runPaths.readme, `${renderReadme(runPaths, workflow)}\n`, 'utf8');

  console.log(JSON.stringify(summarize(loadRun(runDir)), null, 2));
}

function cmdClassify(options) {
  const result = classifyDynamicWorkflow(options.task);
  console.log(JSON.stringify(result, null, 2));
}

function cmdAutomode(options) {
  const task = options.task || options.goal;
  if (!task) {
    throw new Error('automode requires --task or --goal');
  }

  const decision = decideAutoMode(task, options);
  if (!decision.createBacklog) {
    console.log(JSON.stringify({
      created: false,
      dryRun: Boolean(options['dry-run']),
      decision
    }, null, 2));
    return;
  }

  const result = createPlannedRun(options, {
    task,
    classification: decision.classification,
    mode: decision.action === 'plan-only' ? 'plan-only' : 'backlog',
    automode: decision
  });

  console.log(JSON.stringify({
    decision,
    ...result
  }, null, 2));
}

function cmdPlan(options) {
  const task = options.task || options.goal;
  if (!options.name) {
    throw new Error('plan requires --name');
  }
  if (!task) {
    throw new Error('plan requires --task or --goal');
  }

  const classification = classifyDynamicWorkflow(task);
  if (!classification.launch && !options.force) {
    console.log(JSON.stringify({
      created: false,
      reason: 'Classifier recommends normal PhaseLoop; pass --force to create a backlog anyway.',
      classification
    }, null, 2));
    return;
  }

  console.log(JSON.stringify(createPlannedRun(options, { task, classification }), null, 2));
}

function cmdAddTask(options) {
  if (!options.run || !options.task) {
    throw new Error('add-task requires --run and --task');
  }

  const run = loadRun(options.run);
  if (run.tasks.length >= run.workflow.maxAgents) {
    throw new Error(`Cannot add task: max-agents reached (${run.workflow.maxAgents})`);
  }

  const spec = parseTaskSpec(options.task, run.tasks.length);
  const task = createTask(spec, nextTaskId(run.tasks), {
    dependsOn: options.depends ? String(options.depends).split(',').map(entry => entry.trim()).filter(Boolean) : []
  });
  run.tasks.push(task);
  saveTasks(run);
  saveWorkflow(run);
  console.log(JSON.stringify(task, null, 2));
}

function cmdAddReview(options) {
  if (!options.run || !options.target || !options.role || !options.title || !options.prompt) {
    throw new Error('add-review requires --run, --target, --role, --title, and --prompt');
  }

  const run = loadRun(options.run);
  taskById(run.tasks, options.target);
  if (run.tasks.length >= run.workflow.maxAgents) {
    throw new Error(`Cannot add review: max-agents reached (${run.workflow.maxAgents})`);
  }

  const task = createTask({
    phase: options.phase || 'verify',
    role: options.role,
    title: options.title,
    prompt: options.prompt
  }, nextTaskId(run.tasks), {
    dependsOn: [options.target],
    reviewOf: options.target
  });
  run.tasks.push(task);
  saveTasks(run);
  saveWorkflow(run);
  appendJsonl(run.paths.claims, {
    type: 'review-task-added',
    taskId: task.id,
    reviewOf: options.target,
    createdAt: now()
  });
  console.log(JSON.stringify(task, null, 2));
}

function cmdAddReviews(options) {
  if (!options.run) {
    throw new Error('add-reviews requires --run');
  }

  const run = loadRun(options.run);
  const existingReviewTargets = new Set(run.tasks.filter(task => task.reviewOf).map(task => task.reviewOf));
  const targets = run.tasks.filter(task => (
    task.status === 'pass' &&
    !task.reviewOf &&
    task.phase !== 'verify' &&
    task.phase !== 'synthesize' &&
    !existingReviewTargets.has(task.id)
  ));
  const prompt = options.prompt || 'Try to refute this completed task. Identify unsupported claims, missing evidence, regressions, and false positives.';
  const created = [];

  for (const target of targets) {
    if (run.tasks.length >= run.workflow.maxAgents) {
      break;
    }

    const task = createTask({
      phase: options.phase || 'verify',
      role: options.role || 'adversary',
      title: `${options['title-prefix'] || 'Challenge'} ${target.id}: ${target.title}`,
      prompt: `${prompt}\n\nTarget task: ${target.id}\nTarget summary: ${target.summary || 'No summary recorded'}\nTarget evidence: ${target.evidence || 'No evidence recorded'}`
    }, nextTaskId(run.tasks), {
      dependsOn: [target.id],
      reviewOf: target.id
    });
    run.tasks.push(task);
    created.push(task);
    existingReviewTargets.add(target.id);
  }

  saveTasks(run);
  saveWorkflow(run);
  appendJsonl(run.paths.claims, {
    type: 'bulk-review-tasks-added',
    taskIds: created.map(task => task.id),
    createdAt: now()
  });
  console.log(JSON.stringify({
    created: created.length,
    tasks: created
  }, null, 2));
}

function normalizeTargets(options) {
  const values = [];
  for (const key of ['path', 'paths', 'target', 'targets']) {
    const option = options[key];
    if (!option) {
      continue;
    }
    const entries = Array.isArray(option) ? option : [option];
    for (const entry of entries) {
      values.push(...String(entry).split(',').map(value => value.trim()).filter(Boolean));
    }
  }
  return unique(values);
}

function cmdShard(options) {
  if (!options.run) {
    throw new Error('shard requires --run');
  }

  const targets = normalizeTargets(options);
  if (targets.length === 0) {
    throw new Error('shard requires at least one --path, --paths, --target, or --targets value');
  }
  if (!options['prompt-template']) {
    throw new Error('shard requires --prompt-template with optional {target} placeholder');
  }

  const run = loadRun(options.run);
  const created = [];

  for (const target of targets) {
    if (run.tasks.length >= run.workflow.maxAgents) {
      break;
    }

    const spec = {
      phase: options.phase || 'execute',
      role: options.role || 'worker',
      title: `${options['title-prefix'] || 'Workstream'}: ${target}`,
      prompt: String(options['prompt-template']).replace(/\{target\}/g, target)
    };
    const task = createTask(spec, nextTaskId(run.tasks));
    task.target = target;
    run.tasks.push(task);
    created.push(task);
  }

  run.workflow.tokenWarning = estimateTokenRisk(run.tasks.length, run.workflow.maxConcurrency);
  saveTasks(run);
  saveWorkflow(run);
  console.log(JSON.stringify({
    created: created.length,
    skippedBecauseMaxAgents: targets.length - created.length,
    tokenWarning: run.workflow.tokenWarning,
    tasks: created
  }, null, 2));
}

function cmdStatus(options) {
  if (!options.run) {
    throw new Error('status requires --run');
  }
  console.log(JSON.stringify(summarize(loadRun(options.run)), null, 2));
}

function cmdNext(options) {
  if (!options.run) {
    throw new Error('next requires --run');
  }
  const run = loadRun(options.run);
  const summary = summarize(run);
  console.log(JSON.stringify({
    ...summary,
    prompt: [
      `Dynamic workflow: ${run.workflow.name}`,
      `Goal: ${run.workflow.goal}`,
      'Take one runnable task. Claim it first, complete it with evidence, then add adversarial review tasks before final synthesis.'
    ].join('\n')
  }, null, 2));
}

function cmdClaim(options) {
  if (!options.run || !options.task || !options.agent) {
    throw new Error('claim requires --run, --task, and --agent');
  }

  const run = loadRun(options.run);
  const running = run.tasks.filter(task => task.status === 'running').length;
  if (running >= run.workflow.maxConcurrency) {
    throw new Error(`Cannot claim task: max-concurrency reached (${run.workflow.maxConcurrency})`);
  }

  const task = taskById(run.tasks, options.task);
  if (task.status !== 'pending') {
    throw new Error(`Cannot claim ${task.id}: status is ${task.status}`);
  }
  if (!dependenciesComplete(run.tasks, task)) {
    throw new Error(`Cannot claim ${task.id}: dependencies are not complete`);
  }

  task.status = 'running';
  task.assignedAgent = options.agent;
  task.updatedAt = now();
  saveTasks(run);
  saveWorkflow(run);
  appendJsonl(run.paths.results, {
    type: 'claim',
    taskId: task.id,
    agent: options.agent,
    createdAt: now()
  });
  console.log(JSON.stringify(task, null, 2));
}

function cmdComplete(options) {
  if (!options.run || !options.task || !options.status || !options.summary) {
    throw new Error('complete requires --run, --task, --status, and --summary');
  }
  if (!['pass', 'fail'].includes(options.status)) {
    throw new Error('--status must be pass or fail');
  }

  const run = loadRun(options.run);
  const task = taskById(run.tasks, options.task);
  if (!['pending', 'running'].includes(task.status)) {
    throw new Error(`Cannot complete ${task.id}: status is ${task.status}`);
  }

  task.status = options.status;
  task.summary = options.summary;
  task.evidence = options.evidence || '';
  task.updatedAt = now();
  saveTasks(run);
  saveWorkflow(run);
  appendJsonl(run.paths.results, {
    type: 'completion',
    taskId: task.id,
    status: options.status,
    agent: task.assignedAgent || null,
    summary: options.summary,
    evidence: options.evidence || '',
    createdAt: now()
  });
  if (options.evidence) {
    appendJsonl(run.paths.claims, {
      type: 'evidence',
      taskId: task.id,
      evidence: options.evidence,
      createdAt: now()
    });
  }
  console.log(JSON.stringify(task, null, 2));
}

function cmdSynthesize(options) {
  if (!options.run) {
    throw new Error('synthesize requires --run');
  }

  const run = loadRun(options.run);
  const state = synthesisState(run);
  const completed = run.tasks.filter(task => task.status === 'pass');
  const failed = run.tasks.filter(task => task.status === 'fail');
  const reviews = run.tasks.filter(task => task.reviewOf);
  const report = {
    workflow: run.workflow.name,
    goal: run.workflow.goal,
    ready: state.ready,
    blockers: state.blockers,
    summary: {
      completed: completed.length,
      failed: failed.length,
      reviews: reviews.length,
      passedReviews: state.passedReviews
    },
    completedTasks: completed.map(task => ({
      id: task.id,
      phase: task.phase,
      role: task.role,
      title: task.title,
      summary: task.summary || '',
      evidence: task.evidence || '',
      reviewOf: task.reviewOf || null
    })),
    failedTasks: failed.map(task => ({
      id: task.id,
      phase: task.phase,
      role: task.role,
      title: task.title,
      summary: task.summary || '',
      evidence: task.evidence || ''
    })),
    nextAction: state.ready
      ? 'Return final answer from completed and reviewed evidence.'
      : 'Do not return final answer yet; resolve blockers or add/pass adversarial review tasks.'
  };

  appendJsonl(run.paths.claims, {
    type: 'synthesis-check',
    ready: state.ready,
    blockers: state.blockers,
    createdAt: now()
  });
  console.log(JSON.stringify(report, null, 2));
}

function cmdExportWorktreePlan(options) {
  if (!options.run || !options.out) {
    throw new Error('export-worktree-plan requires --run and --out');
  }

  const run = loadRun(options.run);
  const tasks = runnableTasks(run);
  if (tasks.length === 0) {
    throw new Error('No runnable tasks to export');
  }

  const selected = tasks.slice(0, run.workflow.maxConcurrency);
  const launcher = options['launcher-command'] ||
    'bash scripts/orchestrate-codex-worker.sh {task_file_sh} {handoff_file_sh} {status_file_sh}';
  const plan = {
    sessionName: run.workflow.name,
    repoRoot: run.workflow.repoRoot,
    coordinationRoot: path.join(run.workflow.repoRoot, '.orchestration'),
    launcherCommand: launcher,
    workers: selected.map(task => ({
      name: `${task.id}-${slugify(task.role)}`,
      task: [
        `Dynamic workflow run: ${run.workflow.name}`,
        `Goal: ${run.workflow.goal}`,
        `Task: ${task.id}`,
        `Phase: ${task.phase}`,
        `Role: ${task.role}`,
        `Title: ${task.title}`,
        '',
        task.prompt,
        '',
        'Return evidence only. Do not claim completion without command, file, or runtime proof.'
      ].join('\n')
    }))
  };

  const outPath = path.resolve(options.out);
  writeJson(outPath, plan);
  console.log(JSON.stringify({
    out: outPath,
    workers: selected.length,
    dryRunCommand: `node scripts/orchestrate-worktrees.js ${outPath}`
  }, null, 2));
}

function buildWorkerEnvPrefix(options) {
  const env = {};
  if (options.model) env.ECC_CODEX_MODEL = options.model;
  if (options.profile) env.ECC_CODEX_PROFILE = options.profile;
  if (options.sandbox) env.ECC_CODEX_SANDBOX = options.sandbox;
  if (options['timeout-seconds']) env.ECC_CODEX_TIMEOUT_SECONDS = options['timeout-seconds'];
  if (options['codex-extra-args']) env.ECC_CODEX_EXTRA_ARGS = options['codex-extra-args'];

  return Object.entries(env)
    .map(([key, value]) => `${key}=${shellQuote(value)}`)
    .join(' ');
}

function codexLaunchLadder() {
  return [
    'classify with automode --dry-run',
    'create or reuse the durable backlog',
    'preview runnable work with run-workers --dry-run',
    'preflight codex, git, tmux, worker script, repo root, and writable run directory before execute',
    'choose native Codex subagents for read/review/research lanes',
    'choose tmux/worktree workers for implementation, build, test, or write-heavy lanes',
    'execute only after explicit user or goal request for parallel workers',
    'collect worker evidence and synthesize only after verification'
  ];
}

function codexExecutionGuidance() {
  return {
    nativeSubagents: 'Use for bounded read-only mapping, review, refutation, or research. The live Codex tool surface must expose spawn_agent, and the user or goal must explicitly request delegation.',
    tmuxWorktree: 'Use for implementation, build/test execution, or any lane that benefits from isolated git state.',
    forbidden: 'Do not silently auto-spawn workers from automode, and do not ask workers to create, resume, update, or complete Codex goals.'
  };
}

function buildWorkerTaskPrompt(run, task) {
  return [
    `Dynamic workflow run: ${run.workflow.name}`,
    `Goal: ${run.workflow.goal}`,
    `Task: ${task.id}`,
    `Phase: ${task.phase}`,
    `Role: ${task.role}`,
    `Title: ${task.title}`,
    '',
    'Goal isolation contract:',
    '- Inherited context is reference only; this task prompt is the only active objective.',
    '- Do not create, resume, update, or complete Codex goals.',
    '- Do not continue the parent thread or project goal.',
    '- Do not spawn subagents or external agents from this worker.',
    '- Report evidence back once and stop.',
    '',
    'Next five steps contract:',
    '- Before making changes, identify the next five concrete steps for this lane.',
    '- Keep the five-step plan scoped to this task, update it when evidence changes, and do not expand ownership.',
    '- Stop early if the next step would cross this worker scope, require secrets, require destructive action, or need parent approval.',
    '',
    task.prompt,
    '',
    'Evidence contract:',
    '- Cite every changed file, command, test, or runtime proof you use.',
    '- Do not claim completion without command, file, or runtime proof.',
    '- Keep ownership narrow to this task.',
    '- Do not perform destructive actions unless the parent workflow explicitly says they were approved.'
  ].join('\n');
}

function buildWavePlan(run, options = {}) {
  const adapter = options.adapter || DEFAULT_ADAPTER;
  if (adapter !== DEFAULT_ADAPTER) {
    throw new Error(`Unsupported worker adapter: ${adapter}. Supported adapter: ${DEFAULT_ADAPTER}`);
  }

  const running = run.tasks.filter(task => task.status === 'running').length;
  const availableSlots = Math.max(0, run.workflow.maxConcurrency - running);
  const maxStart = Math.min(
    availableSlots,
    parsePositiveInteger(options['max-start'], run.workflow.maxConcurrency, 'max-start')
  );
  const selected = runnableTasks(run).slice(0, maxStart);
  const id = options.wave || waveId();
  const waveDir = path.join(run.paths.waves, id);
  const sessionName = slugify(`${run.workflow.name}-${id}`, 'workers');
  const coordinationRoot = path.join(waveDir, 'workers');
  const coordinationDir = path.join(coordinationRoot, sessionName);
  const workerScript = path.join(pluginRoot(), 'scripts', 'orchestrate-codex-worker.sh');
  const envPrefix = buildWorkerEnvPrefix(options);
  const launcher = [
    envPrefix,
    'bash',
    shellQuote(workerScript),
    '{task_file_sh}',
    '{handoff_file_sh}',
    '{status_file_sh}'
  ].filter(Boolean).join(' ');

  const workers = selected.map(task => {
    const workerSlug = slugify(task.id, task.id.toLowerCase());
    return {
      taskId: task.id,
      workerName: task.id,
      workerSlug,
      taskFilePath: path.join(coordinationDir, workerSlug, 'task.md'),
      handoffFilePath: path.join(coordinationDir, workerSlug, 'handoff.md'),
      statusFilePath: path.join(coordinationDir, workerSlug, 'status.md')
    };
  });

  const plan = {
    sessionName,
    repoRoot: run.workflow.repoRoot,
    coordinationRoot,
    launcherCommand: launcher,
    workers: selected.map(task => ({
      name: task.id,
      task: buildWorkerTaskPrompt(run, task)
    }))
  };

  return {
    waveId: id,
    adapter,
    status: 'planned',
    runDir: run.paths.runDir,
    createdAt: now(),
    planPath: path.join(waveDir, 'plan.json'),
    eventsPath: path.join(waveDir, 'events.jsonl'),
    wavePath: path.join(waveDir, 'wave.json'),
    waveDir,
    sessionName,
    coordinationRoot,
    coordinationDir,
    retryLimit: parseNonNegativeInteger(options['retry-limit'], 0, 'retry-limit'),
    pollSeconds: parsePositiveInteger(options['poll-seconds'], 5, 'poll-seconds'),
    tasks: workers,
    plan
  };
}

function materializeWave(wave) {
  fs.mkdirSync(wave.waveDir, { recursive: true });
  writeJson(wave.planPath, wave.plan);
  writeJson(wave.wavePath, wave);
  appendJsonl(wave.eventsPath, {
    type: 'wave-planned',
    waveId: wave.waveId,
    tasks: wave.tasks.map(task => task.taskId),
    createdAt: now()
  });
}

function saveWave(wave) {
  writeJson(wave.wavePath, wave);
}

function loadWave(run, waveIdValue) {
  if (!waveIdValue) {
    throw new Error('collect-workers requires --wave');
  }
  const wavePath = path.join(run.paths.waves, waveIdValue, 'wave.json');
  const wave = readJson(wavePath);
  if (!wave) {
    throw new Error(`No wave metadata found at ${wavePath}`);
  }
  return wave;
}

function markWaveTasksRunning(run, wave) {
  const startedAt = now();
  for (const worker of wave.tasks) {
    const task = taskById(run.tasks, worker.taskId);
    task.status = 'running';
    task.assignedAgent = worker.workerName;
    task.workerAdapter = wave.adapter;
    task.waveId = wave.waveId;
    task.lastError = null;
    task.updatedAt = startedAt;
    const attempt = {
      attempt: (task.attemptCount || 0) + 1,
      waveId: wave.waveId,
      adapter: wave.adapter,
      workerName: worker.workerName,
      status: 'running',
      startedAt,
      statusFilePath: worker.statusFilePath,
      handoffFilePath: worker.handoffFilePath
    };
    task.attempts = Array.isArray(task.attempts) ? task.attempts : [];
    task.attempts.push(attempt);
    task.attemptCount = task.attempts.length;
    task.lastAttempt = attempt;
  }
  saveTasks(run);
  saveWorkflow(run);
  appendJsonl(run.paths.results, {
    type: 'worker-wave-started',
    waveId: wave.waveId,
    adapter: wave.adapter,
    taskIds: wave.tasks.map(task => task.taskId),
    createdAt: startedAt
  });
}

function executeWave(wave) {
  const result = spawnSync(
    process.execPath,
    [path.join(pluginRoot(), 'scripts', 'orchestrate-worktrees.js'), wave.planPath, '--execute'],
    {
      cwd: pluginRoot(),
      encoding: 'utf8',
      maxBuffer: 10 * 1024 * 1024
    }
  );

  if (result.error) {
    throw result.error;
  }

  return {
    status: result.status,
    stdout: result.stdout || '',
    stderr: result.stderr || ''
  };
}

function preflightWorkerExecution(run, wave) {
  const checks = [];
  const missing = [];
  const warnings = [];

  function record(name, ok, detail, remediation) {
    const check = { name, ok, detail: detail || null, remediation: remediation || null };
    checks.push(check);
    if (!ok) {
      missing.push(name);
    }
    return check;
  }

  const codex = commandAvailable('codex');
  record('codex', codex.available, codex.path || codex.stderr, 'Install or expose the Codex CLI on PATH before tmux/worktree worker execution.');

  const git = commandAvailable('git');
  record('git', git.available, git.path || git.stderr, 'Install or expose git on PATH before creating isolated worker branches/worktrees.');

  const tmux = commandAvailable('tmux');
  record('tmux', tmux.available, tmux.path || tmux.stderr, 'Install tmux or use native read/review subagents or Codex app worktrees instead of run-workers --execute.');

  const workerScript = path.join(pluginRoot(), 'scripts', 'orchestrate-codex-worker.sh');
  let workerScriptOk = false;
  try {
    fs.accessSync(workerScript, fs.constants.R_OK);
    workerScriptOk = fs.statSync(workerScript).isFile();
  } catch (error) {
    workerScriptOk = false;
  }
  record('workerScript', workerScriptOk, workerScript, 'Restore scripts/orchestrate-codex-worker.sh before executing worker waves.');

  const repoRoot = run.workflow.repoRoot;
  const repoExists = Boolean(repoRoot && fs.existsSync(repoRoot) && fs.statSync(repoRoot).isDirectory());
  record('repoRoot', repoExists, repoRoot, 'Pass --repo <repo-root> for an existing repository root.');

  if (git.available && repoExists) {
    const gitRoot = spawnSync('git', ['rev-parse', '--show-toplevel'], {
      cwd: repoRoot,
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'pipe']
    });
    record(
      'gitRepository',
      gitRoot.status === 0,
      String(gitRoot.stdout || gitRoot.stderr || '').trim(),
      'Initialize or choose a git repository before isolated worker execution.'
    );
  } else {
    record('gitRepository', false, null, 'git and an existing repo root are required before repository preflight can pass.');
  }

  let writableRunDir = false;
  try {
    fs.accessSync(run.paths.runDir, fs.constants.W_OK);
    writableRunDir = true;
  } catch (error) {
    writableRunDir = false;
  }
  record('writableRunDir', writableRunDir, run.paths.runDir, 'Ensure the workflow run directory is writable before launching a worker wave.');

  if (wave.tasks.length === 0) {
    warnings.push('No runnable tasks were selected; execution will be a no-op.');
  }

  return {
    ok: missing.length === 0,
    missing,
    checks,
    warnings,
    fallback: missing.includes('tmux')
      ? 'Use native Codex subagents only for read/review/research lanes, or use Codex app worktrees for write-heavy lanes until tmux is available.'
      : null
  };
}

function completeTaskFromWorker(run, wave, worker, workerStatus, statusValue) {
  const task = taskById(run.tasks, worker.taskId);
  const handoffContent = readText(worker.handoffFilePath);
  const completedAt = workerStatus.updated || now();
  const startedAt = task.lastAttempt && task.lastAttempt.startedAt ? task.lastAttempt.startedAt : null;
  const durationMs = startedAt ? Math.max(0, new Date(completedAt).getTime() - new Date(startedAt).getTime()) : null;
  const summary = summarizeHandoff(
    handoffContent,
    statusValue === 'pass' ? `Worker ${worker.workerName} completed` : `Worker ${worker.workerName} failed`
  );
  const evidence = `status: ${worker.statusFilePath}; handoff: ${worker.handoffFilePath}`;

  if (task.status === statusValue && task.waveId === wave.waveId) {
    return false;
  }

  task.status = statusValue;
  task.summary = summary;
  task.evidence = evidence;
  task.durationMs = durationMs;
  task.lastError = statusValue === 'fail' ? summary : null;
  task.updatedAt = completedAt;
  if (task.lastAttempt) {
    task.lastAttempt.status = statusValue;
    task.lastAttempt.finishedAt = completedAt;
    task.lastAttempt.durationMs = durationMs;
  }
  task.attempts = Array.isArray(task.attempts) ? task.attempts : [];
  if (task.attempts.length > 0) {
    task.attempts[task.attempts.length - 1] = task.lastAttempt;
  }

  const alreadyRecorded = run.results.some(result => (
    result.type === 'completion' &&
    result.taskId === task.id &&
    result.waveId === wave.waveId
  ));

  if (!alreadyRecorded) {
    appendJsonl(run.paths.results, {
      type: 'completion',
      taskId: task.id,
      waveId: wave.waveId,
      status: statusValue,
      agent: task.assignedAgent || null,
      summary,
      evidence,
      createdAt: completedAt
    });
    appendJsonl(run.paths.claims, {
      type: statusValue === 'pass' ? 'evidence' : 'worker-failure',
      taskId: task.id,
      waveId: wave.waveId,
      evidence,
      createdAt: completedAt
    });
    run.results.push({
      type: 'completion',
      taskId: task.id,
      waveId: wave.waveId
    });
  }

  return true;
}

function collectWave(run, waveIdValue) {
  const wave = loadWave(run, waveIdValue);
  const collected = [];
  const stillRunning = [];

  for (const worker of wave.tasks) {
    const statusContent = readText(worker.statusFilePath);
    const workerStatus = parseWorkerStatusMarkdown(statusContent);
    const state = workerStatus.state || 'not started';

    if (state === 'completed') {
      if (completeTaskFromWorker(run, wave, worker, workerStatus, 'pass')) {
        collected.push({ taskId: worker.taskId, status: 'pass' });
      }
    } else if (state === 'failed') {
      if (completeTaskFromWorker(run, wave, worker, workerStatus, 'fail')) {
        collected.push({ taskId: worker.taskId, status: 'fail' });
      }
    } else {
      stillRunning.push({ taskId: worker.taskId, state });
    }
  }

  wave.status = stillRunning.length === 0 ? 'collected' : 'running';
  wave.collectedAt = now();
  saveWave(wave);
  appendJsonl(wave.eventsPath, {
    type: 'wave-collected',
    waveId: wave.waveId,
    collected,
    stillRunning,
    createdAt: now()
  });

  saveTasks(run);
  saveWorkflow(run);

  return {
    waveId: wave.waveId,
    collected,
    stillRunning,
    status: wave.status
  };
}

function markWaveLaunchFailure(run, wave, errorMessage) {
  const failedAt = now();
  wave.status = 'launch-failed';
  wave.failedAt = failedAt;
  wave.error = errorMessage;
  saveWave(wave);
  appendJsonl(wave.eventsPath, {
    type: 'wave-launch-failed',
    waveId: wave.waveId,
    error: errorMessage,
    createdAt: failedAt
  });

  for (const worker of wave.tasks) {
    const task = taskById(run.tasks, worker.taskId);
    task.status = 'fail';
    task.summary = 'Worker wave failed to launch';
    task.evidence = errorMessage;
    task.lastError = errorMessage;
    task.updatedAt = failedAt;
    if (task.lastAttempt) {
      task.lastAttempt.status = 'fail';
      task.lastAttempt.finishedAt = failedAt;
      task.lastAttempt.error = errorMessage;
    }
  }
  saveTasks(run);
  saveWorkflow(run);
}

function waitForWave(runDir, waveIdValue, pollSeconds, maxPolls) {
  let latest = null;
  for (let poll = 0; poll < maxPolls; poll += 1) {
    const run = loadRun(runDir);
    latest = collectWave(run, waveIdValue);
    if (latest.stillRunning.length === 0) {
      break;
    }
    spawnSync('sleep', [String(pollSeconds)], { stdio: 'ignore' });
  }
  return latest;
}

function cmdRunWorkers(options) {
  if (!options.run) {
    throw new Error('run-workers requires --run');
  }

  const run = loadRun(options.run);
  if (options['approve-execution']) {
    run.workflow.executionApproved = true;
    saveWorkflow(run);
  }

  const execute = Boolean(options.execute);
  if (run.workflow.mode === 'plan-only' && execute && !run.workflow.executionApproved) {
    throw new Error('Workflow is plan-only. Use resume --approve-execution before run-workers --execute.');
  }
  const dryRun = !execute || Boolean(options['dry-run']);
  const wave = buildWavePlan(run, options);
  const preview = {
    dryRun,
    execute,
    adapter: wave.adapter,
    waveId: wave.waveId,
    runDir: run.paths.runDir,
    paused: Boolean(run.workflow.paused),
    selectedTasks: wave.tasks.map(task => task.taskId),
    workers: wave.plan.workers,
    plan: wave.plan,
    launchLadder: codexLaunchLadder(),
    executionGuidance: codexExecutionGuidance(),
    tokenWarning: run.workflow.tokenWarning || estimateTokenRisk(run.tasks.length, run.workflow.maxConcurrency)
  };

  if (dryRun) {
    console.log(JSON.stringify(preview, null, 2));
    return;
  }
  if (run.workflow.paused || run.workflow.cancelledAt) {
    throw new Error('Workflow is paused or cancelled; resume it before launching workers.');
  }
  if (wave.tasks.length === 0) {
    console.log(JSON.stringify({
      launched: false,
      reason: 'No runnable tasks available',
      ...summarize(run)
    }, null, 2));
    return;
  }

  const preflight = preflightWorkerExecution(run, wave);
  if (!preflight.ok) {
    console.log(JSON.stringify({
      launched: false,
      reason: 'Worker execution preflight failed',
      waveId: wave.waveId,
      selectedTasks: wave.tasks.map(task => task.taskId),
      preflight,
      launchLadder: codexLaunchLadder(),
      executionGuidance: codexExecutionGuidance()
    }, null, 2));
    return;
  }

  materializeWave(wave);
  markWaveTasksRunning(run, wave);

  const execution = executeWave(wave);
  if (execution.status !== 0) {
    const errorMessage = [execution.stderr.trim(), execution.stdout.trim()].filter(Boolean).join('\n') ||
      `orchestrate-worktrees exited with status ${execution.status}`;
    markWaveLaunchFailure(loadRun(run.paths.runDir), wave, errorMessage);
    throw new Error(errorMessage);
  }

  wave.status = 'launched';
  wave.launchedAt = now();
  wave.launchStdout = execution.stdout.trim();
  wave.launchStderr = execution.stderr.trim();
  saveWave(wave);
  appendJsonl(wave.eventsPath, {
    type: 'wave-launched',
    waveId: wave.waveId,
    stdout: wave.launchStdout,
    stderr: wave.launchStderr,
    createdAt: wave.launchedAt
  });

  const output = {
    launched: true,
    waveId: wave.waveId,
    planPath: wave.planPath,
    coordinationDir: wave.coordinationDir,
    workers: wave.tasks.length,
    launchStdout: wave.launchStdout,
    collectCommand: `node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js collect-workers --run ${run.paths.runDir} --wave ${wave.waveId}`,
    dashboardCommand: `node skills/dynamic-workflow-backlog/scripts/dynamic-workflow-backlog.js dashboard --run ${run.paths.runDir}`
  };

  if (options.wait) {
    output.collection = waitForWave(
      run.paths.runDir,
      wave.waveId,
      wave.pollSeconds,
      parsePositiveInteger(options['max-polls'], 120, 'max-polls')
    );
  }

  console.log(JSON.stringify(output, null, 2));
}

function cmdCollectWorkers(options) {
  if (!options.run || !options.wave) {
    throw new Error('collect-workers requires --run and --wave');
  }
  console.log(JSON.stringify(collectWave(loadRun(options.run), options.wave), null, 2));
}

function cmdPause(options) {
  if (!options.run) {
    throw new Error('pause requires --run');
  }
  const run = loadRun(options.run);
  if (options.task) {
    const task = taskById(run.tasks, options.task);
    task.paused = true;
    task.updatedAt = now();
    saveTasks(run);
  } else {
    run.workflow.paused = true;
  }
  saveWorkflow(run);
  appendJsonl(run.paths.claims, {
    type: 'pause',
    taskId: options.task || null,
    createdAt: now()
  });
  console.log(JSON.stringify(summarize(loadRun(options.run)), null, 2));
}

function cmdResume(options) {
  if (!options.run) {
    throw new Error('resume requires --run');
  }
  const run = loadRun(options.run);
  if (options.task) {
    const task = taskById(run.tasks, options.task);
    task.paused = false;
    task.updatedAt = now();
    saveTasks(run);
  } else {
    run.workflow.paused = false;
  }
  if (options['approve-execution']) {
    run.workflow.executionApproved = true;
    run.workflow.executionApprovedAt = now();
  }
  saveWorkflow(run);
  appendJsonl(run.paths.claims, {
    type: 'resume',
    taskId: options.task || null,
    approveExecution: Boolean(options['approve-execution']),
    createdAt: now()
  });
  console.log(JSON.stringify(summarize(loadRun(options.run)), null, 2));
}

function cmdRetry(options) {
  if (!options.run || !options.task) {
    throw new Error('retry requires --run and --task');
  }
  const run = loadRun(options.run);
  const task = taskById(run.tasks, options.task);
  if (!['fail', 'cancelled'].includes(task.status) && !options.force) {
    throw new Error(`Cannot retry ${task.id}: status is ${task.status}. Use --force to retry anyway.`);
  }
  task.status = 'pending';
  task.assignedAgent = null;
  task.paused = false;
  task.cancelledAt = null;
  task.lastError = null;
  task.retryCount = (task.retryCount || 0) + 1;
  task.retryRequestedAt = now();
  task.updatedAt = task.retryRequestedAt;
  saveTasks(run);
  saveWorkflow(run);
  appendJsonl(run.paths.claims, {
    type: 'retry',
    taskId: task.id,
    retryCount: task.retryCount,
    createdAt: task.retryRequestedAt
  });
  console.log(JSON.stringify(task, null, 2));
}

function cmdCancel(options) {
  if (!options.run) {
    throw new Error('cancel requires --run');
  }
  const run = loadRun(options.run);
  if (options['kill-active']) {
    throw new Error('cancel --kill-active is intentionally not implemented in v1; stop tmux sessions manually after inspecting them.');
  }
  if (options.task) {
    const task = taskById(run.tasks, options.task);
    task.status = 'fail';
    task.cancelledAt = now();
    task.lastError = 'Cancelled by workflow operator';
    task.summary = task.summary || 'Cancelled by workflow operator';
    task.evidence = task.evidence || 'No worker kill was attempted by cancel.';
    task.updatedAt = task.cancelledAt;
    saveTasks(run);
  } else {
    run.workflow.paused = true;
    run.workflow.cancelledAt = now();
  }
  saveWorkflow(run);
  appendJsonl(run.paths.claims, {
    type: 'cancel',
    taskId: options.task || null,
    killActive: false,
    createdAt: now()
  });
  console.log(JSON.stringify(summarize(loadRun(options.run)), null, 2));
}

function buildDashboardSnapshot(run) {
  return {
    ...summarize(run),
    tasks: run.tasks.map(task => ({
      id: task.id,
      phase: task.phase,
      role: task.role,
      title: task.title,
      status: task.status,
      assignedAgent: task.assignedAgent || null,
      attemptCount: task.attemptCount || 0,
      retryCount: task.retryCount || 0,
      paused: Boolean(task.paused),
      waveId: task.waveId || null,
      summary: task.summary || '',
      evidence: task.evidence || '',
      lastError: task.lastError || null,
      updatedAt: task.updatedAt
    }))
  };
}

function escapeHtml(value) {
  return String(value == null ? '' : value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function renderDashboardHtml(snapshot) {
  const taskRows = snapshot.tasks.map(task => `
      <tr>
        <td>${escapeHtml(task.id)}</td>
        <td>${escapeHtml(task.phase)}</td>
        <td>${escapeHtml(task.role)}</td>
        <td>${escapeHtml(task.title)}</td>
        <td><span class="badge ${escapeHtml(task.status)}">${escapeHtml(task.status)}</span></td>
        <td>${escapeHtml(task.attemptCount)}</td>
        <td>${escapeHtml(task.waveId || '')}</td>
        <td>${escapeHtml(task.summary || task.lastError || '')}</td>
      </tr>`).join('');
  const waveRows = snapshot.waves.map(wave => `
      <tr>
        <td>${escapeHtml(wave.waveId)}</td>
        <td>${escapeHtml(wave.adapter)}</td>
        <td>${escapeHtml(wave.status)}</td>
        <td>${escapeHtml(wave.taskCount)}</td>
        <td>${escapeHtml(wave.createdAt)}</td>
      </tr>`).join('');

  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ECC Dynamic Workflow Dashboard</title>
  <style>
    :root { color-scheme: light dark; font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    body { margin: 0; padding: 24px; background: #f7f8fa; color: #171923; }
    main { max-width: 1180px; margin: 0 auto; }
    h1 { font-size: 24px; margin: 0 0 8px; }
    h2 { font-size: 17px; margin: 26px 0 10px; }
    .meta, .grid { display: grid; gap: 10px; }
    .meta { grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); margin-top: 16px; }
    .cell { border: 1px solid #d8dee8; background: #fff; border-radius: 8px; padding: 12px; }
    .label { font-size: 12px; color: #667085; text-transform: uppercase; letter-spacing: .04em; }
    .value { font-size: 18px; font-weight: 650; margin-top: 4px; }
    table { border-collapse: collapse; width: 100%; background: #fff; border: 1px solid #d8dee8; border-radius: 8px; overflow: hidden; }
    th, td { border-bottom: 1px solid #e6e9ef; padding: 9px 10px; text-align: left; vertical-align: top; font-size: 13px; }
    th { background: #eef2f7; color: #344054; font-weight: 650; }
    .badge { display: inline-block; padding: 2px 7px; border-radius: 999px; background: #e6e9ef; font-size: 12px; font-weight: 650; }
    .pass, .completed, .collected { background: #d9f5e5; color: #067647; }
    .fail, .launch-failed { background: #fee4e2; color: #b42318; }
    .running, .launched { background: #dbeafe; color: #175cd3; }
    .pending, .planned { background: #fef0c7; color: #b54708; }
    @media (prefers-color-scheme: dark) {
      body { background: #111827; color: #f9fafb; }
      .cell, table { background: #1f2937; border-color: #374151; }
      th { background: #273549; color: #d1d5db; }
      td, th { border-color: #374151; }
      .label { color: #9ca3af; }
    }
  </style>
</head>
<body>
<main>
  <h1>${escapeHtml(snapshot.name)}</h1>
  <div>${escapeHtml(snapshot.goal)}</div>
  <section class="meta">
    <div class="cell"><div class="label">Run Mode</div><div class="value">${escapeHtml(snapshot.mode)}</div></div>
    <div class="cell"><div class="label">Runnable</div><div class="value">${escapeHtml(snapshot.runnable.length)}</div></div>
    <div class="cell"><div class="label">Running</div><div class="value">${escapeHtml(snapshot.running)}</div></div>
    <div class="cell"><div class="label">Synthesis Ready</div><div class="value">${snapshot.synthesis.ready ? 'yes' : 'no'}</div></div>
  </section>
  <h2>Tasks</h2>
  <table>
    <thead><tr><th>ID</th><th>Phase</th><th>Role</th><th>Title</th><th>Status</th><th>Attempts</th><th>Wave</th><th>Evidence Summary</th></tr></thead>
    <tbody>${taskRows || '<tr><td colspan="8">No tasks</td></tr>'}</tbody>
  </table>
  <h2>Waves</h2>
  <table>
    <thead><tr><th>Wave</th><th>Adapter</th><th>Status</th><th>Tasks</th><th>Created</th></tr></thead>
    <tbody>${waveRows || '<tr><td colspan="5">No worker waves</td></tr>'}</tbody>
  </table>
  <h2>Synthesis Blockers</h2>
  <div class="cell">${escapeHtml(snapshot.synthesis.blockers.join('; ') || 'None')}</div>
</main>
</body>
</html>`;
}

function renderWatchText(snapshot) {
  const counts = Object.entries(snapshot.counts)
    .map(([status, count]) => `${status}:${count}`)
    .join(' ');
  return [
    `Workflow: ${snapshot.name}`,
    `Goal: ${snapshot.goal}`,
    `Mode: ${snapshot.mode}${snapshot.paused ? ' (paused)' : ''}`,
    `Counts: ${counts || 'none'} | running:${snapshot.running} | runnable:${snapshot.runnable.length}`,
    `Synthesis ready: ${snapshot.synthesis.ready ? 'yes' : 'no'}`,
    `Blockers: ${snapshot.synthesis.blockers.join('; ') || 'none'}`,
    '',
    'Runnable tasks:',
    ...snapshot.runnable.map(task => `- ${task.id} ${task.phase}/${task.role}: ${task.title}`)
  ].join('\n');
}

function cmdWatch(options) {
  if (!options.run) {
    throw new Error('watch requires --run');
  }
  const snapshot = buildDashboardSnapshot(loadRun(options.run));
  if (options.json) {
    console.log(JSON.stringify(snapshot, null, 2));
  } else {
    console.log(renderWatchText(snapshot));
  }
}

function cmdDashboard(options) {
  if (!options.run) {
    throw new Error('dashboard requires --run');
  }
  if (options['print-html']) {
    console.log(renderDashboardHtml(buildDashboardSnapshot(loadRun(options.run))));
    return;
  }

  const port = Number.parseInt(options.port || DEFAULT_DASHBOARD_PORT, 10);
  if (!Number.isInteger(port) || port < 0 || port > 65535) {
    throw new Error('--port must be between 0 and 65535');
  }
  const runDir = path.resolve(options.run);
  const server = http.createServer((request, response) => {
    try {
      const snapshot = buildDashboardSnapshot(loadRun(runDir));
      if (request.url === '/status.json') {
        response.writeHead(200, { 'content-type': 'application/json; charset=utf-8' });
        response.end(`${JSON.stringify(snapshot, null, 2)}\n`);
        return;
      }
      response.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
      response.end(renderDashboardHtml(snapshot));
    } catch (error) {
      response.writeHead(500, { 'content-type': 'application/json; charset=utf-8' });
      response.end(`${JSON.stringify({ error: error.message })}\n`);
    }
  });

  server.listen(port, '127.0.0.1', () => {
    const address = server.address();
    console.log(JSON.stringify({
      url: `http://127.0.0.1:${address.port}/`,
      statusUrl: `http://127.0.0.1:${address.port}/status.json`,
      runDir
    }, null, 2));
  });
}

function main() {
  const { command, options } = parseArgs(process.argv);

  if (!command || ['-h', '--help', 'help'].includes(command)) {
    usage();
    return;
  }

  const commands = {
    automode: cmdAutomode,
    classify: cmdClassify,
    plan: cmdPlan,
    init: cmdInit,
    'add-task': cmdAddTask,
    'add-review': cmdAddReview,
    'add-reviews': cmdAddReviews,
    shard: cmdShard,
    status: cmdStatus,
    next: cmdNext,
    claim: cmdClaim,
    complete: cmdComplete,
    synthesize: cmdSynthesize,
    'export-worktree-plan': cmdExportWorktreePlan,
    'run-workers': cmdRunWorkers,
    'collect-workers': cmdCollectWorkers,
    pause: cmdPause,
    resume: cmdResume,
    retry: cmdRetry,
    cancel: cmdCancel,
    watch: cmdWatch,
    dashboard: cmdDashboard
  };

  const handler = commands[command];
  if (!handler) {
    throw new Error(`Unknown command: ${command}`);
  }

  handler(options);
}

if (require.main === module) {
  try {
    main();
  } catch (error) {
    console.error(`[dynamic-workflow-backlog] ${error.message}`);
    process.exit(1);
  }
}

module.exports = {
  buildDashboardSnapshot,
  buildWavePlan,
  classifyDynamicWorkflow,
  collectWave,
  decideAutoMode,
  estimateTokenRisk,
  parseTaskSpec,
  renderDashboardHtml,
  runnableTasks,
  synthesisState,
  summarize
};
