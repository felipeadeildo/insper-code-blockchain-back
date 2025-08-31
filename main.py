import json
import uuid
from datetime import timedelta
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, col, select

from auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    create_access_token,
    get_current_user,
)
from database import (
    create_db_and_tables,
    create_default_user,
    create_sample_articles,
    get_session,
)
from models import (
    Article,
    ArticlesResponse,
    AuthResponse,
    CreateArticleData,
    LoginCredentials,
    StatusEnum,
    UpdateArticleData,
    User,
)

app = FastAPI(title="Insper Code Blockchain News API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    create_default_user()
    create_sample_articles()


@app.post("/auth/login", response_model=AuthResponse)
def login(credentials: LoginCredentials, session: Session = Depends(get_session)):
    user = authenticate_user(session, credentials.email, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    return AuthResponse(
        token=access_token,
        user={"id": user.id, "name": user.name, "email": user.email, "role": user.role},
    )


@app.get("/auth/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
    }


@app.get("/news", response_model=ArticlesResponse)
def get_articles(
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(10),
    offset: int = Query(0),
    session: Session = Depends(get_session),
):
    query = select(Article)

    if category:
        query = query.where(Article.category == category)
    if status:
        query = query.where(Article.status == status)
    if search:
        query = query.where(
            col(Article.title).contains(search) | col(Article.content).contains(search)
        )

    total_query = query
    total = len(session.exec(total_query).all())

    articles = session.exec(query.offset(offset).limit(limit)).all()

    article_dicts = []
    for article in articles:
        article_dict = {
            "id": article.id,
            "title": article.title,
            "content": article.content,
            "excerpt": article.excerpt,
            "category": article.category,
            "author": article.author,
            "publishedAt": article.published_at.isoformat(),
            "readTime": article.read_time,
            "imageUrl": article.image_url,
            "tags": json.loads(article.tags),
            "status": article.status,
        }
        article_dicts.append(article_dict)

    has_more = (offset + limit) < total

    return ArticlesResponse(articles=article_dicts, total=total, has_more=has_more)


@app.get("/news/{article_id}")
def get_article(article_id: str, session: Session = Depends(get_session)):
    article = session.exec(select(Article).where(Article.id == article_id)).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    return {
        "id": article.id,
        "title": article.title,
        "content": article.content,
        "excerpt": article.excerpt,
        "category": article.category,
        "author": article.author,
        "publishedAt": article.published_at.isoformat(),
        "readTime": article.read_time,
        "imageUrl": article.image_url,
        "tags": json.loads(article.tags),
        "status": article.status,
    }


@app.post("/news")
def create_article(
    data: CreateArticleData,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    article = Article(
        id=str(uuid.uuid4()),
        title=data.title,
        content=data.content,
        excerpt=data.excerpt,
        category=data.category,
        author=current_user.name,
        read_time=f"{len(data.content.split()) // 200 + 1} min",
        image_url=data.image_url,
        tags=json.dumps(data.tags),
        status=data.status or StatusEnum.published,
    )
    session.add(article)
    session.commit()
    session.refresh(article)

    return {
        "id": article.id,
        "title": article.title,
        "content": article.content,
        "excerpt": article.excerpt,
        "category": article.category,
        "author": article.author,
        "publishedAt": article.published_at.isoformat(),
        "readTime": article.read_time,
        "imageUrl": article.image_url,
        "tags": json.loads(article.tags),
        "status": article.status,
    }


@app.put("/news/{article_id}")
def update_article(
    article_id: str,
    data: UpdateArticleData,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    article = session.exec(select(Article).where(Article.id == article_id)).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    if data.title is not None:
        article.title = data.title
    if data.content is not None:
        article.content = data.content
        article.read_time = f"{len(data.content.split()) // 200 + 1} min"
    if data.excerpt is not None:
        article.excerpt = data.excerpt
    if data.category is not None:
        article.category = data.category
    if data.tags is not None:
        article.tags = json.dumps(data.tags)
    if data.image_url is not None:
        article.image_url = data.image_url
    if data.status is not None:
        article.status = data.status

    session.add(article)
    session.commit()
    session.refresh(article)

    return {
        "id": article.id,
        "title": article.title,
        "content": article.content,
        "excerpt": article.excerpt,
        "category": article.category,
        "author": article.author,
        "publishedAt": article.published_at.isoformat(),
        "readTime": article.read_time,
        "imageUrl": article.image_url,
        "tags": json.loads(article.tags),
        "status": article.status,
    }


@app.delete("/news/{article_id}")
def delete_article(
    article_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    article = session.exec(select(Article).where(Article.id == article_id)).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    session.delete(article)
    session.commit()

    return {"message": "Article deleted successfully"}


def main():
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
