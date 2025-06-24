#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修复用户状态脚本
"""

from app import app, db, User

def fix_users():
    """修复用户状态"""
    with app.app_context():
        # 修复管理员账户
        admin = User.query.filter_by(username='admin').first()
        if admin:
            admin.is_active = True
            admin.is_admin = True
            print(f"已修复管理员账户状态 - 用户名: {admin.username}, 状态: 启用")
        else:
            print("未找到管理员账户")

        # 修复测试账户
        test = User.query.filter_by(username='test').first()
        if test:
            test.is_active = True
            print(f"已修复测试账户状态 - 用户名: {test.username}, 状态: 启用")
        else:
            print("未找到测试账户")

        # 提交更改
        db.session.commit()
        print("所有更改已保存")

if __name__ == '__main__':
    fix_users() 