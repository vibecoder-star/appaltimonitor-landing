#!/usr/bin/env python3
import os
import json
import ssl
import smtplib
from datetime import datetime
from collections import Counter

# Load .env
env_path = '/opt/autonomous-venture-engine/appalti-monitor/.env'
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# Analyze failures
failed = []
with open('/opt/autonomous-venture-engine/appalti-monitor/data/logs/email_log.jsonl') as f:
    for line in f:
        try:
            e = json.loads(line.strip())
            if not e.get('sent'):
                failed.append(e)
        except:
            pass

print(f"=== SMTP FAILURE ANALYSIS ===")
print(f"Total failures: {len(failed)}")
print(f"First: {failed[0]['timestamp'][:19] if failed else 'N/A'}")
print(f"Last: {failed[-1]['timestamp'][:19] if failed else 'N/A'}")

# Error types
errors = Counter()
for e in failed:
    err = e.get('error', 'None')
    if err and err != 'None':
        errors[err[:60]] += 1
    else:
        errors['None (logged but not sent)'] += 1

print(f"\nError types:")
for e, c in errors.most_common():
    print(f"  {c}x: {e}")

# Test SMTP
print(f"\n=== SMTP TEST ===")
server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
port = int(os.environ.get('SMTP_PORT', '587'))
sender = os.environ.get('SENDER_EMAIL', '')
password = os.environ.get('SENDER_PASSWORD', '')

print(f"Server: {server}:{port}")
print(f"Sender: {sender}")
print(f"Password length: {len(password) if password else 0}")

try:
    context = ssl.create_default_context()
    with smtplib.SMTP(server, port) as smtp:
        smtp.ehlo()
        smtp.starttls(context=context)
        smtp.ehlo()
        smtp.login(sender, password)
        print("SMTP STATUS: SUCCESS")
except Exception as e:
    print(f"SMTP STATUS: FAILED - {e}")
