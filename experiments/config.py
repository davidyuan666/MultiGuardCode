"""CD4Code Experiment Configuration.

All secrets and proxy settings are read from environment variables.
Never hard-code API keys in this file.
"""
import os

# DeepSeek API configuration
DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"

# Proxy configuration (from environment variable)
HTTP_PROXY = os.environ.get("HTTP_PROXY", os.environ.get("http_proxy", ""))

# CD4Code tier parameters
TIER1_CONFIDENCE_THRESHOLD = 0.6       # Token-level proofreading
TIER2_LINTER = "pylint"                # Static analysis tool
TIER2_TYPE_CHECKER = "mypy"            # Type checker
TIER3_MAX_RETRIES = 3                  # Max regeneration attempts
TIER4_DEFECT_THRESHOLD = 0.4           # Global defect density threshold
TIER4_CONSERVATIVE_TEMP = 0.3          # Conservative temperature
TIER4_CONSERVATIVE_TOPP = 0.85         # Conservative top-p

# Generation defaults
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_P = 0.95
DEFAULT_MAX_TOKENS = 512

# Paths
HUMANEVAL_PATH = "data/HumanEval.jsonl"
MBPP_PATH = "data/mbpp.jsonl"
RESULTS_DIR = "results"
FIGURES_DIR = "../paper/figures"
