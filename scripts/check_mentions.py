#!/usr/bin/env python3
"""
Prompt Score — check_mentions.py
Calls OpenAI + Perplexity APIs, parses responses for brand mentions.
Uses a secondary gpt-4o-mini call for robust mention detection
(handles brand name variations, abbreviations, indirect references).
"""

import os
import json
import re
import time
import logging
from dataclasses import dataclass, asdict
from typing import Optional

import requests
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("check_mentions")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
OPENAI_MODEL = "gpt-4o-mini"
PERPLEXITY_MODEL = "sonar"  # default; sonar-pro for harder queries


# ─────────────────────────────────────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class MentionResult:
    brand_mentioned: bool
    sentiment: str  # positive | neutral | negative
    hallucination_flag: bool
    competitor_1_mentioned: bool
    competitor_2_mentioned: bool
    raw_response: str
    engine: str
    tokens_used: int


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _call_openai(messages: list[dict], model: str = OPENAI_MODEL) -> tuple[str, int]:
    """Call OpenAI Chat Completions API. Returns (content, approx_tokens)."""
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.3,
    }
    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    tokens = data.get("usage", {}).get("total_tokens", 0)
    return content, tokens


@retry(
    retry=retry_if_exception_type((requests.HTTPError, TimeoutError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=4, max=30),
)
def call_perplexity(prompt: str, model: str = PERPLEXITY_MODEL) -> tuple[str, int]:
    """Call Perplexity API (Sonar). Returns (content, approx_tokens)."""
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant. Answer the user's question directly "
                    "and in full. Do not say you are an AI."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    }
    resp = requests.post(
        "https://api.perplexity.ai/chat/completions",
        headers=headers,
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    tokens = data.get("usage", {}).get("total_tokens", 0)
    return content, tokens


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

    user_prompt = (
        f'Brand to check: "{brand_name}"\n'
        f'Competitors to check: {competitors or "none"}\n\n'
        f'Raw AI response:\n---\n{response}\n---'
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    content, _ = _call_openai(messages, model=OPENAI_MODEL)
    # Strip markdown code fences if present
    content = re.sub(r"^```json\s*", "", content.strip())
    content = re.sub(r"^```\s*", "", content.strip())
    content = re.sub(r"\s*```$", "", content.strip())

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        logger.warning("Failed to parse LLM mention analysis, falling back to string match")
        brand_mentioned = brand_name.lower() in response.lower()
        return {
            "brand_mentioned": brand_mentioned,
            "sentiment": "neutral",
            "hallucination_flag": False,
            "competitor_1_mentioned": (competitor_1 or "").lower() in response.lower() if competitor_1 else False,
            "competitor_2_mentioned": (competitor_2 or "").lower() in response.lower() if competitor_2 else False,
        }

    return parsed


# ─────────────────────────────────────────────────────────────────────────────
# Main entry points
# ─────────────────────────────────────────────────────────────────────────────

def check_chatgpt(prompt: str, brand_name: str, competitor_1: Optional[str], competitor_2: Optional[str]) -> MentionResult:
    """Run a single prompt against ChatGPT (gpt-4o-mini)."""
    logger.info(f"[ChatGPT] Running: {prompt[:60]}...")

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant. Answer the user's question directly and thoroughly. "
                "Do not say you are an AI or refer to your capabilities."
            ),
        },
        {"role": "user", "content": prompt},
    ]

    response, tokens = _call_openai(messages)
    parsed = parse_mentions_with_llm(response, brand_name, competitor_1, competitor_2, "chatgpt")

    return MentionResult(
        brand_mentioned=parsed["brand_mentioned"],
        sentiment=parsed["sentiment"],
        hallucination_flag=parsed["hallucination_flag"],
        competitor_1_mentioned=parsed.get("competitor_1_mentioned", False),
        competitor_2_mentioned=parsed.get("competitor_2_mentioned", False),
        raw_response=response,
        engine="chatgpt",
        tokens_used=tokens,
    )


