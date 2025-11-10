"""测试 PostgreSQL 连接

用于验证 Supabase 数据库连接配置是否正确
"""

import os
import sys

# 设置 PostgreSQL 连接
os.environ['DB_TYPE'] = 'postgresql'
os.environ['DATABASE_URL'] = 'postgresql://postgres.pdezvkbhbynfgqtwaqaw:NG86DDhGUIehlLZ8@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres'

# 导入数据库连接模块
from src.database.connection import get_connection, get_db_type

def test_connection():
    """测试数据库连接"""
    print("=" * 60)
    print("PostgreSQL 连接测试")
    print("=" * 60)

    # 1. 检查数据库类型
    db_type = get_db_type()
    print(f"\n✓ 数据库类型: {db_type}")

    # 2. 尝试连接
    try:
        print("\n尝试连接到 Supabase PostgreSQL...")
        conn = get_connection()
        print("✓ 连接成功！")

        # 3. 测试查询
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()
        # PostgreSQL RealDictCursor 返回字典，需要使用键访问
        version_str = version['version'] if isinstance(version, dict) else version[0]
        print(f"\n✓ PostgreSQL 版本: {version_str[:80]}...")

        # 4. 列出现有表
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        print(f"\n✓ 现有表数量: {len(tables)}")
        if tables:
            print("  表列表:")
            for table in tables:
                # RealDictCursor 返回字典
                table_name = table['table_name'] if isinstance(table, dict) else table[0]
                print(f"    - {table_name}")
        else:
            print("  （暂无表，需要运行初始化脚本）")

        # 清理
        cursor.close()
        conn.close()

        print("\n" + "=" * 60)
        print("✅ 所有测试通过！数据库连接正常")
        print("=" * 60)
        return True

    except Exception as e:
        import traceback
        print(f"\n❌ 连接失败: {e}")
        print(f"\n详细错误信息:")
        traceback.print_exc()
        print("\n" + "=" * 60)
        print("请检查：")
        print("1. DATABASE_URL 是否正确")
        print("2. Supabase 项目是否已启动")
        print("3. 网络连接是否正常")
        print("=" * 60)
        return False

if __name__ == '__main__':
    success = test_connection()
    sys.exit(0 if success else 1)
