from datetime import datetime, timedelta

from app.database.mongodb import get_database


class AnalyticsService:
    async def get_dashboard_stats(self) -> dict:
        db = get_database()
        week_ago = datetime.utcnow() - timedelta(days=7)

        active_users = await db.users.count_documents({"updated_at": {"$gte": week_ago}})
        resources = await db.resources.count_documents({})
        discussions = await db.discussions.count_documents({})
        total_downloads = 0
        async for r in db.resources.find({}, {"downloads": 1}):
            total_downloads += r.get("downloads", 0)

        ai_requests = await db.ai_logs.count_documents({}) if "ai_logs" in await db.list_collection_names() else 0

        # Popular topics via aggregation
        pipeline = [
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10},
        ]
        topics = []
        async for doc in db.posts.aggregate(pipeline):
            topics.append({"topic": doc["_id"], "count": doc["count"]})

        return {
            "active_users": active_users,
            "resources_uploaded": resources,
            "discussions_created": discussions,
            "total_downloads": total_downloads,
            "ai_requests": ai_requests,
            "popular_topics": topics,
            "engagement_rate": round(min(discussions * 3 + resources * 2, 100), 2),
        }

    async def get_admin_users(self, page: int = 1, page_size: int = 20) -> tuple[list, int]:
        db = get_database()
        skip = (page - 1) * page_size
        total = await db.users.count_documents({})
        cursor = db.users.find({}, {"hashed_password": 0}).skip(skip).limit(page_size)
        docs = await cursor.to_list(page_size)
        users = [{"id": str(d.pop("_id")), **d} for d in docs]
        return users, total
