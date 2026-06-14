import asyncio
from datetime import datetime

from app.core.security import hash_password
from app.database.mongodb import connect_to_mongo, close_mongo_connection, get_database


async def seed():
    await connect_to_mongo()
    db = get_database()

    if await db.users.count_documents({}) > 0:
        print("Database already seeded.")
        await close_mongo_connection()
        return

    users = [
        {
            "first_name": "Admin", "last_name": "User", "username": "admin",
            "email": "admin@educonnect.edu", "hashed_password": hash_password("Admin123!"),
            "role": "admin", "department": "Administration", "faculty": "Management",
            "bio": "Platform administrator", "profile_picture": "", "cover_photo": "",
            "skills": ["Management"], "interests": ["Education"], "followers": [], "following": [],
            "achievements": [], "is_active": True, "is_verified": True,
            "created_at": datetime.utcnow(), "updated_at": datetime.utcnow(),
        },
        {
            "first_name": "Sarah", "last_name": "Johnson", "username": "sarahj",
            "email": "sarah@educonnect.edu", "hashed_password": hash_password("Teacher123!"),
            "role": "teacher", "department": "Computer Science", "faculty": "Engineering",
            "bio": "CS Professor passionate about AI and algorithms", "profile_picture": "", "cover_photo": "",
            "skills": ["Python", "AI", "Algorithms"], "interests": ["Machine Learning", "Teaching"],
            "followers": [], "following": [], "achievements": [{"title": "Top Educator 2025"}],
            "is_active": True, "is_verified": True,
            "created_at": datetime.utcnow(), "updated_at": datetime.utcnow(),
        },
        {
            "first_name": "Alex", "last_name": "Chen", "username": "alexc",
            "email": "alex@educonnect.edu", "hashed_password": hash_password("Student123!"),
            "role": "student", "department": "Computer Science", "faculty": "Engineering",
            "bio": "CS student exploring full-stack development", "profile_picture": "", "cover_photo": "",
            "skills": ["React", "Python"], "interests": ["Web Dev", "Open Source"],
            "followers": [], "following": [], "achievements": [],
            "is_active": True, "is_verified": True,
            "created_at": datetime.utcnow(), "updated_at": datetime.utcnow(),
        },
    ]

    result = await db.users.insert_many(users)
    user_ids = [str(uid) for uid in result.inserted_ids]

    posts = [
        {
            "author_id": user_ids[1], "content": "Welcome to EduConnect! Share your learning journey.",
            "post_type": "text", "media_url": "", "tags": ["welcome", "education"],
            "department": "Computer Science", "likes": [user_ids[2]], "comments": [],
            "shares": [], "bookmarks": [], "reports": [], "is_edited": False,
            "created_at": datetime.utcnow(), "updated_at": datetime.utcnow(),
        },
        {
            "author_id": user_ids[2], "content": "Just finished my first React project! Any tips for state management?",
            "post_type": "text", "media_url": "", "tags": ["react", "webdev"],
            "department": "Computer Science", "likes": [], "comments": [],
            "shares": [], "bookmarks": [], "reports": [], "is_edited": False,
            "created_at": datetime.utcnow(), "updated_at": datetime.utcnow(),
        },
    ]
    await db.posts.insert_many(posts)

    discussions = [
        {
            "author_id": user_ids[2], "title": "Best resources for learning FastAPI?",
            "content": "I'm building a backend project and want to learn FastAPI. What resources do you recommend?",
            "tags": ["fastapi", "python", "backend"], "department": "Computer Science",
            "likes": [user_ids[1]], "comments": [], "is_pinned": True, "trending_score": 10.0,
            "views": 25, "resource_ids": [], "created_at": datetime.utcnow(), "updated_at": datetime.utcnow(),
        },
    ]
    await db.discussions.insert_many(discussions)

    announcements = [
        {
            "author_id": user_ids[1], "title": "Midterm Exam Schedule",
            "content": "CS101 midterm exam will be held on March 15th. Study materials are available in Resources.",
            "announcement_type": "exam", "priority": "high", "department": "Computer Science",
            "scheduled_at": None, "expires_at": None, "is_active": True, "created_at": datetime.utcnow(),
        },
    ]
    await db.announcements.insert_many(announcements)

    groups = [
        {
            "name": "CS Study Group", "description": "Collaborative study for Computer Science students",
            "group_type": "study", "department": "Computer Science", "course": "CS101",
            "creator_id": user_ids[1], "members": [user_ids[1], user_ids[2]],
            "moderators": [user_ids[1]], "invited": [], "cover_image": "", "is_private": False,
            "resource_ids": [], "created_at": datetime.utcnow(),
        },
    ]
    await db.groups.insert_many(groups)

    print("Seed data created successfully!")
    print("  Admin: admin@educonnect.edu / Admin123!")
    print("  Teacher: sarah@educonnect.edu / Teacher123!")
    print("  Student: alex@educonnect.edu / Student123!")
    await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(seed())
