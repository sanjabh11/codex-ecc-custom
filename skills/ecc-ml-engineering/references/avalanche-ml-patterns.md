# Avalanche Forecasting ML Patterns

ML patterns specific to the Avalanche Insight Hub codebase — time-series
prediction, SAR change detection, calibrated probability, and snowpack
physics-ML hybrids.

---

## Model Architecture Summary

| Model | Type | File | Role |
|-------|------|------|------|
| Random Forest + TreeSHAP | Calibrated surrogate | `train_model.py` | Reference path (production) |
| MTS-LSTM (BranchedMTSLSTM) | Multi-temporal-scale LSTM | `lstm_model.py` | Shadow candidate |
| SAR U-Net | Semantic segmentation | `sar_unet_training.py` | Shadow candidate |
| COSIPY | Snowpack physics model | `backend/common/` | Physics proxy |

---

## Random Forest + TreeSHAP (Reference Path)

### Recipe Template

```
Paper: Avalanche susceptibility mapping using RF + SHAP
Task: Binary classification (avalanche/no-avalanche)
Architecture: RandomForestClassifier(n_estimators=500, max_depth=None)
Dataset: Historical avalanche events + weather/terrain features
Recipe:
  - Optimizer: Not applicable (tree-based)
  - Feature importance: TreeSHAP (shap.TreeExplainer)
  - Calibration: Platt scaling or isotonic regression
  - Class balance: class_weight='balanced' or BalancedRandomForest
  - Evaluation: Peirce Skill Score (PSS), Brier Score, ROC-AUC
  - Hardware: CPU (no GPU needed)
Results: PSS > 0.3 is operational threshold for avalanche forecasting
```

### Key Patterns from Your Codebase

- `peirce_skill_score_max` in `backend/models/surrogate_rf.py` — threshold optimization
- `wasserstein_distance` in `train_model.py` — feature drift detection
- `label_governance.py` — auto-label eligibility checks before training
- `continuous_learning.py` — auto-label audit trail
- `cold_start_config.py` — synthetic data generation for cold start

### Audit Checklist for RF Training

- [ ] `FEATURE_COLUMNS` from `backend/common/features.py` matches dataset schema
- [ ] `feature_columns_hash` and `label_schema_hash` from `schema_drift.py` recorded
- [ ] `GOVERNANCE_VERSION` from `label_governance.py` logged in artifact
- [ ] PSS computed on held-out test set (not validation)
- [ ] SHAP summary plot generated for top 20 features
- [ ] Calibration curve generated (reliability diagram)
- [ ] Cold start synthetic frame quality verified (if using cold start mode)

---

## MTS-LSTM (Shadow Candidate)

### Recipe Template

```
Paper: Multi-Temporal-Scale LSTM for time-series prediction
Task: Sequence forecasting (avalanche probability from weather sequences)
Architecture: BranchedMTSLSTM (daily + hourly branches)
Dataset: Weather sequences + terrain features
Recipe:
  - Optimizer: Adam (lr=0.001, default from code)
  - Batch size: configurable via env
  - Epochs: 50 (MTS_LSTM_EPOCHS), early stopping patience=7
  - Dropout: 0.15 (MTS_DROPOUT)
  - Sequence length: DEFAULT_DAILY_STEPS, DEFAULT_HOURLY_STEPS
  - Precision: fp32 (or bf16 if A100 available)
  - Hardware: GPU (Modal.com L40S or similar)
Results: Compare PSS against RF reference path
```

### Literature Research Priorities

1. **Multi-temporal-scale architectures**: Papers on dual-timescale LSTMs for
   environmental prediction
2. **Avalanche prediction with deep learning**: Recent papers on neural
   approaches to avalanche forecasting
3. **Transfer learning for weather**: Pre-trained weather models that could
   be fine-tuned with LoRA instead of training from scratch
4. **Sequence length optimization**: Papers on optimal lookback windows for
   avalanche prediction (your `DEFAULT_DAILY_STEPS` and `DEFAULT_HOURLY_STEPS`)

### Preflight Checklist for LSTM Training

- [ ] `BranchedMTSLSTM` model loads without import errors
- [ ] `build_mts_lstm_dataloaders` produces correct shapes (batch, seq_len, features)
- [ ] `SequenceBranches` config matches data loader output
- [ ] `TRAIN_MTS_LSTM_HEAD` flag set correctly (env vs code)
- [ ] Early stopping config: `MTS_LSTM_MIN_EPOCHS_BEFORE_EARLY_STOPPING=10`
- [ ] Gradient clipping enabled (add if missing: `torch.nn.utils.clip_grad_norm_`)
- [ ] Learning rate scheduler (add if missing: cosine or ReduceLROnPlateau)
- [ ] `torch.cuda.empty_cache()` called between epochs if memory grows

