#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
创建管理员用户脚本
"""

import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User

def create_admin_user():
    """创建管理员用户"""
    with app.app_context():
        # 检查是否已存在管理员用户
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print("管理员用户已存在")
            print(f"用户名: {admin.username}")
            print(f"邮箱: {admin.email}")
            print(f"是否为VIP: {admin.is_vip}")
            print(f"积分: {admin.credits}")
            return
        
        # 创建新的管理员用户
        admin = User(
            username='admin',
            email='admin@baisu.ai',
            is_admin=True,
            is_vip=True,  # 设置为VIP用户
            credits=100,  # 给予100积分
            is_active=True
        )
        admin.set_password('admin123')
        
        db.session.add(admin)
        db.session.commit()
        
        print("✅ 管理员用户创建成功！")
        print(f"用户名: {admin.username}")
        print(f"密码: admin123")
        print(f"邮箱: {admin.email}")
        print(f"是否为VIP: {admin.is_vip}")
        print(f"积分: {admin.credits}")

if __name__ == "__main__":
    create_admin_user() 