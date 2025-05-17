#!/usr/bin/env python3
"""
Test script for file upload and processing flow
"""
import requests
import json
import time
import sys

API_BASE = "http://localhost:8000"

def test_file_upload_flow():
    """Test the complete file upload flow"""
    
    print("🧪 Testing File Upload Flow")
    print("=" * 40)
    
    # Step 1: Create test user (if needed)
    print("\n1️⃣ Creating test user...")
    response = requests.post(f"{API_BASE}/api/v1/setup/test-user")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    # Step 2: Initiate file upload
    print("\n2️⃣ Initiating file upload...")
    upload_params = {
        "filename": "test_document.pdf",
        "content_type": "application/pdf",
        "size_bytes": 1024
    }
    response = requests.post(
        f"{API_BASE}/api/v1/files/ingest",
        params=upload_params
    )
    
    if response.status_code != 200:
        print(f"   ❌ Error: {response.status_code}")
        print(f"   Response: {response.text}")
        return
    
    upload_data = response.json()
    file_id = upload_data.get("fileId")
    upload_url = upload_data.get("uploadUrl")
    
    print(f"   ✅ File ID: {file_id}")
    print(f"   Upload URL: {upload_url}")
    
    # Step 3: Simulate file upload (in real scenario, would upload to the URL)
    print("\n3️⃣ Simulating file upload to storage...")
    print("   (In production, file would be uploaded to presigned URL)")
    
    # Step 4: Process the file
    print("\n4️⃣ Processing the file...")
    response = requests.post(f"{API_BASE}/api/v1/files/{file_id}/process")
    
    if response.status_code != 200:
        print(f"   ❌ Error: {response.status_code}")
        print(f"   Response: {response.text}")
        return
    
    process_result = response.json()
    print(f"   ✅ Status: {process_result.get('status')}")
    print(f"   Text Length: {process_result.get('text_length')} characters")
    
    # Step 5: Check file status
    print("\n5️⃣ Checking file status...")
    response = requests.get(f"{API_BASE}/api/v1/files/{file_id}/status")
    
    if response.status_code != 200:
        print(f"   ❌ Error: {response.status_code}")
        print(f"   Response: {response.text}")
        return
    
    status_data = response.json()
    print(f"   ✅ Status: {status_data.get('status')}")
    print(f"   Filename: {status_data.get('filename')}")
    print(f"   Size: {status_data.get('size')} bytes")
    
    # Step 6: List all files
    print("\n6️⃣ Listing all files...")
    response = requests.get(f"{API_BASE}/api/v1/files/")
    
    if response.status_code != 200:
        print(f"   ❌ Error: {response.status_code}")
        print(f"   Response: {response.text}")
        return
    
    files_list = response.json()
    print(f"   ✅ Total files: {len(files_list)}")
    for file in files_list[:3]:  # Show first 3 files
        print(f"   - {file.get('filename')} ({file.get('status')})")
    
    print("\n✅ Test completed successfully!")
    print("=" * 40)

def test_api_health():
    """Test basic API connectivity"""
    print("\n🏥 Testing API Health...")
    
    try:
        response = requests.get(f"{API_BASE}/health")
        if response.status_code == 200:
            print("   ✅ API is healthy")
            return True
        else:
            print(f"   ❌ API returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Could not connect to API: {e}")
        return False

if __name__ == "__main__":
    print("🚀 File Upload Test Script")
    print("=" * 40)
    
    # Check if API is running
    if not test_api_health():
        print("\n❌ API is not running. Please start it first.")
        sys.exit(1)
    
    # Run the test
    try:
        test_file_upload_flow()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)