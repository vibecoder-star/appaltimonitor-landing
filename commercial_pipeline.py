#!/usr/bin/env python3
"""
AppaltiMonitor — Commercial MVP End-to-End Pipeline
Integrates: Opt-in → TED Query → Report → Email → Trial → Conversion
"""

import json
import logging
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List
import hashlib
import uuid

logger = logging.getLogger(__name__)

# Import existing pipeline components
import sys
sys.path.insert(0, '/opt/autonomous-venture-engine/appalti-monitor')
from mvp_pipeline import (
    PipelineOrchestrator, ProfileEngine, RelevanceEngine,
    QualityControl, ReportGenerator, TEDAPIClient,
    OUTPUT_DIR, PROFILES_DIR, REPORTS_DIR, KPIS_DIR
)

# Configuration
BASE_DIR = Path("/opt/autonomous-venture-engine/appalti-monitor")
DATA_DIR = BASE_DIR / "data"
OPTINS_DIR = DATA_DIR / "optins"
CONFIRMED_DIR = DATA_DIR / "confirmed"
TRIALS_DIR = DATA_DIR / "trials"
EMAILS_DIR = DATA_DIR / "emails"
LOGS_DIR = DATA_DIR / "logs"

for d in [OPTINS_DIR, CONFIRMED_DIR, TRIALS_DIR, EMAILS_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Email configuration (use environment variables or config file)
EMAIL_CONFIG = {
    "smtp_server": os.environ.get("SMTP_SERVER", "smtp.gmail.com"),
    "smtp_port": int(os.environ.get("SMTP_PORT", "587")),
    "sender_email": os.environ.get("SENDER_EMAIL", ""),
    "sender_password": os.environ.get("SENDER_PASSWORD", ""),
    "use_tls": True
}

# Trial configuration
TRIAL_DURATION_DAYS = 7

# Consent versions
CONSENT_VERSION = "1.0"


class EmailSender:
    """Send emails using SMTP"""
    
    def __init__(self, config: Dict = None):
        self.config = config or EMAIL_CONFIG
        self.enabled = bool(self.config.get("sender_email") and self.config.get("sender_password"))
    
    def send(self, to_email: str, subject: str, html_body: str, text_body: str = None) -> bool:
        """Send email"""
        if not self.enabled:
            # Log email instead of sending
            self._log_email(to_email, subject, html_body)
            return True
        
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.config["sender_email"]
            msg["To"] = to_email
            
            if text_body:
                msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))
            
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.config["smtp_server"], self.config["smtp_port"]) as server:
                if self.config["use_tls"]:
                    server.starttls(context=context)
                server.login(self.config["sender_email"], self.config["sender_password"])
                server.send_message(msg)
            
            self._log_email(to_email, subject, html_body, sent=True)
            return True
            
        except Exception as e:
            self._log_email(to_email, subject, html_body, error=str(e))
            return False
    
    def _log_email(self, to: str, subject: str, body: str, sent: bool = False, error: str = None):
        """Log email for debugging"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "to": to,
            "subject": subject,
            "sent": sent,
            "error": error,
            "body_preview": body[:200] if body else ""
        }
        
        log_path = LOGS_DIR / "email_log.jsonl"
        with open(log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")


class TrialManager:
    """Manage trial states"""
    
    STATES = [
        "PENDING",          # Opt-in created, awaiting confirmation
        "CONFIRMED",        # Double opt-in confirmed
        "TRIAL_ACTIVE",     # Trial started, reports being sent
        "TRIAL_ENDING",     # Trial ending soon (day 5-6)
        "TRIAL_EXPIRED",    # Trial ended
        "PAID",             # Converted to paid
        "CANCELLED"         # User cancelled
    ]
    
    def __init__(self):
        self.trials_dir = TRIALS_DIR
    
    def create_trial(self, profile_id: str, email: str, profile: Dict) -> Dict:
        """Create new trial record"""
        trial = {
            "id": str(uuid.uuid4())[:8],
            "profile_id": profile_id,
            "email": email,
            "company_name": profile.get("company_name", ""),
            "state": "PENDING",
            "created_at": datetime.now().isoformat(),
            "confirmed_at": None,
            "trial_start": None,
            "trial_end": None,
            "reports_sent": [],
            "conversion_offered": False,
            "conversion_plan": None,
            "cancelled_at": None
        }
        
        self._save_trial(trial)
        return trial
    
    def confirm_trial(self, trial_id: str) -> Optional[Dict]:
        """Confirm trial after double opt-in"""
        trial = self._load_trial(trial_id)
        if not trial:
            return None
        
        trial["state"] = "TRIAL_ACTIVE"
        trial["confirmed_at"] = datetime.now().isoformat()
        trial["trial_start"] = datetime.now().isoformat()
        trial["trial_end"] = (datetime.now() + timedelta(days=TRIAL_DURATION_DAYS)).isoformat()
        
        self._save_trial(trial)
        return trial
    
    def get_trial(self, trial_id: str) -> Optional[Dict]:
        """Get trial by ID"""
        return self._load_trial(trial_id)
    
    def get_trials_by_state(self, state: str) -> List[Dict]:
        """Get all trials in a given state"""
        trials = []
        for f in self.trials_dir.glob("*.json"):
            with open(f, "r") as fh:
                trial = json.load(fh)
                if trial.get("state") == state:
                    trials.append(trial)
        return trials
    
    def update_state(self, trial_id: str, new_state: str) -> Optional[Dict]:
        """Update trial state"""
        if new_state not in self.STATES:
            return None
        
        trial = self._load_trial(trial_id)
        if not trial:
            return None
        
        trial["state"] = new_state
        
        if new_state == "TRIAL_EXPIRED":
            trial["conversion_offered"] = True
        elif new_state == "PAID":
            trial["conversion_plan"] = "pending_payment"
        elif new_state == "CANCELLED":
            trial["cancelled_at"] = datetime.now().isoformat()
        
        self._save_trial(trial)
        return trial
    
    def add_report_sent(self, trial_id: str, report_path: str, opportunities: int):
        """Record report sent"""
        trial = self._load_trial(trial_id)
        if not trial:
            return False
        
        trial["reports_sent"].append({
            "timestamp": datetime.now().isoformat(),
            "report_path": report_path,
            "opportunities": opportunities
        })
        
        self._save_trial(trial)
        return True
    
    def check_trial_expiration(self, trial_id: str) -> str:
        """Check and update trial expiration"""
        trial = self._load_trial(trial_id)
        if not trial:
            return "NOT_FOUND"
        
        if trial["state"] != "TRIAL_ACTIVE":
            return trial["state"]
        
        trial_end = datetime.fromisoformat(trial["trial_end"])
        now = datetime.now()
        
        if now >= trial_end:
            self.update_state(trial_id, "TRIAL_EXPIRED")
            return "TRIAL_EXPIRED"
        elif now >= trial_end - timedelta(days=2):
            self.update_state(trial_id, "TRIAL_ENDING")
            return "TRIAL_ENDING"
        
        return "TRIAL_ACTIVE"
    
    def _save_trial(self, trial: Dict):
        """Save trial to disk"""
        filepath = self.trials_dir / f"{trial['id']}.json"
        with open(filepath, "w") as f:
            json.dump(trial, f, indent=2)
    
    def _load_trial(self, trial_id: str) -> Optional[Dict]:
        """Load trial from disk"""
        filepath = self.trials_dir / f"{trial_id}.json"
        if not filepath.exists():
            return None
        
        with open(filepath, "r") as f:
            return json.load(f)


class CommercialPipeline:
    """End-to-end commercial pipeline"""
    
    def __init__(self):
        self.pipeline = PipelineOrchestrator()
        self.profile_engine = ProfileEngine()
        self.email_sender = EmailSender()
        self.trial_manager = TrialManager()
    
    def process_optin(self, optin_data: Dict) -> Dict:
        """
        Process new opt-in from landing page
        
        Steps:
        1. Validate data
        2. Create profile
        3. Create trial
        4. Send confirmation email
        """
        # Validate required fields
        required = ["companyName", "businessEmail", "industry", "geoArea"]
        for field in required:
            if not optin_data.get(field):
                return {"error": f"Missing required field: {field}"}
        
        # Validate consent
        if not optin_data.get("consentService") or not optin_data.get("consentPrivacy"):
            return {"error": "Service and privacy consent required"}
        
        # Create profile
        profile_data = {
            "id": f"com_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}",
            "company_name": optin_data["companyName"],
            "industry": optin_data["industry"],
            "cpv_codes": self._extract_cpvs(optin_data),
            "cpv_detailed": [],
            "countries": ["ITA"],
            "value_min": self._get_value_min(optin_data.get("valueRange")),
            "value_max": self._get_value_max(optin_data.get("valueRange")),
            "keywords": self._extract_keywords(optin_data),
            "excluded_keywords": [],
            "preferred_buyers": [],
            "notes": f"Commercial opt-in from {optin_data['businessEmail']}"
        }
        
        profile = self.profile_engine.create_profile(profile_data)
        
        # Create trial
        trial = self.trial_manager.create_trial(
            profile_id=profile["id"],
            email=optin_data["businessEmail"],
            profile=profile
        )
        
        # Send confirmation email
        confirmation_sent = self._send_confirmation_email(trial, profile)
        
        return {
            "success": True,
            "trial_id": trial["id"],
            "profile_id": profile["id"],
            "confirmation_sent": confirmation_sent,
            "message": "Opt-in received. Please check your email to confirm."
        }
    
    def confirm_and_start_trial(self, trial_id: str) -> Dict:
        """
        Confirm double opt-in and start trial
        
        Steps:
        1. Confirm trial
        2. Run TED pipeline
        3. Generate report
        4. Send welcome email with report
        """
        # Confirm trial
        trial = self.trial_manager.confirm_trial(trial_id)
        if not trial:
            return {"error": "Trial not found"}
        
        # Load profile
        profile = self.profile_engine.load_profile(trial["profile_id"])
        if not profile:
            return {"error": "Profile not found"}
        
        # Run TED pipeline
        status = self.pipeline.run(profile["id"])
        
        if status.get("error"):
            return {"error": status["error"]}
        
        # Get report path
        report_path = status["reports"].get("markdown", "")
        
        # Update trial with report
        self.trial_manager.add_report_sent(
            trial_id=trial_id,
            report_path=report_path,
            opportunities=status["high_priority"] + status["medium_priority"]
        )
        
        # Send welcome email with report
        self._send_welcome_email(trial, profile, status, report_path)
        
        return {
            "success": True,
            "trial_id": trial_id,
            "opportunities_found": status["relevant"],
            "high_priority": status["high_priority"],
            "report_sent": True
        }
    
    def run_scheduled_scan(self):
        """
        Run scheduled scan for all active trials
        Called by cron job
        """
        active_trials = self.trial_manager.get_trials_by_state("TRIAL_ACTIVE")
        ending_trials = self.trial_manager.get_trials_by_state("TRIAL_ENDING")
        
        all_trials = active_trials + ending_trials
        results = []
        
        for trial in all_trials:
            # Check expiration
            state = self.trial_manager.check_trial_expiration(trial["id"])
            
            if state == "TRIAL_EXPIRED":
                # Send conversion offer
                self._send_conversion_email(trial)
                results.append({"trial_id": trial["id"], "action": "conversion_sent"})
            elif state == "TRIAL_ENDING":
                # Send reminder
                self._send_reminder_email(trial)
                results.append({"trial_id": trial["id"], "action": "reminder_sent"})
            elif state == "TRIAL_ACTIVE":
                # Generate new report
                profile = self.profile_engine.load_profile(trial["profile_id"])
                if profile:
                    status = self.pipeline.run(profile["id"])
                    if not status.get("error"):
                        report_path = status["reports"].get("markdown", "")
                        self.trial_manager.add_report_sent(
                            trial["id"], report_path,
                            status["high_priority"] + status["medium_priority"]
                        )
                        self._send_report_email(trial, profile, status, report_path)
                        results.append({"trial_id": trial["id"], "action": "report_sent"})
        
        return results
    
    def _send_confirmation_email(self, trial: Dict, profile: Dict) -> bool:
        """Send double opt-in confirmation email"""
        token = trial["id"]
        
        subject = "Conferma la tua richiesta — AppaltiMonitor"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2>Conferma la tua richiesta</h2>
            <p>Grazie per esserti registrato ad AppaltiMonitor per <strong>{profile['company_name']}</strong>!</p>
            <p>Per completare la registrazione e ricevere il tuo report personalizzato, 
            clicca il pulsante qui sotto:</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="https://vibecoder-star.github.io/appaltimonitor-landing/confirm.html?token={token}" 
                   style="background: #3498db; color: white; padding: 15px 30px; 
                          text-decoration: none; border-radius: 5px; font-weight: bold;">
                    Conferma e ricevi il report
                </a>
            </div>
            
            <p style="color: #666; font-size: 0.9rem;">
                Se il pulsante non funziona, copia e incolla questo link:<br>
                https://vibecoder-star.github.io/appaltimonitor-landing/confirm.html?token={token}
            </p>
            
            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
            <p style="color: #666; font-size: 0.85rem;">
                Questo link scade tra 24 ore. Se non hai richiesto questo servizio, 
                ignora questa email.
            </p>
        </body>
        </html>
        """
        
        return self.email_sender.send(trial["email"], subject, html)
    
    def _send_welcome_email(self, trial: Dict, profile: Dict, status: Dict, report_path: str):
        """Send welcome email with first report"""
        subject = "Benvenuto su AppaltiMonitor — Il tuo primo report"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2>Benvenuto su AppaltiMonitor!</h2>
            <p>Grazie per aver confermato la registrazione per <strong>{profile['company_name']}</strong>.</p>
            <p>Il tuo trial di 7 giorni è ora attivo. Ecco il tuo primo report:</p>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3>📋 Report Settimanale</h3>
                <ul>
                    <li><strong>Opportunità trovate:</strong> {status['relevant']}</li>
                    <li><strong>Alta priorità:</strong> {status['high_priority']}</li>
                    <li><strong>Media priorità:</strong> {status['medium_priority']}</li>
                </ul>
            </div>
            
            <p>Il report completo è disponibile nel sistema. Continuerai a ricevere 
            report settimanali per tutta la durata del trial.</p>
            
            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
            <p style="color: #666; font-size: 0.85rem;">
                Puoi cancellare il tuo account in qualsiasi momento cliccando 
                <a href="https://vibecoder-star.github.io/appaltimonitor-landing/unsubscribe.html?token={trial['id']}">qui</a>.
            </p>
        </body>
        </html>
        """
        
        return self.email_sender.send(trial["email"], subject, html)
    
    def _send_report_email(self, trial: Dict, profile: Dict, status: Dict, report_path: str):
        """Send weekly report email"""
        subject = "Il tuo report settimanale — AppaltiMonitor"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2>Report Settimanale — {profile['company_name']}</h2>
            <p>Ecco le nuove opportunità di appalto pubblico per la tua azienda:</p>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <ul>
                    <li><strong>Opportunità trovate:</strong> {status['relevant']}</li>
                    <li><strong>Alta priorità:</strong> {status['high_priority']}</li>
                    <li><strong>Media priorità:</strong> {status['medium_priority']}</li>
                </ul>
            </div>
            
            <p>Il report completo è disponibile nel sistema.</p>
        </body>
        </html>
        """
        
        return self.email_sender.send(trial["email"], subject, html)
    
    def _send_reminder_email(self, trial: Dict):
        """Send trial ending reminder"""
        subject = "Il tuo trial sta per terminare — AppaltiMonitor"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2>Il tuo trial sta per terminare</h2>
            <p>Il tuo trial di 7 giorni su AppaltiMonitor sta per terminare.</p>
            <p>Per continuare a ricevere report settimanali sulle opportunità di appalto pubblico, 
            scegli un piano:</p>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <ul>
                    <li><strong>Starter:</strong> €29/mese — 1 settore, report settimanale</li>
                    <li><strong>Professional:</strong> €59/mese — 3 settori, alert urgenti</li>
                    <li><strong>Enterprise:</strong> €99/mese — Illimitato, account manager</li>
                </ul>
            </div>
            
            <p><em>I prezzi sono ipotesi in attesa di validazione commerciale.</em></p>
        </body>
        </html>
        """
        
        return self.email_sender.send(trial["email"], subject, html)
    
    def _send_conversion_email(self, trial: Dict):
        """Send conversion offer after trial expiration"""
        subject = "Il tuo trial è terminato — Continua con AppaltiMonitor"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2>Il tuo trial è terminato</h2>
            <p>Grazie per aver provato AppaltiMonitor!</p>
            <p>Per continuare a ricevere intelligence sulle opportunità di appalto pubblico:</p>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3>Piani disponibili</h3>
                <ul>
                    <li><strong>Starter:</strong> €29/mese</li>
                    <li><strong>Professional:</strong> €59/mese</li>
                    <li><strong>Enterprise:</strong> €99/mese</li>
                </ul>
            </div>
            
            <p><em>I prezzi sono ipotesi in attesa di validazione commerciale.</em></p>
            
            <p>Per iscriverti, contattaci rispondendo a questa email.</p>
        </body>
        </html>
        """
        
        return self.email_sender.send(trial["email"], subject, html)
    
    def _extract_cpvs(self, optin_data: Dict) -> List[str]:
        """Extract CPV codes from opt-in data"""
        cpvs = []
        
        # If CPV codes provided directly
        if optin_data.get("cpvCodes"):
            cpvs = [c.strip() for c in optin_data["cpvCodes"].split(",") if c.strip()]
        
        # Map industry to CPVs
        industry_cpvs = {
            "costruzioni": ["45"],
            "manutenzione": ["45"],
            "infrastrutture": ["45"],
            "it-software": ["72", "48"],
            "it-cloud": ["72", "48"],
            "it-security": ["72"],
            "it-digitale": ["72", "48"],
            "pulizie": ["90", "99"],
            "facility": ["90", "99", "79"],
        }
        
        industry = optin_data.get("industry", "")
        if industry in industry_cpvs:
            cpvs.extend(industry_cpvs[industry])
        
        return list(set(cpvs))  # Remove duplicates
    
    def _extract_keywords(self, optin_data: Dict) -> List[str]:
        """Extract keywords from services"""
        services = optin_data.get("services", "")
        if not services:
            return []
        
        # Simple keyword extraction
        words = services.lower().split()
        # Filter out common words
        stop_words = {"di", "e", "il", "la", "i", "le", "del", "della", "dei", "delle", "un", "una", "in", "con", "per", "su"}
        return [w for w in words if w not in stop_words and len(w) > 2]
    
    def _get_value_min(self, value_range: str) -> int:
        """Get minimum value from range"""
        ranges = {
            "small": 10000,
            "medium": 100000,
            "large": 500000,
            "xlarge": 2000000
        }
        return ranges.get(value_range, 10000)
    
    def _get_value_max(self, value_range: str) -> int:
        """Get maximum value from range"""
        ranges = {
            "small": 100000,
            "medium": 500000,
            "large": 2000000,
            "xlarge": 10000000
        }
        return ranges.get(value_range, 1000000)


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("AppaltiMonitor — Commercial Pipeline Test")
    logger.info("=" * 60)
    
    pipeline = CommercialPipeline()
    
    # Test opt-in
    logger.info("\n1. Testing opt-in...")
    optin_data = {
        "companyName": "Test Commercial SRL",
        "businessEmail": "test@example.com",
        "industry": "it-software",
        "geoArea": "nord",
        "services": "Sviluppo software, cloud computing",
        "cpvCodes": "72260000",
        "valueRange": "medium",
        "consentService": True,
        "consentMarketing": False,
        "consentPrivacy": True
    }
    
    result = pipeline.process_optin(optin_data)
    logger.info(f"   Result: {result}")
    
    if result.get("success"):
        trial_id = result["trial_id"]
        
        # Test confirmation
        logger.info("\n2. Testing confirmation...")
        confirm_result = pipeline.confirm_and_start_trial(trial_id)
        logger.info(f"   Result: {confirm_result}")
    
    logger.info("\n" + "=" * 60)
    logger.info("COMMERCIAL PIPELINE TEST COMPLETE")
    logger.info("=" * 60)
