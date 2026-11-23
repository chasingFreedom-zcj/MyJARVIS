
import asyncio

from sqlalchemy import text
from app.db.session import engine


async def test_connection():
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("数据库连接成功！")
            print("测试查询结果：", result.scalar())
    except Exception as e:
        print("数据库连接失败：", repr(e))
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_connection())
