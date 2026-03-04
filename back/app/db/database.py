import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

Base = declarative_base()

user = os.getenv("MYSQL_USER", "my_app_user")
password = os.getenv("MYSQL_PASSWORD", "my_app_password")
host = os.getenv("MYSQL_HOST", "db")
port = os.getenv("MYSQL_PORT", "3306")
db = os.getenv("MYSQL_DATABASE", "my_app_db")
root_password = os.getenv("MYSQL_ROOT_PASSWORD", "root_password")

DATABASE_URL = os.getenv(
    "DATABASE_URL", f"mysql+aiomysql://{user}:{password}@{host}:{port}/{db}"
)

engine = create_async_engine(DATABASE_URL, echo=True)

async_session = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_session():
    async with async_session() as session:
        yield session


async def init_db():
    from sqlalchemy import text

    root_url = f"mysql+aiomysql://root:{root_password}@{host}:{port}"
    root_engine = create_async_engine(root_url, echo=True, isolation_level="AUTOCOMMIT")

    async with root_engine.connect() as conn:
        await conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{db}`"))
        await conn.execute(
            text(f"CREATE USER IF NOT EXISTS '{user}'@'%' IDENTIFIED BY '{password}'")
        )
        await conn.execute(text(f"GRANT ALL PRIVILEGES ON `{db}`.* TO '{user}'@'%'"))

    await root_engine.dispose()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
