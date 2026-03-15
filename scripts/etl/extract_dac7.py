"""
DAC7 Extraction Script
Extracts platform reporting obligations for EU member states
from primary public sources using Claude ETL agent.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parents[2] / ".env")

# Add scripts directory to path
sys.path.append(str(Path(__file__).parents[1]))

from etl.etl_extractor import load_prompt, fetch_source, run_extraction, save_extraction

SOURCES = [
    {
        "url": "https://taxation-customs.ec.europa.eu/taxation/tax-transparency-cooperation/administrative-co-operation-and-mutual-assistance/dac7_en",
        "filename": "dac7_eu_commission_2026Q1.json",
        "description": "EU Commission DAC7 main page"
    },
]

if __name__ == "__main__":
    prompt = load_prompt("dac7_extraction_v1.txt")
    
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