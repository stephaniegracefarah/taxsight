"""
Marketplace Facilitator Extraction Script
Extracts US state marketplace facilitator laws from two primary public sources:
1. Avalara marketplace facilitator guide — platform-specific fields
2. Avalara economic nexus guide — revenue/transaction threshold fields

Both sources are extracted independently and merged in build_marketplace_fac_seed.py.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parents[2] / ".env")
sys.path.append(str(Path(__file__).parents[1]))

from etl.etl_extractor import load_prompt, fetch_source, run_extraction, save_extraction

MARKETPLACE_FAC_URL = "https://www.avalara.com/us/en/learn/guides/state-by-state-guide-to-marketplace-facilitator-laws.html"
ECONOMIC_NEXUS_URL = "https://www.avalara.com/us/en/learn/guides/state-by-state-guide-economic-nexus-laws.html"

SOURCES = [
    {
        "url": MARKETPLACE_FAC_URL,
        "prompt": "marketplace_fac_extraction_v1.txt",
        "filename": "marketplace_fac_avalara_am_2026Q1.json",
        "description": "Avalara marketplace facilitator guide — states A through M",
        "batch_instruction": "Extract only states Alabama through Missouri (A-M alphabetically). Return a JSON array."
    },
    {
        "url": MARKETPLACE_FAC_URL,
        "prompt": "marketplace_fac_extraction_v1.txt",
        "filename": "marketplace_fac_avalara_nw_2026Q1.json",
        "description": "Avalara marketplace facilitator guide — states N through Wyoming",
        "batch_instruction": "Extract only states Nebraska through Wyoming (N-W alphabetically), plus District of Columbia and Puerto Rico. Return a JSON array."
    },
    {
        "url": ECONOMIC_NEXUS_URL,
        "prompt": "marketplace_fac_en_extraction_v1.txt",
        "filename": "marketplace_fac_en_am_2026Q1.json",
        "description": "Avalara economic nexus guide — states A through M",
        "batch_instruction": "Extract only states Alabama through Missouri (A-M alphabetically). Return a JSON array."
    },
    {
        "url": ECONOMIC_NEXUS_URL,
        "prompt": "marketplace_fac_en_extraction_v1.txt",
        "filename": "marketplace_fac_en_nw_2026Q1.json",
        "description": "Avalara economic nexus guide — states N through Wyoming",
        "batch_instruction": "Extract only states Nebraska through Wyoming (N-W alphabetically), plus District of Columbia and Puerto Rico. Return a JSON array."
    }
]

if __name__ == "__main__":
    for source in SOURCES:
        print(f"\nFetching: {source['description']}")
        print(f"URL: {source['url']}")

        try:
            prompt = load_prompt(source["prompt"])
            content = fetch_source(source["url"])
            print(f"Fetched {len(content)} characters")

            print("Running Claude extraction...")
            data = run_extraction(
                prompt,
                source["url"],
                content,
                batch_instruction=source.get("batch_instruction", "")
            )

            save_extraction(data, source["filename"])
            print(f"Done: {source['filename']}")

        except Exception as e:
            print(f"Error processing {source['description']}: {e}")