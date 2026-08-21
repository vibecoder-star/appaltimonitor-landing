#!/usr/bin/env python3
"""
AppaltiMonitor — Autonomous Background Process
Runs independently using nohup. Survives SSH disconnection.

Start: python3 scripts/auto_daemon.py &
Stop: kill $(cat /tmp/appaltimonitor.pid)
"""

import os
import sys
import time
import signal
import atexit
from datetime import datetime
from pathlib import Path

# Setup paths
BASE_DIR = Path("/opt/autonomous-venture-engine/appalti-monitor")
sys.path.insert(0, str(BASE_DIR))

# Setup logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(BASE_DIR / 'data/logs/auto_daemon.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# PID file
PID_FILE = Path("/tmp/appaltimonitor.pid")

def write_pid():
    """Write PID file"""
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

def remove_pid():
    """Remove PID file"""
    if PID_FILE.exists():
        PID_FILE.unlink()

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Signal {signum} received, shutting down...")
    remove_pid()
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

def run_scan():
    """Run one scan cycle"""
    try:
        from commercial_pipeline import CommercialPipeline, TrialManager
        
        pipeline = CommercialPipeline()
        results = pipeline.run_scheduled_scan()
        logger.info(f"Scan: {len(results)} actions")
        
        manager = TrialManager()
        active = manager.get_trials_by_state("TRIAL_ACTIVE")
        for trial in active:
            state = manager.check_trial_expiration(trial["id"])
            if state != "TRIAL_ACTIVE":
                logger.info(f"Trial {trial['id']}: {state}")
        
        return True
    except Exception as e:
        logger.error(f"Scan failed: {e}", exc_info=True)
        return False

def main():
    """Main loop"""
    write_pid()
    atexit.register(remove_pid)
    
    logger.info("="*50)
    logger.info("AppaltiMonitor Auto-Daemon Started")
    logger.info("="*50)
    
    SCAN_INTERVAL = 3600  # 1 hour
    
    while True:
        run_scan()
        logger.info(f"Sleeping {SCAN_INTERVAL}s...")
        time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    main()
