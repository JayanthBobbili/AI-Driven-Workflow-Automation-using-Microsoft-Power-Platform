"""
Quick test script — run this to verify your FastAPI is working
before connecting Power Automate.

Usage:
    python test_api.py
    python test_api.py http://your-ngrok-url.ngrok.io
"""

import sys
import json
import urllib.request
import urllib.error

BASE_URL = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:8000"

TEST_CASES = [
    {
        "name": "High Priority (urgent keywords)",
        "payload": {
            "request_id":   "REQ-001",
            "user_name":    "Test User",
            "request_text": "urgent approval needed ASAP this is critical",
            "timestamp":    "2026-05-07T10:00:00Z"
        },
        "expected_category": "High Priority"
    },
    {
        "name": "Medium Priority",
        "payload": {
            "request_id":   "REQ-002",
            "user_name":    "Test User 2",
            "request_text": "please review this change request when you get a chance",
            "timestamp":    "2026-05-07T10:01:00Z"
        },
        "expected_category": "Medium Priority"
    },
    {
        "name": "Low Priority",
        "payload": {
            "request_id":   "REQ-003",
            "user_name":    "Test User 3",
            "request_text": "just an FYI no rush whenever you have time",
            "timestamp":    "2026-05-07T10:02:00Z"
        },
        "expected_category": "Low Priority"
    },
    {
        "name": "Your exact sample row",
        "payload": {
            "request_id":   "REQ-001",
            "user_name":    "Test User",
            "request_text": "urgent approval needed",
            "timestamp":    "2026-05-07T00:00:00Z"
        },
        "expected_category": "High Priority"
    }
]

def post_json(url, data):
    body = json.dumps(data).encode()
    req  = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

def run_tests():
    print(f"\n🔍 Testing FastAPI at: {BASE_URL}\n{'─'*55}")

    # Health check
    try:
        req = urllib.request.Request(f"{BASE_URL}/health")
        with urllib.request.urlopen(req, timeout=5) as r:
            health = json.loads(r.read())
        print(f"✅ Health check passed: {health['status']}\n{'─'*55}")
    except Exception as e:
        print(f"❌ Health check FAILED — is the server running?\n   Error: {e}")
        print(f"\n   Start it with:  uvicorn main:app --reload")
        return

    passed = 0
    for i, tc in enumerate(TEST_CASES, 1):
        print(f"Test {i}: {tc['name']}")
        try:
            result = post_json(f"{BASE_URL}/classify", tc["payload"])
            ok = result.get("category") == tc["expected_category"]
            status = "✅ PASS" if ok else "⚠️  UNEXPECTED"
            print(f"  {status}")
            print(f"  Category  : {result.get('category')}")
            print(f"  Confidence: {result.get('confidence')}")
            print(f"  Reason    : {result.get('reason')}")
            if ok:
                passed += 1
        except Exception as e:
            print(f"  ❌ FAILED — {e}")
        print()

    print(f"{'─'*55}")
    print(f"Results: {passed}/{len(TEST_CASES)} passed\n")
    if passed == len(TEST_CASES):
        print("🎉 All tests passed! Your API is ready.")
        print(f"   Docs: {BASE_URL}/docs")
    else:
        print("⚠️  Some tests returned unexpected categories.")
        print("   This may be fine — check the reasons above.")

if __name__ == "__main__":
    run_tests()