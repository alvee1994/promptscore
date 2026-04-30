#!/usr/bin/env python3
"""
SOV Check — check_mentions.py
All AI calls routed through OpenRouter (openrouter.ai) — single key for OpenAI,
Anthropic, Perplexity, Gemini, and more. Parses responses for brand mentions using
a secondary gpt-4o-mini call for robust detection.
"""

import os
import json
import re
import time
import logging
from dataclasses import dataclass
from typing import Optional

import requests
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("check_mentions")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Model aliases — mapped to OpenRouter model IDs
MODEL_ALIASES = {
    "chatgpt":    "openai/gpt-4o-mini",
    "gpt":        "openai/gpt-4o-mini",
    "perplexity": "perplexity/sonar",
    "sonar":      "perplexity/sonar",
    "gemini":     "google/gemini-2.0-flash",
    "claude":     "anthropic/claude-3.5-haiku",
}


@dataclass
class MentionResult:
    brand_mentioned: bool
    sentiment: str          # positive | neutral | negative
    hallucination_flag: bool
    competitor_1_mentioned: bool
    competitor_2_mentioned: bool
    raw_response: str
    engine: str
    tokens_used: int


def _call_openrouter(
    messages: list[dict],
    model: str,
    temperature: float = 0.3,
) -> tuple[str, int]:
    """
    Route a chat completion through OpenRouter.
    Returns (content, approx_tokens).
    Works for OpenAI, Perplexity (sonar), Gemini, Claude — any model OpenRouter hosts.
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://sovcheck.online",
        "X-Title": "SOV Check",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    resp = requests.post(
        f"{OPENROUTER_BASE_URL}/chat/completions",
        headers=headers,
        json=payload,
        timeout=90,
    )
    resp.raise_for_status()
    data = resp.json()
    # OpenRouter may return usage at top level or nested
    usage = data.get("usage", {})
    tokens = usage.get("total_tokens", 0) or usage.get("completion_tokens", 0)
    return data["choices"][0]["message"]["content"], tokens


@retry(
    retry=retry_if_exception_type((requests.HTTPError, TimeoutError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=4, max=30),
)
def _call_openrouter_with_retry(
    messages: list[dict],
    model: str,
    temperature: float = 0.3,
) -> tuple[str, int]:
    """Wrapper with tenacity retry on transient errors."""
    return _call_openrouter(messages, model, temperature)


# ─────────────────────────────────────────────────────────────────────────────

def parse_mentions_with_llm(
    response: str,
    brand_name: str,
    competitor_1: Optional[str],
    competitor_2: Optional[str],
    engine: str,
) -> dict:
    """
    Use gpt-4o-mini to parse the raw AI response for brand mentions.
    Handles: variations, abbreviations, indirect references, sentiment, hallucinations.
    """
    competitors = [c for c in [competitor_1, competitor_2] if c]
    comp_list = ", ".join(f'"{c}"' for c in competitors) if competitors else '"none"'

    system_prompt = (
        f'You are an AI response analyst. Given a raw response from an AI engine '
        f'and a brand name, determine:\n'
        f'1. Was the brand "{brand_name}" mentioned? (yes/no)\n'
        f'2. What is the sentiment of the mention? (positive/neutral/negative)\n'
        f'3. Is this a hallucination — mentioned but the description is factually wrong? (yes/no)\n'
        f'4. Was each competitor mentioned? ({comp_list})\n'
        f'Respond ONLY as valid JSON with keys: brand_mentioned, sentiment, hallucination_flag, '
        f'competitor_1_mentioned, competitor_2_mentioned\n'
        f'Be strict: do NOT mark as mentioned if the brand name appears only in '
        f'a URL or domain unless it is explicitly discussed.'
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (
                f'Brand to check: "{brand_name}"\n'
                f'Competitors to check: {competitors or "none"}\n\n'
                f'Raw AI response:\n---\n{response}\n---'
            ),
        },
    ]

    content, _ = _call_openrouter_with_retry(messages, model=MODEL_ALIASES["gpt"])
    content = re.sub(r"^```json\s*", "", content.strip())
    content = re.sub(r"^```\s*", "", content.strip())
    content = re.sub(r"\s*```$", "", content.strip())

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        logger.warning("Failed to parse LLM mention analysis, falling back to string match")
        brand_lower = brand_name.lower()
        return {
            "brand_mentioned": brand_lower in response.lower(),
            "sentiment": "neutral",
            "hallucination_flag": False,
            "competitor_1_mentioned": (competitor_1 or "").lower() in response.lower() if competitor_1 else False,
            "competitor_2_mentioned": (competitor_2 or "").lower() in response.lower() if competitor_2 else False,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Engine runners
# ─────────────────────────────────────────────────────────────────────────────

def check_engine(
    engine: str,
    prompt: str,
    brand_name: str,
    competitor_1: Optional[str],
    competitor_2: Optional[str],
) -> MentionResult:
    """
    Dispatch a single prompt to any engine by name.
    engine: one of 'chatgpt', 'perplexity', 'gemini', 'claude'
    All calls go through OpenRouter via a single API key.
    """
    model = MODEL_ALIASES.get(engine, engine)  # accept alias or raw model ID

    logger.info(f"[{engine}] Running: {prompt[:60]}...")

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant. Answer the user's question directly "
                "and thoroughly. Do not say you are an AI."
            ),
        },
        {"role": "user", "content": prompt},
    ]

    response, tokens = _call_openrouter_with_retry(messages, model=model, temperature=0.3)
    parsed = parse_mentions_with_llm(response, brand_name, competitor_1, competitor_2, engine)

    return MentionResult(
        brand_mentioned=parsed["brand_mentioned"],
        sentiment=parsed["sentiment"],
        hallucination_flag=parsed["hallucination_flag"],
        competitor_1_mentioned=parsed.get("competitor_1_mentioned", False),
        competitor_2_mentioned=parsed.get("competitor_2_mentioned", False),
        raw_response=response,
        engine=engine,
        tokens_used=tokens,
    )


# Convenience aliases for the old entry-point names
def check_chatgpt(prompt: str, brand: str, c1=None, c2=None) -> MentionResult:
    return check_engine("chatgpt", prompt, brand, c1, c2)


def check_perplexity(prompt: str, brand: str, c1=None, c2=None) -> MentionResult:
    return check_engine("perplexity", prompt, brand, c1, c2)


def check_gemini(prompt: str, brand: str, c1=None, c2=None) -> MentionResult:
    return check_engine("gemini", prompt, brand, c1, c2)


def check_claude(prompt: str, brand: str, c1=None, c2=None) -> MentionResult:
    return check_engine("claude", prompt, brand, c1, c2)


# ─────────────────────────────────────────────────────────────────────────────
# Batch runner
# ─────────────────────────────────────────────────────────────────────────────

def run_prompts(
    prompts: list[str],
    brand_name: str,
    competitor_1: Optional[str] = None,
    competitor_2: Optional[str] = None,
    engines: list[str] = None,
) -> list[MentionResult]:
    """
    Run all prompts across specified engines.
    Default engines: chatgpt, perplexity
    """
    engines = engines or ["chatgpt", "perplexity"]
    results: list[MentionResult] = []

    for i, prompt in enumerate(prompts):
        logger.info(f"  Prompt {i+1}/{len(prompts)}: {prompt[:50]}...")

        for engine in engines:
            try:
                result = check_engine(engine, prompt, brand_name, competitor_1, competitor_2)
                results.append(result)
                time.sleep(0.5)  # rate limit between calls

            except Exception as exc:
                logger.error(f"  Error on {engine} for prompt {i+1}: {exc}")
                continue

    return results


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test brand mention detection")
    parser.add_argument("brand", help="Brand name to check")
    parser.add_argument("--prompt", default='"best CRM for small startups"',
                       help="Prompt to run")
    parser.add_argument("--competitor", default=None, help="Competitor brand")
    parser.add_argument("--engine", default="chatgpt",
                       help="Engine: chatgpt, perplexity, gemini, claude")
    args = parser.parse_args()

    print(f"Brand: {args.brand}")
    print(f"Engine: {args.engine}")
    print(f"Prompt: {args.prompt}")

    result = check_engine(args.engine, args.prompt, args.brand, args.competitor, None)
    print(f"\nResult:")
    print(f"  Mentioned:     {result.brand_mentioned}")
    print(f"  Sentiment:     {result.sentiment}")
    print(f"  Hallucination: {result.hallucination_flag}")
    print(f"  Competitor:   {result.competitor_1_mentioned}")
    print(f"  Tokens:       {result.tokens_used}")
