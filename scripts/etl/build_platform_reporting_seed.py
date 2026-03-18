
"""
Build Platform Reporting Seed CSV
Converts raw Claude ETL extraction JSON files into the
platform_reporting seed CSV for dbt.
"""

import json
import csv
from pathlib import Path

ROOT = Path(__file__).parents[2]
RAW_PATH = ROOT / "data" / "raw_extractions" / "2026-Q1"
SEED_PATH = ROOT / "taxsight_dbt" / "seeds" / "platform_reporting"
OUTPUT_FILE = SEED_PATH / "platform_reporting.csv"

SOURCE_FILES = [
    RAW_PATH / "dac7_eu_commission_2026Q1.json",
    RAW_PATH / "uk_dpi_hmrc_2026Q1.json",
    RAW_PATH / "ca_dpi_cra_2026Q1.json",
]

COLUMNS = [
    "obligation_id",
    "country_iso3",
    "country_name",
    "regime_type",
    "regime_framework",
    "is_enacted",
    "effective_date",
    "applies_to_platform",
    "has_revenue_threshold",
    "reporting_deadline",
    "covered_activities",
    "seller_transaction_threshold",
    "seller_revenue_threshold",
    "single_registration_eligible",
    "penalty_financial_severity",
    "penalty_operational_severity",
    "penalties_description",
    "guidance_maturity",
    "regulatory_attention_level",
    "complexity_score_base",
    "source_url",
    "verbatim_quote",
    "confidence_flag",
    "last_verified_date",
    "notes",
]


def compute_complexity_score_base(row):
    """Recency + Guidance Maturity score per TDD Decision 4."""
    effective_date = row.get("effective_date")
    guidance_maturity = row.get("guidance_maturity", "developing")

    if effective_date is None:
        base = 5
    else:
        year = int(str(effective_date)[:4])
        if year >= 2022:
            base = 10
        elif year >= 2019:
            base = 7
        elif year >= 2015:
            base = 4
        else:
            base = 2

    modifier = {"nascent": 1, "developing": 0, "mature": -1}.get(guidance_maturity, 0)
    return max(1, min(10, base + modifier))


def load_json(filepath):
    with open(filepath) as f:
        data = json.load(f)
    if isinstance(data, dict):
        return [data]
    return data


def build_obligation_id(row):
    regime = row.get("regime_framework", "").upper().replace("-", "_")
    iso3 = row.get("country_iso3", "").upper()
    return f"{regime}_{iso3}"


def normalize_row(row):
    return {
        "obligation_id": build_obligation_id(row),
        "country_iso3": row.get("country_iso3"),
        "country_name": row.get("country_name"),
        "regime_type": row.get("regime_type"),
        "regime_framework": row.get("regime_framework"),
        "is_enacted": row.get("is_enacted"),
        "effective_date": row.get("effective_date"),
        "applies_to_platform": True,
        "has_revenue_threshold": False,
        "reporting_deadline": row.get("reporting_deadline"),
        "covered_activities": row.get("covered_activities"),
        "seller_transaction_threshold": row.get("seller_transaction_threshold"),
        "seller_revenue_threshold": row.get("seller_revenue_threshold"),
        "single_registration_eligible": row.get("single_registration_eligible"),
        "penalty_financial_severity": row.get("penalty_financial_severity"),
        "penalty_operational_severity": row.get("penalty_operational_severity"),
        "penalties_description": row.get("penalties_description"),
        "guidance_maturity": row.get("guidance_maturity", "developing"),
        "regulatory_attention_level": row.get("regulatory_attention_level", "high"),
        "complexity_score_base": compute_complexity_score_base(row),
        "source_url": row.get("source_url"),
        "verbatim_quote": row.get("verbatim_quote"),
        "confidence_flag": row.get("confidence_flag"),
        "last_verified_date": row.get("last_verified_date"),
        "notes": row.get("notes"),
    }


if __name__ == "__main__":
    all_rows = []

    for source_file in SOURCE_FILES:
        print(f"Loading {source_file.name}...")
        rows = load_json(source_file)
        normalized = [normalize_row(r) for r in rows]
        all_rows.extend(normalized)
        print(f"  {len(normalized)} rows loaded")

    print(f"\nTotal rows: {len(all_rows)}")

    SEED_PATH.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Saved to {OUTPUT_FILE}")