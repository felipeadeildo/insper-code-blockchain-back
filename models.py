from datetime import datetime
from typing import List, Optional
from enum import Enum

from sqlmodel import Field, SQLModel


class CategoryEnum(str, Enum):
    market = "market"
    technology = "technology"
    event = "event"
    regulation = "regulation"
    innovation = "innovation"
    analysis = "analysis"


class StatusEnum(str, Enum):
    published = "published"
    draft = "draft"


class User(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    name: str
    email: str = Field(unique=True, index=True)
    password_hash: str
    role: Optional[str] = "user"


class Article(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    title: str
    content: str
    excerpt: str
    category: CategoryEnum
    author: str
    published_at: datetime = Field(default_factory=datetime.now)
    read_time: str
    image_url: Optional[str] = None
    tags: str  # JSON string of tags array
    status: StatusEnum = StatusEnum.published


# Request/Response models
class LoginCredentials(SQLModel):
    email: str
    password: str


class AuthResponse(SQLModel):
    token: str
    user: dict


class CreateArticleData(SQLModel):
    title: str
    content: str
    excerpt: str
    category: CategoryEnum
    tags: List[str]
    image_url: Optional[str] = None
    status: Optional[StatusEnum] = StatusEnum.published


class UpdateArticleData(SQLModel):
    title: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    category: Optional[CategoryEnum] = None
    tags: Optional[List[str]] = None
    image_url: Optional[str] = None
    status: Optional[StatusEnum] = None


class ArticlesResponse(SQLModel):
    articles: List[dict]
    total: int
    has_more: bool
