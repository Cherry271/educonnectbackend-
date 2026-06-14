"""
Minimal startup test — verifies all critical systems before the server starts.
Run with:  venv/Scripts/python start.py
"""

import asyncio
import sys


async def verify():
    errors = []

    # 1. Settings
    try:
        from app.core.config import get_settings

        s = get_settings()
        print(f"✅ Settings loaded (DB={s.MONGODB_DB})")
    except Exception as e:
        errors.append(f"❌ Settings: {e}")
        print(errors[-1])

    # 2. MongoDB
    try:
        import motor.motor_asyncio
        from app.core.config import get_settings

        s = get_settings()
        client = motor.motor_asyncio.AsyncIOMotorClient(
            s.MONGODB_URI, serverSelectionTimeoutMS=10000
        )
        await client.admin.command("ping")
        db = client[s.MONGODB_DB]
        count = await db.users.count_documents({})
        print(f"✅ MongoDB connected ({count} users in DB)")
    except Exception as e:
        errors.append(f"❌ MongoDB: {e}")
        print(errors[-1])

    # 3. Password hashing
    try:
        from app.core.security import hash_password, verify_password

        h = hash_password("TestPassword123!")
        assert verify_password("TestPassword123!", h)
        print("✅ Password hashing works")
    except Exception as e:
        errors.append(f"❌ Security: {e}")
        print(errors[-1])

    # 4. JWT tokens
    try:
        from app.core.security import create_access_token, verify_token

        tok = create_access_token("test-user-id", "student")
        payload = verify_token(tok)
        assert payload and payload.get("sub") == "test-user-id"
        print("✅ JWT token creation/verification works")
    except Exception as e:
        errors.append(f"❌ JWT: {e}")
        print(errors[-1])

    print()
    if errors:
        print(f"⚠️  {len(errors)} issue(s) found. Fix them before starting the server.")
        sys.exit(1)
    else:
        print("✅ All systems OK — starting server...")
        import subprocess

        subprocess.run(
            [
                sys.executable.replace("python.exe", "uvicorn.exe"),
                "app.main:socket_app",
                "--host",
                "0.0.0.0",
                "--port",
                "8000",
                "--reload",
            ]
        )


asyncio.run(verify())
