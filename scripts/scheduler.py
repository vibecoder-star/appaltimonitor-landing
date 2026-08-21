#!/usr/bin/env python3
"""
AppaltiMonitor — Autonomous Scheduler
Runs independently from Hermes CLI.

Can be:
1. Started as a background daemon
2. Called by cron every hour
3. Run as a systemd service

Environment variables required:
- SENDER_EMAIL
- SENDER_PASSWORD
- TEST_RECIPIENT_EMAIL
"""

import os
import sys
import time
import signal
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('/opt/autonomous-venture-engine/appalti-monitor/data/logs/scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add app to path
sys.path.insert(0, '/opt/autonomous-venture-engine/appalti-monitor')

from commercial_pipeline import CommercialPipeline, TrialManager

running = True

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global running
    logger.info(f"Received signal {signum}, shutting down...")
    running = False

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


def run_scan():
    """Run a single scan cycle"""
    try:
        pipeline = CommercialPipeline()
        
        # 1. Run scheduled scan (reports, expiration checks)
        results = pipeline.run_scheduled_scan()
        logger.info(f"Scan completed: {len(results)} actions performed")
        
        # 2. Check for trials needing attention
        manager = TrialManager()
        
        active_trials = manager.get_trials_by_state("TRIAL_ACTIVE")
        for trial in active_trials:
            state = manager.check_trial_expiration(trial["id"])
            if state in ("TRIAL_ENDING", "TRIAL_EXPIRED"):
                logger.info(f"Trial {trial['id']}: {state}")
        
        return True
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        return False


def run_daemon():
    """Run as a persistent daemon"""
    logger.info("AppaltiMonitor Scheduler started")
    
    while running:
        run_scan()
        
        # Sleep for 1 hour
        for _ in range(3600):
            if not running:
                break
            time.sleep(1)
    
    logger.info("Scheduler stopped")


def run_once():
    """Run a single scan (for cron)"""
    logger.info("Running single scan")
    run_scan()
    logger.info("Single scan completed")


if __name__ == "__main__":
    if "--daemon" in sys.argv:
        run_daemon()
    elif "--once" in sys.argv:
        run_once()
    else:
        run_once()
