from app.core.config import get_settings
from app.core.dependencies import (
    RequireAdmin,
    RequireTeacher,
    get_current_user,
    get_current_user_id,
)
from app.schemas.ai import (
    FlashcardRequest,
    QuizRequest,
    StudyAssistantRequest,
    StudyPlanRequest,
)
from app.schemas.announcement import AnnouncementCreate
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.common import PaginatedResponse
from app.schemas.discussion import DiscussionCommentCreate, DiscussionCreate
from app.schemas.group import GroupCreate, GroupInvite
from app.schemas.message import ConversationCreate, MessageCreate
from app.schemas.post import CommentCreate, PostCreate, PostUpdate, ReportPostRequest
from app.schemas.resource import ResourceCreate, ResourceRating
from app.schemas.user import (
    NotificationSettings,
    PasswordChangeRequest,
    UserProfileUpdate,
)
from app.services.analytics_service import AnalyticsService
from app.services.announcement_service import AnnouncementService
from app.services.auth_service import AuthService
from app.services.discussion_service import DiscussionService
from app.services.group_service import GroupService
from app.services.message_service import MessageService
from app.services.notification_service import NotificationService
from app.services.post_service import PostService
from app.services.resource_service import ResourceService
from app.services.search_service import SearchService
from app.services.user_service import UserService
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.security import OAuth2PasswordRequestForm

# AI modules are lazily imported inside endpoints to avoid heavy deps at startup

router = APIRouter()


def _paginated(items, total, page, page_size):
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=page * page_size < total,
    )


# Auth
@router.post("/auth/register", response_model=TokenResponse)
async def register(data: RegisterRequest):
    try:
        return await AuthService().register(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable. Please ensure MongoDB is running and try again.",
        )


@router.post("/auth/login", response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends()):
    from app.schemas.auth import LoginRequest

    try:
        return await AuthService().login(
            LoginRequest(identifier=form.username, password=form.password)
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable. Please ensure MongoDB is running and try again.",
        )


@router.post("/auth/login/json", response_model=TokenResponse)
async def login_json(data: LoginRequest):
    try:
        return await AuthService().login(data)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable. Please ensure MongoDB is running and try again.",
        )


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest):
    try:
        return await AuthService().refresh(data.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable. Please ensure MongoDB is running and try again.",
        )


# Users
@router.get("/users/me")
async def get_me(user: dict = Depends(get_current_user)):
    return await UserService().to_public(user)


