# TECHNICAL INVESTIGATION REPORT
## ANAC Analytics & Public Procurement Data Sources

**Date**: 2026-08-21
**Status**: COMPLETED — Critical findings

---

## 1. EXACT CURRENT DATA ARCHITECTURE

### ANAC Data Infrastructure

| Component | URL | Update Frequency | Access |
|-----------|-----|------------------|--------|
| **ANAC Open Data Portal** | https://dati.anticorruzione.it/opendata | Monthly | Direct download |
| **ANAC OCDS Portal** | https://dati.anticorruzione.it/opendata/ocds_it | Monthly | Direct download |
| **ANAC Analytics** | https://www.anticorruzione.it/analytics | Daily (claimed) | Web interface |
| **PDND API (Consultazione BDNCP)** | https://api.gov.it/.../8cc63078-fa20-4c32-8a4b-5a8b510297c2 | Real-time (claimed) | REST API (auth required) |

### ANAC Open Data (Monthly)

| Dataset | Format | Records | Coverage |
|---------|--------|---------|----------|
| CIG (bandi) | CSV/JSON | ~40K-80K/month | Above-threshold tenders |
| Partecipanti | CSV/JSON | ~500K/month | Participants |
| Pubblicazioni | CSV/JSON | ~300K/month | Publications |
| OCDS | JSON/CSV | ~8K/year | Structured data |

### ANAC OCDS (Annual)

| Dataset | Format | Records | Coverage |
|---------|--------|---------|----------|
| 2025 | JSONL | 8,601 | Full year |
| 2024 | JSONL | ~48K | Full year |
| 2023 | JSONL | ~45K | Full year |

---

## 2. EXACT ACCESS METHOD

### ANAC Monthly Open Data (Verified)

```
URL: https://dati.anticorruzione.it/opendata/download/dataset/cig-{YYYY}/filesystem/cig_csv_{YYYY}_{MM}.zip
Method: GET
Auth: None
Format: CSV (semicolon-delimited)
```

### ANAC OCDS (Verified)

```
URL: https://data.open-contracting.org/en/publication/117/download?name={YYYY}.jsonl.gz
Method: GET
Auth: None
Format: JSONL (gzip)
```

### PDND API (Not Publicly Accessible)

```
URL: https://api.gov.it/en/catalogue/8cc63078-fa20-4c32-8a4b-5a8b510297c2
Method: REST (POST)
Auth: Required (PDND Interop)
Status: Active but restricted access
```

### TED API (Tested)

```
URL: https://api.ted.europa.eu/v3/notices/search
Method: POST
Auth: None (public)
Format: JSON
Query: Lucene syntax
Fields: Specific TED field names required
```

---

## 3. CURRENT-DATA TEST RESULTS

### ANAC Monthly Open Data (August 2025)

| Metric | Value |
|--------|-------|
| Total records | 79,140 |
| Date range | 2025-08-01 to 2025-08-31 |
| Deadline range | 2015-01-01 to 2028-06-30 |
| **Active (deadline >= 2026-08-21)** | **6** |
| IT Services active | 0 |
| Construction active | 1 |
| Cleaning active | 4 |

### ANAC OCDS 2025 (open-contracting.org)

| Metric | Value |
|--------|-------|
| Total records | 8,601 |
| Date range | 2025-01-01 to 2025-09-01 |
| Deadline range | 2022-01-03 to 2025-03-27 |
| **Active (deadline >= 2026-08-21)** | **0** |

### TED API (Tested)

| Query | Result |
|-------|--------|
| `*:*` (all) | Works, returns notices |
| `publication-date:[2025-08-01 TO 2025-08-31]` | Works |
| `main-classification:45` | Works |
| **Current tenders (deadline >= 2026-08-21)** | **Not directly queryable** |

**TED API Limitations**:
- Complex field names (e.g., `deadline-receipt-tender-date-lot`)
- No direct "active tenders" filter
- Requires post-processing to identify active tenders

---

## 4. SOURCE COMPARISON

| Source | Freshness | Coverage | Access | Quality | Cost |
|--------|-----------|----------|--------|---------|------|
| **ANAC Monthly** | Monthly | Above-threshold | Direct download | High | €0 |
| **ANAC OCDS** | Annual | Above-threshold | Direct download | High | €0 |
| **ANAC Analytics** | Daily (claimed) | Full | Web scraping | Unknown | €0 |
| **PDND API** | Real-time | Full | Auth required | High | €0 |
| **TED API** | Daily | EU > threshold | Public API | High | €0 |
| **MEPA** | Real-time | Below-threshold | Scraping/API | Medium | €0 |

### Detailed Comparison

| Criterion | ANAC Monthly | ANAC OCDS | TED API | MEPA |
|-----------|--------------|-----------|---------|------|
| **Active tenders** | ~6/month | 0 | Unknown | Unknown |
| **Update latency** | 30-60 days | 365 days | 1-7 days | Real-time |
| **CPV coverage** | 43.9% | 100% | 100% | 100% |
| **Legal risk** | None | None | None | Low |
| **Implementation** | Trivial | Trivial | Complex | Complex |
| **Automation** | Full | Full | Full | Partial |

---

## 5. LEGAL/TECHNICAL RISKS

### ANAC Monthly Open Data

