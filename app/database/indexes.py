from app.database.mongodb import get_database


async def create_indexes() -> None:
    db = get_database()

    await db.users.create_index("email", unique=True)
    await db.users.create_index("username", unique=True)
    await db.users.create_index("department")
    await db.users.create_index("faculty")
    await db.users.create_index("role")

    await db.posts.create_index([("author_id", 1), ("created_at", -1)])
    await db.posts.create_index("tags")
    await db.posts.create_index("department")
    await db.posts.create_index("created_at")

    await db.discussions.create_index([("created_at", -1)])
    await db.discussions.create_index("tags")
    await db.discussions.create_index("is_pinned")
    await db.discussions.create_index("trending_score")

    await db.resources.create_index([("course", 1), ("department", 1)])
    await db.resources.create_index("tags")
    await db.resources.create_index("uploader_id")
    await db.resources.create_index("created_at")

    await db.announcements.create_index([("priority", -1), ("created_at", -1)])
    await db.announcements.create_index("expires_at")
    await db.announcements.create_index("department")

    await db.groups.create_index("type")
    await db.groups.create_index("department")
    await db.groups.create_index("members")

    await db.notifications.create_index([("user_id", 1), ("created_at", -1)])
    await db.notifications.create_index("is_read")

    await db.messages.create_index([("conversation_id", 1), ("created_at", -1)])
    await db.conversations.create_index("participants")

    await db.embeddings.create_index("resource_id")
    await db.embeddings.create_index("chunk_index")
