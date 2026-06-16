# CD4Code: A Central Dogma-Inspired Multi-Tier Error Suppression Framework for LLM Code Generation

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)

Source code and experiments for the paper **"A Central Dogma-Inspired Multi-Tier Error Suppression Framework for Code Generation with Large Language Models"**, submitted to the *International Journal of Bio-Inspired Computation (IJBIC)*.

## Overview

CD4Code maps the four-tier quality control architecture of the Central Dogma of molecular biology onto the LLM code generation pipeline:

| Biological Tier | Code Generation Analog | Mechanism |
|---|---|---|
| DNA Polymerase Proofreading | Token Confidence Filtering | Reject low-confidence tokens in real-time |
| Mismatch Repair (MMR) | Static Analysis + Local Regeneration | Detect and fix syntax/type errors post-hoc |
| Ubiquitin-Proteasome System | Test-Driven Discard + Regeneration | Degrade outputs that fail functional tests |
| ER Stress Response (UPR) | Global Defect Density Monitor | Switch to conservative generation when failure rate exceeds threshold |

## Quick Start

### 1. Clone and setup

```bash
git clone git@github.com:davidyuan666/cd4code.git
cd cd4code

# Windows:
python -m venv .venv
.venv\Scripts\Activate.ps1

# Linux/macOS:
./setup.sh
```

### 2. Set API credentials

```bash
# Windows PowerShell:
$env:DEEPSEEK_API_KEY = "sk-your-key-here"
$env:HTTP_PROXY = "http://127.0.0.1:10809"  # if behind proxy

# Linux/macOS:
export DEEPSEEK_API_KEY=sk-your-key-here
export HTTP_PROXY=http://127.0.0.1:10809
```

### 3. Download datasets

```bash
# Download HumanEval and MBPP datasets
mkdir -p data
# Place HumanEval.jsonl and mbpp.jsonl in data/
```

### 4. Run experiments

```bash
# Full experiment:
python experiments/run_all.py

# Quick test (20 problems):
python experiments/run_all.py --max-problems 20

# Single dataset:
python experiments/run_all.py --dataset humaneval
```

### 5. Generate paper

```bash
cd paper
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

## Project Structure

```
cd4code/
├── experiments/
│   ├── config.py          # API & experiment configuration
│   ├── generate.py        # DeepSeek API code generation
│   ├── suppressor.py      # Four-tier error suppression
│   ├── evaluate.py        # Metrics computation (Pass@k, FDD)
│   ├── plot.py            # Paper figure generation
│   └── run_all.py         # Full experiment pipeline
├── paper/
│   ├── main.tex           # LaTeX manuscript (IJBIC template)
│   ├── refs.bib           # Bibliography
│   ├── doublecol-new.cls  # Inderscience class file
│   └── figures/           # Generated figures
├── requirements.txt
├── setup.sh
└── README.md
```

## Citation

```bibtex
@article{cd4code2026,
  title={A Central Dogma-Inspired Multi-Tier Error Suppression Framework for Code Generation with Large Language Models},
  author={Author},
  journal={International Journal of Bio-Inspired Computation},
  year={2026}
}
```

## License

MIT
