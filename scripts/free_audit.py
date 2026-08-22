#!/usr/bin/env python3
"""
AppaltiMonitor — Free Audit Generator
Generates a vertical-specific tender audit report for IT/cybersecurity companies.
Called by the API when a free audit is requested.
"""

import json
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

BASE_DIR = Path("/opt/autonomous-venture-engine/appalti-monitor")
sys.path.insert(0, str(BASE_DIR))

from mvp_pipeline import PipelineOrchestrator, ProfileEngine, TEDAPIClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Vertical-specific configurations
VERTICAL_CONFIGS = {
    "cybersecurity": {
        "cpv_codes": ["72", "48", "30"],
        "cpv_detailed": ["72220000", "72260000", "72510000", "48000000", "30200000"],
        "keywords": ["cybersecurity", "sicurezza", "penetration testing", "vulnerability", 
                     "SOC", "security operations", "GDPR", "privacy", "risk assessment",
                     "incident response", "forensics", "antivirus", "firewall"],
        "excluded_keywords": ["farmaci", "medicinali", "costruzioni edili"],
        "buyer_preferences": ["MINISTERO", "ASL", "OSPEDALE", "COMUNE", "REGIONE", "UNIVERSITA"],
        "description": "Sicurezza informatica e cybersecurity"
    },
    "sviluppo-software": {
        "cpv_codes": ["72", "48"],
        "cpv_detailed": ["72260000", "72262000", "72220000", "72510000", "48983000"],
        "keywords": ["sviluppo software", "software development", "applicazione", "app",
                     "web", "mobile", "cloud", "API", "integrazione", "manutenzione software",
                     "devops", "agile", "full stack"],
        "excluded_keywords": ["farmaci", "medicinali"],
        "buyer_preferences": ["MINISTERO", "COMUNE", "REGIONE", "ASL", "UNIVERSITA", "PUBBLICA AMMINISTRAZIONE"],
        "description": "Sviluppo software e applicazioni"
    },
    "cloud": {
        "cpv_codes": ["72", "48", "30"],
        "cpv_detailed": ["72510000", "72260000", "48000000", "30200000"],
        "keywords": ["cloud", "infrastrutture", "hosting", "SaaS", "IaaS", "PaaS",
                     "migration", "azure", "aws", "google cloud", "infrastrutture IT",
                     "datacenter", "virtualizzazione"],
        "excluded_keywords": ["farmaci", "medicinali"],
        "buyer_preferences": ["MINISTERO", "COMUNE", "REGIONE", "PUBBLICA AMMINISTRAZIONE"],
        "description": "Cloud computing e infrastrutture IT"
    },
    "digitale": {
        "cpv_codes": ["72", "48", "80"],
        "cpv_detailed": ["72260000", "72220000", "72510000", "80500000", "48000000"],
        "keywords": ["trasformazione digitale", "digitale", "innovazione", "e-government",
                     "smart city", "PIATTAFORMA", "portale", "servizi digitali",
                     "identità digitale", "firma digitale", "PEC", "SPID"],
        "excluded_keywords": ["farmaci", "medicinali"],
        "buyer_preferences": ["MINISTERO", "COMUNE", "REGIONE", "PUBBLICA AMMINISTRAZIONE", "ANAC"],
        "description": "Trasformazione digitale e innovazione"
    }
}

# Geo area to country/region mapping
GEO_MAP = {
    "nord": ["LOMBARDIA", "PIEMONTE", "VENETO", "EMILIA-ROMAGNA", "LIGURIA", "TRENTINO", "FRIULI", "VALLE D'AOSTA"],
    "centro": ["LAZIO", "TOSCANA", "MARCHE", "UMBRIA"],
    "sud": ["CAMPANIA", "PUGLIA", "BASILICATA", "CALABRIA", "SICILIA", "SARDEGNA"],
    "tutta": []
}


