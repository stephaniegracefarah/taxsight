"""
DST Extraction Script
Extracts Digital Services Tax obligations from primary public sources
using Claude ETL agent.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parents[2] / ".env")
sys.path.append(str(Path(__file__).parents[1]))

from etl.etl_extractor import load_prompt, fetch_source, run_extraction, save_extraction

SOURCES = [
    {
        "url": "https://www.gov.uk/government/publications/introduction-of-the-digital-services-tax/digital-services-tax",
        "filename": "dst_uk_2026Q1.json",
        "description": "UK Digital Services Tax — GOV.UK"
    },
    {
        "url": "https://www.canada.ca/en/services/taxes/excise-taxes-duties-and-levies/digital-services-tax.html",
        "filename": "dst_canada_2026Q1.json",
        "description": "Canada Digital Services Tax — Canada.ca (repealed June 2025)"
    },
    {
        "url": "https://taxfoundation.org/data/all/eu/digital-services-taxes-europe/",
        "filename": "dst_europe_2026Q1.json",
        "description": "Tax Foundation — DSTs in Europe 2025"
    }
]

if __name__ == "__main__":
    prompt = load_prompt("dst_extraction_v1.txt")

    for source in SOURCES:
        print(f"\nFetching: {source['description']}")
        print(f"URL: {source['url']}")

        try:
            content = fetch_source(source["url"])
            print(f"Fetched {len(content)} characters")

            print("Running Claude extraction...")
            data = run_extraction(prompt, source["url"], content)

            save_extraction(data, source["filename"])
            print(f"Done: {source['filename']}")

        except Exception as e:
            print(f"Error processing {source['url']}: {e}")