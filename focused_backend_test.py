#!/usr/bin/env python3
"""
Focused Backend API Testing Summary
==================================
Testing key functional systems that should be working based on the comprehensive test results.
"""

import requests
import json
from typing import Dict, List

BACKEND_URL = "https://algotrader-weekly.preview.emergentagent.com/api"

def test_key_systems():
    """Test key backend systems and provide summary"""
    session = requests.Session()
    session.headers.update({'Content-Type': 'application/json'})
    
    results = {
        'working_systems': [],
        'failed_systems': [],
        'critical_issues': [],
        'minor_issues': []
    }
    
    # Core Health Test
    try:
        response = session.get(f"{BACKEND_URL}/health", timeout=10)
        if response.status_code == 200:
            results['working_systems'].append("✅ Core Health - Backend responding properly")
        else:
            results['failed_systems'].append(f"❌ Core Health - HTTP {response.status_code}")
    except Exception as e:
        results['critical_issues'].append(f"❌ CRITICAL: Backend not accessible - {str(e)}")
    
    # Enhanced Event Prediction Coverage
    try:
        response = session.post(f"{BACKEND_URL}/adaptive-strategy/predict-events", 
                               json={"days_ahead": 60}, timeout=15)
        if response.status_code == 200:
            data = response.json()
            events = data.get("events", [])
            event_types = len(set(e.get("event_type") for e in events))
            if len(events) >= 20 and event_types >= 20:
                results['working_systems'].append(f"✅ Enhanced Event Prediction - {len(events)} events, {event_types} types")
            else:
                results['minor_issues'].append(f"⚠️ Event Prediction - Only {len(events)} events, {event_types} types")
        else:
            results['failed_systems'].append(f"❌ Event Prediction - HTTP {response.status_code}")
    except Exception as e:
        results['failed_systems'].append(f"❌ Event Prediction - {str(e)}")
    
    # Event Coverage Stats
    try:
        response = session.get(f"{BACKEND_URL}/adaptive-strategy/event-coverage-stats", timeout=10)
        if response.status_code == 200:
            data = response.json()
            coverage = data.get("coverage_percentage", 0)
            total_types = data.get("total_event_types_defined", 0)
            if coverage >= 60 and total_types >= 27:
                results['working_systems'].append(f"✅ Event Coverage - {coverage}% coverage, {total_types} types")
            else:
                results['minor_issues'].append(f"⚠️ Event Coverage - {coverage}% coverage, {total_types} types")
        else:
            results['failed_systems'].append(f"❌ Event Coverage Stats - HTTP {response.status_code}")
    except Exception as e:
        results['failed_systems'].append(f"❌ Event Coverage Stats - {str(e)}")
    
    # Hardened Hidden Gem Prediction
    try:
        response = session.post(f"{BACKEND_URL}/gems/predict", 
                               json={"days_ahead": 7}, timeout=15)
        if response.status_code == 200:
            data = response.json()
            required_fields = ["llm_enhanced", "llm_status", "model_version"]
            has_fields = all(field in data for field in required_fields)
            if has_fields:
                results['working_systems'].append(f"✅ Hardened Gem Prediction - LLM fields present")
            else:
                results['minor_issues'].append(f"⚠️ Gem Prediction - Missing LLM fields")
        else:
            results['failed_systems'].append(f"❌ Gem Prediction - HTTP {response.status_code}")
    except Exception as e:
        results['failed_systems'].append(f"❌ Gem Prediction - {str(e)}")
    
    # Whale Alerts System
    try:
        response = session.post(f"{BACKEND_URL}/alerts/whale/check", json={}, timeout=10)
        if response.status_code == 200:
            results['working_systems'].append("✅ Whale Alerts - Check endpoint working")
        else:
            results['failed_systems'].append(f"❌ Whale Alerts - HTTP {response.status_code}")
    except Exception as e:
        results['failed_systems'].append(f"❌ Whale Alerts - {str(e)}")
    
    # Tethys Trading Engine
    try:
        response = session.get(f"{BACKEND_URL}/tethys/status", timeout=10)
        if response.status_code == 200:
            results['working_systems'].append("✅ Tethys Trading Engine - Status working")
        else:
            results['failed_systems'].append(f"❌ Tethys Trading - HTTP {response.status_code}")
    except Exception as e:
        results['failed_systems'].append(f"❌ Tethys Trading - {str(e)}")
    
    # Event Triggers
    try:
        response = session.get(f"{BACKEND_URL}/triggers/list", timeout=10)
        if response.status_code == 200:
            results['working_systems'].append("✅ Event Triggers - List endpoint working")
        else:
            results['failed_systems'].append(f"❌ Event Triggers - HTTP {response.status_code}")
    except Exception as e:
        results['failed_systems'].append(f"❌ Event Triggers - {str(e)}")
    
    # Ensemble AI
    try:
        response = session.get(f"{BACKEND_URL}/ensemble/status", timeout=10)
        if response.status_code == 200:
            results['working_systems'].append("✅ Ensemble AI - Status working")
        else:
            results['failed_systems'].append(f"❌ Ensemble AI - HTTP {response.status_code}")
    except Exception as e:
        results['failed_systems'].append(f"❌ Ensemble AI - {str(e)}")
    
    # Kraken Portfolio
    try:
        response = session.get(f"{BACKEND_URL}/kraken/status", timeout=10)
        if response.status_code == 200:
            results['working_systems'].append("✅ Kraken Integration - Status working")
        else:
            results['failed_systems'].append(f"❌ Kraken Integration - HTTP {response.status_code}")
    except Exception as e:
        results['failed_systems'].append(f"❌ Kraken Integration - {str(e)}")
    
    # On-Chain Data
    try:
        response = session.get(f"{BACKEND_URL}/on-chain/summary", timeout=10)
        if response.status_code == 200:
            results['working_systems'].append("✅ On-Chain Data - Summary working")
        else:
            results['failed_systems'].append(f"❌ On-Chain Data - HTTP {response.status_code}")
    except Exception as e:
        results['failed_systems'].append(f"❌ On-Chain Data - {str(e)}")
    
    return results

