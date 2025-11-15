#!/usr/bin/env python3
"""
添加缺失的数据库列
"""

import sqlite3
import sys
import os

# 将src添加到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def add_missing_columns():
    """添加缺失的数据库列"""
    db_path = 'data/dashboard.db'

    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 要添加的列
    columns_to_add = [
        ('timezone', 'TEXT DEFAULT "Asia/Shanghai"'),
        ('access_token', 'TEXT'),
        ('token_generated_at', 'TEXT'),
        ('token_expires_at', 'TEXT')
    ]

    print(f"正在更新数据库表结构...")

    for column_name, column_def in columns_to_add:
        try:
            # 检查列是否已存在
            cursor.execute(f"PRAGMA table_info(users)")
            columns = [row[1] for row in cursor.fetchall()]

            if column_name not in columns:
                # 添加列
                alter_query = f"ALTER TABLE users ADD COLUMN {column_name} {column_def}"
                cursor.execute(alter_query)
                print(f"✅ 成功添加列: {column_name}")
            else:
                print(f"⚠️  列已存在: {column_name}")

        except sqlite3.Error as e:
            print(f"❌ 添加列 {column_name} 失败: {e}")
            conn.rollback()
            return False

    # 提交更改
    conn.commit()
    print("\n✅ 数据库更新完成!")

    # 验证更新
    print("\n验证数据库结构:")
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    print(f"当前列数: {len(columns)}")
    for col in columns:
        print(f"  - {col[1]}: {col[2]}")

    conn.close()
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("数据库迁移：添加缺失的列")
    print("=" * 60)

    if add_missing_columns():
        print("\n✅ 迁移成功完成!")
    else:
        print("\n❌ 迁移失败!")
        sys.exit(1)