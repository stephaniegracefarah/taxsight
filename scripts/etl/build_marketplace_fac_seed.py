"""
Build Marketplace Facilitator Seed CSV
Converts raw Claude ETL extraction JSON files into the
marketplace_fac seed CSV for dbt.
"""

import json
import csv
from pathlib import Path

ROOT = Path(__file__).parents[2]
RAW_PATH = ROOT / "data" / "raw_extractions" / "2026-Q1"
SEED_PATH = ROOT / "taxsight_dbt" / "seeds" / "marketplace_fac"
OUTPUT_FILE = SEED_PATH / "marketplace_fac.csv"

SOURCE_FILES = [
    RAW_PATH / "marketplace_fac_avalara_am_2026Q1.json",
    RAW_PATH / "marketplace_fac_avalara_nw_2026Q1.json",
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
    "state_code",
    "revenue_threshold_usd",
    "transaction_threshold",
    "transaction_threshold_active",
    "platform_vs_seller_liability",
    "filing_frequency",
    "third_party_sales_inclusion",
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
    return base + modifier


def load_json(filepath):
    with open(filepath) as f:
        data = json.load(f)
    if isinstance(data, dict):
        return [data]
    return data


def build_obligation_id(row):
    iso3 = row.get("country_iso3", "").upper().replace("-", "_")
    return f"MKT_FAC_{iso3}"


def normalize_row(row):
    return {
        "obligation_id": build_obligation_id(row),
        "country_iso3": row.get("country_iso3"),
        "country_name": row.get("country_name"),
        "regime_type": row.get("regime_type", "marketplace_fac"),
        "regime_framework": row.get("regime_framework", "na_state"),
        "is_enacted": row.get("is_enacted"),
        "effective_date": row.get("effective_date"),
        "applies_to_platform": row.get("applies_to_platform", True),
        "has_revenue_threshold": row.get("has_revenue_threshold"),
        "state_code": row.get("state_code"),
        "revenue_threshold_usd": row.get("revenue_threshold_usd"),
        "transaction_threshold": row.get("transaction_threshold"),
        "transaction_threshold_active": row.get("transaction_threshold_active"),
        "platform_vs_seller_liability": row.get("platform_vs_seller_liability"),
        "filing_frequency": row.get("filing_frequency"),
        "third_party_sales_inclusion": row.get("third_party_sales_inclusion"),
        "penalty_financial_severity": row.get("penalty_financial_severity", "medium"),
        "penalty_operational_severity": row.get("penalty_operational_severity", "low"),
        "penalties_description": row.get("penalties_description"),
        "guidance_maturity": row.get("guidance_maturity", "mature"),
        "regulatory_attention_level": row.get("regulatory_attention_level", "medium"),
        "complexity_score_base": compute_complexity_score_base(row),
        "source_url": row.get("source_url"),
        "verbatim_quote": row.get("verbatim_quote"),
        "confidence_flag": row.get("confidence_flag", "medium"),
        "last_verified_date": row.get("last_verified_date"),
        "notes": row.get("notes"),
    }


def deduplicate(rows):
    seen = set()
    deduped = []
    for row in rows:
        iso3 = row.get("country_iso3")
        if iso3 not in seen:
            seen.add(iso3)
            deduped.append(row)
    return deduped


if __name__ == "__main__":
    all_rows = []

    for source_file in SOURCE_FILES:
        if not source_file.exists():
            print(f"Missing: {source_file.name} — skipping")
            continue
        print(f"Loading {source_file.name}...")
        rows = load_json(source_file)
        normalized = [normalize_row(r) for r in rows]
        all_rows.extend(normalized)
        print(f"  {len(normalized)} rows loaded")

    before = len(all_rows)
    all_rows = deduplicate(all_rows)
    print(f"\nDeduplication: {before} → {len(all_rows)} rows")
    print(f"Total rows: {len(all_rows)}")

    SEED_PATH.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Saved to {OUTPUT_FILE}")