from sqlalchemy import URL, create_engine # type: ignore
from sqlalchemy.orm import DeclarativeBase, sessionmaker # type: ignore

from app.core.config import settings


DATABASE_URL = (
    settings.DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
    if settings.DATABASE_URL
    else URL.create(
    drivername="mysql+pymysql",
    username=settings.MYSQL_USER,
    password=settings.MYSQL_PASSWORD,
    host=settings.MYSQL_HOST,
    port=settings.MYSQL_PORT,
    database=settings.MYSQL_DATABASE,
    )
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()