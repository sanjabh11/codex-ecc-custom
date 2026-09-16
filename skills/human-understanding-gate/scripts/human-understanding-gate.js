#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const SKILL_NAME = 'human-understanding-gate';
const DEFAULT_DEPTH = 'intern';

function usage() {
  console.log([
    'Usage:',
    '  node skills/human-understanding-gate/scripts/human-understanding-gate.js resolve --task <task> [--json]',
    '  node skills/human-understanding-gate/scripts/human-understanding-gate.js eval-skill [--cases <file>] [--json]',
    '  node skills/human-understanding-gate/scripts/human-understanding-gate.js eval-resolver [--cases <file>] [--json]',
    '  node skills/human-understanding-gate/scripts/human-understanding-gate.js check-pack [--root <repo>] [--json]',
    '  node skills/human-understanding-gate/scripts/human-understanding-gate.js checklist --topic <topic> [--json]'
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
    options[key] = next;
    index += 1;
  }

  return { command, options };
}

function repoRootFromScript() {
  return path.resolve(__dirname, '..', '..', '..');
}

function skillRootFromRepo(repoRoot) {
  return path.join(repoRoot, 'skills', SKILL_NAME);
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function loadResolver(skillRoot = path.resolve(__dirname, '..')) {
  return readJson(path.join(skillRoot, 'resolver.json'));
}

function loadResolverCases(skillRoot = path.resolve(__dirname, '..'), casesPath = null) {
  return readJson(casesPath ? path.resolve(casesPath) : path.join(skillRoot, 'evals', 'resolver-cases.json'));
}

function loadSkillEvalCases(skillRoot = path.resolve(__dirname, '..'), casesPath = null) {
  return readJson(casesPath ? path.resolve(casesPath) : path.join(skillRoot, 'evals', 'skill-behavior-cases.json'));
}

function toRegExp(rule) {
  return new RegExp(rule.pattern, 'i');
}

function detectDepth(task, resolver) {
  const text = String(task || '');
  for (const rule of resolver.depthRules || []) {
    if (toRegExp(rule).test(text)) {
      return rule.depth;
    }
  }
  return DEFAULT_DEPTH;
}

function resolveTask(task, resolver = loadResolver()) {
  const text = String(task || '').trim();
  if (!text) {
    throw new Error('resolve requires --task');
  }

  const reasons = [];
  const suppressions = [];
  let score = 0;

  for (const rule of resolver.rules || []) {
    if (toRegExp(rule).test(text)) {
      score += Number(rule.points || 0);
      reasons.push({
        id: rule.id,
        points: Number(rule.points || 0),
        reason: rule.reason
      });
    }
  }

  for (const suppressor of resolver.suppressors || []) {
    if (toRegExp(suppressor).test(text)) {
      suppressions.push({
        id: suppressor.id,
        reason: suppressor.reason
      });
    }
  }

  const threshold = Number(resolver.threshold || 1);
  const invoke = score >= threshold && suppressions.length === 0;

  return {
    skill: SKILL_NAME,
    invoke,
    score,
    threshold,
    depth: detectDepth(text, resolver),
    reasons,
    suppressions
  };
}

function buildChecklist(topic = 'current session') {
  return [
    'Problem',
    'Branches',
    'Solution',
    'Design decisions',
    'Edge cases',
    'Evidence',
    'Impact',
    'Next action'
  ].map(item => ({
    item,
    topic,
    status: 'not verified yet'
  }));
}

function evaluateResolverCases(cases, resolver = loadResolver()) {
  const results = cases.map(testCase => {
    const actual = resolveTask(testCase.task, resolver);
    const invokePass = actual.invoke === testCase.expectInvoke;
    const depthPass = !testCase.expectDepth || actual.depth === testCase.expectDepth;

    return {
      id: testCase.id,
      pass: invokePass && depthPass,
      expected: {
        invoke: testCase.expectInvoke,
        depth: testCase.expectDepth || null
      },
      actual
    };
  });

  return {
    ok: results.every(result => result.pass),
    count: results.length,
    passed: results.filter(result => result.pass).length,
    failed: results.filter(result => !result.pass).length,
    results
  };
}

function evaluateSkillEvalCases(cases) {
  const results = cases.map(testCase => {
    const missing = [];
    if (!testCase.id) missing.push('id');
    if (!testCase.prompt) missing.push('prompt');
    if (!Array.isArray(testCase.required) || testCase.required.length === 0) missing.push('required');
    if (!Array.isArray(testCase.forbidden)) missing.push('forbidden');

    return {
      id: testCase.id || '(missing id)',
      pass: missing.length === 0,
      missing
    };
  });

  return {
    ok: results.every(result => result.pass),
    count: results.length,
    passed: results.filter(result => result.pass).length,
    failed: results.filter(result => !result.pass).length,
    results
  };
}

function checkSkillPack(repoRoot = repoRootFromScript()) {
  const root = path.resolve(repoRoot);
  const skillRoot = skillRootFromRepo(root);
  const checks = [];

  function add(id, ok, detail) {
    checks.push({ id, ok: Boolean(ok), detail });
  }

  const skillPath = path.join(skillRoot, 'SKILL.md');
  const commandPath = path.join(root, 'commands', 'understanding-gate.md');
  const scriptPath = path.join(skillRoot, 'scripts', 'human-understanding-gate.js');
  const resolverPath = path.join(skillRoot, 'resolver.json');
  const evalPath = path.join(skillRoot, 'evals', 'resolver-cases.json');
  const skillEvalPath = path.join(skillRoot, 'evals', 'skill-behavior-cases.json');
  const testPath = path.join(root, 'tests', 'scripts', 'human-understanding-gate.test.js');
  const agentPath = path.join(root, 'agent.yaml');
  const manifestPath = path.join(root, 'manifests', 'install-modules.json');

  add('skill-markdown-exists', fs.existsSync(skillPath), skillPath);
  add('command-exists', fs.existsSync(commandPath), commandPath);
  add('deterministic-script-exists', fs.existsSync(scriptPath), scriptPath);
  add('resolver-exists', fs.existsSync(resolverPath), resolverPath);
  add('resolver-evals-exist', fs.existsSync(evalPath), evalPath);
  add('skill-evals-exist', fs.existsSync(skillEvalPath), skillEvalPath);
  add('unit-test-exists', fs.existsSync(testPath), testPath);

  if (fs.existsSync(skillPath)) {
    const skill = fs.readFileSync(skillPath, 'utf8');
    for (const phrase of [
      'Skill Pack Contract',
      'scripts/human-understanding-gate.js',
      'resolver.json',
      'evals/skill-behavior-cases.json',
      'evals/resolver-cases.json',
      'Understanding Checklist',
      'not verified yet',
      'agent-phase-ratchet',
      'verification-loop',
      'conformance-gate',
      'perf-ratchet',
      'fuzz-regression'
    ]) {
      add(`skill-contains-${phrase.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`, skill.includes(phrase), phrase);
    }
  }

  if (fs.existsSync(resolverPath) && fs.existsSync(evalPath)) {
    const resolver = readJson(resolverPath);
    const cases = readJson(evalPath);
    const evalResult = evaluateResolverCases(cases, resolver);
    add('resolver-eval-passes', evalResult.ok, `${evalResult.passed}/${evalResult.count} cases passed`);
  }

  if (fs.existsSync(skillEvalPath)) {
    const skillEvalResult = evaluateSkillEvalCases(readJson(skillEvalPath));
    add('skill-eval-schema-passes', skillEvalResult.ok, `${skillEvalResult.passed}/${skillEvalResult.count} cases passed`);
  }

  if (fs.existsSync(agentPath)) {
    add('agent-yaml-registers-skill', fs.readFileSync(agentPath, 'utf8').includes(`- ${SKILL_NAME}`), agentPath);
  }

  if (fs.existsSync(manifestPath)) {
    const manifest = readJson(manifestPath);
    const workflow = (manifest.modules || []).find(module => module.id === 'workflow-quality');
    add(
      'workflow-quality-installs-skill',
      Boolean(workflow && workflow.paths && workflow.paths.includes(`skills/${SKILL_NAME}`)),
      manifestPath
    );
  }

  return {
    ok: checks.every(check => check.ok),
    checks
  };
}

function print(value, json) {
  if (json) {
    console.log(JSON.stringify(value, null, 2));
  } else {
    console.log(value.ok === false ? 'FAIL' : 'PASS');
  }
}

function main() {
  const { command, options } = parseArgs(process.argv);

  try {
    if (!command || command === 'help' || options.help) {
      usage();
      return;
    }

    if (command === 'resolve') {
      print(resolveTask(options.task), options.json);
      return;
    }

    if (command === 'eval-resolver') {
      const skillRoot = path.resolve(__dirname, '..');
      const resolver = loadResolver(skillRoot);
      const cases = loadResolverCases(skillRoot, options.cases || null);
      const result = evaluateResolverCases(cases, resolver);
      print(result, options.json);
      process.exitCode = result.ok ? 0 : 1;
      return;
    }

    if (command === 'eval-skill') {
      const skillRoot = path.resolve(__dirname, '..');
      const cases = loadSkillEvalCases(skillRoot, options.cases || null);
      const result = evaluateSkillEvalCases(cases);
      print(result, options.json);
      process.exitCode = result.ok ? 0 : 1;
      return;
    }

    if (command === 'check-pack') {
      const result = checkSkillPack(options.root || repoRootFromScript());
      print(result, options.json);
      process.exitCode = result.ok ? 0 : 1;
      return;
    }

    if (command === 'checklist') {
      print({ checklist: buildChecklist(options.topic || 'current session') }, options.json);
      return;
    }

    throw new Error(`Unknown command: ${command}`);
  } catch (error) {
    if (options.json) {
      console.log(JSON.stringify({ ok: false, error: error.message }, null, 2));
    } else {
      console.error(error.message);
    }
    process.exitCode = 1;
  }
}

if (require.main === module) {
  main();
}

module.exports = {
  SKILL_NAME,
  DEFAULT_DEPTH,
  buildChecklist,
  checkSkillPack,
  detectDepth,
  evaluateResolverCases,
  evaluateSkillEvalCases,
  loadResolver,
  loadResolverCases,
  loadSkillEvalCases,
  resolveTask
};
