---
name: ecc-ml-engineering
description: >-
  Research-first ML engineering workflow covering literature-driven recipe
  design, dataset audit, training script preflight, CPU smoke test, GPU
  training, experiment tracking, and budget-bounded hyperparameter sweeps.
  Adapts HuggingFace ml-intern patterns as tool-agnostic guidance — works
  with any GPU provider (Modal, HF Jobs, local, cloud). Use for fine-tuning,
  model training, hyperparameter tuning, dataset validation, ML experiment
  tracking, or when building ML training pipelines. Triggers: "fine-tune",
  "train model", "ML training", "hyperparameter sweep", "experiment
  tracking", "dataset audit", "training preflight", "smoke test", "ML
  recipe", "model provenance", "avalanche model".
---

# ecc-ml-engineering

## When to Use

- Designing a training recipe grounded in ML literature (not guessing hyperparameters)
- Auditing a dataset before training (class imbalance, drift, leakage, schema)
- Preflight-checking a training script before spending GPU budget
- Running a CPU smoke test before submitting a paid GPU job
- Tracking experiments and comparing runs side-by-side
- Running budget-bounded hyperparameter sweeps
- Archiving model provenance (code + papers + config) for reproducibility

## 6-Step Workflow

### Step 1: Research (Literature-Driven Recipe Design)

Find the landmark paper for the task, crawl the citation graph for recent SOTA,
and extract a training recipe from the methodology section.

**Recipe Extraction Template:**
```
Paper: [title, authors, year, DOI/arXiv]
Task: [classification | regression | segmentation | forecasting]
Architecture: [model name, key layers, parameter count]
Dataset: [name, size, train/val/test split]
Recipe:
  - Optimizer: [AdamW | SGD | Lion]
  - Learning rate: [value, schedule (cosine | linear | step)]
  - Batch size: [value, effective batch via gradient accumulation]
  - Epochs: [value, early stopping criteria]
  - Regularization: [dropout rate, weight decay, label smoothing]
  - Data augmentation: [list of transforms]
  - Precision: [fp32 | bf16 | fp16 with grad scaler]
  - Hardware: [GPU type, memory, training time]
Results: [metric name, value, comparison to baseline]
```

**Research Checklist:**
- [ ] Found landmark paper for the task type
- [ ] Crawled 2-hop citation graph for recent improvements
- [ ] Extracted recipe from methodology (not abstract)
- [ ] Verified recipe against current library APIs (not deprecated)
- [ ] Noted at least 2 alternative recipes for comparison

### Step 2: Dataset Audit

Validate the dataset before spending GPU budget.

**Audit Checklist:**
- [ ] **Schema**: Column names, types, and units are consistent
- [ ] **Class balance**: Positive/negative ratio documented; if >10:1, plan mitigation (oversampling, SMOTE, class weights, focal loss)
- [ ] **Missing data**: Percentage of NaN/null per column; imputation strategy defined
- [ ] **Feature drift**: Distribution shift between train and eval (Wasserstein distance, PSI, KS test)
- [ ] **Data leakage**: No future information in training features (temporal, spatial, target leakage)
- [ ] **Label quality**: Manual spot-check of 50+ labels; inter-annotator agreement if applicable
- [ ] **Train/val/test split**: No overlap; temporal split for time-series; spatial split for geospatial
- [ ] **Outliers**: Identified and documented; clipping/winsorization strategy defined
- [ ] **Feature importance**: Quick baseline (Random Forest) to verify signal exists
- [ ] **Dataset version**: Hash or version tag recorded for reproducibility

**Class Imbalance Decision Tree:**
```
Is positive/negative ratio > 10:1?
├── Yes → Use: class_weight='balanced' + focal_loss + oversampling
│         OR: BalancedPositivePatchSampler (for segmentation)
│         OR: SMOTE (for tabular)
└── No (< 10:1) → Use: class_weight='balanced' only
    └── Ratio < 3:1 → No mitigation needed
```

### Step 3: Training Script Preflight

Catch common training bugs before GPU spend.

**Preflight Checklist:**
- [ ] `push_to_hub` / model save call present (not just printing metrics)
- [ ] Gradient clipping configured (`max_norm=1.0` recommended)
- [ ] Learning rate scheduler configured (not constant LR)
- [ ] Early stopping patience set (not training to max epochs blindly)
- [ ] Precision correct: `bf16` for A100/H100, `fp16` for T4/V100 (with grad scaler)
- [ ] `flash_attn` installed if using attention-heavy models
- [ ] Timeout set appropriately (not default 30min for long jobs)
- [ ] Checkpoint saving at regular intervals (not just final)
- [ ] Evaluation metric computed on validation set during training
- [ ] Random seeds set for reproducibility (`torch.manual_seed`, `np.random.seed`)
- [ ] Mixed device handling (no `.to(device)` on tensors already on device)
- [ ] No `print` of full tensors (use `.shape` or `.item()`)
- [ ] Memory cleanup: `torch.cuda.empty_cache()` between epochs if needed

### Step 4: CPU Smoke Test

Run 1 train step + 1 eval step on CPU before paid GPU.