### Smoke Test for LSTM

```python
# Add to lstm_model.py training loop
def lstm_smoke_test(model, train_loader, optimizer, criterion):
    """1 train + 1 eval step on CPU."""
    model.cpu()
    model.train()
    batch = next(iter(train_loader))
    # Unpack based on your data loader format
    inputs, targets = batch
    inputs = {k: v.cpu() for k, v in inputs.items()} if isinstance(inputs, dict) else inputs.cpu()
    targets = targets.cpu()
    optimizer.zero_grad()
    outputs = model(inputs)
    loss = criterion(outputs, targets)
    loss.backward()
    optimizer.step()
    assert not torch.isnan(loss), f"NaN loss: {loss.item()}"
    print(f"LSTM smoke test passed: loss={loss.item():.4f}")
```

---

## SAR U-Net (Shadow Candidate)

### Recipe Template

```
Paper: U-Net for SAR change detection in avalanche terrain
Task: Binary semantic segmentation (avalanche debris / no-avalanche)
Architecture: U-Net with SAR_DEFAULT_INPUT_CHANNELS
Dataset: Sentinel-1 SAR image patches with truth masks
Recipe:
  - Optimizer: Adam (lr=1e-4, DEFAULT_TRAIN_SAR_LR)
  - Batch size: 8 (DEFAULT_TRAIN_SAR_BATCH_SIZE)
  - Epochs: 8 (DEFAULT_TRAIN_SAR_EPOCHS)
  - Patience: 4 (DEFAULT_TRAIN_SAR_PATIENCE)
  - Loss: DiceLoss (eps=1e-6) + BCE
  - F-beta: 1.5 (DEFAULT_F_BETA, favors recall)
  - Precision floor: 0.05 (DEFAULT_PRECISION_FLOOR)
  - Threshold grid: np.linspace(0.05, 0.95, 19)
  - Augmentation: BalancedPositivePatchSampler
  - Hardware: GPU (Modal.com, A100/L40S recommended)
Results: F1, IoU, precision, recall at optimal threshold
```

### Preflight Checklist for U-Net Training

- [ ] `SarPatchDataset` loads patches with correct shapes
- [ ] `BalancedPositivePatchSampler` produces balanced batches
- [ ] `compute_sar_normalization` stats saved with model
- [ ] `DiceLoss` handles empty mask case (`ignore_empty` flag)
- [ ] `DEFAULT_MAX_VALIDATION_POSITIVE_RATE_RATIO=20.0` not exceeded
- [ ] Post-processing recall floor (0.50) applied to predictions
- [ ] Model family normalized via `normalize_model_family()`
- [ ] `segmentation-models-pytorch==0.5.0` installed and compatible
- [ ] `timm==1.0.27` installed (encoder backbone dependency)

### Smoke Test for U-Net

```python
def sar_smoke_test(model, dataloader, criterion):
    """1 train + 1 eval step on CPU for SAR U-Net."""
    model.cpu()
    model.train()
    images, masks = next(iter(dataloader))
    images, masks = images.cpu(), masks.cpu()
    outputs = model(images)
    loss = criterion(outputs, masks)
    loss.backward()
    assert not torch.isnan(loss), f"NaN Dice loss: {loss.item()}"
    # Check output shape matches mask shape
    assert outputs.shape == masks.shape, f"Shape mismatch: {outputs.shape} vs {masks.shape}"
    print(f"SAR U-Net smoke test passed: Dice loss={loss.item():.4f}")
```

---

## Evaluation Patterns

### Metrics for Avalanche Forecasting

| Metric | Code Location | Threshold | Notes |
|--------|---------------|-----------|-------|
| Peirce Skill Score (PSS) | `surrogate_rf.py` | > 0.3 = operational | Primary metric for RF |
| Brier Score | `evaluation.py` | < 0.2 = good | Probability calibration |
| ROC-AUC | `evaluation.py` | > 0.75 = good | Discrimination ability |
| F1 / Precision / Recall | `evaluation.py` | Context-dependent | Per-class for imbalance |
| F-beta (β=1.5) | `sar_unet_training.py` | Favors recall | For SAR detection |
| Dice / IoU | `sar_unet_training.py` | > 0.5 = acceptable | Segmentation quality |

