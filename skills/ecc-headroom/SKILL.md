---
name: ecc-headroom
description: Optimize context window usage and reduce token cost by 60-95% using Headroom compression before sending files/logs to the LLM.
---

# ECC Headroom

Use this skill when you encounter context budget limits, when reading large log files, database dumps, JSON assets, or when working in massive codebases.

## Setup Requirements

Ensure `headroom` is installed:
```bash
which headroom || pip install "headroom-ai[all]" || npm install -g headroom-ai
```

## Optimization Techniques & Under-the-Hood Details

Headroom achieves its 60–95% compression via four distinct algorithms depending on the payload:
1. **AST-Aware Code Compression (`CodeCompressor`)**: Prunes method bodies, comments, and boilerplate from code (Python, JS, Go, Rust, Java, C++), retaining only structural signatures (classes, functions, types).
2. **JSON SmartCrusher**: Profiles deep JSON structures, maps repeating keys to short aliases, and truncates large arrays into representative schema samples.
3. **Kompress-Base & CacheAligner**: Compresses text/prose semantically using an agentic trace model while aligning prefixes to trigger LLM prompt cache hits.
4. **Lossless Retrieval (CCR)**: Stores raw uncompressed code/logs locally, injecting compressed hashes in the prompt. The LLM can dynamically call `headroom_retrieve <hash>` when full text is required.

## Compression Ledger Requirement

Every time you process files or logs using Headroom, you must output a **Compression Ledger** in the following format:

| Target File/Log | Original Size (Tokens) | Compressed Size (Tokens) | Token Savings | Method Applied |
| :--- | :--- | :--- | :--- | :--- |
| `path/to/file` | `Original` | `Compressed` | `Savings %` | `AST / JSON / Prose` |

Provide specific, calculated numbers for the work done in the session.

## Best Practices
- If files exceed 1000 lines and are not fully read, compress them before processing.
- Maintain original content in local workspace cache and only query full text via Lossless Retrieval (CCR) when specific detail is required.

