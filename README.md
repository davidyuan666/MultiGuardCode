# MultiGuardCode: A Multi-Tier Error Suppression Framework for LLM Code Generation

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)

Source code and experiments for the paper **"MultiGuardCode: A Multi-Tier Error Suppression Framework for LLM Code Generation"**.

## Overview

MultiGuardCode applies four sequential error suppression stages to the LLM code generation pipeline. Each stage operates at a different granularity, from lightweight output filtering to global generation-parameter control:

| Tier | Mechanism | Description |
|---|---|---|
| T1 | Output Quality Filter | Rejects malformed or degenerate outputs early |
| T2 | AST Structure Validation | Extracts code and validates syntax via AST parsing |
| T3 | Test-Driven Repair | Executes code against test cases; regenerates on failure with failure-aware prompts |
| T4 | Defect Density Monitor | Tracks cumulative failure rate and switches to conservative generation when crossing threshold |

The framework is model-agnostic, requires no training, and can be deployed as a post-processing layer on any LLM API.

## Quick Start

### 1. Clone and setup

```bash
git clone git@github.com:davidyuan666/MultiGuardCode.git
cd MultiGuardCode

# Windows:
python -m venv .venv
.venv\Scripts\Activate.ps1

# Linux/macOS:
./setup.sh
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set API credentials

```bash
# Windows PowerShell:
$env:DEEPSEEK_API_KEY = "sk-your-key-here"
$env:HTTP_PROXY = "http://127.0.0.1:10809"  # if behind proxy

# Linux/macOS:
export DEEPSEEK_API_KEY=sk-your-key-here
export HTTP_PROXY=http://127.0.0.1:10809
```

### 4. Download datasets

```bash
mkdir -p data
# Place HumanEval.jsonl and mbpp.jsonl in data/
```

### 5. Run experiments

```bash
# HumanEval (164 problems):
python experiments/run_all.py --dataset humaneval

# MBPP (50 sampled problems):
python experiments/run_all.py --dataset mbpp --mbpp-samples 50

# Quick test (20 problems):
python experiments/run_all.py --max-problems 20

# Specific modes:
python experiments/run_all.py --mode raw,multiguardcode
```

## Project Structure

```
MultiGuardCode/
├── experiments/
│   ├── config.py              # API & experiment configuration
│   ├── generate.py            # DeepSeek API code generation
│   ├── suppressor.py          # Four-tier error suppression
│   ├── evaluate.py            # Metrics computation (Pass@k, FDD)
│   ├── baselines.py           # Raw and Self-Debug baselines
│   ├── transitions.py         # Per-problem transition logging
│   ├── plot.py                # Paper figure generation
│   ├── framework_diagram.py   # Framework pipeline diagram
│   ├── regenerate_figures.py  # Regenerate figures from saved JSONs
│   └── run_all.py             # Full experiment pipeline
├── requirements.txt
├── setup.sh
└── README.md
```

## Evaluation

### HumanEval (164 problems)

| Method | Pass@1 | FDD | vs Raw |
|---|---|---|---|
| Raw (No Intervention) | 0.634 | 0.366 | -- |
| Self-Debug (3-Round) | 0.671 | 0.329 | +3.7% |
| T3-Only (Test Repair) | 0.726 | 0.274 | +9.2% |
| T1+T2+T3 (No T4) | 0.665 | 0.335 | +3.1% |
| MultiGuardCode (All 4 Tiers) | 0.640 | 0.360 | +0.6% |

### MBPP (50 problems)

| Method | Pass@1 | FDD | vs Raw |
|---|---|---|---|
| Raw (No Intervention) | 0.580 | 0.420 | -- |
| MultiGuardCode (All 4 Tiers) | 0.640 | 0.360 | +6.0% |

## Citation

```bibtex
@article{multiguardcode2026,
  title={MultiGuardCode: A Multi-Tier Error Suppression Framework for LLM Code Generation},
  author={Yuan, Dawei and Liang, Guojun and Liu, Suping},
  journal={Automated Software Engineering},
  year={2026}
}
```

## License

MIT
