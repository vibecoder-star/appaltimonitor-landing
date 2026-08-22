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
from commercial_pipeline import CommercialPipeline

app = Flask(__name__)
pipeline = CommercialPipeline()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/api/optin', methods=['POST'])
def handle_optin():
    """Handle opt-in form submission."""
    try:
        data = request.get_json() or request.form.to_dict()
        data['source'] = 'api'
        
        result = pipeline.process_optin(data)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Opt-in error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/trial/<trial_id>/confirm', methods=['POST'])
def confirm_trial(trial_id):
    """Confirm a trial and start report generation."""
    try:
        result = pipeline.confirm_and_start_trial(trial_id)
        return jsonify(result), 200 if result.get('success') else 400
    except Exception as e:
        logger.error(f"Confirm error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'AppaltiMonitor API'
    }), 200

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
