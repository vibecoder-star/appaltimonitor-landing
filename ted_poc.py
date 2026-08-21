#!/usr/bin/env python3
"""
AppaltiMonitor — TED Search API v3 POC v2
Public Procurement Intelligence for Italian SMEs
"""

import csv
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

# TED API Configuration
TED_API_URL = "https://api.ted.europa.eu/v3/notices/search"
TED_API_KEY = None  # Public API, no key required for basic use

# Output directory
OUTPUT_DIR = Path("/opt/autonomous-venture-engine/appalti-monitor/output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# SME Profiles
SME_PROFILES = {
    "sme_a_it": {
        "name": "SME A — IT Services",
        "description": "Software development, IT consulting, cloud services, cybersecurity",
        "cpv_codes": ["72", "48", "302"],
        "keywords": ["software", "informatica", "cloud", "cybersecurity", "sviluppo", "integrazione", "digitale", "piattaforma", "applicazione"],
        "countries": ["IT"],
        "value_min": 30000,
        "value_max": 500000,
        "buyer_pref": ["ASST", "AZIENDA", "COMUNE", "REGIONE", "MINISTERO", "UNIVERSITA"]
    },
    "sme_b_construction": {
        "name": "SME B — Construction",
        "description": "Building construction, renovation, civil engineering",
        "cpv_codes": ["45"],
        "keywords": ["costruz", "ediliz", "manutenz", "ristruttur", "opere", "lavori", "sopraelev", "rifaciment"],
        "countries": ["IT"],
        "value_min": 50000,
        "value_max": 2000000,
        "buyer_pref": ["COMUNE", "REGIONE", "ANAS", "FERROVIE", "MIT"]
    },
    "sme_c_cleaning": {
        "name": "SME C — Cleaning & Facility",
        "description": "Industrial cleaning, building maintenance, waste management",
        "cpv_codes": ["90", "99"],
        "keywords": ["puliz", "manutenz", "igiene", "sanific", "facility", "rifiut", "verde", "condomin"],
        "countries": ["IT"],
        "value_min": 10000,
        "value_max": 200000,
        "buyer_pref": ["COMUNE", "ASST", "AZIENDA", "OSPEDALE"]
    }
}

def build_ted_query(profile, date_from=None, date_to=None):
    """Build TED expert query using correct syntax"""
    if not date_from:
        date_from = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")
    if not date_to:
        date_to = datetime.now().strftime("%Y%m%d")
    
    # Build CPV filter using IN syntax
    cpv_codes = " ".join([f"{cpv}*" for cpv in profile["cpv_codes"]])
    cpv_filter = f"classification-cpv IN ({cpv_codes})"
    
    # Build country filter
    countries = " ".join(profile["countries"])
    country_filter = f"buyer-country IN ({countries})"
    
    # Build date filter using range syntax
    date_filter = f"publication-date = ({date_from} <> {date_to})"
    
    # Combine
    query = f"({date_filter}) AND ({country_filter}) AND ({cpv_filter})"
    
    return query

def call_ted_api(query, fields, page=1, limit=50):
    """Call TED Search API v3"""
    import urllib.request
    import urllib.error
    
    payload = {
        "query": query,
        "fields": fields,
        "page": page,
        "limit": limit,
        "scope": "ALL",
        "checkQuerySyntax": False,
        "paginationMode": "PAGE_NUMBER",
        "onlyLatestVersions": False
    }
    
    if TED_API_KEY:
        payload["apiKey"] = TED_API_KEY
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    req = urllib.request.Request(
        TED_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        return {"error": True, "status": e.code, "message": body}
    except Exception as e:
        return {"error": True, "message": str(e)}

def parse_tender_notice(notice):
    """Parse a TED notice into our normalized schema"""
    # Extract fields from TED notice structure
    f = notice.get("fields", {})
    
    # Get title
    title = f.get("notice-title", [""])[0] if isinstance(f.get("notice-title"), list) else f.get("notice-title", "")
    
    # Get buyer
    buyer = f.get("buyer-name", [""])[0] if isinstance(f.get("buyer-name"), list) else f.get("buyer-name", "")
    
    # Get CPV
    cpv = f.get("classification-cpv", [""])[0] if isinstance(f.get("classification-cpv"), list) else f.get("classification-cpv", "")
    cpv_desc = f.get("classification-cpv-description", [""])[0] if isinstance(f.get("classification-cpv-description"), list) else ""
    
    # Get publication date
    pub_date = f.get("publication-date", [""])[0] if isinstance(f.get("publication-date"), list) else f.get("publication-date", "")
    
    # Get deadline
    deadline = f.get("deadline-receipt-tender-date-lot", [""])[0] if isinstance(f.get("deadline-receipt-tender-date-lot"), list) else f.get("deadline-receipt-tender-date-lot", "")
    
    # Get value
    value = f.get("estimated-value-cur-lot", [""])[0] if isinstance(f.get("estimated-value-cur-lot"), list) else f.get("estimated-value-cur-lot", "")
    
    # Get place of performance
    place = f.get("place-of-performance", [""])[0] if isinstance(f.get("place-of-performance"), list) else f.get("place-of-performance", "")
    
    # Get notice identifier
    notice_id = f.get("notice-identifier", [""])[0] if isinstance(f.get("notice-identifier"), list) else f.get("notice-identifier", "")
    
    # Get procedure type
    proc_type = f.get("form-type", [""])[0] if isinstance(f.get("form-type"), list) else f.get("form-type", "")
    
    # Build source URL
    source_url = f"https://ted.europa.eu/en/notice/{notice_id}" if notice_id else ""
    
    # Parse deadline
    deadline_date = None
    if deadline:
        try:
            deadline_date = datetime.strptime(deadline[:10], "%Y-%m-%d")
        except:
            pass
    
    # Check if active
    is_active = False
    if deadline_date:
        is_active = deadline_date >= datetime.now()
    
    # Parse value
    value_num = None
    if value:
        try:
            value_num = float(str(value).replace(",", "").replace(" ", ""))
        except:
            pass
    
    return {
        "notice_id": notice_id,
        "title": title[:200],
        "buyer": buyer[:100],
        "country": "IT",
        "place_performance": place[:100],
        "cpv": cpv[:20],
        "publication_date": pub_date[:10],
        "deadline": deadline[:10] if deadline else "",
        "is_active": is_active,
        "estimated_value": value_num,
        "procedure_type": proc_type,
        "source_url": source_url
    }

def filter_by_profile(tenders, profile):
    """Filter tenders by SME profile"""
    filtered = []
    for t in tenders:
        # Check value
        if t["estimated_value"]:
            if t["estimated_value"] < profile["value_min"] or t["estimated_value"] > profile["value_max"]:
                continue
        
        # Check CPV match
        cpv = t.get("cpv", "")
        cpv_match = any(cpv.startswith(c) for c in profile["cpv_codes"])
        
        # Check keyword match
        title = t.get("title", "").lower()
        keyword_match = any(kw.lower() in title for kw in profile["keywords"])
        
        if cpv_match or keyword_match:
            t["match_reasons"] = []
            if cpv_match:
                t["match_reasons"].append("cpv_match")
            if keyword_match:
                t["match_reasons"].append("keyword_match")
            filtered.append(t)
    
    return filtered

def rank_tenders(tenders, profile):
    """Rank tenders by relevance"""
    for t in tenders:
        score = 0
        
        # Value score (higher is better, within range)
        if t["estimated_value"]:
            value_range = profile["value_max"] - profile["value_min"]
            if value_range > 0:
                value_score = (t["estimated_value"] - profile["value_min"]) / value_range
                score += min(value_score, 1.0) * 30
        
        # Active deadline bonus
        if t["is_active"]:
            score += 25
        
        # CPV exact match
        cpv = t.get("cpv", "")
        if any(cpv.startswith(c) for c in profile.get("cpv_exact", [])):
            score += 20
        
        # Buyer preference
        buyer = t.get("buyer", "")
        if any(bp.upper() in buyer.upper() for bp in profile.get("buyer_pref", [])):
            score += 15
        
        t["score"] = round(score, 1)
    
    tenders.sort(key=lambda x: x["score"], reverse=True)
    return tenders

def generate_sme_report(profile, tenders, top_n=5):
    """Generate intelligence report for an SME profile"""
    report = []
    report.append(f"=== WEEKLY PROCUREMENT INTELLIGENCE REPORT ===")
    report.append(f"Profile: {profile['name']}")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append(f"")
    report.append(f"NEW RELEVANT TENDERS: {len(tenders)}")
    report.append(f"")
    
    # High priority (score > 50)
    high = [t for t in tenders if t["score"] > 50]
    medium = [t for t in tenders if 30 < t["score"] <= 50]
    low = [t for t in tenders if t["score"] <= 30]
    
    if high:
        report.append(f"HIGH PRIORITY ({len(high)} tenders):")
        for i, t in enumerate(high[:top_n], 1):
            report.append(f"")
            report.append(f"{i}. {t['title'][:70]}")
            report.append(f"   Score: {t['score']} | Notice: {t['notice_id']}")
            report.append(f"   Buyer: {t['buyer'][:50]}")
            report.append(f"   Value: €{t['estimated_value']:,.2f}" if t['estimated_value'] else "   Value: Not specified")
            report.append(f"   Deadline: {t['deadline']}" if t['deadline'] else "   Deadline: Not specified")
            report.append(f"   CPV: {t['cpv']} - {t['cpv_description'][:40]}")
            report.append(f"   Status: {'ACTIVE' if t['is_active'] else 'EXPIRED/UNKNOWN'}")
            report.append(f"   Why: {', '.join(t.get('match_reasons', []))}")
            report.append(f"   URL: {t['source_url']}")
    
    if medium:
        report.append(f"")
        report.append(f"MEDIUM PRIORITY ({len(medium)} tenders):")
        for i, t in enumerate(medium[:3], 1):
            report.append(f"")
            report.append(f"{i}. {t['title'][:70]}")
            report.append(f"   Score: {t['score']} | Value: €{t['estimated_value']:,.2f}" if t['estimated_value'] else f"   Score: {t['score']}")
            report.append(f"   Deadline: {t['deadline']}" if t['deadline'] else "   Deadline: Not specified")
    
    report.append(f"")
    report.append(f"RECOMMENDATION:")
    if high:
        report.append(f"- Pursue top {min(3, len(high))} high-priority tenders")
        report.append(f"- Review deadlines and prepare documentation")
    else:
        report.append(f"- No high-priority tenders this week")
        report.append(f"- Consider expanding search criteria")
    
    return "\n".join(report)

def run_ted_poc():
    """Run the TED POC for all SME profiles"""
    print("=" * 60)
    print("AppaltiMonitor — TED Search API v3 POC")
    print("=" * 60)
    
    # Define fields to retrieve (CORRECTED based on TED API supported fields)
    fields = [
        "notice-identifier",
        "notice-title",
        "buyer-name",
        "buyer-country",
        "place-of-performance",
        "classification-cpv",
        "publication-date",
        "deadline-receipt-tender-date-lot",
        "estimated-value-cur-lot",
        "form-type"
    ]
    
    all_results = {}
    
    for profile_id, profile in SME_PROFILES.items():
        print(f"\n{'='*60}")
        print(f"Processing: {profile['name']}")
        print(f"{'='*60}")
        
        # Build query
        query = build_ted_query(profile)
        print(f"Query: {query}")
        
        # Call TED API
        result = call_ted_api(query, fields, page=1, limit=50)
        
        if result.get("error"):
            print(f"ERROR: {result.get('message', 'Unknown error')}")
            all_results[profile_id] = {"error": result, "tenders": []}
            continue
        
        # Parse results
        notices = result.get("notices", [])
        total_count = result.get("totalCount", 0)
        page_count = result.get("pageCount", 1)
        
        print(f"Total notices found: {total_count}")
        print(f"Pages: {page_count}")
        print(f"Notices in this page: {len(notices)}")
        
        # Parse each notice
        tenders = []
        for notice in notices:
            tender = parse_tender_notice(notice)
            tenders.append(tender)
        
        print(f"Parsed: {len(tenders)} tenders")
        
        # Filter by profile
        filtered = filter_by_profile(tenders, profile)
        print(f"After filtering: {len(filtered)} tenders")
        
        # Rank
        ranked = rank_tenders(filtered, profile)
        
        # Count active
        active = [t for t in ranked if t["is_active"]]
        print(f"Active tenders: {len(active)}")
        
        # Generate report
        report = generate_sme_report(profile, ranked)
        report_path = OUTPUT_DIR / f"ted_report_{profile_id}.txt"
        with open(report_path, "w") as f:
            f.write(report)
        print(f"Report saved: {report_path}")
        
        # Save tenders to JSON
        json_path = OUTPUT_DIR / f"ted_tenders_{profile_id}.json"
        with open(json_path, "w") as f:
            json.dump(ranked[:20], f, indent=2, default=str)
        print(f"Tenders saved: {json_path}")
        
        # Save to CSV
        csv_path = OUTPUT_DIR / f"ted_tenders_{profile_id}.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["notice_id", "title", "buyer", "country", "place_performance", "cpv", "cpv_description", "publication_date", "deadline", "is_active", "estimated_value", "currency", "procedure_type", "source_url", "score", "match_reasons"])
            writer.writeheader()
            for t in ranked[:20]:
                row = t.copy()
                row["match_reasons"] = ", ".join(row.get("match_reasons", []))
                writer.writerow(row)
        print(f"CSV saved: {csv_path}")
        
        all_results[profile_id] = {
            "profile": profile["name"],
            "total_found": total_count,
            "parsed": len(tenders),
            "filtered": len(filtered),
            "active": len(active),
            "top_score": ranked[0]["score"] if ranked else 0,
            "report_path": str(report_path)
        }
        
        # Print top 3
        print(f"\nTop 3 tenders:")
        for t in ranked[:3]:
            print(f"  - {t['title'][:60]}")
            print(f"    Score: {t['score']} | Value: €{t['estimated_value']:,.2f}" if t['estimated_value'] else f"    Score: {t['score']}")
            print(f"    Deadline: {t['deadline']}" if t['deadline'] else "    Deadline: N/A")
            print(f"    Active: {t['is_active']}")
    
    # Save summary
    summary_path = OUTPUT_DIR / "ted_poc_summary.json"
    with open(summary_path, "w") as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"POC COMPLETE")
    print(f"Summary saved: {summary_path}")
    
    return all_results

if __name__ == "__main__":
    run_ted_poc()