### Evaluation Checklist

- [ ] Metrics computed on held-out test set (not validation)
- [ ] Per-region metrics (not just global) — `pir_panjal`, other regions
- [ ] Temporal split used (no future leakage) — train on past seasons, test on future
- [ ] PSS computed at multiple probability thresholds (not just 0.5)
- [ ] Brier score computed on calibrated probabilities (not raw RF scores)
- [ ] Confusion matrix per region
- [ ] Comparison to DGRE baseline (if available)

---

## DGRE-Governed Benchmark Requirements

For the benchmark to be DGRE-approved, model provenance must include:

- [ ] Git commit hash of exact training code
- [ ] Paper references for the recipe (with DOIs)
- [ ] Dataset version + hash (training and evaluation)
- [ ] Full hyperparameter config (env vars + defaults)
- [ ] Training log (loss curve, metrics per epoch)
- [ ] Hardware used (GPU type, memory, wall-clock time)
- [ ] Random seed
- [ ] Model artifact with version tag
- [ ] Evaluation script version
- [ ] Reviewer sign-off (scientist release decision)

---

## Continuous Learning Integration

Your codebase has `continuous_learning.py` and `label_governance.py`. The ML
engineering skill's dataset audit step can validate auto-labeled data:

1. **Before training**: Run dataset audit on auto-labeled rows
2. **Label quality check**: Sample 50+ auto-labeled rows for manual review
3. **Governance version**: Verify `GOVERNANCE_VERSION` is current
4. **Auto-label audit trail**: Verify `get_auto_label_audit_trail()` returns
   complete provenance for each auto-labeled example
5. **Schema drift**: Verify `feature_columns_hash` and `label_schema_hash`
   match between auto-labeling time and training time

---

## Time-Series Dataset Audit Patterns

Avalanche forecasting uses time-series data (weather sequences, snowpack
observations, seismic activity). Standard dataset audit must be extended
with time-series-specific checks.

### Stationarity Testing

- [ ] **ADF test** (Augmented Dickey-Fuller): p < 0.05 indicates stationary
- [ ] **KPSS test**: p > 0.05 indicates stationary (confirm ADF result)
- [ ] If non-stationary: apply differencing or log transform, re-test
- [ ] Document which features are non-stationary (temperature, snow depth)

```python
from statsmodels.tsa.stattools import adfuller, kpss

def check_stationarity(series, name="feature"):
    adf_p = adfuller(series.dropna())[1]
    kpss_p = kpss(series.dropna())[1]
    stationary = adf_p < 0.05 and kpss_p > 0.05
    print(f"{name}: ADF p={adf_p:.4f}, KPSS p={kpss_p:.4f}, stationary={stationary}")
    return stationary
```

### Autocorrelation Analysis

- [ ] **ACF plot**: Check for significant lags (weather data has 24h and 365d cycles)
- [ ] **PACF plot**: Identify direct lag relationships for feature engineering
- [ ] **Ljung-Box test**: p < 0.05 indicates autocorrelation present
- [ ] Document lag structure for LSTM sequence length selection

### Seasonal Decomposition

- [ ] **STL decomposition**: Trend + Seasonal + Residual components
- [ ] Document seasonal period (24h for daily, 365d for annual)
- [ ] Check residual for remaining structure (should be white noise)
- [ ] Use seasonal indices as features if seasonality is strong

### Temporal Leakage Check

- [ ] **No future data in training features**: Verify `train_end_date < val_start_date < test_start_date`
- [ ] **No rolling features computed on full dataset**: Window features must use only past data
- [ ] **No station metadata from future**: Station installation dates checked
- [ ] **Cross-validation is temporal**: Use `TimeSeriesSplit`, not `KFold`
- [ ] **Backtesting is walk-forward**: Simulate real forecasting conditions

---

## Model Comparison Patterns

When comparing RF vs LSTM vs U-Net against the DGRE baseline, use
statistically rigorous tests — not just "our metric is higher."

### Statistical Significance Tests

