#!/usr/bin/env python3
import os, json, logging
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "time": datetime.utcnow().isoformat()})

@app.route("/api/optin", methods=["POST"])
def optin():
    data = request.get_json() or request.form.to_dict()
    return jsonify({"success": True, "message": "Opt-in received", "data": data})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
