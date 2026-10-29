# Multimodal Extraction — PDFs, Images, Video, Audio

## How Multimodal Extraction Works

Graphify runs two passes:

1. **Deterministic AST pass** (code only, no LLM, local): Extracts structure from code files — classes, functions, imports, call graphs, docstrings, rationale comments (`# NOTE:`, `# WHY:`) — using tree-sitter. Nothing leaves your machine.

2. **LLM semantic pass** (docs, papers, images, video): Claude subagents run in parallel over non-code files to extract concepts, relationships, and design rationale. Uses the harness model or a configured API key.

## Supported File Types

| Type | Extensions | Extraction | LLM Cost |
|------|-----------|------------|----------|
| Code | 19+ languages via tree-sitter | AST + call graph | **Free** (local) |
| Docs | `.md .txt .rst` | Concepts + relationships | LLM tokens |
| Papers | `.pdf` | Citation mining + concept extraction | LLM tokens |
| Images | `.png .jpg .webp .gif` | Vision — screenshots, diagrams, any language | LLM tokens |
| Video | `.mp4 .webm` | Whisper transcription → text | LLM tokens + Whisper |
| Audio | `.mp3 .wav` | Whisper transcription → text | LLM tokens + Whisper |

## Code Languages (tree-sitter, 19+)

Python, JavaScript, TypeScript, Go, Rust, Java, C, C++, Ruby, C#, Kotlin, Scala, PHP, Swift, Lua, Zig, PowerShell, Elixir, Objective-C.

## PDF Extraction

PDFs are processed with citation mining and concept extraction:

```bash
graphify ./papers --no-viz  # papers/ contains .pdf files
```

What you get:
- Concept nodes extracted from the paper content
- Citation edges connecting papers to referenced concepts
- Cross-references between papers and code (if both are in the corpus)

**Token cost warning:** Each PDF typically requires 5,000-15,000 tokens for the semantic pass. A corpus of 10 papers ≈ 50,000-150,000 tokens. Warn the user before building large PDF corpora.

## Image Extraction

Images are processed with Claude vision:

```bash
graphify ./screenshots --no-viz  # screenshots/ contains .png .jpg files
```

What you get:
- Concept nodes from diagrams, architecture screenshots, whiteboard photos
- Text extraction from images in any language (OCR via vision)
- Cross-references between image concepts and code/docs

**Use cases:**
- Architecture diagrams → graph nodes
- Whiteboard photos → concept extraction
- UI screenshots → component relationships
- Foreign-language images → text extraction + translation

## Video and Audio Extraction

Video and audio are transcribed first (Whisper), then treated as docs:

```bash
graphify ./demos --no-viz  # demos/ contains .mp4 .webm files
```

Video/audio model selection is backend/version-dependent. The audited
v0.9.33 `extract` help does not expose a stable `--whisper-model` flag; do not
put that option into automated commands without re-auditing the installed
version.

**Token cost:** Video transcription + semantic pass can be expensive. A 10-minute video ≈ 1,500 words transcript ≈ 2,000 tokens for semantic pass. Warn the user.

## Sensitive File Detection

Graphify automatically skips:
- `.env` files
- Files with `credential`, `secret`, `token`, `password` in the name
- Files in `.git/`, `node_modules/`, `__pycache__/`, `.venv/`, `venv/`
- Files matching `.gitignore` patterns

If a file is wrongly skipped, the detect step reports `skipped_sensitive` count and lists the filenames so you can rename or move them.

## Configuring an API Key (for headless contexts)

If the harness model is not available (for example, in CI), configure a
secret-manager-provided API key in the process environment. Do not paste or
commit a token in a skill, shell history, fixture, or audit artifact:

```bash
# Example only: inject the value from the approved secret manager.
export ANTHROPIC_API_KEY="<injected-at-runtime>"
# or export OPENAI_API_KEY="<injected-at-runtime>"
graphify . --no-viz
```

Graphify will use the configured API for the semantic pass. Code extraction remains local and free.

## Estimating Token Cost

The audited v0.9.33 CLI has no stable `--detect-only` command. Before a large
multimodal build, use a bounded file inventory (`find`, file-size inspection,
and a representative sample), then obtain approval before starting semantic
extraction. Do not treat a hand estimate as Graphify telemetry.

Rule of thumb: ~1 LLM token per 3 words for docs/papers, ~500-2000 tokens per image for vision.
