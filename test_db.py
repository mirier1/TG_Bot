import asyncio
from sqlalchemy import text
from database import AsyncSessionLocal

async def test_connection():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT 1"))
        print("✅ База данных работает:", result.scalar())

asyncio.run(test_connection())