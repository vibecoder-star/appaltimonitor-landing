#!/usr/bin/env python3
"""
AppaltiMonitor — Demo Report Generator for 10 SME Profiles
"""

import json
import os
import sys
sys.path.insert(0, '/opt/autonomous-venture-engine/appalti-monitor')

from mvp_pipeline import PipelineOrchestrator, ProfileEngine
from datetime import datetime

# 10 realistic Italian SME profiles
PROFILES = [
    {
        "id": "edilpro_milano",
        "company_name": "EdilPro SRL (Demo)",
        "industry": "Costruzioni edili",
        "cpv_codes": ["45"],
        "cpv_detailed": ["45210000", "45230000", "45110000"],
        "countries": ["ITA"],
        "value_min": 200000,
        "value_max": 2000000,
        "keywords": ["costruzioni", "edilizia", "manutenzione", "ristrutturazione", "opere", "lavori"],
        "excluded_keywords": ["software", "informatica", "medicinali"],
        "preferred_buyers": ["COMUNE", "REGIONE", "ANAS", "FERROVIE"],
        "notes": "PMI costruzioni Milano - 15-20 dipendenti"
    },
    {
        "id": "manutenzioni_roma",
        "company_name": "ManutenzioniStrutturali SRL (Demo)",
        "industry": "Manutenzione e restauro edifici",
        "cpv_codes": ["45"],
        "cpv_detailed": ["45420000", "45262522", "45210000"],
        "countries": ["ITA"],
        "value_min": 50000,
        "value_max": 500000,
        "keywords": ["restauro", "manutenzione", "edilizia", "ristrutturazione"],
        "excluded_keywords": ["software", "informatica"],
        "preferred_buyers": ["COMUNE", "PROVINCIA", "MINISTERO"],
        "notes": "PMI restauro Roma - 8-12 dipendenti"
    },
    {
        "id": "infrastrutture_bologna",
        "company_name": "InfrastruttureVerdi SRL (Demo)",
        "industry": "Opere infrastrutturali e verde pubblico",
        "cpv_codes": ["45"],
        "cpv_detailed": ["45230000", "45110000", "45220000"],
        "countries": ["ITA"],
        "value_min": 500000,
        "value_max": 5000000,
        "keywords": ["infrastrutture", "strade", "ponti", "verde", "opere"],
        "excluded_keywords": ["software", "informatica"],
        "preferred_buyers": ["ANAS", "REGIONE", "COMUNE", "MIT"],
        "notes": "PMI infrastrutture Bologna - 25-40 dipendenti"
    },
    {
        "id": "edilrestauro_firenze",
        "company_name": "EdilRestauro Cooperativa (Demo)",
        "industry": "Restauro e recupero edifici",
        "cpv_codes": ["45"],
        "cpv_detailed": ["45420000", "45210000", "45330000"],
        "countries": ["ITA"],
        "value_min": 50000,
        "value_max": 300000,
        "keywords": ["restauro", "recupero", "beni culturali", "edilizia"],
        "excluded_keywords": ["software", "informatica"],
        "preferred_buyers": ["MINISTERO", "COMUNE", "SOPRINTENDENZA"],
        "notes": "Cooperativa restauro Firenze - 5-10 dipendenti"
    },
    {
        "id": "techsolutions_milano",
        "company_name": "TechSolutions SRL (Demo)",
        "industry": "Sviluppo software e servizi IT",
        "cpv_codes": ["72", "48"],
        "cpv_detailed": ["72260000", "72210000", "72510000"],
        "countries": ["ITA"],
        "value_min": 30000,
        "value_max": 300000,
        "keywords": ["software", "informatica", "cloud", "cybersecurity", "sviluppo", "integrazione", "digitale"],
        "excluded_keywords": ["farmaci", "medicinali", "costruzioni"],
        "preferred_buyers": ["ASST", "AZIENDA", "COMUNE", "REGIONE", "MINISTERO"],
        "notes": "PMI IT Milano - 10-15 dipendenti"
    },
    {
        "id": "cloudnet_roma",
        "company_name": "CloudNet SRL (Demo)",
        "industry": "Cloud computing e infrastrutture IT",
        "cpv_codes": ["72", "48"],
        "cpv_detailed": ["72413000", "72510000", "72260000"],
        "countries": ["ITA"],
        "value_min": 50000,
        "value_max": 500000,
        "keywords": ["cloud", "infrastruttura", "migrazione", "data center", "IT"],
        "excluded_keywords": ["farmaci", "medicinali", "costruzioni"],
        "preferred_buyers": ["CONSIP", "REGIONE", "MINISTERO", "PA"],
        "notes": "PMI cloud Roma - 8-12 dipendenti"
    },
    {
        "id": "cybersecure_torino",
        "company_name": "CyberSecure SRL (Demo)",
        "industry": "Sicurezza informatica",
        "cpv_codes": ["72"],
        "cpv_detailed": ["72413000", "72510000"],
        "countries": ["ITA"],
        "value_min": 20000,
        "value_max": 200000,
        "keywords": ["sicurezza", "cybersecurity", "protezione", "IT", "informatica"],
        "excluded_keywords": ["farmaci", "medicinali", "costruzioni"],
        "preferred_buyers": ["ACN", "MINISTERO", "REGIONE", "PA"],
        "notes": "PMI cybersecurity Torino - 5-8 dipendenti"
    },
    {
        "id": "digitpa_bologna",
        "company_name": "DigitPA SRL (Demo)",
        "industry": "Trasformazione digitale PA",
        "cpv_codes": ["72", "48"],
        "cpv_detailed": ["72210000", "72260000", "72510000"],
        "countries": ["ITA"],
        "value_min": 100000,
        "value_max": 1000000,
        "keywords": ["digitale", "trasformazione", "software", "PA", "informatica"],
        "excluded_keywords": ["farmaci", "medicinali", "costruzioni"],
        "preferred_buyers": ["COMUNE", "PROVINCIA", "REGIONE", "MINISTERO"],
        "notes": "PMI digitalizzazione Bologna - 15-25 dipendenti"
    },
    {
        "id": "pulizieverde_napoli",
        "company_name": "PulizieVerde SRL (Demo)",
        "industry": "Pulizie civili e industriali",
        "cpv_codes": ["90", "99"],
        "cpv_detailed": ["90511000", "90480000", "90620000"],
        "countries": ["ITA"],
        "value_min": 20000,
        "value_max": 200000,
        "keywords": ["pulizie", "manutenzione", "igiene", "sanificazione", "facility", "rifiuti"],
        "excluded_keywords": ["software", "informatica", "costruzioni"],
        "preferred_buyers": ["COMUNE", "ASST", "OSPEDALE"],
        "notes": "PMI pulizie Napoli - 20-30 dipendenti"
    },
    {
        "id": "facilitymulti_genova",
        "company_name": "FacilityMulti SRL (Demo)",
        "industry": "Facility management integrato",
        "cpv_codes": ["90", "99", "79"],
        "cpv_detailed": ["90511000", "90620000", "79990000"],
        "countries": ["ITA"],
        "value_min": 50000,
        "value_max": 500000,
        "keywords": ["facility", "manutenzione", "servizi", "pulizie", "gestione"],
        "excluded_keywords": ["software", "informatica", "costruzioni"],
        "preferred_buyers": ["CONSIP", "COMUNE", "REGIONE", "OSPEDALE"],
        "notes": "PMI facility Genova - 30-50 dipendenti"
    }
]


