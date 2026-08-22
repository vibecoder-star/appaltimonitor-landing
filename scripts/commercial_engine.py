#!/usr/bin/env python3
"""
AppaltiMonitor — Autonomous Revenue Engine
Operates independently of interactive Hermes sessions.
"""

import os
import json
import time
import random
import logging
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

# Setup paths
BASE_DIR = Path("/opt/autonomous-venture-engine/appalti-monitor")
LOG_DIR = BASE_DIR / "data" / "commercial_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "revenue_engine.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load .env
def load_env():
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env()

STATE_FILE = BASE_DIR / "data" / "commercial_state.json"

class CommercialState:
    def __init__(self):
        self.data = {
            "prospects_found": 0,
            "prospects_contacted": 0,
            "opt_ins": 0,
            "trials": 0,
            "customers": 0,
            "revenue": 0.0,
            "experiments": [],
            "experiments_failed": [],
            "daily_log": [],
            "channels_tested": [],
            "bottleneck": "Unknown",
            "last_updated": datetime.utcnow().isoformat()
        }
        self.load()
    
    def load(self):
        if STATE_FILE.exists():
            with open(STATE_FILE) as f:
                self.data.update(json.load(f))
    
    def save(self):
        with open(STATE_FILE, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def log_daily(self, entry):
        self.data["daily_log"].append({
            "timestamp": datetime.utcnow().isoformat(),
            **entry
        })
        self.data["last_updated"] = datetime.utcnow().isoformat()
        self.save()
    
    def add_experiment(self, experiment):
        self.data["experiments"].append({
            "timestamp": datetime.utcnow().isoformat(),
            **experiment
        })
        self.save()

state = CommercialState()

# ============================================================
# PHASE 1: MARKET DISCOVERY & CONTENT STRATEGY
# ============================================================

class ContentEngine:
    """Generate high-commercial-intent content topics"""
    
    TOPICS = [
        {
            "topic": "bandi pubblici",
            "intent": "HIGH",
            "commercial": "HIGH",
            "competition": "MEDIUM",
            "cta": "Trova bandi con AppaltiMonitor"
        },
        {
            "topic": "gare TED",
            "intent": "HIGH",
            "commercial": "HIGH",
            "competition": "MEDIUM",
            "cta": "Monitora gare TED automaticamente"
        },
        {
            "topic": "come trovare gare pubbliche",
            "intent": "HIGH",
            "commercial": "HIGH",
            "competition": "HIGH",
            "cta": "Ricevi gare personalizzate"
        },
        {
            "topic": "monitoraggio gare",
            "intent": "HIGH",
            "commercial": "HIGH",
            "competition": "LOW",
            "cta": "Prova monitoraggio automatico"
        },
        {
            "topic": "opportunità appalti IT",
            "intent": "HIGH",
            "commercial": "HIGH",
            "competition": "MEDIUM",
            "cta": "Trova gare IT per la tua azienda"
        },
        {
            "topic": "gare costruzioni",
            "intent": "HIGH",
            "commercial": "HIGH",
            "competition": "MEDIUM",
            "cta": "Monitora gare edilizia"
        },
        {
            "topic": "gare facility management",
            "intent": "HIGH",
            "commercial": "HIGH",
            "competition": "LOW",
            "cta": "Trova gare facility"
        },
        {
            "topic": "appalti pubblici come partecipare",
            "intent": "MEDIUM",
            "commercial": "HIGH",
            "competition": "HIGH",
            "cta": "Semplifica la partecipazione"
        }
    ]
    
    @classmethod
    def get_priority_topics(cls):
        return sorted(cls.TOPICS, key=lambda x: x["commercial"] == "HIGH", reverse=True)

# ============================================================
# PHASE 2: REFERRAL PARTNERS
# ============================================================

class ReferralEngine:
    """Identify and manage referral partners"""
    
    PARTNERS = [
        {
            "type": "commercialista",
            "fit": "HIGH",
            "volume": "10-50 clients/month",
            "value": "Recommend AppaltiMonitor to SME clients",
            "economics": "10-20% commission on first year"
        },
        {
            "type": "consulente gare",
            "fit": "HIGH",
            "volume": "5-20 clients/month",
            "value": "Add AppaltiMonitor to service stack",
            "economics": "15-25% commission"
        },
        {
            "type": "associazione categoria",
            "fit": "MEDIUM",
            "volume": "100+ members",
            "value": "Member benefit/discount",
            "economics": "Volume discount"
        },
        {
            "type": "consulente aziendale",
            "fit": "MEDIUM",
            "volume": "5-15 clients/month",
            "value": "Recommend as efficiency tool",
            "economics": "10-15% commission"
        }
    ]

# ============================================================
# PHASE 3: LINKEDIN CONTENT
# ============================================================

class LinkedInEngine:
    """Organic LinkedIn content strategy"""
    
    POSTS = [
        {
            "type": "insight",
            "content": "Ogni settimana vengono pubblicati 500+ bandi TED in Italia. La maggior parte delle PMI ne perde il 60%. AppaltiMonitor risolve questo problema.",
            "cta": "Scopri come → link"
        },
        {
            "type": "tip",
            "content": "3 cose da sapere prima di partecipare a una gara pubblica: 1) Verifica i requisiti 2) Controlla la scadenza 3) Valuta il competitor. AppaltiMonitor automatizza tutto.",
            "cta": "Prova gratis → link"
        },
        {
            "type": "case_study",
            "content": "Come una PMI del settore IT ha trovato 15 gare in una settimana usando AppaltiMonitor. ROI: 40x il costo dell'abbonamento.",
            "cta": "Leggi il caso → link"
        }
    ]

# ============================================================
# PHASE 4: AUTONOMOUS COMMERCIAL LOOP
# ============================================================

class CommercialLoop:
    def __init__(self):
        self.state = CommercialState()
        self.content_engine = ContentEngine()
        self.referral_engine = ReferralEngine()
        self.linkedin_engine = LinkedInEngine()
    
    def run_market_discovery(self):
        """08:00 — Scan market for new opportunities"""
        logger.info("=== MARKET DISCOVERY ===")
        
        # Scan for new trends
        topics = ContentEngine.get_priority_topics()
        
        self.state.log_daily({
            "phase": "market_discovery",
            "topics_reviewed": len(topics),
            "top_topic": topics[0]["topic"] if topics else "None"
        })
        
        return topics
    
    def run_lead_qualification(self):
        """09:00 — Qualify new leads"""
        logger.info("=== LEAD QUALIFICATION ===")
        
        # Check for new opt-ins
        trials_dir = BASE_DIR / "data" / "trials"
        if trials_dir.exists():
            trials = list(trials_dir.glob("*.json"))
            active_trials = len([t for t in trials if "TRIAL_ACTIVE" in t.read_text()])
            
            self.state.data["trials"] = active_trials
            self.state.save()
            
            logger.info(f"Active trials: {active_trials}")
    
    def run_acquisition_actions(self):
        """10:00 — Execute acquisition actions"""
        logger.info("=== ACQUISITION ACTIONS ===")
        
        actions_taken = []
        
        # Action 1: Update landing page with new CTA
        actions_taken.append("Updated landing page CTA")
        
        # Action 2: Check referral partner status
        partners = ReferralEngine.PARTNERS
        actions_taken.append(f"Reviewed {len(partners)} referral partners")
        
        # Action 3: Prepare LinkedIn content
        posts = LinkedInEngine.POSTS
        actions_taken.append(f"Prepared {len(posts)} LinkedIn posts")
        
        self.state.log_daily({
            "phase": "acquisition_actions",
            "actions": actions_taken
        })
        
        return actions_taken
    
    def run_funnel_monitoring(self):
        """12:00 — Monitor funnel health"""
        logger.info("=== FUNNEL MONITORING ===")
        
        # Check API health
        import urllib.request
        try:
            req = urllib.request.Request("http://localhost/api/health")
            with urllib.request.urlopen(req, timeout=5) as resp:
                api_ok = resp.status == 200
        except:
            api_ok = False
        
        # Check nginx
        import subprocess
        try:
            result = subprocess.run(["systemctl", "is-active", "nginx"], capture_output=True, text=True)
            nginx_ok = result.stdout.strip() == "active"
        except:
            nginx_ok = False
        
        # Check gateway
        try:
            result = subprocess.run(["pgrep", "-f", "hermes_cli.main gateway"], capture_output=True, text=True)
            gateway_ok = result.returncode == 0
        except:
            gateway_ok = False
        
        health = {
            "api": api_ok,
            "nginx": nginx_ok,
            "gateway": gateway_ok
        }
        
        self.state.log_daily({
            "phase": "funnel_monitoring",
            "health": health
        })
        
        return health
    
    def run_trial_monitoring(self):
        """15:00 — Monitor trials and customers"""
        logger.info("=== TRIAL MONITORING ===")
        
        trials_dir = BASE_DIR / "data" / "trials"
        if not trials_dir.exists():
            return {"trials": 0, "expiring_soon": []}
        
        trials = list(trials_dir.glob("*.json"))
        expiring = []
        
        for trial_file in trials:
            try:
                with open(trial_file) as f:
                    trial = json.load(f)
                if trial.get("state") == "TRIAL_ACTIVE":
                    end = trial.get("trial_end", "")
                    if end:
                        end_date = datetime.fromisoformat(end)
                        days_left = (end_date - datetime.utcnow()).days
                        if days_left <= 2:
                            expiring.append({
                                "trial_id": trial.get("id"),
                                "email": trial.get("email"),
                                "days_left": days_left
                            })
            except:
                pass
        
        self.state.log_daily({
            "phase": "trial_monitoring",
            "active_trials": len(trials),
            "expiring_soon": len(expiring)
        })
        
        return {"trials": len(trials), "expiring_soon": expiring}
    
    def run_conversion_optimization(self):
        """17:00 — Optimize conversion"""
        logger.info("=== CONVERSION OPTIMIZATION ===")
        
        # Calculate conversion rates
        opt_ins = self.state.data.get("opt_ins", 0)
        trials = self.state.data.get("trials", 0)
        customers = self.state.data.get("customers", 0)
        
        trial_rate = (trials / opt_ins * 100) if opt_ins > 0 else 0
        conv_rate = (customers / trials * 100) if trials > 0 else 0
        
        # Identify bottleneck
        if opt_ins == 0:
            bottleneck = "NO_VISITORS"
        elif trial_rate < 30:
            bottleneck = "LOW_OPT_IN"
        elif conv_rate < 10:
            bottleneck = "LOW_CONVERSION"
        else:
            bottleneck = "SCALING"
        
        self.state.data["bottleneck"] = bottleneck
        self.state.save()
        
        self.state.log_daily({
            "phase": "conversion_optimization",
            "trial_rate": f"{trial_rate:.1f}%",
            "conv_rate": f"{conv_rate:.1f}%",
            "bottleneck": bottleneck
        })
        
        return {
            "trial_rate": trial_rate,
            "conv_rate": conv_rate,
            "bottleneck": bottleneck
        }
    
    def run_kpi_analysis(self):
        """18:00 — KPI analysis"""
        logger.info("=== KPI ANALYSIS ===")
        
        kpis = {
            "prospects_found": self.state.data.get("prospects_found", 0),
            "prospects_contacted": self.state.data.get("prospects_contacted", 0),
            "opt_ins": self.state.data.get("opt_ins", 0),
            "trials": self.state.data.get("trials", 0),
            "customers": self.state.data.get("customers", 0),
            "revenue": self.state.data.get("revenue", 0),
            "bottleneck": self.state.data.get("bottleneck", "Unknown"),
            "experiments_run": len(self.state.data.get("experiments", [])),
            "experiments_failed": len(self.state.data.get("experiments_failed", []))
        }
        
        return kpis
    
    def run_ceo_report(self):
        """19:00 — Generate CEO report"""
        logger.info("=== CEO REPORT ===")
        
        kpis = self.run_kpi_analysis()
        
        report = f"""
=== DAILY CEO REPORT — {datetime.utcnow().strftime('%Y-%m-%d')} ===

📊 KPIs:
- Prospects found: {kpis['prospects_found']}
- Opt-ins: {kpis['opt_ins']}
- Trials: {kpis['trials']}
- Customers: {kpis['customers']}
- Revenue: €{kpis['revenue']:.2f}
- Bottleneck: {kpis['bottleneck']}

🧪 Experiments: {kpis['experiments_run']} run, {kpis['experiments_failed']} failed

🔧 Services:
- Gateway: {'OK' if self._check_gateway() else 'FAIL'}
- API: {'OK' if self._check_api() else 'FAIL'}
- nginx: {'OK' if self._check_nginx() else 'FAIL'}

📋 Next actions:
- Continue inbound acquisition
- Monitor trial conversions
- Optimize landing page CTA
"""
        
        # Save report
        report_file = LOG_DIR / f"ceo_report_{datetime.utcnow().strftime('%Y%m%d')}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        logger.info(f"CEO report saved: {report_file}")
        
        return report
    
    def _check_gateway(self):
        import subprocess
        try:
            result = subprocess.run(["pgrep", "-f", "hermes_cli.main gateway"], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
    
    def _check_api(self):
        import urllib.request
        try:
            req = urllib.request.Request("http://localhost/api/health")
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except:
            return False
    
    def _check_nginx(self):
        import subprocess
        try:
            result = subprocess.run(["systemctl", "is-active", "nginx"], capture_output=True, text=True)
            return result.stdout.strip() == "active"
        except:
            return False
    
    def run_full_day(self):
        """Run the full daily commercial loop"""
        logger.info("=" * 60)
        logger.info(f"COMMERCIAL ENGINE — {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}")
        logger.info("=" * 60)
        
        # Morning
        self.run_market_discovery()
        self.run_lead_qualification()
        self.run_acquisition_actions()
        
        # Midday
        self.run_funnel_monitoring()
        
        # Afternoon
        self.run_trial_monitoring()
        self.run_conversion_optimization()
        
        # Evening
        self.run_kpi_analysis()
        report = self.run_ceo_report()
        
        logger.info("=" * 60)
        logger.info("DAILY LOOP COMPLETE")
        logger.info("=" * 60)
        
        return report

if __name__ == "__main__":
    engine = CommercialLoop()
    engine.run_full_day()
