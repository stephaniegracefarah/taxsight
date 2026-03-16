"""
VAT/GST Extraction Script
Extracts global VAT/GST marketplace rules from primary public sources
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
    # Oceania
    {"url": "https://www.avalara.com/vatlive/en/country-guides/oceania/australia.html", "filename": "vat_gst_australia_2026Q1.json", "description": "Australia"},
    {"url": "https://www.avalara.com/vatlive/en/country-guides/oceania/new-zealand.html", "filename": "vat_gst_newzealand_2026Q1.json", "description": "New Zealand"},
    # North America
    {"url": "https://www.avalara.com/vatlive/en/country-guides/north-america/canada.html", "filename": "vat_gst_canada_2026Q1.json", "description": "Canada"},
    {"url": "https://www.avalara.com/vatlive/en/country-guides/north-america/mexico.html", "filename": "vat_gst_mexico_2026Q1.json", "description": "Mexico"},
    # South America
    {"url": "https://www.avalara.com/vatlive/en/country-guides/south-america/brazil.html", "filename": "vat_gst_brazil_2026Q1.json", "description": "Brazil"},
    {"url": "https://www.avalara.com/vatlive/en/country-guides/south-america/argentina.html", "filename": "vat_gst_argentina_2026Q1.json", "description": "Argentina"},
    {"url": "https://www.avalara.com/vatlive/en/country-guides/south-america/colombia.html", "filename": "vat_gst_colombia_2026Q1.json", "description": "Colombia"},
    {"url": "https://www.avalara.com/vatlive/en/country-guides/south-america/chile.html", "filename": "vat_gst_chile_2026Q1.json", "description": "Chile"},
    # Asia
    {"url": "https://www.avalara.com/vatlive/en/country-guides/asia/japan.html", "filename": "vat_gst_japan_2026Q1.json", "description": "Japan"},
    {"url": "https://www.avalara.com/vatlive/en/country-guides/asia/singapore.html", "filename": "vat_gst_singapore_2026Q1.json", "description": "Singapore"},
    {"url": "https://www.avalara.com/vatlive/en/country-guides/asia/south-korea.html", "filename": "vat_gst_southkorea_2026Q1.json", "description": "South Korea"},
    {"url": "https://www.avalara.com/vatlive/en/country-guides/asia/india.html", "filename": "vat_gst_india_2026Q1.json", "description": "India"},
    {"url": "https://www.avalara.com/vatlive/en/country-guides/asia/indonesia.html", "filename": "vat_gst_indonesia_2026Q1.json", "description": "Indonesia"},
    {"url": "https://www.avalara.com/vatlive/en/country-guides/asia/malaysia.html", "filename": "vat_gst_malaysia_2026Q1.json", "description": "Malaysia"},
    {"url": "https://www.avalara.com/vatlive/en/country-guides/asia/thailand.html", "filename": "vat_gst_thailand_2026Q1.json", "description": "Thailand"},
    {"url": "https://www.avalara.com/vatlive/en/country-guides/asia/china.html", "filename": "vat_gst_china_2026Q1.json", "description": "China"},
    # Europe (key non-EU)
    {"url": "https://www.avalara.com/vatlive/en/country-guides/europe/uk.html", "filename": "vat_gst_uk_2026Q1.json", "description": "United Kingdom"},
    {"url": "https://www.avalara.com/vatlive/en/country-guides/europe/norway.html", "filename": "vat_gst_norway_2026Q1.json", "description": "Norway"},
    {"url": "https://www.avalara.com/vatlive/en/country-guides/europe/switzerland.html", "filename": "vat_gst_switzerland_2026Q1.json", "description": "Switzerland"},
    # EU key markets (individual pages)
    {"url": "https://www.avalara.com/vatlive/en/country-guides/europe/germany.html", "filename": "vat_gst_germany_2026Q1.json", "description": "Germany"},
    {"url": "https://www.avalara.com/vatlive/en/country-guides/europe/france.html", "filename": "vat_gst_france_2026Q1.json", "description": "France"},
    {"url": "https://www.avalara.com/vatlive/en/country-guides/europe/italy.html", "filename": "vat_gst_italy_2026Q1.json", "description": "Italy"},
    {"url": "https://www.avalara.com/vatlive/en/country-guides/europe/spain.html", "filename": "vat_gst_spain_2026Q1.json", "description": "Spain"},
    {"url": "https://www.avalara.com/vatlive/en/country-guides/europe/netherlands.html", "filename": "vat_gst_netherlands_2026Q1.json", "description": "Netherlands"},
    {"url": "https://www.avalara.com/vatlive/en/country-guides/europe/sweden.html", "filename": "vat_gst_sweden_2026Q1.json", "description": "Sweden"},
    {"url": "https://www.avalara.com/vatlive/en/country-guides/europe/poland.html", "filename": "vat_gst_poland_2026Q1.json", "description": "Poland"},
    {"url": "https://www.avalara.com/vatlive/en/country-guides/europe/belgium.html", "filename": "vat_gst_belgium_2026Q1.json", "description": "Belgium"},
    {"url": "https://www.avalara.com/vatlive/en/country-guides/europe/austria.html", "filename": "vat_gst_austria_2026Q1.json", "description": "Austria"},
    {"url": "https://www.avalara.com/vatlive/en/country-guides/europe/ireland.html", "filename": "vat_gst_ireland_2026Q1.json", "description": "Ireland"},
    # Africa & Middle East
    {"url": "https://www.avalara.com/vatlive/en/country-guides/africa-and-middle-east/south-africa.html", "filename": "vat_gst_southafrica_2026Q1.json", "description": "South Africa"},
    {"url": "https://www.avalara.com/vatlive/en/country-guides/africa-and-middle-east/united-arab-emirates.html", "filename": "vat_gst_uae_2026Q1.json", "description": "UAE"},
    {"url": "https://www.avalara.com/vatlive/en/country-guides/africa-and-middle-east/saudi-arabia.html", "filename": "vat_gst_saudiarabia_2026Q1.json", "description": "Saudi Arabia"},
    {"url": "https://www.avalara.com/vatlive/en/country-guides/africa-and-middle-east/kenya.html", "filename": "vat_gst_kenya_2026Q1.json", "description": "Kenya"},
    {"url": "https://www.avalara.com/vatlive/en/country-guides/africa-and-middle-east/nigeria.html", "filename": "vat_gst_nigeria_2026Q1.json", "description": "Nigeria"},
]


if __name__ == "__main__":
    prompt = load_prompt("vat_gst_extraction_v1.txt")

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