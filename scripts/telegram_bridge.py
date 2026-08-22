#!/usr/bin/env python3
"""
AppaltiMonitor — Telegram CEO Bridge v2
Fix: gestione risposte testuali + poll updates
"""

import os
import json
import time
import logging
from datetime import datetime, timezone
from pathlib import Path
import urllib.request
import urllib.parse
import threading

# Setup
BASE_DIR = Path("/opt/autonomous-venture-engine/appalti-monitor")
LOG_DIR = BASE_DIR / "data" / "telegram_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "telegram_bridge.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load config
def load_env():
    env_path = Path.home() / ".hermes" / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env()

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
CEO_ID = int(os.environ.get('TELEGRAM_ALLOWED_USERS', '7592820797'))
HOME_CHANNEL = os.environ.get('TELEGRAM_HOME_CHANNEL', '7592820797')

# State
STATE_FILE = BASE_DIR / "data" / "telegram_state.json"
PENDING_APPROVALS = {}

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def send_message(chat_id, text, reply_markup=None):
    try:
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
        
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"}
        )
        
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            if result.get('ok'):
                logger.info(f"Message sent to {chat_id}")
                return True
            else:
                logger.error(f"Failed: {result}")
                return False
    except Exception as e:
        logger.error(f"Send error: {e}")
        return False

def get_updates(offset=None, timeout=30):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?timeout={timeout}"
        if offset:
            url += f"&offset={offset}"
        
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            if result.get('ok'):
                return result.get('result', [])
            return []
    except Exception as e:
        logger.error(f"Get updates error: {e}")
        return []

def handle_callback(callback_query):
    data = callback_query.get('data', '')
    from_user = callback_query.get('from', {}).get('id')
    
    if from_user != CEO_ID:
        return False
    
    if ':' in data:
        request_id, decision = data.split(':', 1)
        if request_id in PENDING_APPROVALS:
            PENDING_APPROVALS[request_id]['status'] = decision
            PENDING_APPROVALS[request_id]['resolved_at'] = now_iso()
            
            action = PENDING_APPROVALS[request_id]['action']
            send_message(CEO_ID, f"✅ Registrato: <b>{decision}</b> per <b>{action}</b>")
            
            with open(STATE_FILE, 'w') as f:
                json.dump({
                    "pending_approvals": PENDING_APPROVALS,
                    "last_saved": now_iso()
                }, f, indent=2)
            
            logger.info(f"CEO decided: {request_id} -> {decision}")
            return True
    return False

