"""
迁移脚本 005: 添加 input_params 字段
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine


async def upgrade():
    async with engine.begin() as conn:
        await conn.execute(text("""
            ALTER TABLE task_instances 
            ADD COLUMN IF NOT EXISTS input_params JSON
        """))
        print("Added input_params column to task_instances")


if __name__ == "__main__":
    asyncio.run(upgrade())