| Comparison Type | Test | When to Use | Code Pattern |
|----------------|------|-------------|--------------|
| Binary classification | **McNemar's test** | Compare RF vs LSTM predictions on same test set | `statsmodels.stats.contingency_tables.mcnemar` |
| Probability forecasts | **Diebold-Mariano test** | Compare Brier scores of two forecast models | Custom implementation or `arch` package |
| Multiple metrics | **Paired t-test** | Compare per-region metrics across models | `scipy.stats.ttest_rel` |
| Non-parametric | **Wilcoxon signed-rank** | When normality assumption fails | `scipy.stats.wilcoxon` |
| Multiple models | **Friedman test + Nemenyi post-hoc** | Rank N models across K regions | `scipy.stats.friedmanchisquare` |

### McNemar's Test (Binary Classification)

```python
from statsmodels.stats.contingency_tables import mcnemar

def compare_models_mcnemar(y_true, preds_a, preds_b, model_a_name, model_b_name):
    """Test if two models have significantly different error patterns."""
    correct_a = (preds_a == y_true)
    correct_b = (preds_b == y_true)
    # Contingency table: [both correct, A correct B wrong, A wrong B correct, both wrong]
    b_c = ((correct_a) & (~correct_b)).sum()  # A correct, B wrong
    c_b = ((~correct_a) & (correct_b)).sum()  # A wrong, B correct
    table = [[0, b_c], [c_b, 0]]
    result = mcnemar(table, exact=True)
    print(f"{model_a_name} vs {model_b_name}: p={result.pvalue:.4f}")
    print(f"  {'Significant' if result.pvalue < 0.05 else 'Not significant'} difference")
    return result
```

### Diebold-Mariano Test (Forecast Accuracy)

```python
import numpy as np
from scipy import stats

def diebold_mariano_test(errors_a, errors_b, loss='squared'):
    """Test if two forecast models have significantly different accuracy."""
    if loss == 'squared':
        loss_a = np.square(errors_a)
        loss_b = np.square(errors_b)
    elif loss == 'absolute':
        loss_a = np.abs(errors_a)
        loss_b = np.abs(errors_b)
    d = loss_a - loss_b
    dm_stat = d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))
    p_value = 2 * stats.norm.sf(np.abs(dm_stat))
    return dm_stat, p_value
```

### Model Comparison Report Template

```
## Model Comparison Report

| Model | PSS | Brier | ROC-AUC | F1 | Rank |
|-------|-----|-------|---------|-----|------|
| DGRE Baseline | 0.31 | 0.18 | 0.78 | 0.45 | 4 |
| Random Forest + SHAP | 0.35 | 0.15 | 0.82 | 0.48 | 2 |
| MTS-LSTM | 0.37 | 0.14 | 0.84 | 0.50 | 1 |
| SAR U-Net | 0.33 | 0.16 | 0.80 | 0.46 | 3 |

### Statistical Significance
- RF vs Baseline: McNemar p=0.032 (significant)
- LSTM vs RF: McNemar p=0.085 (not significant)
- LSTM vs Baseline: McNemar p=0.011 (significant)
- Friedman test: p=0.004 (significant differences exist)
- Nemenyi post-hoc: LSTM > Baseline (p=0.012)

### Recommendation
Deploy MTS-LSTM as new reference path. RF remains as interpretable fallback.
SAR U-Net not significantly better than baseline — defer.
```

---

## CI/CD for ML Pipelines

GitHub Actions patterns for avalanche forecast model training and evaluation.

### Training Pipeline CI

```yaml
# .github/workflows/ml-training-ci.yml
name: ML Training CI
on:
  pull_request:
    paths: ['backend/**/*.py', 'backend/**/*.in']
jobs:
  preflight:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install deps
        run: pip install -r backend/requirements-core.in
      - name: Dataset audit
        run: python3 scripts/dataset_audit.py --config config/training.yaml
      - name: Preflight check
        run: python3 scripts/preflight_check.py --model rf --config config/rf.yaml
      - name: CPU smoke test
        run: python3 scripts/smoke_test.py --model rf --steps 1
```

### Model Release Gate

```yaml
# .github/workflows/model-release-gate.yml
name: Model Release Gate
on:
  push:
    tags: ['model-v*']
jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run evaluation
        run: python3 backend/evaluation.py --model ${{ github.ref_name }}
      - name: Check PSS threshold
        run: |
          PSS=$(python3 -c "import json; print(json.load(open('results/metrics.json'))['pss'])")
          if (( $(echo "$PSS < 0.3" | bc -l) )); then
            echo "PSS $PSS below 0.3 threshold — blocking release"
            exit 1
          fi
      - name: Compare to baseline
        run: python3 scripts/compare_models.py --baseline dgre --candidate ${{ github.ref_name }}
```
