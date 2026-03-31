"""
Teklovossen Card Balance Predictor — SageMaker Train & Push to HuggingFace Hub

Educational project: Fan-made ML model for Flesh and Blood TCG card balance prediction.
This is NOT affiliated with Legend Story Studios.

Two modes:
  1. --mode sagemaker  : Train on SageMaker, download artifacts from S3, push to HF Hub
  2. --mode local      : Train locally (same pipeline), push to HF Hub

Usage:
    # Local training + HuggingFace push
    python scripts/train_and_push_to_hf.py --mode local --hf_repo YOUR_USER/teklo-card-balance

    # SageMaker training + HuggingFace push
    python scripts/train_and_push_to_hf.py --mode sagemaker --hf_repo YOUR_USER/teklo-card-balance

Prerequisites:
    pip install huggingface_hub scikit-learn pandas numpy boto3 sagemaker python-dotenv joblib
"""

import argparse
import json
import os
import sys
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

load_dotenv()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
FEATURE_COLUMNS = [
    "AI", "Nano", "Quantum", "Base",
    "0_cost", "1_cost", "2_cost", "3_cost", "4_plus_cost",
    "equipment", "item", "action",
    "avg_turns", "avg_evos", "avg_teklo_energy",
    "avg_nanite_counters", "avg_quantum_charges",
    "consistency_score", "avg_expert_balance_score",
]
TARGET_COLUMN = "avg_win_rate"


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def find_latest_training_data(data_dir: str = "data/processed") -> str:
    """Find the most recent sagemaker_training_data CSV."""
    data_path = Path(data_dir)
    candidates = sorted(data_path.glob("sagemaker_training_data_*.csv"), reverse=True)
    if not candidates:
        raise FileNotFoundError(f"No sagemaker_training_data_*.csv in {data_dir}")
    print(f"[data] Using: {candidates[0]}")
    return str(candidates[0])


def load_training_data(csv_path: str):
    """Load headerless CSV (SageMaker convention: col 0 = target)."""
    df = pd.read_csv(csv_path, header=None)
    y = df.iloc[:, 0].values.astype(np.float64)
    X = df.iloc[:, 1:].values.astype(np.float64)
    X = np.nan_to_num(X, nan=0.0)
    y = np.nan_to_num(y, nan=float(np.nanmean(y)))
    print(f"[data] {X.shape[0]} samples, {X.shape[1]} features")
    return X, y


# ---------------------------------------------------------------------------
# Local training
# ---------------------------------------------------------------------------

