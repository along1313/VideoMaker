#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
邮件功能测试脚本
测试腾讯企业邮箱发送功能
"""

import os
import sys
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 加载环境变量
load_dotenv()

def test_email_sending():
    """测试邮件发送功能"""
    print("🧪 开始测试邮件发送功能...")
    
    # 检查环境变量
    required_env_vars = [
        'MAIL_SERVER',
        'MAIL_PORT', 
        'MAIL_USERNAME',
        'MAIL_PASSWORD',
        'MAIL_DEFAULT_SENDER'
    ]
    
    print("\n📋 检查环境变量配置...")
    missing_vars = []
    for var in required_env_vars:
        value = os.environ.get(var)
        if value:
            if var == 'MAIL_PASSWORD':
                print(f"✅ {var}: {'*' * len(value)}")  # 隐藏密码
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: 未配置")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ 缺少环境变量: {', '.join(missing_vars)}")
        print("请先在 .env 文件中配置邮件服务")
        return False
    
    # 导入应用和邮件服务
    try:
        from app import app
        from service.email_service import email_service
        print("\n✅ 成功导入应用和邮件服务")
    except Exception as e:
        print(f"\n❌ 导入失败: {str(e)}")
        return False
    
    # 在应用上下文中测试
    with app.app_context():
        print("\n📧 开始测试邮件发送...")
        
        # 测试邮箱（请替换为您的真实邮箱）
        test_email = input("请输入测试邮箱地址: ").strip()
        if not test_email:
            print("❌ 请输入有效的邮箱地址")
            return False
        
        # 测试 1: 发送验证码邮件
        print(f"\n🧪 测试1: 发送验证码到 {test_email}")
        try:
            verification_code = email_service.generate_verification_code()
            print(f"生成的验证码: {verification_code}")
            
            success = email_service.send_verification_email(
                user_email=test_email,
                verification_code=verification_code,
                username="测试用户"
            )
            
            if success:
                print("✅ 验证码邮件发送成功！")
            else:
                print("❌ 验证码邮件发送失败")
                return False
                
        except Exception as e:
            print(f"❌ 发送验证码邮件时出错: {str(e)}")
            return False
        
        # 测试 2: 发送欢迎邮件
        print(f"\n🧪 测试2: 发送欢迎邮件到 {test_email}")
        try:
            success = email_service.send_welcome_email(
                user_email=test_email,
                username="测试用户"
            )
            
            if success:
                print("✅ 欢迎邮件发送成功！")
            else:
                print("❌ 欢迎邮件发送失败")
                return False
                
        except Exception as e:
            print(f"❌ 发送欢迎邮件时出错: {str(e)}")
            return False
        
        print(f"\n🎉 所有邮件测试通过！")
        print(f"📬 请检查邮箱 {test_email} 是否收到了两封邮件:")
        print("   1. 验证码邮件")
        print("   2. 欢迎邮件")
        
        return True

def test_mail_config():
    """测试邮件配置连接"""
    print("\n🔧 测试SMTP连接...")
    
    import smtplib
    from email.mime.text import MIMEText
    
    try:
        # 获取配置
        mail_server = os.environ.get('MAIL_SERVER')
        mail_port = int(os.environ.get('MAIL_PORT', 465))
        mail_username = os.environ.get('MAIL_USERNAME')
        mail_password = os.environ.get('MAIL_PASSWORD')
        
        # 创建SMTP连接
        if mail_port == 465:
            server = smtplib.SMTP_SSL(mail_server, mail_port)
        else:
            server = smtplib.SMTP(mail_server, mail_port)
            server.starttls()
        
        # 登录
        server.login(mail_username, mail_password)
        print("✅ SMTP连接和认证成功！")
        
        server.quit()
        return True
        
    except Exception as e:
        print(f"❌ SMTP连接失败: {str(e)}")
        print("\n📝 常见问题排查:")
        print("1. 检查邮箱密码是否正确")
        print("2. 检查是否开启了SMTP服务")
        print("3. 检查网络连接")
        print("4. 检查DNS解析")
        return False

if __name__ == "__main__":
    print("="*60)
    print("🚀 百速AI邮件服务测试")
    print("="*60)
    
    # 首先测试SMTP连接
    if test_mail_config():
        print("\n" + "="*60)
        # 然后测试邮件发送
        if test_email_sending():
            print("\n🎊 邮件服务配置完成！可以正常使用邮箱验证功能了。")
        else:
            print("\n💥 邮件发送测试失败，请检查配置。")
    else:
        print("\n💥 SMTP连接失败，请检查邮件服务器配置。")
    
    print("="*60) 