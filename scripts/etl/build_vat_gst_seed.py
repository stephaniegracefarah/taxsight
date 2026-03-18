"""
Build VAT/GST Seed CSV
Converts raw Claude ETL research extraction JSON files into the
vat_gst seed CSV for dbt.
"""

import json
import csv
from pathlib import Path

ROOT = Path(__file__).parents[2]
RAW_PATH = ROOT / "data" / "raw_extractions" / "2026-Q1"
SEED_PATH = ROOT / "taxsight_dbt" / "seeds" / "vat_gst"
OUTPUT_FILE = SEED_PATH / "vat_gst.csv"

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
    "standard_rate_pct",
    "registration_threshold_usd",
    "local_currency_code",
    "local_currency_amount",
    "deemed_supplier_rules",
    "edp_classification",
    "b2c_scope",
    "import_vat_rules",
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
    iso3 = row.get("country_iso3", "").upper()
    return f"VAT_GST_{iso3}"


def normalize_row(row):
    return {
        "obligation_id": build_obligation_id(row),
        "country_iso3": row.get("country_iso3"),
        "country_name": row.get("country_name"),
        "regime_type": row.get("regime_type", "vat_gst"),
        "regime_framework": row.get("regime_framework", "vat_gst_marketplace"),
        "is_enacted": row.get("is_enacted"),
        "effective_date": row.get("effective_date"),
        "applies_to_platform": row.get("applies_to_platform"),
        "has_revenue_threshold": row.get("has_revenue_threshold"),
        "standard_rate_pct": row.get("standard_rate_pct"),
        "registration_threshold_usd": row.get("registration_threshold_usd"),
        "local_currency_code": row.get("local_currency_code"),
        "local_currency_amount": row.get("local_currency_amount"),
        "deemed_supplier_rules": row.get("deemed_supplier_rules"),
        "edp_classification": row.get("edp_classification"),
        "b2c_scope": row.get("b2c_scope"),
        "import_vat_rules": row.get("import_vat_rules"),
        "penalty_financial_severity": row.get("penalty_financial_severity"),
        "penalty_operational_severity": row.get("penalty_operational_severity"),
        "penalties_description": row.get("penalties_description"),
        "guidance_maturity": row.get("guidance_maturity", "developing"),
        "regulatory_attention_level": row.get("regulatory_attention_level", "medium"),
        "complexity_score_base": compute_complexity_score_base(row),
        "source_url": row.get("source_url"),
        "verbatim_quote": row.get("verbatim_quote"),
        "confidence_flag": row.get("confidence_flag"),
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
    source_files = sorted(RAW_PATH.glob("vat_gst_*.json"))

    if not source_files:
        print("No VAT/GST extraction files found.")
        exit(1)

    for source_file in source_files:
        print(f"Loading {source_file.name}...")
        try:
            rows = load_json(source_file)
            normalized = [normalize_row(r) for r in rows]
            all_rows.extend(normalized)
            print(f"  {len(normalized)} rows loaded")
        except Exception as e:
            print(f"  Error loading {source_file.name}: {e}")

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