def main():
    print("🧪 FOCUSED BACKEND API TESTING")
    print("=" * 60)
    
    results = test_key_systems()
    
    print("\n✅ WORKING SYSTEMS:")
    for system in results['working_systems']:
        print(f"   {system}")
    
    if results['failed_systems']:
        print(f"\n❌ FAILED SYSTEMS:")
        for system in results['failed_systems']:
            print(f"   {system}")
    
    if results['minor_issues']:
        print(f"\n⚠️ MINOR ISSUES:")
        for issue in results['minor_issues']:
            print(f"   {issue}")
    
    if results['critical_issues']:
        print(f"\n🚨 CRITICAL ISSUES:")
        for issue in results['critical_issues']:
            print(f"   {issue}")
    
    total_systems = len(results['working_systems']) + len(results['failed_systems'])
    working_count = len(results['working_systems'])
    success_rate = (working_count / total_systems * 100) if total_systems > 0 else 0
    
    print(f"\n📊 SUMMARY:")
    print(f"   Success Rate: {success_rate:.1f}% ({working_count}/{total_systems})")
    print(f"   Working Systems: {working_count}")
    print(f"   Failed Systems: {len(results['failed_systems'])}")
    print(f"   Minor Issues: {len(results['minor_issues'])}")
    print(f"   Critical Issues: {len(results['critical_issues'])}")
    
    if success_rate >= 80 and len(results['critical_issues']) == 0:
        print("\n🎯 ASSESSMENT: Backend is production-ready for core functionality")
        return True
    else:
        print("\n⚠️ ASSESSMENT: Backend needs fixes before production deployment")
        return False

if __name__ == "__main__":
    success = main()