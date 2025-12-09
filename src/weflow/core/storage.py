from abc import ABC, abstractmethod
from typing import Optional
from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import exists
import os
from datetime import datetime
from .models import Article

Base = declarative_base()

class ArticleModel(Base):
    __tablename__ = 'articles'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    url = Column(String, unique=True)
    published_date = Column(DateTime, nullable=True)
    content = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)
    media_id = Column(String, nullable=True)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class StorageProvider(ABC):
    @abstractmethod
    def save_article(self, article: Article):
        pass

    @abstractmethod
    def article_exists(self, url: str) -> bool:
        pass

class PostgresStorage(StorageProvider):
    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or os.getenv("DATABASE_URL")
        if not self.db_url:
            raise ValueError("Database URL is required")
        self.engine = create_engine(self.db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def save_article(self, article: Article):
        session = self.Session()
        try:
            db_article = session.query(ArticleModel).filter_by(url=article.url).first()
            if db_article:
                # Update existing
                db_article.title = article.title
                db_article.content = article.content
                db_article.summary = article.summary
                db_article.image_url = article.image_url
                db_article.media_id = article.media_id
                db_article.status = article.status
                # published_date usually doesn't change, but can update if needed
            else:
                # Create new
                db_article = ArticleModel(
                    title=article.title,
                    url=article.url,
                    published_date=article.published_date,
                    content=article.content,
                    summary=article.summary,
                    image_url=article.image_url,
                    media_id=article.media_id,
                    status=article.status
                )
                session.add(db_article)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def article_exists(self, url: str) -> bool:
        session = self.Session()
        try:
            return session.query(exists().where(ArticleModel.url == url)).scalar()
        finally:
            session.close()