def train_local(X, y):
    """Train the same sklearn pipeline used in the SageMaker training script."""
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("model", RandomForestRegressor(
            n_estimators=20, max_depth=5, random_state=42, n_jobs=-1,
        )),
    ])
    pipeline.fit(X, y)

    preds = pipeline.predict(X)
    cv_folds = min(3, max(2, len(y) // 2))
    cv = cross_val_score(pipeline, X, y, cv=cv_folds, scoring="r2")

    metrics = {
        "train_r2": round(float(r2_score(y, preds)), 4),
        "train_mse": round(float(mean_squared_error(y, preds)), 4),
        "train_mae": round(float(mean_absolute_error(y, preds)), 4),
        "cv_r2_mean": round(float(cv.mean()), 4),
        "cv_r2_std": round(float(cv.std()), 4),
        "n_samples": int(X.shape[0]),
        "n_features": int(X.shape[1]),
        "training_mode": "local",
    }
    print(f"[train] R²={metrics['train_r2']}  CV R²={metrics['cv_r2_mean']}±{metrics['cv_r2_std']}")
    return pipeline, metrics


# ---------------------------------------------------------------------------
# SageMaker training
# ---------------------------------------------------------------------------

def train_on_sagemaker(data_dir: str = "data/processed"):
    """
    Launch a SageMaker training job using the existing orchestrator,
    wait for completion, download model artifacts, and return the pipeline.
    """
    import boto3
    import sagemaker
    from sagemaker.sklearn.estimator import SKLearn
    from sagemaker.inputs import TrainingInput

    # Re-use the project's existing data-prep logic
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from data_analytics import TekloDataAnalyzer

    role = os.environ.get("SAGEMAKER_ROLE")
    if not role:
        raise ValueError("Set SAGEMAKER_ROLE in .env (see .env.example)")

    region = os.environ.get("AWS_REGION", "us-east-1")
    sess = sagemaker.Session(boto_session=boto3.Session(region_name=region))
    bucket = sess.default_bucket()

    # --- prepare & upload data ---
    analyzer = TekloDataAnalyzer(str(Path(data_dir).parent))
    analyzer.load_simulation_data()
    analyzer.load_ml_data()
    export_path = analyzer.export_for_sagemaker(TARGET_COLUMN)

    s3_key = f"teklo-card-balance/training/training_data.csv"
    s3_uri = sess.upload_data(export_path, bucket=bucket, key_prefix="teklo-card-balance/training")
    # s3_uri points to the directory
    print(f"[sagemaker] Data uploaded -> s3://{bucket}/{s3_key}")

    # --- training script (reuse existing one) ---
    scripts_dir = Path(__file__).resolve().parent / "training_scripts"
    if not (scripts_dir / "balance_predictor_train.py").exists():
        # Generate it via the orchestrator helper
        from sagemaker_integration import TekloSageMakerOrchestrator
        orch = TekloSageMakerOrchestrator.__new__(TekloSageMakerOrchestrator)
        orch.create_training_scripts()

    # --- launch job ---
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    job_name = f"teklo-balance-{ts}"

    estimator = SKLearn(
        entry_point="balance_predictor_train.py",
        source_dir=str(scripts_dir),
        role=role,
        instance_type="ml.m5.large",
        instance_count=1,
        framework_version="1.2-1",
        py_version="py3",
        sagemaker_session=sess,
        max_run=3600,
    )

    print(f"[sagemaker] Starting training job: {job_name}")
    estimator.fit(
        inputs={"training": TrainingInput(s3_data=s3_uri, content_type="text/csv")},
        job_name=job_name,
        wait=True,   # block until done
    )
    print(f"[sagemaker] Training complete.")

    # --- download model artifacts ---
    model_data = estimator.model_data  # s3://bucket/.../model.tar.gz
    print(f"[sagemaker] Model artifacts: {model_data}")

    tmpdir = tempfile.mkdtemp()
    local_tar = os.path.join(tmpdir, "model.tar.gz")
    s3 = boto3.client("s3", region_name=region)

    # parse s3 uri
    parts = model_data.replace("s3://", "").split("/", 1)
    s3.download_file(parts[0], parts[1], local_tar)

    with tarfile.open(local_tar, "r:gz") as tar:
        tar.extractall(tmpdir)

    # load the model
    model_path = os.path.join(tmpdir, "model.joblib")
    if not os.path.exists(model_path):
        model_path = os.path.join(tmpdir, "model.pkl")
    pipeline = joblib.load(model_path)
    print(f"[sagemaker] Model loaded from artifacts")

    # compute metrics on local data for the model card
    csv_path = find_latest_training_data(data_dir)
    X, y = load_training_data(csv_path)
    preds = pipeline.predict(X)
    cv_folds = min(3, max(2, len(y) // 2))
    cv = cross_val_score(pipeline, X, y, cv=cv_folds, scoring="r2")

    metrics = {
        "train_r2": round(float(r2_score(y, preds)), 4),
        "train_mse": round(float(mean_squared_error(y, preds)), 4),
        "train_mae": round(float(mean_absolute_error(y, preds)), 4),
        "cv_r2_mean": round(float(cv.mean()), 4),
        "cv_r2_std": round(float(cv.std()), 4),
        "n_samples": int(X.shape[0]),
        "n_features": int(X.shape[1]),
        "training_mode": "sagemaker",
        "sagemaker_job": job_name,
        "instance_type": "ml.m5.large",
    }
    return pipeline, metrics


# ---------------------------------------------------------------------------
# HuggingFace push
# ---------------------------------------------------------------------------

MODEL_CARD = """\
---
license: mit
tags:
  - tabular-regression
  - sklearn
  - card-game
  - flesh-and-blood
  - game-balance
  - educational
library_name: sklearn
pipeline_tag: tabular-regression
datasets:
  - custom
metrics:
  - r2
  - mse
  - mae
---

# FAB Prediction Model - Teklovossen Card Balance

> **Educational Project - NOT affiliated with Legend Story Studios or the official Flesh and Blood game.**

A scikit-learn model that predicts **win rates** for custom Teklovossen (Mechanologist)
card decks in the [Flesh and Blood](https://fabtcg.com/) trading card game.

This project explores how machine learning can be applied to game balance analysis
using simulated gameplay data from a custom game engine.

## Model

| Detail | Value |
|--------|-------|
| Type | `Pipeline(StandardScaler + RandomForestRegressor)` |
| Task | Tabular regression - predict average win rate |
| Framework | scikit-learn {sklearn_version} |
| Training data | Simulated gameplay (custom engine) |

## Features (inputs)

| # | Feature | Description |
|---|---------|-------------|
| 0 | AI | AI-themed card count |
| 1 | Nano | Nano-themed card count |
| 2 | Quantum | Quantum-themed card count |
| 3 | Base | Base card count |
| 4-8 | 0_cost to 4_plus_cost | Cost curve distribution |
| 9-11 | equipment, item, action | Card type counts |
| 12 | avg_turns | Average game length |
| 13 | avg_evos | Average Evo equipment used |
| 14 | avg_teklo_energy | Avg Teklo Energy generated |
| 15 | avg_nanite_counters | Avg Nanite counters |
| 16 | avg_quantum_charges | Avg Quantum charges |
| 17 | consistency_score | Deck consistency (0-1) |
| 18 | avg_expert_balance_score | Expert balance score (1-10) |

## Output

`avg_win_rate` - float in [0, 1] representing predicted deck win rate.

## Metrics

| Metric | Value |
|--------|-------|
| Train R2 | {train_r2} |
| CV R2 (mean +/- std) | {cv_r2_mean} +/- {cv_r2_std} |
| Train MSE | {train_mse} |
| Train MAE | {train_mae} |
| Samples | {n_samples} |
| Features | {n_features} |

## Quick Start

```python
from huggingface_hub import hf_hub_download
import joblib, numpy as np

path = hf_hub_download(repo_id="{repo_id}", filename="model.joblib")
model = joblib.load(path)

# Example: a Nano-focused deck
features = np.array([[9,0,0,2, 5,2,1,0, 9,9,12, 0.6, 9.4,13.6,7.3, 0.74, 6.7, 0,0]])
print(model.predict(features))  # predicted win rate
```

## About This Project

This is a fan-made educational project exploring ML for TCG game balance.
The model is trained on simulated gameplay data from a custom Flesh and Blood
game engine featuring Teklovossen, a Mechanologist hero with custom Evo cards
across four tech themes: AI, Nano, Quantum, and Biomancy.

## Limitations

- Trained on **simulated** data, not real tournament results
- Small dataset ({n_samples} samples) - treat predictions as rough estimates
- Simplified card mechanics in the simulation engine
- Fan-made cards only - does not cover the official card pool

## License

MIT
"""


def push_to_huggingface(pipeline, metrics: dict, repo_id: str):
    """Upload model + model card to HuggingFace Hub using login() + upload_folder()."""
    from huggingface_hub import login, upload_folder
    import sklearn

    # Interactive login — uses cached token if already logged in
    login()

    with tempfile.TemporaryDirectory() as tmpdir:
        # model artifact
        joblib.dump(pipeline, os.path.join(tmpdir, "model.joblib"))

        # config
        config = {
            "model_type": "sklearn-pipeline",
            "task": "tabular-regression",
            "target": TARGET_COLUMN,
            "features": FEATURE_COLUMNS[:pipeline.named_steps["model"].n_features_in_],
            "sklearn_version": sklearn.__version__,
            "trained_at": datetime.utcnow().isoformat(),
            "metrics": metrics,
            "educational": True,
            "disclaimer": "Fan-made project. NOT affiliated with Legend Story Studios.",
        }
        with open(os.path.join(tmpdir, "config.json"), "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        # model card
        card = MODEL_CARD.format(
            sklearn_version=sklearn.__version__,
            repo_id=repo_id,
            **{k: v for k, v in metrics.items()
               if k in ("train_r2", "train_mse", "train_mae", "cv_r2_mean", "cv_r2_std", "n_samples", "n_features")},
        )
        with open(os.path.join(tmpdir, "README.md"), "w", encoding="utf-8") as f:
            f.write(card)

        # Push using the simple pattern from HF docs
        upload_folder(
            folder_path=tmpdir,
            repo_id=repo_id,
            repo_type="model",
        )

    print(f"\n[OK] Pushed to https://huggingface.co/{repo_id}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Train Teklovossen card balance model & push to HuggingFace Hub"
    )
    parser.add_argument("--mode", choices=["local", "sagemaker"], default="local",
                        help="Training mode: 'local' or 'sagemaker' (default: local)")
    parser.add_argument("--data_dir", default="data/processed",
                        help="Dir with sagemaker_training_data CSVs")
    parser.add_argument("--hf_repo", default="4math/FAB_Prediction_Model",
                        help="HuggingFace repo (default: 4math/FAB_Prediction_Model)")
    parser.add_argument("--save_local", default=None,
                        help="Also save model locally to this path")
    args = parser.parse_args()

    # --- Train ---
    if args.mode == "sagemaker":
        print("=" * 60)
        print("  SageMaker Training -> HuggingFace Hub")
        print("=" * 60)
        pipeline, metrics = train_on_sagemaker(args.data_dir)
    else:
        print("=" * 60)
        print("  Local Training -> HuggingFace Hub")
        print("=" * 60)
        csv_path = find_latest_training_data(args.data_dir)
        X, y = load_training_data(csv_path)
        pipeline, metrics = train_local(X, y)

    # --- Save locally ---
    if args.save_local:
        os.makedirs(os.path.dirname(args.save_local) or ".", exist_ok=True)
        joblib.dump(pipeline, args.save_local)
        print(f"[local] Saved to {args.save_local}")

    # --- Push to HuggingFace ---
    push_to_huggingface(pipeline, metrics, args.hf_repo)


if __name__ == "__main__":
    main()
