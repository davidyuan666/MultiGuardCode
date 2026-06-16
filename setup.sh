#!/bin/bash
# CD4Code setup script for Unix/macOS
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo ""
echo "Setup complete. Activate with: source .venv/bin/activate"
echo "Set your API key: export DEEPSEEK_API_KEY=sk-xxx"
echo "Set proxy (if needed): export HTTP_PROXY=http://127.0.0.1:10809"
echo "Run experiments: python experiments/run_all.py"
