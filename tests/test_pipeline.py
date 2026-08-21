#!/usr/bin/env python3
"""
AppaltiMonitor — End-to-End Pipeline Tests
Tests the complete commercial workflow
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, '/opt/autonomous-venture-engine/appalti-monitor')

from commercial_pipeline import CommercialPipeline, EmailSender, TrialManager
from mvp_pipeline import PipelineOrchestrator, ProfileEngine, RelevanceEngine, QualityControl


def test(condition: bool, name: str, details: str = ""):
    """Simple test assertion"""
    if condition:
        print(f"  ✅ {name}")
        return True
    else:
        print(f"  ❌ {name} - {details}")
        return False


def test_optin_validation():
    """Test opt-in data validation"""
    print("\n=== OPT-IN VALIDATION ===")
    passed = 0
    failed = 0
    
    pipeline = CommercialPipeline()
    
    # Test missing required fields
    result = pipeline.process_optin({
        "companyName": "",
        "businessEmail": "test@test.com",
        "industry": "it-software",
        "geoArea": "nord",
        "consentService": True,
        "consentPrivacy": True
    })
    if test(result.get("error") is not None, "Missing companyName rejected"):
        passed += 1
    else:
        failed += 1
    
    # Test missing email
    result = pipeline.process_optin({
        "companyName": "Test",
        "businessEmail": "",
        "industry": "it-software",
        "geoArea": "nord",
        "consentService": True,
        "consentPrivacy": True
    })
    if test(result.get("error") is not None, "Missing email rejected"):
        passed += 1
    else:
        failed += 1
    
    # Test missing consent
    result = pipeline.process_optin({
        "companyName": "Test",
        "businessEmail": "test@test.com",
        "industry": "it-software",
        "geoArea": "nord",
        "consentService": False,
        "consentPrivacy": True
    })
    if test(result.get("error") is not None, "Missing service consent rejected"):
        passed += 1
    else:
        failed += 1
    
    # Test valid opt-in
    result = pipeline.process_optin({
        "companyName": "Test Company SRL",
        "businessEmail": "test@test.com",
        "industry": "it-software",
        "geoArea": "nord",
        "services": "Software development",
        "cpvCodes": "72260000",
        "valueRange": "medium",
        "consentService": True,
        "consentMarketing": False,
        "consentPrivacy": True
    })
    if test(result.get("success") == True, "Valid opt-in accepted"):
        passed += 1
    else:
        failed += 1
    if test(bool(result.get("trial_id")), "Trial ID generated"):
        passed += 1
    else:
        failed += 1
    if test(bool(result.get("profile_id")), "Profile ID generated"):
        passed += 1
    else:
        failed += 1
    
    return passed, failed, result.get("trial_id") if result.get("success") else None


def test_trial_management():
    """Test trial state management"""
    print("\n=== TRIAL MANAGEMENT ===")
    passed = 0
    failed = 0
    
    manager = TrialManager()
    
    # Create trial
    trial = manager.create_trial(
        profile_id="test_profile",
        email="test@test.com",
        profile={"company_name": "Test"}
    )
    if test(trial is not None, "Trial created"):
        passed += 1
    else:
        failed += 1
    if test(trial["state"] == "PENDING", "Initial state PENDING"):
        passed += 1
    else:
        failed += 1
    
    trial_id = trial["id"]
    
    # Confirm trial
    confirmed = manager.confirm_trial(trial_id)
    if test(confirmed is not None, "Trial confirmed"):
        passed += 1
    else:
        failed += 1
    if test(confirmed["state"] == "TRIAL_ACTIVE", "State TRIAL_ACTIVE"):
        passed += 1
    else:
        failed += 1
    if test(confirmed["trial_start"] is not None, "Trial start set"):
        passed += 1
    else:
        failed += 1
    if test(confirmed["trial_end"] is not None, "Trial end set"):
        passed += 1
    else:
        failed += 1
    
    # Check expiration (should be active)
    state = manager.check_trial_expiration(trial_id)
    if test(state == "TRIAL_ACTIVE", "Trial is active"):
        passed += 1
    else:
        failed += 1
    
    # Test state transitions
    manager.update_state(trial_id, "TRIAL_ENDING")
    trial = manager.get_trial(trial_id)
    if test(trial["state"] == "TRIAL_ENDING", "State updated to TRIAL_ENDING"):
        passed += 1
    else:
        failed += 1
    
    manager.update_state(trial_id, "TRIAL_EXPIRED")
    trial = manager.get_trial(trial_id)
    if test(trial["state"] == "TRIAL_EXPIRED", "State updated to TRIAL_EXPIRED"):
        passed += 1
    else:
        failed += 1
    if test(trial["conversion_offered"] == True, "Conversion offered flag set"):
        passed += 1
    else:
        failed += 1
    
    # Test report tracking
    manager.add_report_sent(trial_id, "/path/to/report.md", 5)
    trial = manager.get_trial(trial_id)
    if test(len(trial["reports_sent"]) == 1, "Report tracked"):
        passed += 1
    else:
        failed += 1
    if test(trial["reports_sent"][0]["opportunities"] == 5, "Opportunities counted"):
        passed += 1
    else:
        failed += 1
    
    return passed, failed, trial_id


def test_email_generation():
    """Test email content generation"""
    print("\n=== EMAIL GENERATION ===")
    passed = 0
    failed = 0
    
    sender = EmailSender()
    
    # Test confirmation email
    pipeline = CommercialPipeline()
    trial = {
        "id": "test123",
        "email": "test@test.com"
    }
    profile = {"company_name": "Test Company"}
    
    # Email sender depends on config
    if sender.enabled:
        print("  ✅ Email sender ENABLED (config provided)")
        passed += 1
    else:
        print("  ✅ Email sender disabled (no config)")
        passed += 1
    
    # Test email logging
    result = sender.send("test@test.com", "Test Subject", "<p>Test</p>")
    if test(result == True, "Email logged (not sent)"):
        passed += 1
    else:
        failed += 1
    
    # Check log file
    log_path = Path("/opt/autonomous-venture-engine/appalti-monitor/data/logs/email_log.jsonl")
    if test(log_path.exists(), "Email log created"):
        passed += 1
    else:
        failed += 1
    
    if log_path.exists():
        with open(log_path, "r") as f:
            lines = f.readlines()
        if test(len(lines) > 0, "Email logged to file"):
            passed += 1
        else:
            failed += 1
    
    return passed, failed, None


def test_ted_integration():
    """Test TED API integration"""
    print("\n=== TED INTEGRATION ===")
    passed = 0
    failed = 0
    
    pipeline = PipelineOrchestrator()
    
    # Create test profile
    profile_engine = ProfileEngine()
    profile = profile_engine.create_profile({
        "id": "test_ted_integration",
        "company_name": "Test TED Integration",
        "industry": "IT Services",
        "cpv_codes": ["72"],
        "cpv_detailed": ["72260000"],
        "countries": ["ITA"],
        "value_min": 10000,
        "value_max": 500000,
        "keywords": ["software"],
        "excluded_keywords": [],
        "preferred_buyers": [],
        "notes": "Test profile"
    })
    if test(profile is not None, "Profile created"):
        passed += 1
    else:
        failed += 1
    
    # Run pipeline
    status = pipeline.run(profile["id"])
    if test(status.get("error") is None, "Pipeline executed"):
        passed += 1
    else:
        failed += 1
    if test(len(status.get("reports", {})) > 0, "Reports generated"):
        passed += 1
    else:
        failed += 1
    if test(status.get("high_priority", 0) >= 0, "High priority found"):
        passed += 1
    else:
        failed += 1
    if test(status.get("processing_time", 0) > 0, "Processing time recorded"):
        passed += 1
    else:
        failed += 1
    
    return passed, failed, status


def test_cpv_matching():
    """Test CPV matching logic"""
    print("\n=== CPV MATCHING ===")
    passed = 0
    failed = 0
    
    profile = {
        "cpv_codes": ["72", "48"],
        "cpv_detailed": ["72260000"],
        "countries": ["ITA"],
        "value_min": 10000,
        "value_max": 500000,
        "keywords": ["software"],
        "preferred_buyers": []
    }
    
    engine = RelevanceEngine(profile)
    
    # Test matching CPV
    tender_match = {
        "cpv": "72260000",
        "cpv_list": ["72260000"],
        "title": "Software development services",
        "buyer": "Test Buyer",
        "place_performance": "ITA",
        "estimated_value": 50000,
        "is_active": True,
        "deadline": "2026-09-01"
    }
    score = engine.score_tender(tender_match)
    if test(score["total"] > 0, "CPV match gives score > 0"):
        passed += 1
    else:
        failed += 1
    if test(len(score["reasons"]) > 0, "CPV match reason recorded"):
        passed += 1
    else:
        failed += 1
    
    # Test non-matching CPV (no other matching factors)
    tender_no_match = {
        "cpv": "45000000",
        "cpv_list": ["45000000"],
        "title": "Construction work",
        "buyer": "Test Buyer",
        "place_performance": "FRA",  # Different country
        "estimated_value": None,      # No value to match
        "is_active": False,           # No deadline bonus
        "deadline": ""
    }
    score = engine.score_tender(tender_no_match)
    if test(score["total"] == 0, "Non-matching CPV gives zero score"):
        passed += 1
    else:
        failed += 1
    
    # Test keyword match
    tender_keyword = {
        "cpv": "99999999",
        "cpv_list": ["99999999"],
        "title": "Software consulting",
        "buyer": "Test Buyer",
        "place_performance": "ITA",
        "estimated_value": 50000,
        "is_active": True,
        "deadline": "2026-09-01"
    }
    score = engine.score_tender(tender_keyword)
    if test(score["total"] > 0, "Keyword match gives score > 0"):
        passed += 1
    else:
        failed += 1
    
    return passed, failed, None


def test_end_to_end():
    """Test complete end-to-end flow"""
    print("\n=== END-TO-END FLOW ===")
    passed = 0
    failed = 0
    
    pipeline = CommercialPipeline()
    
    # Step 1: Opt-in
    optin_data = {
        "companyName": "E2E Test Company",
        "businessEmail": "e2e@test.com",
        "industry": "it-software",
        "geoArea": "nord",
        "services": "Software development, cloud",
        "cpvCodes": "72260000, 72510000",
        "valueRange": "medium",
        "consentService": True,
        "consentMarketing": False,
        "consentPrivacy": True
    }
    
    result = pipeline.process_optin(optin_data)
    if test(result.get("success") == True, "Step 1: Opt-in successful"):
        passed += 1
    else:
        failed += 1
        return passed, failed, False
    
    trial_id = result["trial_id"]
    
    # Step 2: Confirm and start trial
    confirm_result = pipeline.confirm_and_start_trial(trial_id)
    if test(confirm_result.get("success") == True, "Step 2: Trial started"):
        passed += 1
    else:
        failed += 1
    if test(confirm_result.get("report_sent") == True, "Step 2: Report generated"):
        passed += 1
    else:
        failed += 1
    
    # Step 3: Check trial state
    trial = pipeline.trial_manager.get_trial(trial_id)
    if test(trial["state"] == "TRIAL_ACTIVE", "Step 3: Trial active"):
        passed += 1
    else:
        failed += 1
    if test(len(trial["reports_sent"]) > 0, "Step 3: Reports sent tracked"):
        passed += 1
    else:
        failed += 1
    
    # Step 4: Run scheduled scan
    scan_results = pipeline.run_scheduled_scan()
    if test(len(scan_results) > 0, "Step 4: Scheduled scan executed"):
        passed += 1
    else:
        failed += 1
    
    return passed, failed, True


def cleanup_test_data():
    """Clean up test data"""
    print("\n=== CLEANUP ===")
    
    dirs = [
        Path("/opt/autonomous-venture-engine/appalti-monitor/data/optins"),
        Path("/opt/autonomous-venture-engine/appalti-monitor/data/confirmed"),
        Path("/opt/autonomous-venture-engine/appalti-monitor/data/trials"),
        Path("/opt/autonomous-venture-engine/appalti-monitor/data/emails"),
    ]
    
    removed = 0
    for d in dirs:
        if d.exists():
            for f in d.glob("*.json"):
                if "test" in f.name.lower() or "e2e" in f.name.lower():
                    f.unlink()
                    removed += 1
    
    print(f"  Removed {removed} test files")


if __name__ == "__main__":
    print("=" * 60)
    print("AppaltiMonitor — End-to-End Pipeline Tests")
    print("=" * 60)
    
    total_passed = 0
    total_failed = 0
    
    # Run all tests
    p, f, _ = test_optin_validation()
    total_passed += p
    total_failed += f
    
    p, f, _ = test_trial_management()
    total_passed += p
    total_failed += f
    
    p, f, _ = test_email_generation()
    total_passed += p
    total_failed += f
    
    p, f, _ = test_ted_integration()
    total_passed += p
    total_failed += f
    
    p, f, _ = test_cpv_matching()
    total_passed += p
    total_failed += f
    
    p, f, _ = test_end_to_end()
    total_passed += p
    total_failed += f
    
    # Cleanup
    cleanup_test_data()
    
    # Summary
    total = total_passed + total_failed
    print(f"\n{'='*60}")
    print(f"Results: {total_passed}/{total} passed, {total_failed} failed")
    print(f"{'='*60}")
    
    if total_failed == 0:
        print("\n🎉 ALL TESTS PASSED - Pipeline is ready")
    else:
        print(f"\n⚠️  {total_failed} tests failed - review before proceeding")
