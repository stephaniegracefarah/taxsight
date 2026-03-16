"""
VAT/GST Research Extraction Script
Uses Claude with web search to research marketplace VAT/GST rules
for each country. Claude finds and cites its own sources.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import time

load_dotenv(Path(__file__).parents[2] / ".env")
sys.path.append(str(Path(__file__).parents[1]))

from etl.etl_extractor import load_prompt, run_research_extraction, save_extraction

# Countries to research with suggested starting sources
COUNTRIES = [
    {"name": "Australia", "iso3": "AUS"},
    {"name": "New Zealand", "iso3": "NZL"},
    {"name": "Canada", "iso3": "CAN"},
    {"name": "Mexico", "iso3": "MEX"},
    {"name": "Brazil", "iso3": "BRA"},
    {"name": "Argentina", "iso3": "ARG"},
    {"name": "Colombia", "iso3": "COL"},
    {"name": "Chile", "iso3": "CHL"},
    {"name": "Japan", "iso3": "JPN"},
    {"name": "Singapore", "iso3": "SGP"},
    {"name": "South Korea", "iso3": "KOR"},
    {"name": "India", "iso3": "IND"},
    {"name": "Indonesia", "iso3": "IDN"},
    {"name": "Malaysia", "iso3": "MYS"},
    {"name": "Thailand", "iso3": "THA"},
    {"name": "China", "iso3": "CHN"},
    {"name": "United Kingdom", "iso3": "GBR"},
    {"name": "Norway", "iso3": "NOR"},
    {"name": "Switzerland", "iso3": "CHE"},
    {"name": "Germany", "iso3": "DEU"},
    {"name": "France", "iso3": "FRA"},
    {"name": "Italy", "iso3": "ITA"},
    {"name": "Spain", "iso3": "ESP"},
    {"name": "Netherlands", "iso3": "NLD"},
    {"name": "Sweden", "iso3": "SWE"},
    {"name": "Poland", "iso3": "POL"},
    {"name": "Belgium", "iso3": "BEL"},
    {"name": "Austria", "iso3": "AUT"},
    {"name": "Ireland", "iso3": "IRL"},
    {"name": "South Africa", "iso3": "ZAF"},
    {"name": "United Arab Emirates", "iso3": "ARE"},
    {"name": "Saudi Arabia", "iso3": "SAU"},
    {"name": "Kenya", "iso3": "KEN"},
    {"name": "Nigeria", "iso3": "NGA"},
]

SUGGESTED_SOURCES = [
    "https://quaderno.io/blog/online-marketplace-tax-laws-around-the-world/",
    "https://www.avalara.com/vatlive/en/country-guides.html",
    "https://vatcalc.com",
]

if __name__ == "__main__":
    prompt = load_prompt("vat_gst_extraction_v1.txt")

    for i, country in enumerate(COUNTRIES):
        filename = f"vat_gst_{country['name'].lower().replace(' ', '_')}_2026Q1.json"
        output_path = Path(__file__).parents[2] / "data" / "raw_extractions" / "2026-Q1" / filename

        # Skip if already extracted
        if output_path.exists():
            print(f"Skipping {country['name']} — already extracted")
            continue

        print(f"\nResearching: {country['name']} ({country['iso3']})")

        try:
            data = run_research_extraction(
                prompt=prompt,
                country_name=country["name"],
                country_iso3=country["iso3"],
                suggested_sources=SUGGESTED_SOURCES
            )

            save_extraction(data, filename)
            print(f"Done: {filename}")

            # Rate limit buffer — 30k tokens/min limit
            print("Waiting 45 seconds before next country...")
            time.sleep(45)

        except Exception as e:
            print(f"Error processing {country['name']}: {e}")
            print("Rate limit hit — waiting 90 seconds...")
            time.sleep(90)