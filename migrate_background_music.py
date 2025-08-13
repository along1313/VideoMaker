#!/usr/bin/env python3
"""
数据库迁移脚本：添加背景音乐管理功能
1. 创建background_music表
2. 在task_queue表中添加bgm_path字段
3. 插入默认背景音乐记录
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, BackgroundMusic
from datetime import datetime

def migrate_database():
    """执行数据库迁移"""
    with app.app_context():
        try:
            print("开始数据库迁移...")
            
            # 1. 创建所有表（包括新的background_music表）
            print("创建新表...")
            db.create_all()
            
            # 2. 手动添加bgm_path字段到task_queue表（如果不存在）
            print("检查task_queue表结构...")
            try:
                # 使用text()和execute()方法添加bgm_path字段
                from sqlalchemy import text
                with db.engine.connect() as conn:
                    conn.execute(text("""
                        ALTER TABLE task_queue 
                        ADD COLUMN bgm_path VARCHAR(200)
                    """))
                    conn.commit()
                print("已添加bgm_path字段到task_queue表")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print("bgm_path字段已存在，跳过...")
                else:
                    print(f"添加bgm_path字段时出错: {e}")
            
            # 3. 检查是否已存在默认背景音乐
            default_music = BackgroundMusic.query.filter_by(is_default=True).first()
            if not default_music:
                print("创建默认背景音乐记录...")
                # 创建默认背景音乐记录
                default_bgm = BackgroundMusic(
                    user_id=None,  # 全局默认音乐
                    name="默认",
                    file_path="lib/music/bgm.wav",
                    file_size=0,  # 默认文件大小设为0
                    file_type="wav",
                    is_default=True,
                    created_at=datetime.utcnow()
                )
                db.session.add(default_bgm)
                db.session.commit()
                print("默认背景音乐记录创建完成")
            else:
                print("默认背景音乐记录已存在，跳过...")
            
            # 4. 创建用户音乐存储目录
            print("创建用户音乐存储目录...")
            music_dir = os.path.join('static', 'music', 'users')
            os.makedirs(music_dir, exist_ok=True)
            print(f"音乐存储目录创建完成: {music_dir}")
            
            print("数据库迁移完成！")
            
        except Exception as e:
            print(f"数据库迁移失败: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    migrate_database()