import asyncio

from app.db.base import Base
from app.db.session import engine


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("数据库表初始化已完成！")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_db())
