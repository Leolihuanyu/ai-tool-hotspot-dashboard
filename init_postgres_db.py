"""初始化 PostgreSQL 数据库

读取 schema.sql 并在 Supabase PostgreSQL 中创建所有表。
"""

import os
import sys
from pathlib import Path

# 设置 PostgreSQL 连接
os.environ['DB_TYPE'] = 'postgresql'
os.environ['DATABASE_URL'] = 'postgresql://postgres.pdezvkbhbynfgqtwaqaw:NG86DDhGUIehlLZ8@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres'

from src.database.connection import execute_script, get_connection


def init_database():
    """初始化数据库表结构"""
    print("=" * 60)
    print("PostgreSQL 数据库初始化")
    print("=" * 60)

    # 读取 schema.sql
    schema_path = Path(__file__).parent / 'src' / 'database' / 'schema.sql'

    if not schema_path.exists():
        print(f"❌ 错误: schema.sql 文件不存在")
        print(f"   路径: {schema_path}")
        return False

    print(f"\n✓ 找到 schema.sql: {schema_path}")

    # 读取 SQL 脚本
    with open(schema_path, 'r', encoding='utf-8') as f:
        sql_script = f.read()

    print(f"✓ 读取完成，共 {len(sql_script)} 字符")

    # 执行 SQL 脚本
    try:
        print("\n开始执行 SQL 脚本...")

        # 直接使用连接执行整个脚本（避免语句分割问题）
        conn = get_connection()
        cursor = conn.cursor()

        # 执行整个SQL脚本
        cursor.execute(sql_script)
        conn.commit()

        cursor.close()
        conn.close()

        print("✓ SQL 脚本执行成功")

        # 验证表创建
        print("\n验证表创建...")
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)

        tables = cursor.fetchall()

        if tables:
            print(f"\n✓ 成功创建 {len(tables)} 个表:")
            for table in tables:
                table_name = table['table_name'] if isinstance(table, dict) else table[0]
                print(f"  - {table_name}")
        else:
            print("\n⚠️  警告: 未检测到任何表")

        cursor.close()
        conn.close()

        print("\n" + "=" * 60)
        print("✅ 数据库初始化完成！")
        print("=" * 60)
        return True

    except Exception as e:
        import traceback
        print(f"\n❌ 初始化失败: {e}")
        print("\n详细错误信息:")
        traceback.print_exc()
        print("\n" + "=" * 60)
        return False


if __name__ == '__main__':
    success = init_database()
    sys.exit(0 if success else 1)
