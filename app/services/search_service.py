from app.repositories.discussion_repo import DiscussionRepository
from app.repositories.group_repo import GroupRepository
from app.repositories.resource_repo import ResourceRepository
from app.repositories.user_repo import UserRepository
from app.schemas.search import SearchResult


class SearchService:
    def __init__(self) -> None:
        self.user_repo = UserRepository()
        self.resource_repo = ResourceRepository()
        self.discussion_repo = DiscussionRepository()
        self.group_repo = GroupRepository()

    async def global_search(self, query: str, search_type: str | None = None, limit: int = 20) -> list[SearchResult]:
        results: list[SearchResult] = []

        if not search_type or search_type == "people":
            users = await self.user_repo.search_users(query, limit=5)
            for u in users:
                results.append(SearchResult(
                    id=u["id"], type="people",
                    title=f"{u['first_name']} {u['last_name']}",
                    snippet=u.get("bio", "")[:100],
                    metadata={"username": u["username"], "department": u.get("department", "")},
                ))

        if not search_type or search_type == "resources":
            resources = await self.resource_repo.search(query, limit=5)
            for r in resources:
                results.append(SearchResult(
                    id=r["id"], type="resources", title=r["title"],
                    snippet=r.get("description", "")[:100],
                    metadata={"course": r.get("course", ""), "department": r.get("department", "")},
                ))

        if not search_type or search_type == "discussions":
            regex = {"$regex": query, "$options": "i"}
            cursor = self.discussion_repo.collection.find(
                {"$or": [{"title": regex}, {"content": regex}, {"tags": regex}]}, limit=5
            )
            docs = await cursor.to_list(5)
            for d in docs:
                s = self.discussion_repo.serialize(d)
                results.append(SearchResult(
                    id=s["id"], type="discussions", title=s["title"],
                    snippet=s.get("content", "")[:100],
                ))

        if not search_type or search_type == "groups":
            groups = await self.group_repo.search(query, limit=5)
            for g in groups:
                results.append(SearchResult(
                    id=g["id"], type="groups", title=g["name"],
                    snippet=g.get("description", "")[:100],
                ))

        return results[:limit]
