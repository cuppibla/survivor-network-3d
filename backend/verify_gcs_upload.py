import os
import requests
import uuid
# Create a dummy image file
dummy_file = f"test_upload_{uuid.uuid4()}.txt"
with open(dummy_file, "w") as f:
    f.write("This is a test file to verify unique uploads.")

from services.gcs_service import GCSService
from config import MediaType

def verify_upload():
    print("--- Verifying GCS Upload Logic ---")
    service = GCSService()
    
    # Upload 1
    print("\n1. Uploading file (Round 1)...")
    uri1, type1, signed_url1 = service.upload_file(dummy_file, "test_user")
    print(f"   URI: {uri1}")
    print(f"   Signed URL (Start): {signed_url1[:50]}...")
    
    # Upload 2 (Same file)
    print("\n2. Uploading same file (Round 2)...")
    uri2, type2, signed_url2 = service.upload_file(dummy_file, "test_user")
    print(f"   URI: {uri2}")
    print(f"   Signed URL (Start): {signed_url2[:50]}...")
    
    # Check Uniqueness
    print("\n3. Checking Uniqueness...")
    if uri1 != uri2:
        print("✅ SUCCESS: Upload URIs are unique.")
    else:
        print("❌ FAILURE: Upload URIs are identical (Overwriting occurred).")

    # Check Connectivity
    print("\n4. Checking Signed URL Access...")
    try:
        resp = requests.get(signed_url1)
        if resp.status_code == 200:
             print("✅ SUCCESS: Signed URL is accessible (200 OK).")
        else:
             print(f"❌ FAILURE: Signed URL returned {resp.status_code}.")
    except Exception as e:
        print(f"❌ FAILURE: Could not connect to Signed URL: {e}")

    # Cleanup
    if os.path.exists(dummy_file):
        os.remove(dummy_file)

if __name__ == "__main__":
    verify_upload()
