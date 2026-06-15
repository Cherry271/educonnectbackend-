from enum import Enum


class UserRole(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    PARENT = "parent"
    ADMIN = "admin"


class PostType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    PDF = "pdf"
    DOCUMENT = "document"
    VIDEO = "video"
    LINK = "link"
    RESOURCE = "resource"


class GroupType(str, Enum):
    COURSE = "course"
    DEPARTMENT = "department"
    PROJECT = "project"
    STUDY = "study"


class PostType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    PDF = "pdf"
    DOCUMENT = "document"
    VIDEO = "video"
    LINK = "link"
    RESOURCE = "resource"
    POLL = "poll"


class AnnouncementType(str, Enum):
    ANNOUNCEMENT = "announcement"
    EVENT = "event"
    DEADLINE = "deadline"
    EXAM = "exam"
    CLASS_UPDATE = "class_update"


class PriorityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class NotificationType(str, Enum):
    LIKE = "like"
    COMMENT = "comment"
    MENTION = "mention"
    MESSAGE = "message"
    ANNOUNCEMENT = "announcement"
    RESOURCE = "resource"
    FOLLOW = "follow"
    GROUP = "group"
