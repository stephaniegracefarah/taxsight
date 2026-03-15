"""
UK DPI Extraction Script
Extracts UK Digital Platform Information reporting obligations
from HMRC primary source using Claude ETL agent.
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
        "url": "https://www.gov.uk/guidance/reporting-rules-for-digital-platforms",
        "filename": "uk_dpi_hmrc_2026Q1.json",
        "description": "UK HMRC Digital Platform Reporting"
    }
]

if __name__ == "__main__":
    prompt = load_prompt("uk_dpi_extraction_v1.txt")
    
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