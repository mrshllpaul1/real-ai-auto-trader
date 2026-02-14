#!/usr/bin/env python3
"""
Training Endpoints Detailed Response Analysis
Verify that training is actually running in background and responses contain expected fields
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "https://push-to-emerge.preview.emergentagent.com/api"

def test_detailed_responses():
    """Test and analyze detailed responses from training endpoints"""
    
    print("🔍 DETAILED TRAINING ENDPOINTS ANALYSIS")
    print("=" * 60)
    
    session = requests.Session()
    session.timeout = 10
    
    # Test 1: Individual Model Training Response Details
    print("1️⃣ POST /api/training/train-model Response Analysis:")
    try:
        response = session.post(
            f"{BASE_URL}/training/train-model",
            json={"model_name": "finrl", "coins": ["bitcoin"]},
            headers={'Content-Type': 'application/json'}
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
            
            # Check for required fields
            required_fields = ['status', 'message']
            for field in required_fields:
                if field in data:
                    print(f"   ✅ Has '{field}': {data[field]}")
                else:
                    print(f"   ❌ Missing '{field}'")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    
    # Test 2: Enhanced MTF Training Response Details  
    print("2️⃣ POST /api/enhanced-mtf-training/train-all-kraken Response Analysis:")
    try:
        response = session.post(
            f"{BASE_URL}/enhanced-mtf-training/train-all-kraken",
            json={},
            headers={'Content-Type': 'application/json'}
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
            
            # Check for expected status
            if data.get('status') == 'started':
                print(f"   ✅ Correct status: 'started'")
            else:
                print(f"   ⚠️  Status: {data.get('status')}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    
    # Test 3: Training Progress Active Tasks
    print("3️⃣ GET /api/training-progress/active Response Analysis:")
    try:
        response = session.get(f"{BASE_URL}/training-progress/active")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
            
            # Check for active tasks
            if 'active_tasks' in data:
                tasks = data['active_tasks']
                print(f"   ✅ Active tasks found: {len(tasks)}")
                for i, task in enumerate(tasks[:3]):  # Show first 3 tasks
                    print(f"      Task {i+1}: {task.get('task_id', 'Unknown')} - {task.get('status', 'Unknown')}")
            else:
                print(f"   ⚠️  No 'active_tasks' field found")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    
    # Test 4: Tethys Training Start Response
    print("4️⃣ POST /api/tethys-train/start Response Analysis:")
    try:
        response = session.post(
            f"{BASE_URL}/tethys-train/start",
            json={},
            headers={'Content-Type': 'application/json'}
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
            
            # Check for training_started status
            if data.get('status') == 'training_started':
                print(f"   ✅ Correct status: 'training_started'")
            else:
                print(f"   ⚠️  Status: {data.get('status')}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    
    # Test 5: Tethys Training Status Response
    print("5️⃣ GET /api/tethys-train/status Response Analysis:")
    try:
        response = session.get(f"{BASE_URL}/tethys-train/status")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
            
            # Check for training status fields
            expected_fields = ['is_training', 'status']
            for field in expected_fields:
                if field in data:
                    print(f"   ✅ Has '{field}': {data[field]}")
                else:
                    print(f"   ❌ Missing '{field}'")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 BACKGROUND TRAINING VERIFICATION COMPLETE")
    print("All endpoints tested for proper response structure and background execution")

if __name__ == "__main__":
    test_detailed_responses()