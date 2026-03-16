"""
taxsight ETL Extractor
Runs Claude extraction prompts against public regulatory sources
and saves structured JSON output to /data/raw_extractions/YYYY-QN/
"""

import os
import json
import anthropic
import requests
from bs4 import BeautifulSoup
from datetime import date
from pathlib import Path

# Config
QUARTER = "2026-Q1"
RAW_EXTRACTIONS_PATH = Path(__file__).parents[2] / "data" / "raw_extractions" / QUARTER
PROMPTS_PATH = Path(__file__).parents[2] / "prompts" / "etl"

def load_prompt(prompt_file: str) -> str:
    with open(PROMPTS_PATH / prompt_file, "r") as f:
        return f.read()

def fetch_source(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)

def run_extraction(prompt: str, source_url: str, source_content: str, batch_instruction: str = "") -> dict:
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    
    user_content = f"{prompt}\n\nSource URL: {source_url}\n\nSource content:\n{source_content}"
    if batch_instruction:
        user_content += f"\n\nIMPORTANT: {batch_instruction}"
    
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        messages=[
            {
                "role": "user",
                "content": user_content
            }
        ]
    )
    
    raw_text = message.content[0].text
    print(f"Claude response preview: {raw_text[:500]}")
    
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
    raw_text = raw_text.strip()
    
    return json.loads(raw_text)

def run_research_extraction(prompt: str, country_name: str, country_iso3: str, suggested_sources: list = None) -> dict:
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    sources_hint = ""
    if suggested_sources:
        sources_hint = f"\n\nSuggested starting sources:\n"
        sources_hint += "\n".join(f"- {s}" for s in suggested_sources)

    user_content = f"""{prompt}

Country to research: {country_name} ({country_iso3})
{sources_hint}

IMPORTANT CONSTRAINTS:
- Do maximum 2 web searches total
- Read only the most relevant page you find
- Focus only on marketplace/platform VAT liability and deemed supplier rules
- Return a single JSON object immediately after finding the key facts
- Do not do exhaustive research — find the key facts and stop

Return only valid JSON — no preamble, no markdown backticks."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=3000,
        tools=[
            {
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 2
            }
        ],
        messages=[
            {
                "role": "user",
                "content": user_content
            }
        ]
    )

    # Extract text from response — may contain tool use blocks
    raw_text = ""
    for block in message.content:
        if hasattr(block, "text"):
            raw_text += block.text

    print(f"Claude response preview: {raw_text[:500]}")

    # Find JSON in response — handle cases where Claude adds reasoning text
    if "```" in raw_text:
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
    elif "[" in raw_text:
        raw_text = raw_text[raw_text.index("["):]
    elif "{" in raw_text:
        raw_text = raw_text[raw_text.index("{"):]

    raw_text = raw_text.strip()

    # Remove any trailing text after the JSON closes
    if raw_text.startswith("["):
        depth = 0
        for i, char in enumerate(raw_text):
            if char == "[":
                depth += 1
            elif char == "]":
                depth -= 1
                if depth == 0:
                    raw_text = raw_text[:i+1]
                    break

    return json.loads(raw_text)

def save_extraction(data: dict, filename: str):
    RAW_EXTRACTIONS_PATH.mkdir(parents=True, exist_ok=True)
    output_path = RAW_EXTRACTIONS_PATH / filename
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved extraction to {output_path}")

if __name__ == "__main__":
    print("taxsight ETL Extractor ready.")
    print(f"Output path: {RAW_EXTRACTIONS_PATH}")
    print(f"Prompts path: {PROMPTS_PATH}")