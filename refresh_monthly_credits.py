#!/usr/bin/env python3
"""
月度免费额度刷新脚本
建议在每月1日自动运行此脚本
"""

from app import app, db, User
from datetime import datetime
import sys

def refresh_all_users_credits():
    """批量刷新所有非VIP用户的月度免费额度"""
    with app.app_context():
        refreshed_count = 0
        total_count = 0
        
        # 获取所有活跃的非VIP用户
        users = User.query.filter_by(is_active=True).all()
        
        for user in users:
            total_count += 1
            if user.refresh_monthly_free_credits():
                refreshed_count += 1
                print(f"✅ 用户 {user.username} 刷新成功，当前额度: {user.credits}")
            else:
                if user.is_current_vip:
                    print(f"⭐ 用户 {user.username} 是VIP，跳过刷新")
                else:
                    print(f"⏭️ 用户 {user.username} 本月已刷新过，跳过")
        
        # 提交数据库更改
        db.session.commit()
        
        print(f"\n📊 刷新完成统计:")
        print(f"   总用户数: {total_count}")
        print(f"   刷新成功: {refreshed_count}")
        print(f"   跳过用户: {total_count - refreshed_count}")
        
        return refreshed_count

def test_refresh_logic():
    """测试刷新逻辑"""
    with app.app_context():
        # 查找一个测试用户
        test_user = User.query.filter_by(username='admin').first()
        
        if not test_user:
            print("❌ 未找到测试用户 admin")
            return
        
        print(f"测试用户: {test_user.username}")
        print(f"当前VIP状态: {test_user.is_current_vip}")
        print(f"当前额度: {test_user.credits}")
        print(f"上次刷新时间: {test_user.last_free_credits_refresh}")
        print(f"是否需要刷新: {test_user.should_refresh_free_credits()}")
        
        # 模拟刷新
        old_credits = test_user.credits
        if test_user.refresh_monthly_free_credits():
            print(f"✅ 刷新成功: {old_credits} -> {test_user.credits}")
            db.session.commit()
        else:
            print("⏭️ 不需要刷新或用户是VIP")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        print("🧪 运行测试模式...")
        test_refresh_logic()
    else:
        print("🚀 开始月度免费额度刷新...")
        refresh_all_users_credits()
        print("✨ 月度免费额度刷新完成！") 