def check_perplexity(prompt: str, brand_name: str, competitor_1: Optional[str], competitor_2: Optional[str]) -> MentionResult:
    """Run a single prompt against Perplexity Sonar."""
    logger.info(f"[Perplexity] Running: {prompt[:60]}...")

    response, tokens = call_perplexity(prompt)
    parsed = parse_mentions_with_llm(response, brand_name, competitor_1, competitor_2, "perplexity")

    return MentionResult(
        brand_mentioned=parsed["brand_mentioned"],
        sentiment=parsed["sentiment"],
        hallucination_flag=parsed["hallucination_flag"],
        competitor_1_mentioned=parsed.get("competitor_1_mentioned", False),
        competitor_2_mentioned=parsed.get("competitor_2_mentioned", False),
        raw_response=response,
        engine="perplexity",
        tokens_used=tokens,
    )


def check_gemini(prompt: str, brand_name: str, competitor_1: Optional[str], competitor_2: Optional[str]) -> MentionResult:
    """
    Run a single prompt against Google Gemini via the Vertex AI API.
    Requires GOOGLE_CLOUD_PROJECT and GOOGLE_APPLICATION_CREDENTIALS env vars,
    OR a Gemini API key via GEMINI_API_KEY.
    """
    import os as _os
    gemini_key = _os.getenv("GEMINI_API_KEY")

    logger.info(f"[Gemini] Running: {prompt[:60]}...")

    if gemini_key:
        # Direct Gemini API
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.3, "maxOutputTokens": 2048},
        }
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}",
            headers=headers,
            json=payload,
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        response = data["candidates"][0]["content"]["parts"][0]["text"]
        tokens = data.get("usageMetadata", {}).get("totalTokenCount", 0)
    else:
        raise NotImplementedError(
            "Gemini via Vertex AI not yet implemented. "
            "Set GEMINI_API_KEY in your .env to use direct Gemini API."
        )

    parsed = parse_mentions_with_llm(response, brand_name, competitor_1, competitor_2, "gemini")

    return MentionResult(
        brand_mentioned=parsed["brand_mentioned"],
        sentiment=parsed["sentiment"],
        hallucination_flag=parsed["hallucination_flag"],
        competitor_1_mentioned=parsed.get("competitor_1_mentioned", False),
        competitor_2_mentioned=parsed.get("competitor_2_mentioned", False),
        raw_response=response,
        engine="gemini",
        tokens_used=tokens,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Batch runner for a full prompt list
# ─────────────────────────────────────────────────────────────────────────────

def run_prompts(
    prompts: list[str],
    brand_name: str,
    competitor_1: Optional[str],
    competitor_2: Optional[str],
    engines: list[str] = None,
) -> list[MentionResult]:
    """
    Run all prompts across specified engines.
    Default engines: chatgpt, perplexity, gemini
    """
    engines = engines or ["chatgpt", "perplexity", "gemini"]
    results: list[MentionResult] = []

    for i, prompt in enumerate(prompts):
        logger.info(f"  Prompt {i+1}/{len(prompts)}: {prompt[:50]}...")

        for engine in engines:
            try:
                if engine == "chatgpt":
                    result = check_chatgpt(prompt, brand_name, competitor_1, competitor_2)
                elif engine == "perplexity":
                    result = check_perplexity(prompt, brand_name, competitor_1, competitor_2)
                elif engine == "gemini":
                    try:
                        result = check_gemini(prompt, brand_name, competitor_1, competitor_2)
                    except NotImplementedError:
                        logger.warning("Gemini not configured, skipping")
                        continue
                else:
                    logger.warning(f"Unknown engine: {engine}")
                    continue

                results.append(result)

                # Rate limit: small delay between calls
                time.sleep(0.5)

            except Exception as exc:
                logger.error(f"  Error on {engine} for prompt {i+1}: {exc}")
                continue

    return results


# ─────────────────────────────────────────────────────────────────────────────
# CLI (quick test)
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test brand mention detection")
    parser.add_argument("brand", help="Brand name to check")
    parser.add_argument("--prompt", default='"best CRM for small startups"', help="Prompt to run")
    parser.add_argument("--competitor", default=None, help="Competitor brand")
    args = parser.parse_args()

    print(f"Checking brand: {args.brand}")
    print(f"Prompt: {args.prompt}")
    print(f"Competitor: {args.competitor or 'none'}")

    result = check_chatgpt(args.prompt, args.brand, args.competitor, None)
    print(f"\nChatGPT result:")
    print(f"  Mentioned:  {result.brand_mentioned}")
    print(f"  Sentiment:  {result.sentiment}")
    print(f"  Hallucination: {result.hallucination_flag}")
    print(f"  Competitor mentioned: {result.competitor_1_mentioned}")
    print(f"  Tokens: {result.tokens_used}")
