#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
创建管理员和测试用户脚本
"""

from app import app, db, User

def create_users():
    """创建管理员和测试用户"""
    with app.app_context():
        # 检查管理员用户是否已存在
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@baisu.com',
                credits=9999  # 管理员账户余额9999
            )
            admin.set_password('admin123')  # 设置密码
            db.session.add(admin)
            print("已创建管理员账户 - 用户名: admin, 密码: admin123, 余额: 9999")
        else:
            admin.credits = 9999
            print("已更新管理员账户余额为9999")

        # 检查测试用户是否已存在
        test_user = User.query.filter_by(username='test').first()
        if not test_user:
            test_user = User(
                username='test',
                email='test@baisu.com',
                credits=100  # 测试账户余额100
            )
            test_user.set_password('test123')  # 设置密码
            db.session.add(test_user)
            print("已创建测试账户 - 用户名: test, 密码: test123, 余额: 100")
        else:
            test_user.credits = 100
            print("已更新测试账户余额为100")

        # 提交更改
        db.session.commit()
        print("用户创建/更新完成")

if __name__ == "__main__":
    create_users()
