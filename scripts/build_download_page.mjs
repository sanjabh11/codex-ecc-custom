import { readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const zipsDir = "public/ecc-bolt-imports/zips";
const names = readdirSync(zipsDir).filter((f) => f.endsWith(".zip")).sort();

const entries = names.map((f) => {
  const buf = readFileSync(join(zipsDir, f));
  const b64 = buf.toString("base64");
  return { name: f.replace(/\.zip$/, ""), size: buf.length, b64 };
});

const totalKb = Math.round(entries.reduce((s, e) => s + e.size, 0) / 1024);

const js = `const FILES = ${JSON.stringify(entries)};

const grid = document.getElementById("grid");
const count = document.getElementById("count");

count.textContent = \`\${FILES.length} skills packaged \\u2022 \${${totalKb}} KB total \\u2022 each imports as one skill\`;

for (const file of FILES) {
  const a = document.createElement("a");
  a.className = "card";
  a.href = \`data:application/zip;base64,\${file.b64}\`;
  a.download = \`\${file.name}.zip\`;

  const name = document.createElement("span");
  name.className = "name";
  name.textContent = file.name;

  const meta = document.createElement("span");
  meta.className = "meta";
  meta.textContent = \`\${(file.size / 1024).toFixed(1)} KB \\u2022 contains SKILL.md\`;

  const dl = document.createElement("span");
  dl.className = "download";
  dl.textContent = "Download";

  a.append(name, meta, dl);
  grid.appendChild(a);
}

document.getElementById("download-all").addEventListener("click", () => {
  for (const file of FILES) {
    const a = document.createElement("a");
    a.href = \`data:application/zip;base64,\${file.b64}\`;
    a.download = \`\${file.name}.zip\`;
    document.body.appendChild(a);
    a.click();
    a.remove();
  }
});
`;

writeFileSync("main.js", js);
console.log(`embedded ${entries.length} zips, ${totalKb} KB total`);