| Risk | Level | Notes |
|------|-------|-------|
| **Legal** | NONE | Public data, no restrictions |
| **Technical** | LOW | Simple CSV download |
| **Data quality** | MEDIUM | 56.1% missing CPV |
| **Freshness** | **CRITICAL** | Monthly refresh = mostly expired |

### ANAC Analytics Scraping

| Risk | Level | Notes |
|------|-------|-------|
| **Legal** | MEDIUM | ToS may prohibit scraping |
| **Technical** | MEDIUM | Requires browser automation |
| **Data quality** | Unknown | Not tested |
| **Freshness** | HIGH (claimed) | Daily updates |

### TED API

| Risk | Level | Notes |
|------|-------|-------|
| **Legal** | NONE | Public API |
| **Technical** | HIGH | Complex query syntax |
| **Data quality** | HIGH | Structured data |
| **Freshness** | HIGH | Daily updates |

### MEPA

| Risk | Level | Notes |
|------|-------|-------|
| **Legal** | LOW | Public data |
| **Technical** | HIGH | No public API |
| **Data quality** | MEDIUM | Unstructured |
| **Freshness** | HIGH | Real-time |

---

## 6. RECOMMENDED ARCHITECTURE

### Option A: ANAC Monthly (Current) — NOT VIABLE

**Problem**: Only 6 active tenders per month. Cannot support a product.

### Option B: TED API — VIABLE but Complex

**Pros**:
- Daily updates
- EU-wide coverage
- Public API, no auth
- High data quality

**Cons**:
- Complex query syntax
- No direct "active tenders" filter
- Requires post-processing
- Only EU-threshold tenders (>€40K)

**Implementation effort**: 3-5 days

### Option C: ANAC Analytics Scraping — VIABLE but Risky

**Pros**:
- Daily updates (claimed)
- Full Italian coverage
- No authentication

**Cons**:
- ToS may prohibit scraping
- Requires browser automation
- Fragile (website changes break scraper)
- Legal risk

**Implementation effort**: 5-10 days

### Option D: ANAC + TED Hybrid — RECOMMENDED

**Pros**:
- Combines Italian + EU coverage
- TED is legal and public
- ANAC provides historical context

**Cons**:
- Two data sources to maintain
- Still missing MEPA (below-threshold)

**Implementation effort**: 5-7 days

---

## 7. ESTIMATED IMPLEMENTATION EFFORT

| Phase | Option B (TED) | Option C (Scraping) | Option D (Hybrid) |
|-------|----------------|---------------------|-------------------|
| Research | 1 day | 1 day | 1 day |
| Prototype | 2 days | 3 days | 3 days |
| Testing | 1 day | 2 days | 2 days |
| Integration | 1 day | 2 days | 2 days |
| **Total** | **5 days** | **8 days** | **8 days** |

---

## 8. ESTIMATED OPERATING COST

| Item | Cost/Month | Notes |
|------|------------|-------|
| TED API | €0 | Free public API |
| ANAC data | €0 | Free public data |
| Server | €0 | Current sufficient |
| Email | €0 | Gmail free tier |
| **Total** | **€0** | |

---

## 9. WHETHER THIS OPPORTUNITY REMAINS VIABLE

### Verdict: **CONDITIONALLY VIABLE**

| Condition | Status |
|-----------|--------|
| **Data availability** | ✅ TED API provides current data |
| **Legal compliance** | ✅ Public APIs, no personal data |
| **Technical feasibility** | ⚠️ Complex but achievable |
| **Product viability** | ⚠️ Requires TED API integration |
| **Market demand** | ✅ Proven (competitors exist) |

### Critical Success Factor

> **The product is ONLY viable if we can integrate TED API or ANAC Analytics. ANAC monthly open data alone is NOT sufficient.**

---

## 10. WHAT THE MINIMUM VIABLE PRODUCT SHOULD CONTAIN

### MVP Scope (Revised)

| Feature | Source | Effort |
|---------|--------|--------|
| **Weekly TED tender alerts** | TED API | 3 days |
| **CPV-based filtering** | TED API | 1 day |
| **Geographic filtering** | TED API | 1 day |
| **Email delivery** | Gmail | 0.5 days |
| **Customer profiles** | Google Sheets | 0.5 days |
| **Weekly reports** | Python | 1 day |
| **Total** | | **7 days** |

### MVP Promise (Honest)

> "Every week, we identify and prioritize the most relevant EU and Italian public procurement opportunities for your company, based on TED and ANAC data."

### What MVP Does NOT Include

- ❌ Real-time monitoring (TED updates daily)
- ❌ Below-threshold tenders (MEPA not integrated)
- ❌ Eligibility verification
- ❌ Complete Italian coverage (only TED + ANAC above-threshold)

---

## CONCLUSION

| Question | Answer |
|----------|--------|
| **Is ANAC monthly data sufficient?** | NO — only 6 active tenders/month |
| **Is TED API viable?** | YES — but complex integration |
| **Is ANAC Analytics scraping viable?** | MAYBE — but legal risk |
| **Is the opportunity viable?** | YES — with TED API integration |
| **Recommended path** | Option D (TED + ANAC hybrid) |
| **Implementation effort** | 5-8 days |
| **Operating cost** | €0 |

---

**RECOMMENDATION**: Proceed with TED API integration (Option B/D). Do NOT proceed with ANAC monthly data alone.

---

**STOP — Awaiting CEO decision on recommended architecture.**
