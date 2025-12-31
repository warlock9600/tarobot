import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from .config import Settings

logger = logging.getLogger(__name__)


Base = declarative_base()
db_settings = Settings.load(require_bot_token=False)
engine = create_async_engine(
    db_settings.database_url, echo=db_settings.debug, future=True
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db() -> None:
    logger.info("Ensuring database schema is up to date")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema ensured")
