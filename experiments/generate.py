"""CD4Code: LLM Code Generator using DeepSeek API."""
import os
import json
import time
import httpx
from openai import OpenAI
from config import (
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL,
    DEFAULT_TEMPERATURE, DEFAULT_TOP_P, DEFAULT_MAX_TOKENS, HTTP_PROXY
)


def create_client():
    http_client = None
    if HTTP_PROXY:
        http_client = httpx.Client(proxy=HTTP_PROXY)
    return OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
        http_client=http_client,
    )


def generate_code(prompt, temperature=DEFAULT_TEMPERATURE,
                  top_p=DEFAULT_TOP_P, max_tokens=DEFAULT_MAX_TOKENS,
                  n=1, client=None):
    if client is None:
        client = create_client()

    messages = [
        {"role": "system", "content": "You are an expert Python programmer. Write clean, correct, well-documented code. Return ONLY the Python code, no explanations."},
        {"role": "user", "content": prompt},
    ]

    try:
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=messages,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            n=n,
        )
        return [choice.message.content for choice in response.choices]
    except Exception as e:
        print(f"API error: {e}")
        return [""] * n


def generate_with_retry(prompt, max_retries=3, client=None):
    for attempt in range(max_retries):
        try:
            codes = generate_code(prompt, n=1, client=client)
            if codes and codes[0].strip():
                return codes[0]
        except Exception as e:
            print(f"Retry {attempt + 1}/{max_retries}: {e}")
            time.sleep(2 ** attempt)
    return ""


def load_humaneval(path=None):
    if path is None:
        from config import HUMANEVAL_PATH
        path = HUMANEVAL_PATH
    problems = []
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                problems.append(json.loads(line.strip()))
    return problems


def load_mbpp(path=None, n_samples=200):
    if path is None:
        from config import MBPP_PATH
        path = MBPP_PATH
    import random
    problems = []
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                problems.append(json.loads(line.strip()))
    if len(problems) > n_samples:
        random.seed(42)
        problems = random.sample(problems, n_samples)
    return problems
