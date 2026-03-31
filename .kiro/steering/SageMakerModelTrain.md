---
inclusion: fileMatch
fileMatchPattern: "*sagemaker*,*train*,*hf*,*huggingface*"
---

# SageMaker Model Training & HuggingFace Push

## Project Context
This is an **educational, fan-made** ML project for Flesh and Blood TCG card balance prediction.
NOT affiliated with Legend Story Studios.

## Training Pipeline
- Model: `sklearn.pipeline.Pipeline(StandardScaler → RandomForestRegressor)`
- Target: `avg_win_rate` (regression, 0-1)
- Features: 19 columns (theme counts, cost curve, card types, game metrics, expert scores)
- Data: headerless CSV, target in column 0 (SageMaker convention)

## Two Training Modes
1. **Local** — trains on the dev machine, pushes to HuggingFace Hub
2. **SageMaker** — launches a training job on `ml.m5.large`, downloads artifacts from S3, pushes to HF Hub

## Key Files
- `scripts/train_and_push_to_hf.py` — main entry point
- `scripts/sagemaker_integration.py` — SageMaker orchestrator (existing)
- `scripts/data_analytics.py` — data prep & export
- `data/processed/sagemaker_training_data_*.csv` — training data

## Environment Variables (.env)
- `SAGEMAKER_ROLE` — required for SageMaker mode
- `AWS_REGION` — defaults to us-east-1
- `HF_TOKEN` — required for HuggingFace push

## Usage
```bash
# Local train + push
python scripts/train_and_push_to_hf.py --mode local --hf_repo USER/teklo-card-balance

# SageMaker train + push
python scripts/train_and_push_to_hf.py --mode sagemaker --hf_repo USER/teklo-card-balance
```