def handle_text_message(chat_id, text, message_id):
    """Rispondi ai messaggi testuali del CEO"""
    if chat_id != CEO_ID:
        return
    
    text = text.strip()
    logger.info(f"CEO message: {text}")
    
    if text == '/start':
        send_message(chat_id, """
🎉 <b>AppaltiMonitor — CEO Control Plane</b>

✅ Bot attivo
✅ Notifiche abilitate
✅ Approval workflow pronto

📋 <b>Comandi:</b>
/status — Stato sistemi
/report — Report giornaliero
/approve — Approvazioni pending

🔔 <b>Notifiche:</b>
🚨 CRITICAL — Urgenti
⚠️ IMPORTANT — Strategiche
📊 DAILY — Report

<i>Non devi più usare SSH per supervisionare Hermes.</i>
""")
    
    elif text == '/status':
        import subprocess
        services = ["nginx", "appaltimonitor-api", "appaltimonitor-telegram", "cron"]
        status_lines = []
        for svc in services:
            try:
                result = subprocess.run(
                    ["systemctl", "is-active", svc],
                    capture_output=True, text=True
                )
                state = "✅" if result.stdout.strip() == "active" else "❌"
                status_lines.append(f"{state} {svc}")
            except:
                status_lines.append(f"❓ {svc}")
        
        send_message(chat_id, f"<b>Stato servizi:</b>\n" + "\n".join(status_lines))
    
    elif text == '/report':
        # Read commercial state
        state_file = BASE_DIR / "data" / "commercial_state.json"
        kpis = {}
        if state_file.exists():
            with open(state_file) as f:
                kpis = json.load(f)
        
        send_message(chat_id, f"""
📊 <b>DAILY CEO REPORT — {datetime.now().strftime('%Y-%m-%d')}</b>

<b>KPIs:</b>
• Prospects: {kpis.get('prospects_found', 0)}
• Opt-ins: {kpis.get('opt_ins', 0)}
• Trials: {kpis.get('trials', 0)}
• Customers: {kpis.get('customers', 0)}
• Revenue: €{kpis.get('revenue', 0):.2f}
• Bottleneck: {kpis.get('bottleneck', 'Unknown')}

<b>Esperimenti:</b> {len(kpis.get('experiments', []))} run
""")
    
    elif text == '/approve':
        if PENDING_APPROVALS:
            for rid, details in PENDING_APPROVALS.items():
                if details['status'] == 'pending':
                    send_message(chat_id, f"""
🔴 <b>APPROVAL REQUIRED</b>

<b>Action:</b> {details['action']}
<b>Details:</b> {details['details']}
<b>Time:</b> {details['timestamp']}

✅ Approve — Procedi
❌ Reject — Annulla
""")
        else:
            send_message(chat_id, "Nessuna approvazione pendente.")
    
    elif text.lower() in ['rifiutato', 'no', 'reject', 'annulla']:
        # Cerca l'ultima pending e la rifiuta
        for rid, details in PENDING_APPROVALS.items():
            if details['status'] == 'pending':
                details['status'] = 'Rejected'
                details['resolved_at'] = now_iso()
                send_message(chat_id, f"❌ Registrato: <b>Reject</b> per <b>{details['action']}</b>")
                with open(STATE_FILE, 'w') as f:
                    json.dump({
                        "pending_approvals": PENDING_APPROVALS,
                        "last_saved": now_iso()
                    }, f, indent=2)
                return
        send_message(chat_id, "Nessuna approvazione pending da rifiutare.")
    
    elif text.lower() in ['approvato', 'sì', 'yes', 'approve', 'ok']:
        for rid, details in PENDING_APPROVALS.items():
            if details['status'] == 'pending':
                details['status'] = 'Approved'
                details['resolved_at'] = now_iso()
                send_message(chat_id, f"✅ Registrato: <b>Approve</b> per <b>{details['action']}</b>")
                with open(STATE_FILE, 'w') as f:
                    json.dump({
                        "pending_approvals": PENDING_APPROVALS,
                        "last_saved": now_iso()
                    }, f, indent=2)
                return
        send_message(chat_id, "Nessuna approvazione pending da approvare.")
    
    else:
        send_message(chat_id, f"Messaggio ricevuto: <i>{text}</i>\n\nUsa /status, /report, /approve per i comandi disponibili.")

def run():
    logger.info("=" * 60)
    logger.info("Telegram CEO Bridge v2 started")
    logger.info(f"CEO ID: {CEO_ID}")
    logger.info("=" * 60)
    
    last_update_id = 0
    
    # Load state
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            data = json.load(f)
            PENDING_APPROVALS.update(data.get('pending_approvals', {}))
    
    while True:
        try:
            updates = get_updates(offset=last_update_id + 1)
            
            for update in updates:
                last_update_id = update.get('update_id', last_update_id)
                
                if 'callback_query' in update:
                    handle_callback(update['callback_query'])
                
                if 'message' in update:
                    msg = update['message']
                    chat_id = msg.get('chat', {}).get('id')
                    text = msg.get('text', '')
                    
                    if text:
                        handle_text_message(chat_id, text, msg.get('message_id'))
            
            # Save state periodically
            with open(STATE_FILE, 'w') as f:
                json.dump({
                    "last_update_id": last_update_id,
                    "pending_approvals": PENDING_APPROVALS,
                    "last_saved": now_iso()
                }, f, indent=2)
            
        except Exception as e:
            logger.error(f"Main loop error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run()
