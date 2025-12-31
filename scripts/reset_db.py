"""Drop and recreate all database tables for debug purposes."""

import asyncio

from app import models  # noqa: F401 - ensure models are registered
from app.db import Base, engine


async def reset_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("Database schema has been dropped and recreated.")


if __name__ == "__main__":
    asyncio.run(reset_db())
