const skills = [
  "agent-architecture-audit",
  "agent-phase-ratchet",
  "benchmark-optimization-loop",
  "benchmark",
  "browser-qa",
  "codebase-onboarding",
  "coding-judgment",
  "conformance-gate",
  "deep-research",
  "dynamic-workflow-backlog",
  "e2e-testing",
  "ecc-advisor",
  "ecc-guide",
  "ecc-prompt-optimize",
  "ecc-role-catalog",
  "fuzz-regression",
  "prompt-optimizer",
  "token-budget-advisor",
  "workflow-audit-router",
];

const grid = document.getElementById("grid");
for (const name of skills) {
  const a = document.createElement("a");
  a.className = "card";
  a.href = `/ecc-bolt-imports/zips/${name}.zip`;
  a.download = `${name}.zip`;
  const label = document.createElement("span");
  label.className = "name";
  label.textContent = name;
  const meta = document.createElement("span");
  meta.className = "meta";
  meta.textContent = ".zip / SKILL.md inside";
  const dl = document.createElement("span");
  dl.className = "download";
  dl.textContent = "Download";
  a.append(label, meta, dl);
  grid.appendChild(a);
}
