#!/usr/bin/env python3
"""
Tethys Toggle Functionality - Complete Cycle Test
Ensures we start from a clean state and test the full toggle cycle.
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "https://launch-crypto-2.preview.emergentagent.com/api"

def test_complete_tethys_cycle():
    """Test complete Tethys toggle cycle starting from clean state"""
    session = requests.Session()
    session.timeout = 5
    
    print("🎯 TETHYS COMPLETE CYCLE TEST")
    print("=" * 50)
    
    # Step 1: Stop any existing training first
    print("\n🛑 STEP 0: Ensure clean state - Stop any existing training")
    try:
        response = session.post(f"{BASE_URL}/tethys-train/stop")
        print(f"   Stop request: {response.status_code}")
        time.sleep(2)  # Wait for stop to take effect
    except Exception as e:
        print(f"   Stop request error: {e}")
    
    # Step 1: Check initial status (should be false now)
    print("\n1️⃣ STEP 1: Check initial training status")
    try:
        response = session.get(f"{BASE_URL}/tethys-train/status")
        data = response.json()
        is_training = data.get('is_training', False)
        print(f"   Status: {response.status_code}")
        print(f"   is_training: {is_training}")
        print(f"   Response time: {response.elapsed.total_seconds():.3f}s")
        
        if is_training:
            print("   ⚠️  Training still active, waiting for stop...")
            time.sleep(3)
            response = session.get(f"{BASE_URL}/tethys-train/status")
            data = response.json()
            is_training = data.get('is_training', False)
            print(f"   After wait - is_training: {is_training}")
        
        step1_success = response.status_code == 200
        print(f"   Result: {'✅ PASS' if step1_success else '❌ FAIL'}")
        
    except Exception as e:
        print(f"   ❌ FAIL - Error: {e}")
        step1_success = False
    
    # Step 2: Start training
    print("\n2️⃣ STEP 2: Start training")
    try:
        config = {"episodes": 5, "symbol": "BTC"}
        response = session.post(f"{BASE_URL}/tethys-train/start", json=config)
        data = response.json()
        status = data.get('status', '')
        print(f"   Status: {response.status_code}")
        print(f"   Response status: {status}")
        print(f"   Response time: {response.elapsed.total_seconds():.3f}s")
        
        step2_success = response.status_code == 200 and status == 'training_started'
        print(f"   Result: {'✅ PASS' if step2_success else '❌ FAIL'}")
        
    except Exception as e:
        print(f"   ❌ FAIL - Error: {e}")
        step2_success = False
    
    # Step 3: Verify training started (with retries)
    print("\n3️⃣ STEP 3: Verify training started")
    step3_success = False
    for attempt in range(5):
        try:
            time.sleep(1)  # Wait between attempts
            response = session.get(f"{BASE_URL}/tethys-train/status")
            data = response.json()
            is_training = data.get('is_training', False)
            current_episode = data.get('current_episode', 0)
            
            print(f"   Attempt {attempt + 1}: is_training={is_training}, episode={current_episode}")
            
            if is_training:
                step3_success = True
                print(f"   ✅ Training confirmed active!")
                break
                
        except Exception as e:
            print(f"   Attempt {attempt + 1} error: {e}")
    
    print(f"   Result: {'✅ PASS' if step3_success else '❌ FAIL'}")
    
    # Step 4: Stop training
    print("\n4️⃣ STEP 4: Stop training")
    try:
        response = session.post(f"{BASE_URL}/tethys-train/stop")
        data = response.json()
        status = data.get('status', '')
        print(f"   Status: {response.status_code}")
        print(f"   Response status: {status}")
        print(f"   Response time: {response.elapsed.total_seconds():.3f}s")
        
        step4_success = response.status_code == 200 and status == 'stop_requested'
        print(f"   Result: {'✅ PASS' if step4_success else '❌ FAIL'}")
        
    except Exception as e:
        print(f"   ❌ FAIL - Error: {e}")
        step4_success = False
    
    # Step 5: Verify training stopped
    print("\n5️⃣ STEP 5: Verify training stopped")
    step5_success = False
    for attempt in range(3):
        try:
            time.sleep(1)  # Wait for stop to take effect
            response = session.get(f"{BASE_URL}/tethys-train/status")
            data = response.json()
            is_training = data.get('is_training', False)
            
            print(f"   Attempt {attempt + 1}: is_training={is_training}")
            
            if not is_training:
                step5_success = True
                print(f"   ✅ Training confirmed stopped!")
                break
                
        except Exception as e:
            print(f"   Attempt {attempt + 1} error: {e}")
    
    print(f"   Result: {'✅ PASS' if step5_success else '❌ FAIL'}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 FINAL SUMMARY")
    print("=" * 50)
    
    results = [step1_success, step2_success, step3_success, step4_success, step5_success]
    passed = sum(results)
    total = len(results)
    success_rate = (passed / total) * 100
    
    print(f"Success Rate: {success_rate:.1f}% ({passed}/{total} tests passed)")
    print(f"")
    print(f"Step 1 - Initial Status: {'✅ PASS' if step1_success else '❌ FAIL'}")
    print(f"Step 2 - Start Training: {'✅ PASS' if step2_success else '❌ FAIL'}")
    print(f"Step 3 - Verify Started: {'✅ PASS' if step3_success else '❌ FAIL'}")
    print(f"Step 4 - Stop Training: {'✅ PASS' if step4_success else '❌ FAIL'}")
    print(f"Step 5 - Verify Stopped: {'✅ PASS' if step5_success else '❌ FAIL'}")
    
    if success_rate == 100:
        print(f"\n🎉 TETHYS TOGGLE FUNCTIONALITY: ✅ FULLY FUNCTIONAL")
    elif success_rate >= 80:
        print(f"\n⚠️  TETHYS TOGGLE FUNCTIONALITY: MOSTLY FUNCTIONAL")
    else:
        print(f"\n❌ TETHYS TOGGLE FUNCTIONALITY: CRITICAL ISSUES")

if __name__ == "__main__":
    test_complete_tethys_cycle()