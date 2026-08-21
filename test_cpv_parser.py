#!/usr/bin/env python3
"""
AppaltiMonitor — Regression Tests for CPV Parser and Matching
"""

import sys
import os
sys.path.insert(0, '/opt/autonomous-venture-engine/appalti-monitor')

from mvp_pipeline import PipelineOrchestrator, ProfileEngine, RelevanceEngine

def test_extract_cpv_list():
    """Test CPV extraction from various TED field formats"""
    orchestrator = PipelineOrchestrator()
    
    tests = [
        # (input, expected_output, description)
        (["72310000", "72316000"], ["72310000", "72316000"], "Simple list of CPVs"),
        (["72310000"], ["72310000"], "Single CPV in list"),
        ([], [], "Empty list"),
        (None, [], "None value"),
        ("", [], "Empty string"),
        ({"ita": ["72310000", "72316000"]}, ["72310000", "72316000"], "Dict with Italian CPVs"),
        ({"eng": ["72310000"]}, ["72310000"], "Dict with English CPVs"),
        ({"ita": "72310000"}, ["72310000"], "Dict with single Italian CPV"),
        ("72310000", ["72310000"], "Plain string CPV"),
        (["72310000", "72316000", "71354100"], ["72310000", "72316000", "71354100"], "Multiple CPVs"),
        ([" 72310000 ", " 72316000 "], ["72310000", "72316000"], "CPVs with whitespace"),
    ]
    
    passed = 0
    failed = 0
    
    for input_val, expected, description in tests:
        result = orchestrator._extract_cpv_list(input_val)
        if result == expected:
            print(f"✅ PASS: {description}")
            passed += 1
        else:
            print(f"❌ FAIL: {description}")
            print(f"   Input: {input_val}")
            print(f"   Expected: {expected}")
            print(f"   Got: {result}")
            failed += 1
    
    print(f"\n{passed}/{passed+failed} tests passed")
    return failed == 0


def test_cpv_matching():
    """Test CPV prefix matching logic"""
    profile = {
        "cpv_codes": ["72", "48"],
        "cpv_detailed": ["72210000", "72220000"],
        "countries": ["ITA"],
        "value_min": 30000,
        "value_max": 500000,
        "keywords": ["software"],
        "preferred_buyers": []
    }
    
    engine = RelevanceEngine(profile)
    
    tests = [
        # (tender_cpv_list, expected_min_score, description)
        (["72310000"], 30, "CPV starting with 72 should match"),
        (["48983000"], 30, "CPV starting with 48 should match"),
        (["72210000"], 40, "Detailed CPV match (72 + 10 bonus)"),
        (["45000000"], 0, "CPV starting with 45 should NOT match"),
        (["90511300"], 0, "CPV starting with 90 should NOT match"),
        (["72310000", "45000000"], 30, "Multiple CPVs, one matches"),
        ([], 0, "Empty CPV list"),
        ([""], 0, "Empty string CPV"),
    ]
    
    passed = 0
    failed = 0
    
    for cpv_list, expected_min_score, description in tests:
        tender = {
            "cpv": cpv_list[0] if cpv_list else "",
            "cpv_list": cpv_list,
            "title": "Test tender",
            "buyer": "Test buyer",
            "place_performance": "ITA",
            "estimated_value": 50000,
            "is_active": True,
            "deadline": "2026-09-01"
        }
        
        result = engine.score_tender(tender)
        score = result["total"]
        
        if score >= expected_min_score:
            print(f"✅ PASS: {description} (score: {score})")
            passed += 1
        else:
            print(f"❌ FAIL: {description}")
            print(f"   Expected min score: {expected_min_score}")
            print(f"   Got: {score}")
            print(f"   Breakdown: {result['breakdown']}")
            failed += 1
    
    print(f"\n{passed}/{passed+failed} tests passed")
    return failed == 0


def test_full_pipeline():
    """Test full pipeline with real TED API"""
    print("\n=== FULL PIPELINE TEST ===")
    
    orchestrator = PipelineOrchestrator()
    profile_engine = ProfileEngine()
    
    # Create test profile
    profile_data = {
        "id": "test_regression",
        "company_name": "Test Company",
        "industry": "IT Services",
        "cpv_codes": ["72", "48"],
        "cpv_detailed": ["72210000"],
        "countries": ["ITA"],
        "value_min": 30000,
        "value_max": 500000,
        "keywords": ["software"],
        "preferred_buyers": [],
        "notes": "Regression test profile"
    }
    
    profile = profile_engine.create_profile(profile_data)
    
    # Run pipeline
    status = orchestrator.run(profile["id"])
    
    if status.get("error"):
        print(f"❌ Pipeline failed: {status['error']}")
        return False
    
    print(f"✅ Pipeline completed")
    print(f"   Total retrieved: {status['total_retrieved']}")
    print(f"   Relevant: {status['relevant']}")
    print(f"   High priority: {status['high_priority']}")
    print(f"   Medium priority: {status['medium_priority']}")
    print(f"   Low priority: {status['low_priority']}")
    
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("AppaltiMonitor — CPV Parser Regression Tests")
    print("=" * 60)
    
    all_passed = True
    
    print("\n=== CPV EXTRACTION TESTS ===")
    if not test_extract_cpv_list():
        all_passed = False
    
    print("\n=== CPV MATCHING TESTS ===")
    if not test_cpv_matching():
        all_passed = False
    
    print("\n=== FULL PIPELINE TEST ===")
    if not test_full_pipeline():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("ALL TESTS PASSED ✅")
    else:
        print("SOME TESTS FAILED ❌")
    print("=" * 60)
