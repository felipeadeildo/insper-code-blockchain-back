import json
import uuid

from sqlmodel import Session, SQLModel, create_engine

from models import Article, User, CategoryEnum, StatusEnum

DATABASE_URL = "sqlite:///./blockchain.db"
engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


def create_default_user():
    with Session(engine) as session:
        existing_user = (
            session.query(User).filter(User.email == "admin@example.com").first()
        )
        if not existing_user:
            from auth import hash_password

            admin_user = User(
                id=str(uuid.uuid4()),
                name="Admin",
                email="admin@example.com",
                password_hash=hash_password("admin123"),
                role="admin",
            )
            session.add(admin_user)
            session.commit()


def create_sample_articles():
    with Session(engine) as session:
        existing_articles = session.query(Article).first()
        if not existing_articles:
            sample_articles = [
                Article(
                    id=str(uuid.uuid4()),
                    title="Bitcoin atinge nova máxima histórica",
                    content="Bitcoin reached a new all-time high today...",
                    excerpt="Cryptocurrency market shows strong momentum",
                    category=CategoryEnum.market,
                    author="Admin",
                    read_time="5 min",
                    tags=json.dumps(["bitcoin", "crypto", "market"]),
                    status=StatusEnum.published,
                ),
                Article(
                    id=str(uuid.uuid4()),
                    title="Nova regulamentação DeFi no Brasil",
                    content="Brazilian government announces new DeFi regulations...",
                    excerpt="New regulatory framework for decentralized finance",
                    category=CategoryEnum.regulation,
                    author="Admin",
                    read_time="8 min",
                    tags=json.dumps(["defi", "regulation", "brazil"]),
                    status=StatusEnum.published,
                ),
            ]
            for article in sample_articles:
                session.add(article)
            session.commit()
