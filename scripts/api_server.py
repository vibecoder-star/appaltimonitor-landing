#!/usr/bin/env python3
"""
AppaltiMonitor — API Server with Mailchimp Marketing Integration
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify

app = Flask(__name__)

# Load .env
def load_env():
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import commercial pipeline
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from commercial_pipeline import CommercialPipeline

pipeline = CommercialPipeline()

# Mailchimp Marketing Integration
class MailchimpService:
    def __init__(self):
        self.api_key = os.environ.get('MC_API_KEY', '')
        self.server = os.environ.get('MC_SERVER', 'us22')
        self.enabled = bool(self.api_key)
        self.client = None
        
        if self.enabled:
            try:
                from mailchimp_marketing import Client
                self.client = Client()
                self.client.set_config({
                    "api_key": self.api_key,
                    "server": self.server
                })
                logger.info("Mailchimp Marketing client initialized")
            except Exception as e:
                logger.error(f"Mailchimp init error: {e}")
                self.enabled = False
    
    def health_check(self):
        if not self.enabled:
            return {"status": "disabled"}
        try:
            response = self.client.ping.get()
            return {"status": "ok", "health": response.get('health_status', 'N/A')}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def get_lists(self):
        if not self.enabled:
            return {"status": "disabled", "lists": []}
        try:
            lists = self.client.lists.get_all_lists()
            return {"status": "ok", "lists": lists.get('lists', [])}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def add_subscriber(self, list_id, email, first_name="", last_name="", tags=None):
        if not self.enabled:
            return {"status": "disabled"}
        try:
            member = {
                "email_address": email,
                "status": "subscribed",
                "merge_fields": {
                    "FNAME": first_name,
                    "LNAME": last_name
                }
            }
            if tags:
                member["tags"] = tags
            
            response = self.client.lists.add_list_member(list_id, member)
            logger.info(f"Added subscriber {email} to list {list_id}")
            return {"status": "ok", "id": response.get("id", "")}
        except Exception as e:
            logger.error(f"Add subscriber error: {e}")
            return {"status": "error", "error": str(e)}

mailchimp = MailchimpService()

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "time": datetime.utcnow().isoformat()})

@app.route('/api/mailchimp/health', methods=['GET'])
def mailchimp_health():
    return jsonify(mailchimp.health_check())

@app.route('/api/mailchimp/lists', methods=['GET'])
def mailchimp_lists():
    return jsonify(mailchimp.get_lists())

@app.route('/api/optin', methods=['POST'])
def optin():
    try:
        data = request.get_json() or request.form.to_dict()
        logger.info(f"Opt-in: {data.get('companyName')} - {data.get('businessEmail')}")
        
        result = pipeline.process_optin(data)
        
        # Add to Mailchimp if available
        if result.get('success') and mailchimp.enabled:
            # Get the first list
            lists = mailchimp.get_lists()
            if lists.get('status') == 'ok' and lists.get('lists'):
                list_id = lists['lists'][0]['id']
                mailchimp.add_subscriber(
                    list_id=list_id,
                    email=data.get('businessEmail', ''),
                    first_name=data.get('companyName', ''),
                    tags=["opt-in", "trial"]
                )
        
        return jsonify(result), 200 if result.get('success') else 400
    except Exception as e:
        logger.error(f"Opt-in error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/trial/<trial_id>/confirm', methods=['POST'])
def confirm(trial_id):
    try:
        result = pipeline.confirm_and_start_trial(trial_id)
        return jsonify(result), 200 if result.get('success') else 400
    except Exception as e:
        logger.error(f"Confirm error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/order', methods=['POST'])
def order():
    try:
        data = request.get_json() or request.form.to_dict()
        logger.info(f"Order received: {data.get('companyName')} - {data.get('businessEmail')} - Offer: {data.get('offer', 'analisi-personalizzata-99')}")
        
        # Save order to file
        order_id = f"order_{datetime.now().strftime('%Y%m%d%H%M%S')}_{data.get('businessEmail', 'unknown').split('@')[0]}"
        order_data = {
            "id": order_id,
            "status": "pending_payment",
            "created": datetime.utcnow().isoformat(),
            **data
        }
        
        # Save to orders directory
        orders_dir = Path("/opt/autonomous-venture-engine/appalti-monitor/data/orders")
        orders_dir.mkdir(parents=True, exist_ok=True)
        with open(orders_dir / f"{order_id}.json", "w") as f:
            json.dump(order_data, f, indent=2)
        
        # Send notification email
        try:
            from commercial_pipeline import EmailSender
            sender = EmailSender()
            sender.send(
                to_email="appalti.monitor@gmail.com",
                subject=f"New Order: {data.get('companyName')} - €99",
                body=f"New order received:\n\nCompany: {data.get('companyName')}\nEmail: {data.get('businessEmail')}\nIndustry: {data.get('industry')}\nGeo: {data.get('geoArea')}\nValue: {data.get('valueRange')}\nNotes: {data.get('notes')}\n\nOrder ID: {order_id}"
            )
        except Exception as e:
            logger.error(f"Failed to send order notification: {e}")
        
        return jsonify({"success": True, "order_id": order_id, "message": "Order received. Payment instructions will be sent within 24h."}), 200
    except Exception as e:
        logger.error(f"Order error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