def generate_demo_reports():
    """Generate demo reports for all 10 profiles"""
    print("=" * 70)
    print("AppaltiMonitor — Demo Report Generation")
    print("=" * 70)
    
    # Clean old profiles
    profiles_dir = '/opt/autonomous-venture-engine/appalti-monitor/profiles'
    for f in os.listdir(profiles_dir):
        os.remove(os.path.join(profiles_dir, f))
    
    # Create all profiles
    engine = ProfileEngine()
    for p in PROFILES:
        engine.create_profile(p)
        print(f"Created profile: {p['id']}")
    
    # Run pipeline for each
    orchestrator = PipelineOrchestrator()
    results = []
    
    for p in PROFILES:
        print(f"\n{'='*70}")
        print(f"Running: {p['company_name']}")
        print(f"{'='*70}")
        
        status = orchestrator.run(p["id"])
        results.append({
            "profile": p,
            "status": status
        })
        
        if status.get("error"):
            print(f"ERROR: {status['error']}")
        else:
            print(f"High: {status['high_priority']}, Medium: {status['medium_priority']}, Low: {status['low_priority']}")
    
    # Save summary
    summary_path = '/opt/autonomous-venture-engine/appalti-monitor/commercial-validation/demo_results.json'
    with open(summary_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n{'='*70}")
    print(f"ALL DEMO REPORTS GENERATED")
    print(f"Summary: {summary_path}")
    print(f"{'='*70}")
    
    return results


if __name__ == "__main__":
    generate_demo_reports()
