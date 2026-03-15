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
    headers = {"User-Agent": "taxsight-etl/1.0 stephanie@email.com"}
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    # Remove scripts and styles
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)

def run_extraction(prompt: str, source_url: str, source_content: str) -> dict:
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        messages=[
            {
                "role": "user",
                "content": f"{prompt}\n\nSource URL: {source_url}\n\nSource content:\n{source_content}"
            }
        ]
    )
    
    raw_text = message.content[0].text
    
    # Debug — show first 500 chars of response
    print(f"Claude response preview: {raw_text[:500]}")
    
    # Strip markdown code fences if present
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
    raw_text = raw_text.strip()
    
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