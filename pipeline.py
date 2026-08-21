#!/usr/bin/env python3
"""
AppaltiMonitor — Concierge MVP Pipeline v2
Public Procurement Intelligence for Italian SMEs
"""

import csv
import json
import os
import re
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from pathlib import Path

# Configuration
DATA_DIR = Path("/tmp/anac_data")
OUTPUT_DIR = Path("/opt/autonomous-venture-engine/appalti-monitor/output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Customer Profiles — STRICT matching
CUSTOMER_PROFILES = {
    "sme_a_it": {
        "name": "SME A — IT Services",
        "description": "Software development, IT consulting, cloud services, cybersecurity",
        "cpv_prefixes": ["72", "48"],
        "keywords": ["software", "informatica", "cloud", "cybersecurity", "sviluppo software", "integrazione", "digitale", "piattaforma", "applicazione", "sistema informatico", "consulenza IT", "servizi IT", "data", "database", "web", "sito web", "ecommerce", "erp", "crm", "intelligenza artificiale", "AI", "machine learning"],
        "geo_pref": ["MILANO", "BERGAMO", "BRESCIA", "VARESE", "COMO", "MONZA E BRIANZA", "LODI", "PAVIA"],
        "value_min": 30000,
        "value_max": 500000,
        "procedure_types": [],
        "excluded_cpvs": ["45", "33", "90"],
        "excluded_keywords": ["farmaci", "medicinali", "chirurgici", "vaccini", "siringhe", "dispositivi medici", "gas", "energia", "elettric", "ediliz", "costruz"],
        "eligibility_notes": "Requires public sector experience for some tenders"
    },
    "sme_b_construction": {
        "name": "SME B — Construction",
        "description": "Building construction, renovation, civil engineering",
        "cpv_prefixes": ["45"],
        "keywords": ["costruz", "ediliz", "manutenz", "ristruttur", "opere", "lavori", "sopraelev", "rifaciment", "recupero", "restauro", "impiant", "struttur"],
        "geo_pref": ["NAPOLI", "CASERTA", "SALERNO", "AVELLINO", "BENEVENTO"],
        "value_min": 50000,
        "value_max": 2000000,
        "procedure_types": [],
        "excluded_cpvs": ["72", "48", "33", "90"],
        "excluded_keywords": ["software", "informatic", "medicinali", "farmaci"],
        "eligibility_notes": "Requires ISO 9001 and sometimes specific construction licenses"
    },
    "sme_c_cleaning": {
        "name": "SME C — Cleaning & Facility",
        "description": "Industrial cleaning, building maintenance, waste management",
        "cpv_prefixes": ["90", "99"],
        "keywords": ["puliz", "manutenz", "igiene", "sanific", "facility", "rifiut", "pulizi", "lavorie", "verde", "condomin"],
        "geo_pref": ["ROMA", "LATINA", "FROSINONE", "RIETI", "VITERBO"],
        "value_min": 10000,
        "value_max": 200000,
        "procedure_types": [],
        "excluded_cpvs": ["72", "48", "45", "33"],
        "excluded_keywords": ["software", "informatic", "medicinali", "costruzioni", "edilizia"],
        "eligibility_notes": "Some tenders require environmental certifications"
    }
}

def load_anac_data():
    """Load ANAC CIG data from CSV"""
    data = []
    csv_files = list((DATA_DIR / "cig_2024").glob("cig_csv_*.csv"))
    for f in sorted(csv_files):
        with open(f, 'r', encoding='utf-8') as fh:
            reader = csv.DictReader(fh, delimiter=';')
            for row in reader:
                data.append(row)
    return data

def normalize_tender(raw):
    """Normalize raw ANAC record to clean schema"""
    try:
        value = float(raw.get('importo_lotto', 0) or 0)
    except (ValueError, TypeError):
        value = 0.0
    
    try:
        total_value = float(raw.get('importo_complessivo_gara', 0) or 0)
    except (ValueError, TypeError):
        total_value = 0.0
    
    return {
        "cig": raw.get('cig', '').strip(),
        "procedure_id": raw.get('numero_gara', '').strip(),
        "title": raw.get('oggetto_lotto', '').strip(),
        "sector": raw.get('oggetto_principale_contratto', '').strip(),
        "cpv_code": raw.get('cod_cpv', '').strip(),
        "cpv_description": raw.get('descrizione_cpv', '').strip(),
        "lot_value": value,
        "total_value": total_value,
        "num_lots": int(raw.get('n_lotti_componenti', 1) or 1),
        "status": raw.get('stato', '').strip(),
        "procedure_type": raw.get('tipo_scelta_contraente', '').strip(),
        "authority": raw.get('denominazione_amministrazione_appaltante', '').strip(),
        "authority_cf": raw.get('cf_amministrazione_appaltante', '').strip(),
        "province": raw.get('provincia', '').strip(),
        "istat_code": raw.get('luogo_istat', '').strip(),
        "region": raw.get('sezione_regionale', '').strip(),
        "publication_date": raw.get('data_pubblicazione', '').strip(),
        "deadline": raw.get('data_scadenza_offerta', '').strip(),
        "duration_days": raw.get('DURATA_PREVISTA', '').strip(),
        "is_urgent": raw.get('FLAG_URGENZA', '0') == '1',
        "is_pnrr": raw.get('FLAG_PNRR_PNC', '0') == '1',
        "outcome": raw.get('ESITO', '').strip(),
        "outcome_date": raw.get('DATA_COMUNICAZIONE_ESITO', '').strip()
    }

def is_valid_cpv(cpv_code):
    """Check if CPV code is valid (not placeholder)"""
    if not cpv_code:
        return False
    if cpv_code in ['99999999', '']:
        return False
    return bool(re.match(r'^\d{8}-\d$', cpv_code))

def matches_profile(tender, profile):
    """Check if tender matches customer profile — STRICT matching"""
    cpv = tender['cpv_code']
    title = tender['title'].lower()
    value = tender['lot_value']
    
    # Value filter
    if value < profile['value_min'] or value > profile['value_max']:
        return False, "value_out_of_range"
    
    # Excluded keywords check
    for kw in profile.get('excluded_keywords', []):
        if kw.lower() in title:
            return False, "excluded_keyword"
    
    # CPV match (strong signal)
    cpv_match = False
    if is_valid_cpv(cpv):
        for prefix in profile['cpv_prefixes']:
            if cpv.startswith(prefix):
                cpv_match = True
                break
    
    # Keyword match (only if no valid CPV, to reduce false positives)
    keyword_match = False
    if not cpv_match:
        for kw in profile['keywords']:
            if kw.lower() in title:
                keyword_match = True
                break
    
    if cpv_match or keyword_match:
        return True, "matched"
    
    return False, "no_match"

def rank_tenders(tenders, profile):
    """Rank tenders by relevance score"""
    scored = []
    for t in tenders:
        score = 0
        reasons = []
        
        # Value score (higher value = higher score, within range)
        value_range = profile['value_max'] - profile['value_min']
        if value_range > 0:
            value_score = (t['lot_value'] - profile['value_min']) / value_range
            score += value_score * 30
            if t['lot_value'] > 100000:
                reasons.append("high_value")
        
        # Geographic match
        if t['province'] in profile.get('geo_pref', []):
            score += 25
            reasons.append("preferred_location")
        elif t['province']:
            score += 10
            reasons.append("other_location")
        
        # CPV exact match (stronger than keyword)
        for prefix in profile['cpv_prefixes']:
            if t['cpv_code'].startswith(prefix):
                score += 20
                reasons.append("cpv_match")
                break
        
        # PNRR bonus (funded projects)
        if t['is_pnrr']:
            score += 10
            reasons.append("pnrr_funded")
        
        # Urgency bonus
        if t['is_urgent']:
            score += 5
            reasons.append("urgent")
        
        # Active status bonus
        if t['status'] == 'ATTIVO':
            score += 10
            reasons.append("active")
        
        t['score'] = round(score, 1)
        t['score_reasons'] = reasons
        scored.append(t)
    
    scored.sort(key=lambda x: x['score'], reverse=True)
    return scored

def generate_report(profile, tenders, top_n=10):
    """Generate intelligence report for a customer profile"""
    report = []
    report.append(f"=== WEEKLY PROCUREMENT INTELLIGENCE REPORT ===")
    report.append(f"Profile: {profile['name']}")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append(f"")
    report.append(f"NEW RELEVANT TENDERS: {len(tenders)}")
    report.append(f"")
    
    # High priority (score > 60)
    high = [t for t in tenders if t['score'] > 60]
    medium = [t for t in tenders if 40 < t['score'] <= 60]
    low = [t for t in tenders if t['score'] <= 40]
    
    if high:
        report.append(f"HIGH PRIORITY ({len(high)} tenders):")
        for i, t in enumerate(high[:top_n], 1):
            report.append(f"")
            report.append(f"{i}. CIG: {t['cig']} | Score: {t['score']}")
            report.append(f"   Title: {t['title'][:70]}")
            report.append(f"   Value: €{t['lot_value']:,.2f}")
            report.append(f"   CPV: {t['cpv_code']} - {t['cpv_description'][:40]}")
            report.append(f"   Location: {t['province']}")
            report.append(f"   Deadline: {t['deadline']}")
            report.append(f"   Authority: {t['authority'][:50]}")
            report.append(f"   Why: {', '.join(t['score_reasons'])}")
    
    if medium:
        report.append(f"")
        report.append(f"MEDIUM PRIORITY ({len(medium)} tenders):")
        for i, t in enumerate(medium[:5], 1):
            report.append(f"")
            report.append(f"{i}. CIG: {t['cig']} | Score: {t['score']}")
            report.append(f"   Title: {t['title'][:70]}")
            report.append(f"   Value: €{t['lot_value']:,.2f}")
            report.append(f"   Location: {t['province']} | Deadline: {t['deadline']}")
    
    if low:
        report.append(f"")
        report.append(f"LOW PRIORITY ({len(low)} tenders):")
        report.append(f"   (Summary available upon request)")
    
    report.append(f"")
    report.append(f"RECOMMENDATION:")
    if high:
        report.append(f"- Pursue top {min(3, len(high))} high-priority tenders")
        report.append(f"- Review deadlines and prepare documentation")
    else:
        report.append(f"- No high-priority tenders this week")
        report.append(f"- Consider expanding search criteria")
    
    return "\n".join(report)

def run_pipeline():
    """Run the full pipeline for all profiles"""
    print("Loading ANAC data...")
    raw_data = load_anac_data()
    print(f"Loaded {len(raw_data)} raw records")
    
    # Normalize
    tenders = []
    for raw in raw_data:
        t = normalize_tender(raw)
        if t['cig'] and t['lot_value'] > 0:
            tenders.append(t)
    
    print(f"Normalized {len(tenders)} valid tenders")
    
    results = {}
    
    for profile_id, profile in CUSTOMER_PROFILES.items():
        print(f"\nProcessing profile: {profile['name']}...")
        
        # Filter
        matched = []
        rejection_reasons = Counter()
        for t in tenders:
            is_match, reason = matches_profile(t, profile)
            if is_match:
                matched.append(t)
            else:
                rejection_reasons[reason] += 1
        
        # Rank
        ranked = rank_tenders(matched, profile)
        
        # Generate report
        report = generate_report(profile, ranked)
        
        # Save report
        report_path = OUTPUT_DIR / f"report_{profile_id}.txt"
        with open(report_path, 'w') as f:
            f.write(report)
        
        # Stats
        results[profile_id] = {
            "profile_name": profile['name'],
            "total_matched": len(matched),
            "high_priority": len([t for t in ranked if t['score'] > 60]),
            "medium_priority": len([t for t in ranked if 40 < t['score'] <= 60]),
            "low_priority": len([t for t in ranked if t['score'] <= 40]),
            "rejection_reasons": dict(rejection_reasons),
            "top_score": ranked[0]['score'] if ranked else 0,
            "report_path": str(report_path)
        }
        
        print(f"  Matched: {len(matched)}")
        print(f"  High priority: {results[profile_id]['high_priority']}")
        print(f"  Report saved: {report_path}")
    
    # Save summary
    summary_path = OUTPUT_DIR / "pipeline_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nPipeline complete. Summary saved: {summary_path}")
    return results

if __name__ == "__main__":
    run_pipeline()