```python
# Smoke test pattern — add to training script
import torch

def smoke_test(model, dataloader, optimizer, criterion):
    """Run 1 train + 1 eval step on CPU. Catches shape bugs, NaN loss."""
    model.cpu()
    model.train()
    batch = next(iter(dataloader))
    inputs, targets = batch[0].cpu(), batch[1].cpu()
    optimizer.zero_grad()
    outputs = model(inputs)
    loss = criterion(outputs, targets)
    loss.backward()
    optimizer.step()

    if torch.isnan(loss) or torch.isinf(loss):
        raise ValueError(f"Smoke test failed: loss is {loss.item()}")

    model.eval()
    with torch.no_grad():
        eval_loss = criterion(model(inputs), targets)

    print(f"Smoke test passed: train_loss={loss.item():.4f}, eval_loss={eval_loss.item():.4f}")
    return True
```

**Smoke Test Checklist:**
- [ ] Forward pass completes without shape errors
- [ ] Loss is finite (not NaN, not Inf)
- [ ] Backward pass completes (gradients flow)
- [ ] Optimizer step updates weights
- [ ] Eval pass completes
- [ ] Model save/load roundtrip works

### Step 5: Train

Submit the full training job after smoke test passes.

**Training Monitoring Checklist:**
- [ ] Loss decreasing monotonically (or with expected oscillation)
- [ ] Validation metric improving (not just training loss)
- [ ] No NaN/Inf in loss curve
- [ ] GPU utilization > 80% (check `nvidia-smi`)
- [ ] Memory usage stable (no leak — check for growing allocation)
- [ ] Checkpoints saved at expected intervals
- [ ] Training time within budget estimate
- [ ] Early stopping triggered if validation metric plateaus

### Step 6: Evaluate and Archive

**Evaluation Checklist:**
- [ ] Metrics computed on held-out test set (not validation)
- [ ] Per-class metrics (not just macro average) for imbalanced data
- [ ] Confusion matrix generated
- [ ] ROC curve / PR curve generated for binary tasks
- [ ] Error analysis: inspect 20+ misclassified examples
- [ ] Compare to baseline (previous model or simple heuristic)

**Model Provenance Checklist:**
- [ ] Git commit hash of training code recorded
- [ ] Paper references that informed the recipe recorded
- [ ] Dataset version/hash recorded
- [ ] Full hyperparameter config saved (not just defaults)
- [ ] Training log saved (loss curve, metrics per epoch)
- [ ] Hardware used recorded (GPU type, memory, training time)
- [ ] Random seed recorded
- [ ] Model artifact saved with version tag

## Hyperparameter Sweep Pattern

Budget-bounded sweep: propose → train → evaluate → keep-best → iterate.

```
1. Define search space: {lr: [1e-4, 5e-4, 1e-3], dropout: [0.1, 0.15, 0.2], ...}
2. Set budget: max_jobs=20, max_cost=$50, max_wallclock=4h
3. Start with random search (not grid) for high-dimensional spaces
4. After 5 jobs: analyze which dimensions matter most (feature importance)
5. Narrow search to promising region
6. Keep best model only if it beats current best by > 1% on target metric
7. Stop when: target metric reached, budget exhausted, or diminishing returns
```

**Sweep Logging:**
```
Run | lr     | dropout | epochs | val_metric | cost  | kept?
1   | 1e-3   | 0.15   | 50     | 0.72       | $2.1  | ✓ (first)
2   | 5e-4   | 0.10   | 50     | 0.68       | $2.0  | ✗
3   | 1e-4   | 0.20   | 50     | 0.71       | $2.2  | ✗
4   | 5e-4   | 0.15   | 80     | 0.74       | $3.1  | ✓ (beats #1)
```

## Integration

- **Router**: `ai-ml-skills` and `scientific-skills` domain routers
- **Production deployment**: Use `mle-workflow` for model deployment, monitoring, rollback, and canary releases. This skill covers the research-to-training phase; `mle-workflow` covers the deployment-to-production phase.
- **Model interpretability**: Use `shap` for SHAP value computation, feature importance plots, and model explainability
- **ML libraries**: Use `scikit-learn` for classical ML patterns, `pytorch-patterns` for deep learning training patterns, `pytorch-lightning` for scalable training
- **Security**: Use `ecc-owasp-security` AG01-AG10 for ML model security (adversarial inputs, model poisoning, prompt injection against ML APIs)
- **Multi-model**: Use `ecc-multi-model-blindspot` for cross-model ML recipe and training review
- **Verification**: Use `ecc-verify` to gate model release on evaluation criteria

## Auto-Revocation

This skill has **no external tool dependencies**. All patterns are markdown
guidance and checklists.

- **Core tools** (never gate): `grep`, `cat`, `head`, `diff` — used for code review
- **Advisory tools**: `python3`, `torch`, `hf` CLI, `gh` CLI — if available,
  use for automated checks; if absent, fall back to manual checklists
- Wrap automated tool calls with `2>/dev/null` and `|| true`
- Never block on tool availability — degrade to manual instructions

## Cross-IDE Compatibility

Pure markdown skill — no runtime dependencies:
- **Windsurf**: SKILL.md auto-discovered
- **Devin**: SKILL.md injected as context
- **Autogravity**: SKILL.md read as agent capability
- **Codex**: `agents/openai.yaml` provides agent definition

## Upstream Source

Adapted from [krasserm/ml-plugins](https://github.com/krasserm/ml-plugins) (Apache 2.0) —
a Claude Code port of HuggingFace's [ml-intern](https://github.com/huggingface/ml-intern).
Original requires `hf` CLI and HF Jobs credits; this port is tool-agnostic and works
with any GPU provider (Modal.com, local GPU, HF Jobs, cloud).