@router.get("/users/{user_id}")
async def get_user(user_id: str, current_id: str = Depends(get_current_user_id)):
    from app.repositories.user_repo import UserRepository

    u = await UserRepository().find_by_id(user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return await UserService().to_public(u, current_id)


@router.patch("/users/me")
async def update_me(data: UserProfileUpdate, user: dict = Depends(get_current_user)):
    return await UserService().update_profile(user["id"], data)


@router.post("/users/{user_id}/follow")
async def follow_user(user_id: str, current: dict = Depends(get_current_user)):
    try:
        await UserService().follow(current["id"], user_id)
        await NotificationService().notify_follow(user_id, current["id"])
        return {"message": "Followed"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/users/{user_id}/follow")
async def unfollow_user(user_id: str, current: dict = Depends(get_current_user)):
    await UserService().unfollow(current["id"], user_id)
    return {"message": "Unfollowed"}


@router.get("/users/me/analytics")
async def profile_analytics(user: dict = Depends(get_current_user)):
    return await UserService().get_analytics(user["id"])


@router.post("/users/me/password")
async def change_password(
    data: PasswordChangeRequest, user: dict = Depends(get_current_user)
):
    try:
        await UserService().change_password(
            user["id"], data.current_password, data.new_password
        )
        return {"message": "Password changed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/users/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...), user: dict = Depends(get_current_user)
):
    import os
    import uuid

    from app.repositories.user_repo import UserRepository

    settings_obj = get_settings()
    os.makedirs(settings_obj.UPLOAD_DIR, exist_ok=True)
    ext = (file.filename or "jpg").rsplit(".", 1)[-1]
    filename = f"avatar_{user['id']}_{uuid.uuid4().hex[:8]}.{ext}"
    path = os.path.join(settings_obj.UPLOAD_DIR, filename)
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)
    url = f"/uploads/{filename}"
    await UserRepository().update_profile(user["id"], {"profile_picture": url})
    return {"profile_picture": url}


@router.get("/users/me/notification-settings")
async def get_notification_settings(user: dict = Depends(get_current_user)):
    return await UserService().get_notification_settings(user["id"])


@router.patch("/users/me/notification-settings")
async def update_notification_settings(
    data: NotificationSettings, user: dict = Depends(get_current_user)
):
    return await UserService().update_notification_settings(
        user["id"], data.model_dump()
    )


# Posts
@router.get("/posts/feed")
async def feed(
    page: int = 1,
    page_size: int = 20,
    department: str | None = None,
    user_id: str = Depends(get_current_user_id),
):
    items, total = await PostService().get_feed(page, page_size, user_id, department)
    return _paginated(items, total, page, page_size)


@router.post("/posts")
async def create_post(data: PostCreate, user: dict = Depends(get_current_user)):
    try:
        return await PostService().create(user["id"], data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/posts/{post_id}")
async def update_post(
    post_id: str, data: PostUpdate, user: dict = Depends(get_current_user)
):
    try:
        return await PostService().update(post_id, user["id"], data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/posts/{post_id}", status_code=204)
async def delete_post(post_id: str, user: dict = Depends(get_current_user)):
    try:
        await PostService().delete(post_id, user["id"])
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/posts/{post_id}/like")
async def like_post(post_id: str, user: dict = Depends(get_current_user)):
    return await PostService().like(post_id, user["id"])


@router.post("/posts/{post_id}/comments")
async def comment_post(
    post_id: str, data: CommentCreate, user: dict = Depends(get_current_user)
):
    return await PostService().comment(post_id, user["id"], data)


@router.post("/posts/{post_id}/bookmark")
async def bookmark_post(post_id: str, user: dict = Depends(get_current_user)):
    bookmarked = await PostService().bookmark(post_id, user["id"])
    return {"bookmarked": bookmarked}


@router.post("/posts/{post_id}/share")
async def share_post(post_id: str, user: dict = Depends(get_current_user)):
    await PostService().share(post_id, user["id"])
    return {"message": "Shared"}


@router.post("/posts/{post_id}/report")
async def report_post(
    post_id: str, data: ReportPostRequest, user: dict = Depends(get_current_user)
):
    await PostService().report(post_id, user["id"], data.reason)
    return {"message": "Reported"}


# Resources
@router.get("/resources")
async def list_resources(
    page: int = 1, page_size: int = 20, user_id: str = Depends(get_current_user_id)
):
    items, total = await ResourceService().list_resources(page, page_size, user_id)
    return _paginated(items, total, page, page_size)


@router.post("/resources")
async def upload_resource(
    title: str,
    description: str = "",
    course: str = "",
    department: str = "",
    tags: str = "",
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    content = await file.read()
    data = ResourceCreate(
        title=title,
        description=description,
        course=course,
        department=department,
        tags=tag_list,
    )
    return await ResourceService().upload(
        user["id"], data, content, file.filename or "file", file.content_type or ""
    )


@router.get("/resources/{resource_id}")
async def get_resource(resource_id: str, user_id: str = Depends(get_current_user_id)):
    try:
        return await ResourceService().get(resource_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/resources/{resource_id}/download")
async def download_resource(resource_id: str, user: dict = Depends(get_current_user)):
    try:
        return await ResourceService().download(resource_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/resources/{resource_id}/rate")
async def rate_resource(
    resource_id: str, data: ResourceRating, user: dict = Depends(get_current_user)
):
    await ResourceService().rate(resource_id, user["id"], data.rating, data.review)
    return {"message": "Rated"}


@router.post("/resources/{resource_id}/bookmark")
async def bookmark_resource(resource_id: str, user: dict = Depends(get_current_user)):
    bookmarked = await ResourceService().bookmark(resource_id, user["id"])
    return {"bookmarked": bookmarked}


# Discussions
@router.get("/discussions")
async def list_discussions(
    page: int = 1, page_size: int = 20, user_id: str = Depends(get_current_user_id)
):
    items, total = await DiscussionService().list_discussions(page, page_size, user_id)
    return _paginated(items, total, page, page_size)


@router.get("/discussions/trending")
async def trending_discussions(user_id: str = Depends(get_current_user_id)):
    return await DiscussionService().get_trending(user_id)


@router.post("/discussions")
async def create_discussion(
    data: DiscussionCreate, user: dict = Depends(get_current_user)
):
    return await DiscussionService().create(user["id"], data)


@router.get("/discussions/{discussion_id}")
async def get_discussion(
    discussion_id: str, user_id: str = Depends(get_current_user_id)
):
    try:
        return await DiscussionService().get(discussion_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/discussions/{discussion_id}/like")
async def like_discussion(discussion_id: str, user: dict = Depends(get_current_user)):
    return await DiscussionService().like(discussion_id, user["id"])


@router.post("/discussions/{discussion_id}/comments")
async def comment_discussion(
    discussion_id: str,
    data: DiscussionCommentCreate,
    user: dict = Depends(get_current_user),
):
    await DiscussionService().add_comment(discussion_id, user["id"], data.content)
    return {"message": "Comment added"}


@router.post("/discussions/{discussion_id}/pin")
async def pin_discussion(
    discussion_id: str, pinned: bool = True, user: dict = Depends(RequireTeacher)
):
    await DiscussionService().pin(discussion_id, pinned)
    return {"message": "Discussion pinned" if pinned else "Discussion unpinned"}


@router.delete("/discussions/{discussion_id}")
async def delete_discussion(discussion_id: str, user: dict = Depends(get_current_user)):
    try:
        await DiscussionService().delete(discussion_id, user["id"], user.get("role"))
        return {"message": "Discussion deleted"}
    except ValueError as e:
        raise HTTPException(
            status_code=404 if str(e) == "Discussion not found" else 403, detail=str(e)
        )


# Announcements
@router.get("/announcements")
async def list_announcements(page: int = 1, page_size: int = 20):
    items, total = await AnnouncementService().list_active(page, page_size)
    return _paginated(items, total, page, page_size)


@router.post("/announcements")
async def create_announcement(
    data: AnnouncementCreate, user: dict = Depends(RequireTeacher)
):
    return await AnnouncementService().create(user["id"], data)


# Groups
@router.get("/groups")
async def list_groups(
    page: int = 1, page_size: int = 20, user_id: str = Depends(get_current_user_id)
):
    items, total = await GroupService().list_groups(page, page_size, user_id)
    return _paginated(items, total, page, page_size)


@router.post("/groups")
async def create_group(data: GroupCreate, user: dict = Depends(get_current_user)):
    return await GroupService().create(user["id"], data)


@router.post("/groups/{group_id}/join")
async def join_group(group_id: str, user: dict = Depends(get_current_user)):
    await GroupService().join(group_id, user["id"])
    return {"message": "Joined"}


@router.post("/groups/{group_id}/leave")
async def leave_group(group_id: str, user: dict = Depends(get_current_user)):
    await GroupService().leave(group_id, user["id"])
    return {"message": "Left"}


@router.post("/groups/{group_id}/invite")
async def invite_to_group(
    group_id: str, data: GroupInvite, user: dict = Depends(get_current_user)
):
    await GroupService().invite(group_id, data.user_ids)
    return {"message": "Invited"}


# Messages
@router.get("/conversations")
async def get_conversations(user: dict = Depends(get_current_user)):
    return await MessageService().get_conversations(user["id"])


@router.post("/conversations")
async def create_conversation(
    data: ConversationCreate, user: dict = Depends(get_current_user)
):
    return await MessageService().create_conversation(user["id"], data)


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: str, page: int = 1, user: dict = Depends(get_current_user)
):
    items, total = await MessageService().get_messages(
        conversation_id, user["id"], page
    )
    return _paginated(items, total, page, 50)


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: str, data: MessageCreate, user: dict = Depends(get_current_user)
):
    return await MessageService().send_message(conversation_id, user["id"], data)


# Notifications
@router.get("/notifications")
async def get_notifications(
    page: int = 1, page_size: int = 20, user: dict = Depends(get_current_user)
):
    from app.repositories.notification_repo import NotificationRepository

    items, total = await NotificationRepository().get_user_notifications(
        user["id"], page, page_size
    )
    return _paginated(items, total, page, page_size)


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str, user: dict = Depends(get_current_user)
):
    from app.repositories.notification_repo import NotificationRepository

    await NotificationRepository().mark_read(notification_id, user["id"])
    return {"message": "Marked read"}


@router.post("/notifications/read-all")
async def mark_all_read(user: dict = Depends(get_current_user)):
    from app.repositories.notification_repo import NotificationRepository

    await NotificationRepository().mark_all_read(user["id"])
    return {"message": "All marked read"}


# Search
@router.get("/search")
async def search(
    q: str = Query(min_length=1),
    type: str | None = None,
    user: dict = Depends(get_current_user),
):
    return await SearchService().global_search(q, type)


# AI
@router.post("/ai/chat")
async def ai_chat(data: StudyAssistantRequest, user: dict = Depends(get_current_user)):
    try:
        from app.ai.study_assistant import study_assistant

        return await study_assistant.chat(data.message, user, data.resource_ids)
    except Exception:
        raise HTTPException(status_code=503, detail="AI service unavailable")


@router.post("/ai/quiz")
async def ai_quiz(data: QuizRequest, user: dict = Depends(get_current_user)):
    try:
        from app.ai.study_assistant import study_assistant

        return await study_assistant.generate_quiz(data)
    except Exception:
        raise HTTPException(status_code=503, detail="AI service unavailable")


@router.post("/ai/flashcards")
async def ai_flashcards(data: FlashcardRequest, user: dict = Depends(get_current_user)):
    try:
        from app.ai.study_assistant import study_assistant

        return await study_assistant.generate_flashcards(data)
    except Exception:
        raise HTTPException(status_code=503, detail="AI service unavailable")


@router.post("/ai/study-plan")
async def ai_study_plan(data: StudyPlanRequest, user: dict = Depends(get_current_user)):
    try:
        from app.ai.study_assistant import study_assistant

        return await study_assistant.generate_study_plan(data)
    except Exception:
        raise HTTPException(status_code=503, detail="AI service unavailable")


@router.post("/ai/moderate")
async def ai_moderate(content: str, user: dict = Depends(get_current_user)):
    try:
        from app.ai.moderation_service import moderation_service

        return await moderation_service.moderate(content)
    except Exception:
        raise HTTPException(status_code=503, detail="AI moderation unavailable")


@router.get("/ai/recommendations")
async def ai_recommendations(user: dict = Depends(get_current_user)):
    try:
        from app.ai.recommendation_service import recommendation_service

        return {
            "resources": await recommendation_service.recommend_resources(user),
            "discussions": await recommendation_service.recommend_discussions(user),
            "groups": await recommendation_service.recommend_groups(user),
            "friends": await recommendation_service.recommend_friends(user),
        }
    except Exception:
        raise HTTPException(status_code=503, detail="AI recommendations unavailable")


# Admin
@router.get("/admin/analytics")
async def admin_analytics(user: dict = Depends(RequireAdmin)):
    return await AnalyticsService().get_dashboard_stats()


@router.get("/admin/users")
async def admin_users(
    page: int = 1, page_size: int = 20, user: dict = Depends(RequireAdmin)
):
    items, total = await AnalyticsService().get_admin_users(page, page_size)
    return _paginated(items, total, page, page_size)