def generate_free_audit(email: str, geo_area: str, services: str) -> dict:
    """
    Generate a free tender audit for a specific company profile.
    
    Args:
        email: Company email
        geo_area: Geographic area (nord/centro/sud/tutta)
        services: Service type (cybersecurity/sviluppo-software/cloud/digitale)
    
    Returns:
        dict with audit results
    """
    # Get vertical config
    vertical = VERTICAL_CONFIGS.get(services, VERTICAL_CONFIGS["sviluppo-software"])
    
    # Build profile
    profile_id = f"free_audit_{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.urandom(4).hex()}"
    
    profile = {
        "id": profile_id,
        "company_name": email.split("@")[1] if "@" in email else "Azienda",
        "industry": vertical["description"],
        "cpv_codes": vertical["cpv_codes"],
        "cpv_detailed": vertical["cpv_detailed"],
        "countries": ["ITA"],
        "value_min": 10000,
        "value_max": 500000,
        "keywords": vertical["keywords"],
        "excluded_keywords": vertical["excluded_keywords"],
        "preferred_buyers": vertical["buyer_preferences"],
        "notes": f"Free audit for {email} - {services} - {geo_area}",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    # Save profile
    profile_engine = ProfileEngine()
    profile_engine.create_profile(profile)
    
    # Run pipeline
    orchestrator = PipelineOrchestrator()
    result = orchestrator.run(profile_id)
    
    if result.get("error"):
        return {"success": False, "error": result["error"]}
    
    # Generate vertical-specific summary
    summary = generate_vertical_summary(result, vertical, services)
    
    return {
        "success": True,
        "profile_id": profile_id,
        "report_path": result["reports"].get("markdown", ""),
        "html_report_path": result["reports"].get("html", ""),
        "summary": summary,
        "total_tenders": result.get("total_retrieved", 0),
        "high_priority": result.get("high_priority", 0),
        "medium_priority": result.get("medium_priority", 0),
        "vertical": services,
        "geo_area": geo_area
    }


def generate_vertical_summary(result: dict, vertical: dict, services: str) -> str:
    """Generate a plain-Italian summary for the vertical."""
    
    high = result.get("high_priority", 0)
    medium = result.get("medium_priority", 0)
    total = result.get("total_retrieved", 0)
    
    # Get top tenders from the report
    top_tenders = []
    reports = result.get("reports", {})
    if reports.get("markdown"):
        report_path = reports["markdown"]
        try:
            with open(report_path) as f:
                content = f.read()
                # Extract top 3 tenders (simplified parsing)
                lines = content.split("\n")
                for line in lines:
                    if line.startswith("### ") and len(top_tenders) < 3:
                        top_tenders.append(line.replace("### ", "").strip())
        except:
            pass
    
    summary = f"""📋 ANALISI GRATUITA — {vertical['description'].upper()}

Ciao,

abbiamo analizzato i bandi TED (Tenders Electronic Daily) per la tua azienda.

RISULTATI:
• {total} bandi trovati in Italia
• {high} alta priorità (match >70%)
• {medium} media priorità (match 40-70%)

"""
    
    if top_tenders:
        summary += "I 3 BANDI PIÙ RILEVANTI:\n\n"
        for i, tender in enumerate(top_tenders, 1):
            summary += f"{i}. {tender}\n"
        summary += "\n"
    
    summary += """COSA FARE ORA:
1. Visualizza il report completo (allegato)
2. Clicca sui link TED per scaricare i documenti di gara
3. Verifica i requisiti di partecipazione
4. Se un bando ti interessa, prepara l'offerta (tempo medio: 15 giorni)

Se vuoi monitorare questi bandi ogni settimana, passa al piano Monitoraggio Settimanale (€49/mo).

Buona fortuna!
— AppaltiMonitor

---
P.IVA: SNSLSN90C09G273P · Palermo · appalti.monitor@gmail.com
"""
    
    return summary


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate free tender audit")
    parser.add_argument("--email", required=True, help="Company email")
    parser.add_argument("--geo", required=True, help="Geographic area")
    parser.add_argument("--service", required=True, help="Service type")
    
    args = parser.parse_args()
    
    result = generate_free_audit(args.email, args.geo, args.service)
    print(json.dumps(result, indent=2, ensure_ascii=False))
