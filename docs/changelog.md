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

## README Notes — To Address Before Launch

### Limitations / Considerations Section
The README should include an honest limitations section covering:

- **Source URL stability** — ETL extraction scripts assume source URLs remain 
  stable. Government and regulatory pages move without notice (e.g. all three 
  original DAC7/UK/Canada URLs returned 404 and required manual correction 
  during Phase 1 build). Quarterly refresh checklist includes URL validation 
  as a manual step.

- **Regulatory scope assumptions** — Scripts assume country-regime applicability 
  is static between quarterly refreshes. Real-world changes (e.g. UK leaving the 
  EU and implementing its own DPI rules rather than DAC7) require manual review 
  and seed CSV updates. taxsight is a point-in-time snapshot, not a real-time 
  monitor.

- **Country classification** — ISO3 codes and country-regime mappings reflect 
  the regulatory landscape as of the last_verified_date in the dataset. 
  Political or regulatory changes between refreshes are not automatically detected.

- **v1 scope** — Real-time rule updates, filing preparation, and private company 
  data are explicitly out of scope. See TDD Section 10.


  ### ETL Architecture — Lessons Learned During Phase 1 Seed Build

**Scrape vs. Research approach:**
Two distinct ETL strategies emerged during Phase 1 seed construction:

**Scrape approach** (fetch URL → pass HTML to Claude → extract JSON):
- Best when: single authoritative source exists, page is scrapable, data is structured
- Used for: DAC7 (EU Commission), UK DPI (HMRC), Canada DPI (CRA), 
  DST (Tax Foundation, GOV.UK), Marketplace Facilitator (Avalara state guide)
- Works well for government pages and aggregator pages with stable URLs

**Research approach** (Claude uses web search → finds own sources → returns JSON):
- Best when: data is fragmented across many country-specific sources,
  government pages block scrapers (403), or no single comprehensive source exists
- Used for: VAT/GST marketplace rules (34 countries)
- Advantage: Claude finds current sources, cites them, and flags confidence honestly

**VAT/GST specifically:** Initial attempt used Avalara VATlive country pages via
scrape approach. Pages loaded but returned sparse data — Avalara country guides 
cover general VAT rules, not marketplace-specific deemed supplier rules. 
Switched to research approach using Claude web search with Quaderno, Avalara, 
and VATCalc as suggested starting sources. Raw extractions deleted and regenerated.

**URL stability:** Government and regulatory URLs are unstable. All three original
DAC7/UK/Canada URLs returned 404 during Phase 1 build. Quarterly refresh checklist
includes URL validation as a manual step. See README limitations section.