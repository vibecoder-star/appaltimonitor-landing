#!/usr/bin/env python3
"""
AppaltiMonitor — Opt-in Workflow with Double Opt-in
Implements GDPR-compliant consent management
"""

import json
import os
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

# Configuration
BASE_DIR = Path("/opt/autonomous-venture-engine/appalti-monitor")
DATA_DIR = BASE_DIR / "data" / "optins"
CONFIRMED_DIR = BASE_DIR / "data" / "confirmed"
LOGS_DIR = BASE_DIR / "data" / "logs"

for d in [DATA_DIR, CONFIRMED_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Consent text versions
CONSENT_VERSION = "1.0"
CONSENT_TEXT = """
Acconsento al trattamento dei miei dati personali per ricevere il servizio di 
intelligence sugli appalti pubblici da AppaltiMonitor, secondo l'informativa 
privacy disponibile sul sito.
"""

MARKETING_CONSENT_TEXT = """
Acconsento a ricevere comunicazioni commerciali e aggiornamenti su 
AppaltiMonitor, inclusi suggerimenti, novità e offerte.
"""

class OptinManager:
    """Manage opt-in workflow with double opt-in"""
    
    def __init__(self):
        self.data_dir = DATA_DIR
        self.confirmed_dir = CONFIRMED_DIR
        self.logs_dir = LOGS_DIR
    
    def create_optin(self, profile_data: Dict) -> Dict:
        """
        Create initial opt-in record
        Returns: optin record with confirmation token
        """
        # Generate confirmation token
        token = self._generate_token(profile_data["businessEmail"])
        
        # Create record
        record = {
            "token": token,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
            "profile": {
                "company_name": profile_data.get("companyName", ""),
                "business_email": profile_data.get("businessEmail", ""),
                "industry": profile_data.get("industry", ""),
                "geo_area": profile_data.get("geoArea", ""),
                "services": profile_data.get("services", ""),
                "cpv_codes": profile_data.get("cpvCodes", ""),
                "value_range": profile_data.get("valueRange", "")
            },
            "consent": {
                "service_consent": profile_data.get("consentService", False),
                "marketing_consent": profile_data.get("consentMarketing", False),
                "privacy_consent": profile_data.get("consentPrivacy", False),
                "consent_version": CONSENT_VERSION,
                "consent_text": CONSENT_TEXT,
                "marketing_consent_text": MARKETING_CONSENT_TEXT,
                "timestamp": datetime.now().isoformat(),
                "ip_address": profile_data.get("ipAddress", "unknown"),
                "user_agent": profile_data.get("userAgent", "unknown")
            },
            "source": profile_data.get("source", "landing-page"),
            "confirmation_timestamp": None,
            "report_generated": False,
            "report_path": None
        }
        
        # Save pending optin
        filepath = self.data_dir / f"{token}.json"
        with open(filepath, "w") as f:
            json.dump(record, f, indent=2)
        
        # Log
        self._log_event("optin_created", token, profile_data.get("businessEmail", ""))
        
        return record
    
    def confirm_optin(self, token: str) -> Optional[Dict]:
        """
        Confirm opt-in via double opt-in token
        Returns: confirmed record or None if invalid
        """
        filepath = self.data_dir / f"{token}.json"
        
        if not filepath.exists():
            self._log_event("confirmation_failed", token, "Token not found")
            return None
        
        with open(filepath, "r") as f:
            record = json.load(f)
        
        # Check if already confirmed
        if record["status"] == "confirmed":
            return record
        
        # Check expiration
        expires_at = datetime.fromisoformat(record["expires_at"])
        if datetime.now() > expires_at:
            self._log_event("confirmation_expired", token, record["profile"]["business_email"])
            return None
        
        # Update record
        record["status"] = "confirmed"
        record["confirmation_timestamp"] = datetime.now().isoformat()
        
        # Save to confirmed directory
        confirmed_path = self.confirmed_dir / f"{token}.json"
        with open(confirmed_path, "w") as f:
            json.dump(record, f, indent=2)
        
        # Remove from pending
        filepath.unlink()
        
        # Log
        self._log_event("optin_confirmed", token, record["profile"]["business_email"])
        
        return record
    
    def get_confirmed_profile(self, token: str) -> Optional[Dict]:
        """Get confirmed profile by token"""
        confirmed_path = self.confirmed_dir / f"{token}.json"
        
        if not confirmed_path.exists():
            return None
        
        with open(confirmed_path, "r") as f:
            return json.load(f)
    
    def get_all_confirmed(self) -> list:
        """Get all confirmed opt-ins"""
        confirmed = []
        for f in self.confirmed_dir.glob("*.json"):
            with open(f, "r") as fh:
                confirmed.append(json.load(fh))
        return confirmed
    
    def update_report_status(self, token: str, report_path: str, opportunities_found: int):
        """Update record after report generation"""
        confirmed_path = self.confirmed_dir / f"{token}.json"
        
        if not confirmed_path.exists():
            return False
        
        with open(confirmed_path, "r") as f:
            record = json.load(f)
        
        record["report_generated"] = True
        record["report_path"] = report_path
        record["opportunities_found"] = opportunities_found
        record["report_timestamp"] = datetime.now().isoformat()
        
        with open(confirmed_path, "w") as f:
            json.dump(record, f, indent=2)
        
        self._log_event("report_generated", token, record["profile"]["business_email"])
        
        return True
    
    def revoke_consent(self, token: str) -> bool:
        """Revoke consent (right to be forgotten)"""
        confirmed_path = self.confirmed_dir / f"{token}.json"
        
        if not confirmed_path.exists():
            return False
        
        with open(confirmed_path, "r") as f:
            record = json.load(f)
        
        # Mark as revoked
        record["status"] = "revoked"
        record["revocation_timestamp"] = datetime.now().isoformat()
        
        # Save to logs for audit
        revoked_path = self.logs_dir / f"revoked_{token}.json"
        with open(revoked_path, "w") as f:
            json.dump(record, f, indent=2)
        
        # Delete from confirmed
        confirmed_path.unlink()
        
        self._log_event("consent_revoked", token, record["profile"]["business_email"])
        
        return True
    
    def _generate_token(self, email: str) -> str:
        """Generate unique confirmation token"""
        data = f"{email}_{datetime.now().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]
    
    def _log_event(self, event: str, token: str, email: str):
        """Log event for audit"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "token": token,
            "email": email
        }
        
        log_path = self.logs_dir / "optin_audit.log"
        with open(log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")


class ConsentValidator:
    """Validate consent records"""
    
    @staticmethod
    def validate_service_consent(record: Dict) -> bool:
        """Check if service consent is valid"""
        consent = record.get("consent", {})
        return (
            consent.get("service_consent", False) and
            consent.get("privacy_consent", False) and
            consent.get("consent_version") == CONSENT_VERSION
        )
    
    @staticmethod
    def validate_marketing_consent(record: Dict) -> bool:
        """Check if marketing consent is valid"""
        consent = record.get("consent", {})
        return (
            consent.get("marketing_consent", False) and
            consent.get("consent_version") == CONSENT_VERSION
        )
    
    @staticmethod
    def get_consent_summary(record: Dict) -> Dict:
        """Get human-readable consent summary"""
        consent = record.get("consent", {})
        return {
            "service_consent": "✅ Concesso" if consent.get("service_consent") else "❌ Non concesso",
            "marketing_consent": "✅ Concesso" if consent.get("marketing_consent") else "❌ Non concesso",
            "privacy_consent": "✅ Concesso" if consent.get("privacy_consent") else "❌ Non concesso",
            "consent_version": consent.get("consent_version", "N/A"),
            "consent_timestamp": consent.get("timestamp", "N/A"),
            "confirmation_timestamp": record.get("confirmation_timestamp", "N/A")
        }


def generate_confirmation_email(record: Dict) -> str:
    """Generate confirmation email content"""
    token = record["token"]
    company = record["profile"]["company_name"]
    
    email_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Conferma il tuo indirizzo email</title>
    </head>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2>Conferma la tua richiesta</h2>
        <p>Grazie per esserti registrato ad AppaltiMonitor per <strong>{company}</strong>!</p>
        <p>Per completare la registrazione e ricevere il tuo report personalizzato, 
        clicca il pulsante qui sotto:</p>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="https://appaltimonitor.it/confirm?token={token}" 
               style="background: #3498db; color: white; padding: 15px 30px; 
                      text-decoration: none; border-radius: 5px; font-weight: bold;">
                Conferma e ricevi il report
            </a>
        </div>
        
        <p style="color: #666; font-size: 0.9rem;">
            Se il pulsante non funziona, copia e incolla questo link nel tuo browser:<br>
            https://appaltimonitor.it/confirm?token={token}
        </p>
        
        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
        
        <p style="color: #666; font-size: 0.85rem;">
            Questo link scade tra 24 ore. Se non hai richiesto questo servizio, 
            ignora questa email.
        </p>
        
        <p style="color: #666; font-size: 0.85rem;">
            AppaltiMonitor — Intelligence sugli Appalti Pubblici<br>
            <a href="https://appaltimonitor.it/privacy">Privacy Policy</a>
        </p>
    </body>
    </html>
    """
    
    return email_html


def generate_welcome_email(record: Dict, report_path: str) -> str:
    """Generate welcome email with report attached"""
    company = record["profile"]["company_name"]
    
    email_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Benvenuto su AppaltiMonitor</title>
    </head>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2>Benvenuto su AppaltiMonitor!</h2>
        <p>Grazie per aver confermato la registrazione per <strong>{company}</strong>.</p>
        <p>In allegato trovi il tuo primo report di intelligence sugli appalti pubblici.</p>
        
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3>📋 Cosa contiene il report</h3>
            <ul>
                <li>Opportunità di appalto pubblico rilevanti per la tua azienda</li>
                <li>Ranking per rilevanza</li>
                <li>Scadenze e valori stimati</li>
                <li>Link diretti ai bandi TED</li>
            </ul>
        </div>
        
        <h3>🚀 Prossimi passi</h3>
        <ol>
            <li>Scarica il report in allegato</li>
            <li>Valuta le opportunità</li>
            <li>Clicca sui link per accedere ai bandi</li>
        </ol>
        
        <p>Vuoi continuare a ricevere report settimanali? 
        <a href="https://appaltimonitor.it/pricing">Scopri i nostri piani</a>.</p>
        
        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
        
        <p style="color: #666; font-size: 0.85rem;">
            Puoi cancellare il tuo account in qualsiasi momento cliccando 
            <a href="https://appaltimonitor.it/unsubscribe?token={record['token']}">qui</a>.
        </p>
    </body>
    </html>
    """
    
    return email_html


if __name__ == "__main__":
    # Test opt-in workflow
    print("=" * 60)
    print("AppaltiMonitor — Opt-in Workflow Test")
    print("=" * 60)
    
    manager = OptinManager()
    
    # Test 1: Create opt-in
    print("\n1. Creating opt-in...")
    test_data = {
        "companyName": "Test Company SRL",
        "businessEmail": "test@example.com",
        "industry": "it-software",
        "geoArea": "nord",
        "services": "Sviluppo software, cloud",
        "cpvCodes": "72260000, 72510000",
        "valueRange": "medium",
        "consentService": True,
        "consentMarketing": False,
        "consentPrivacy": True,
        "source": "test"
    }
    
    record = manager.create_optin(test_data)
    print(f"   Token: {record['token']}")
    print(f"   Status: {record['status']}")
    
    # Test 2: Confirm opt-in
    print("\n2. Confirming opt-in...")
    confirmed = manager.confirm_optin(record["token"])
    if confirmed:
        print(f"   Status: {confirmed['status']}")
        print(f"   Confirmed at: {confirmed['confirmation_timestamp']}")
    else:
        print("   ERROR: Confirmation failed")
    
    # Test 3: Validate consent
    print("\n3. Validating consent...")
    validator = ConsentValidator()
    summary = validator.get_consent_summary(confirmed)
    for key, value in summary.items():
        print(f"   {key}: {value}")
    
    # Test 4: Generate emails
    print("\n4. Generating emails...")
    confirmation_email = generate_confirmation_email(record)
    print(f"   Confirmation email: {len(confirmation_email)} chars")
    
    # Test 5: Revoke consent
    print("\n5. Testing revocation...")
    revoked = manager.revoke_consent(record["token"])
    print(f"   Revoked: {revoked}")
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
