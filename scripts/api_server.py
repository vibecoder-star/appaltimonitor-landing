#!/usr/bin/env python3
"""
AppaltiMonitor — Minimal API Server
Handles opt-in form submissions and returns JSON responses.
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "time": datetime.utcnow().isoformat()})

@app.route('/api/optin', methods=['POST'])
def optin():
    try:
        data = request.get_json() or request.form.to_dict()
        logger.info(f"Opt-in received: {data.get('companyName', 'N/A')} - {data.get('businessEmail', 'N/A')}")
        
        required = ['companyName', 'businessEmail', 'industry', 'geoArea']
        for field in required:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        if not data.get('consentService') or not data.get('consentPrivacy'):
            return jsonify({'success': False, 'error': 'Consent required for service and privacy'}), 400
        
        trial_id = f"trial_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        return jsonify({
            'success': True,
            'trial_id': trial_id,
            'message': 'Opt-in received. Please check your email to confirm.',
            'next_step': f'/api/trial/{trial_id}/confirm'
        })
    except Exception as e:
        logger.error(f"Opt-in error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
