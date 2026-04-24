"""
数据库迁移脚本：004_add_decomposition_fields

添加动态分解任务相关字段到 sub_task_records 表：
- is_decomposition_task (BOOLEAN)
- decomposition_output (TEXT)

执行方式：
    python migrations/004_add_decomposition_fields.py
"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import text
from app.core.database import engine


async def migrate():
    """执行数据库迁移"""
    print("Starting migration: 004_add_decomposition_fields")
    
    async with engine.begin() as conn:
        # 1. 添加 is_decomposition_task 字段
        await conn.execute(text("""
            ALTER TABLE sub_task_records 
            ADD COLUMN IF NOT EXISTS is_decomposition_task BOOLEAN DEFAULT FALSE
        """))
        print("✅ Added column: is_decomposition_task")
        
        # 2. 添加 decomposition_output 字段
        await conn.execute(text("""
            ALTER TABLE sub_task_records 
            ADD COLUMN IF NOT EXISTS decomposition_output TEXT
        """))
        print("✅ Added column: decomposition_output")
        
        # 3. 添加注释（PostgreSQL 支持）
        await conn.execute(text("""
            COMMENT ON COLUMN sub_task_records.is_decomposition_task IS '是否为动态分解任务'
        """))
        await conn.execute(text("""
            COMMENT ON COLUMN sub_task_records.decomposition_output IS '分解任务返回的 JSON'
        """))
        print("✅ Added column comments")
    
    print("✅ Migration completed successfully")


if __name__ == "__main__":
    asyncio.run(migrate())
