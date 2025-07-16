#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修复密码哈希兼容性问题
将 scrypt 哈希格式转换为 pbkdf2 格式
"""

from app import app, db, User
from werkzeug.security import generate_password_hash

def fix_password_hashes():
    """修复所有用户的密码哈希格式"""
    with app.app_context():
        users = User.query.all()
        
        print(f"发现 {len(users)} 个用户需要修复密码哈希格式")
        
        # 为每个用户设置一个临时密码（实际部署时请使用更安全的方式）
        default_passwords = {
            'admin': 'admin123',
            'test': 'test123',
            'test2': 'test123',
            'test3': 'test123',
            'test_user': 'test123',
            'test4': 'test123',
            'test5': 'test123',
            'test9': 'test123'
        }
        
        for user in users:
            old_hash = user.password_hash
            
            # 获取用户的默认密码
            default_password = default_passwords.get(user.username, 'default123')
            
            # 使用 pbkdf2 算法重新生成密码哈希
            new_hash = generate_password_hash(default_password, method='pbkdf2:sha256')
            
            # 更新用户密码哈希
            user.password_hash = new_hash
            
            print(f"用户 {user.username}:")
            print(f"  旧哈希: {old_hash[:50]}...")
            print(f"  新哈希: {new_hash[:50]}...")
            print(f"  默认密码: {default_password}")
            print()
        
        # 提交更改
        db.session.commit()
        print("✅ 所有用户密码哈希已修复完成")
        
        # 验证修复结果
        print("\n验证修复结果:")
        for user in users:
            if user.check_password(default_passwords.get(user.username, 'default123')):
                print(f"✅ {user.username} 密码验证成功")
            else:
                print(f"❌ {user.username} 密码验证失败")

if __name__ == "__main__":
    fix_password_hashes()