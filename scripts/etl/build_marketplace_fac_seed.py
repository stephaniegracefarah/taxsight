"""
Build Marketplace Facilitator Seed CSV
Converts raw Claude ETL extraction JSON files into the
marketplace_fac seed CSV for dbt.

Two source types:
- marketplace_fac_avalara_*.json: platform-specific fields (primary)
- marketplace_fac_en_*.json: threshold fields from economic nexus page (secondary)

Threshold fields are merged into primary rows where null.
"""

import json
import csv
from pathlib import Path

ROOT = Path(__file__).parents[2]
RAW_PATH = ROOT / "data" / "raw_extractions" / "2026-Q1"
SEED_PATH = ROOT / "taxsight_dbt" / "seeds" / "marketplace_fac"
OUTPUT_FILE = SEED_PATH / "marketplace_fac.csv"

PRIMARY_FILES = [
    RAW_PATH / "marketplace_fac_avalara_am_2026Q1.json",
    RAW_PATH / "marketplace_fac_avalara_nw_2026Q1.json",
]

THRESHOLD_FILES = [
    RAW_PATH / "marketplace_fac_en_am_2026Q1.json",
    RAW_PATH / "marketplace_fac_en_nw_2026Q1.json",
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
    guidance_maturity = row.get("guidance_maturity") or "developing"

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
        "guidance_maturity": row.get("guidance_maturity") or "mature",
        "regulatory_attention_level": row.get("regulatory_attention_level") or "medium",
        "complexity_score_base": compute_complexity_score_base(row),
        "source_url": row.get("source_url"),
        "verbatim_quote": row.get("verbatim_quote"),
        "confidence_flag": row.get("confidence_flag", "medium"),
        "last_verified_date": row.get("last_verified_date"),
        "notes": row.get("notes"),
    }


def deduplicate(rows):
    """Remove duplicate state_code entries, keeping first occurrence."""
    seen = set()
    deduped = []
    for row in rows:
        key = row.get("state_code") or row.get("country_iso3")
        if key not in seen:
            seen.add(key)
            deduped.append(row)
    return deduped


def build_threshold_index(threshold_files):
    """
    Load economic nexus extractions and index by state_code.
    Returns dict keyed by state_code with threshold fields.
    """
    index = {}
    for filepath in threshold_files:
        if not filepath.exists():
            print(f"Missing threshold file: {filepath.name} — skipping")
            continue
        print(f"Loading threshold file {filepath.name}...")
        rows = load_json(filepath)
        for row in rows:
            state_code = row.get("state_code")
            if state_code:
                index[state_code] = row
        print(f"  {len(rows)} threshold rows indexed")
    return index


def merge_thresholds(primary_rows, threshold_index):
    """
    For each primary row, patch null threshold fields from
    the economic nexus index where available.

    Rules:
    - Only patch revenue_threshold_usd and transaction_threshold
      when has_revenue_threshold is True in both sources
    - When primary has has_revenue_threshold=False but economic nexus
      has a threshold, leave revenue_threshold_usd null and note the
      conflict in notes for Claude's benefit
    - Always patch has_revenue_threshold if null in primary
    """
    merged = []
    for row in primary_rows:
        state_code = row.get("state_code")
        if state_code and state_code in threshold_index:
            en_row = threshold_index[state_code]
            en_has_threshold = en_row.get("has_revenue_threshold")
            primary_has_threshold = row.get("has_revenue_threshold")

            if primary_has_threshold is None:
                # Primary didn't state — trust economic nexus
                row["has_revenue_threshold"] = en_has_threshold
                row["revenue_threshold_usd"] = en_row.get("revenue_threshold_usd")
                row["transaction_threshold"] = en_row.get("transaction_threshold")

            elif primary_has_threshold is True:
                # Primary confirms threshold exists — fill in amounts if null
                if row.get("revenue_threshold_usd") is None:
                    row["revenue_threshold_usd"] = en_row.get("revenue_threshold_usd")
                if row.get("transaction_threshold") is None:
                    row["transaction_threshold"] = en_row.get("transaction_threshold")
                # Append threshold detail notes
                en_notes = en_row.get("notes")
                if en_notes:
                    existing_notes = row.get("notes") or ""
                    row["notes"] = f"{existing_notes} | Threshold detail: {en_notes}".strip(" |")

            elif primary_has_threshold is False and en_has_threshold is True:
                # Conflict — marketplace fac page says no threshold,
                # economic nexus page says there is one.
                # Leave revenue_threshold_usd null, flag in notes for Claude.
                en_threshold = en_row.get("revenue_threshold_usd")
                conflict_note = (
                    f"No explicit marketplace facilitator threshold stated. "
                    f"Economic nexus threshold for remote sellers is ${en_threshold:,} — "
                    f"verify whether this applies to marketplace facilitators specifically."
                )
                existing_notes = row.get("notes") or ""
                row["notes"] = f"{existing_notes} | {conflict_note}".strip(" |")

        merged.append(row)
    return merged


if __name__ == "__main__":
    # Load and normalize primary marketplace fac rows
    all_rows = []
    for source_file in PRIMARY_FILES:
        if not source_file.exists():
            print(f"Missing: {source_file.name} — skipping")
            continue
        print(f"Loading {source_file.name}...")
        rows = load_json(source_file)
        normalized = [normalize_row(r) for r in rows]
        all_rows.extend(normalized)
        print(f"  {len(normalized)} rows loaded")

    # Deduplicate primary rows
    before = len(all_rows)
    all_rows = deduplicate(all_rows)
    print(f"\nDeduplication: {before} → {len(all_rows)} rows")

    # Build threshold index from economic nexus files
    threshold_index = build_threshold_index(THRESHOLD_FILES)

    # Merge threshold fields into primary rows
    all_rows = merge_thresholds(all_rows, threshold_index)
    print(f"Threshold merge complete")
    print(f"Total rows: {len(all_rows)}")

    SEED_PATH.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Saved to {OUTPUT_FILE}")