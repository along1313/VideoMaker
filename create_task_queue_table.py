#!/usr/bin/env python3
"""
数据库迁移脚本：创建 task_queue 表
解决服务器端缺失任务队列表的问题
"""

import sqlite3
import os
import sys
from datetime import datetime

def create_missing_tables():
    """创建缺失的数据库表"""
    
    # 数据库文件路径
    db_path = 'instance/baisu_video.db'
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return False
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        success = True
        
        # 检查并创建 task_queue 表
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='task_queue'
        """)
        
        if cursor.fetchone():
            print("✅ task_queue 表已存在")
        else:
            success &= create_task_queue_table_sql(cursor)
        
        # 检查并创建 feedback 表
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='feedback'
        """)
        
        if cursor.fetchone():
            print("✅ feedback 表已存在")
        else:
            success &= create_feedback_table_sql(cursor)
        
        if success:
            conn.commit()
            print("✅ 所有缺失的表创建成功！")
        else:
            conn.rollback()
            print("❌ 创建表过程中发生错误")
        
        conn.close()
        return success
        
    except Exception as e:
        print(f"❌ 创建表失败: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def create_task_queue_table_sql(cursor):
    """创建 task_queue 表的SQL执行"""
    try:
        
        print("📊 正在创建 task_queue 表...")
        
        # 创建 task_queue 表
        cursor.execute("""
            CREATE TABLE task_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                video_id INTEGER,
                title VARCHAR(200) NOT NULL,
                prompt TEXT NOT NULL,
                style VARCHAR(50) NOT NULL,
                template VARCHAR(50) NOT NULL DEFAULT '通用',
                mode VARCHAR(20) DEFAULT 'prompt',
                estimated_credits INTEGER DEFAULT 1,
                is_display_title BOOLEAN DEFAULT 1,
                user_name VARCHAR(100),
                tts_model_str VARCHAR(50) DEFAULT 'cosyvoice-v1',
                book_title VARCHAR(200),
                book_cover_path VARCHAR(200),
                status VARCHAR(20) DEFAULT 'waiting',
                queue_position INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                started_at DATETIME,
                completed_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES user (id),
                FOREIGN KEY (video_id) REFERENCES video (id)
            )
        """)
        
        # 创建索引以提高查询性能
        cursor.execute("""
            CREATE INDEX idx_task_queue_user_id ON task_queue(user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_task_queue_status ON task_queue(status)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_task_queue_queue_position ON task_queue(queue_position)
        """)
        
        print("✅ task_queue 表创建成功！")
        
        # 验证表结构
        cursor.execute("PRAGMA table_info(task_queue)")
        columns = cursor.fetchall()
        
        print("📋 task_queue 表结构:")
        for column in columns:
            print(f"  - {column[1]} ({column[2]})")
        
        return True
        
    except Exception as e:
        print(f"❌ 创建 task_queue 表失败: {str(e)}")
        return False

def create_feedback_table_sql(cursor):
    """创建 feedback 表的SQL执行"""
    try:
        print("📊 正在创建 feedback 表...")
        
        # 创建 feedback 表
        cursor.execute("""
            CREATE TABLE feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                email VARCHAR(120),
                wechat VARCHAR(100),
                qq VARCHAR(50),
                phone VARCHAR(20),
                content TEXT NOT NULL,
                is_read BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                replied_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES user (id)
            )
        """)
        
        # 创建索引
        cursor.execute("""
            CREATE INDEX idx_feedback_user_id ON feedback(user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_feedback_is_read ON feedback(is_read)
        """)
        
        print("✅ feedback 表创建成功！")
        
        # 验证表结构
        cursor.execute("PRAGMA table_info(feedback)")
        columns = cursor.fetchall()
        
        print("📋 feedback 表结构:")
        for column in columns:
            print(f"  - {column[1]} ({column[2]})")
        
        return True
        
    except Exception as e:
        print(f"❌ 创建 feedback 表失败: {str(e)}")
        return False

def verify_database():
    """验证数据库完整性"""
    db_path = 'instance/baisu_video.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取所有表
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        
        tables = cursor.fetchall()
        print(f"\n📊 数据库中的表 ({len(tables)} 个):")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"  ✅ {table[0]}: {count} 条记录")
        
        conn.close()
        
        # 检查必要的表是否存在
        required_tables = ['user', 'video', 'feedback', 'task_queue']
        existing_tables = [t[0] for t in tables]
        
        missing_tables = []
        for table in required_tables:
            if table not in existing_tables:
                missing_tables.append(table)
        
        if missing_tables:
            print(f"\n⚠️  缺失的表: {', '.join(missing_tables)}")
            return False
        else:
            print("\n✅ 所有必要的表都存在")
            return True
        
    except Exception as e:
        print(f"❌ 数据库验证失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("百速AI视频生成系统 - 数据库迁移脚本")
    print("=" * 50)
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("目标: 创建缺失的 task_queue 表")
    print("=" * 50)
    
    # 切换到脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # 验证当前数据库状态
    print("步骤 1: 验证当前数据库状态")
    verify_database()
    
    print("\n步骤 2: 创建缺失的表")
    success = create_missing_tables()
    
    print("\n步骤 3: 最终验证")
    final_check = verify_database()
    
    print("\n" + "=" * 50)
    if success and final_check:
        print("🎉 数据库迁移成功完成！")
        print("✅ 所有必要的表已创建并就绪")
        sys.exit(0)
    else:
        print("❌ 数据库迁移失败")
        print("请检查错误信息并手动修复")
        sys.exit(1)