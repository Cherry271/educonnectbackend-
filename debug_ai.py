"""Debug the live AI endpoint — non-interactive."""

import json
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000/api/v1"


def req(method, path, body=None, token=None):
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(
        f"{BASE}{path}", data=data, headers=headers, method=method
    )
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())
    except Exception as e:
        return 0, {"error": str(e)}


# 1. Register a fresh debug account
rand = int(time.time())
email = f"debugai{rand}@test.com"
password = "DebugAI1234!"
print(f"Registering test account: {email}")
status, data = req(
    "POST",
    "/auth/register",
    {
        "first_name": "Debug",
        "last_name": "AI",
        "username": f"debugai{rand}",
        "email": email,
        "password": password,
        "role": "student",
    },
)
if status != 200:
    print(f"Register failed [{status}]: {data}")
    exit(1)
token = data["access_token"]
print(f"✅ Registered OK, token: {token[:20]}...")

# 2. Call /ai/chat
print()
print("Calling POST /api/v1/ai/chat ...")
status, data = req(
    "POST",
    "/ai/chat",
    {"message": "What is 2 plus 2? Answer in one word.", "resource_ids": []},
    token,
)
print(f"HTTP {status}")
if status == 200:
    print(f"✅ AI response: {data.get('response', '')[:200]}")
    print(f"   Model: {data.get('model_used')}")
    print(f"   Tokens: {data.get('tokens_used')}")
else:
    print(f"❌ Error body: {json.dumps(data, indent=2)}")

# 3. Also test quiz endpoint
print()
print("Calling POST /api/v1/ai/quiz ...")
status, data = req(
    "POST",
    "/ai/quiz",
    {"topic": "Mathematics", "num_questions": 2, "difficulty": "easy"},
    token,
)
print(f"HTTP {status}")
if status == 200:
    print(f"✅ Quiz response: {str(data.get('response', ''))[:200]}")
else:
    print(f"❌ Error: {data}")
