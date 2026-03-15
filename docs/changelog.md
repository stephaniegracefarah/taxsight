# taxsight Changelog

## Q1 2026 — March 2026 (Phase 1 in progress)

### STUB Validation Result
- STUB (StubHub Holdings) checked against Tier 1 geographic segment policy
- Result: **FAIL** — srt_StatementGeographicalAxis contains only `country:US`, 
  `country:CH`, `us-gaap:NonUsMember`, and `stub:RestOfWorldMember`
- Classification: Tier 3 (US + one named country + catch-all only)
- UBER checked as primary replacement — **FAIL** — regional aggregates only 
  (EMEA, APAC, LATAM), no individual countries beyond GB
- DASH checked as secondary replacement — **PASS** — Tier 1 confirmed
- **Hero ticker replacement: EBAY** (US, UK, Germany, China all named — clean Tier 1)
- Final Phase 1 hero tickers: ETSY, ABNB, SPOT, EBAY, FVRR

### Dataset
- Phase 1 build started March 2026
- Platform reporting regime only (DAC7, UK DPI, Canada DPI)
- 10 verified tickers: ETSY, ABNB, SPOT, EBAY, FVRR, DASH, UBER, NFLX, AMZN, EBAY