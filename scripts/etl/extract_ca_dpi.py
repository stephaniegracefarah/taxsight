"""
Canada DPI Extraction Script
Extracts Canada Digital Platform Information reporting obligations
from CRA primary source using Claude ETL agent.
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
        "url": "https://www.canada.ca/en/revenue-agency/programs/about-canada-revenue-agency-cra/compliance/reporting-rules-digital-platforms.html",
        "filename": "ca_dpi_cra_2026Q1.json",
        "description": "Canada CRA Digital Platform Operators"
    }
]

if __name__ == "__main__":
    prompt = load_prompt("ca_dpi_extraction_v1.txt")
    
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