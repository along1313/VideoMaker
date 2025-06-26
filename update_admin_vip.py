#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
更新管理员用户为VIP脚本
"""

import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User

def update_admin_vip():
    """更新管理员用户为VIP"""
    with app.app_context():
        # 查找管理员用户
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("❌ 管理员用户不存在")
            return
        
        # 更新为VIP用户
        admin.is_vip = True
        admin.credits = 100  # 重置积分为100
        
        db.session.commit()
        
        print("✅ 管理员用户更新成功！")
        print(f"用户名: {admin.username}")
        print(f"邮箱: {admin.email}")
        print(f"是否为VIP: {admin.is_vip}")
        print(f"积分: {admin.credits}")

if __name__ == "__main__":
    update_admin_vip() 