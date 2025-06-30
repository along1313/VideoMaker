#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
完整邮箱功能测试脚本
测试邮箱验证注册、找回密码等功能
"""

import requests
import time

def test_email_verification_registration():
    """测试邮箱验证注册流程"""
    print("🧪 测试邮箱验证注册流程")
    print("=" * 50)
    
    base_url = "http://localhost:5002"
    test_email = input("请输入测试邮箱: ").strip()
    
    if not test_email:
        print("❌ 请输入有效邮箱")
        return False
    
    # 步骤1：发送验证码
    print(f"\n📤 步骤1: 发送验证码到 {test_email}")
    response = requests.post(f"{base_url}/api/send-verification-code", 
                           json={"email": test_email})
    
    if response.status_code == 200:
        result = response.json()
        if result['success']:
            print(f"✅ {result['message']}")
        else:
            print(f"❌ {result['message']}")
            return False
    else:
        print(f"❌ 请求失败: HTTP {response.status_code}")
        return False
    
    # 步骤2：输入验证码
    verification_code = input("\n🔑 请输入收到的6位验证码: ").strip()
    if len(verification_code) != 6:
        print("❌ 验证码应为6位数字")
        return False
    
    print(f"\n🔍 步骤2: 验证邮箱验证码")
    response = requests.post(f"{base_url}/api/verify-email-code", 
                           json={"email": test_email, "code": verification_code})
    
    if response.status_code == 200:
        result = response.json()
        if result['success']:
            print(f"✅ {result['message']}")
        else:
            print(f"❌ {result['message']}")
            return False
    else:
        print(f"❌ 请求失败: HTTP {response.status_code}")
        return False
    
    # 步骤3：完成注册
    username = input("\n👤 请输入用户名: ").strip()
    password = input("🔐 请输入密码: ").strip()
    
    if not username or not password:
        print("❌ 用户名和密码不能为空")
        return False
    
    print(f"\n📝 步骤3: 完成注册")
    response = requests.post(f"{base_url}/register-with-verification", 
                           json={
                               "email": test_email,
                               "username": username,
                               "password": password
                           })
    
    if response.status_code == 200:
        result = response.json()
        if result['success']:
            print(f"✅ {result['message']}")
            return True
        else:
            print(f"❌ {result['message']}")
            return False
    else:
        print(f"❌ 请求失败: HTTP {response.status_code}")
        return False

def test_password_reset():
    """测试密码重置流程"""
    print("\n🧪 测试密码重置流程")
    print("=" * 50)
    
    base_url = "http://localhost:5002"
    test_email = input("请输入已注册的邮箱: ").strip()
    
    if not test_email:
        print("❌ 请输入有效邮箱")
        return False
    
    # 发送重置邮件
    print(f"\n📤 发送密码重置邮件到 {test_email}")
    response = requests.post(f"{base_url}/api/send-reset-email", 
                           json={"email": test_email})
    
    if response.status_code == 200:
        result = response.json()
        if result['success']:
            print(f"✅ {result['message']}")
            print("📧 请检查您的邮箱，点击重置链接完成密码重置")
            return True
        else:
            print(f"❌ {result['message']}")
            return False
    else:
        print(f"❌ 请求失败: HTTP {response.status_code}")
        return False

def test_all_pages():
    """测试所有新增页面是否可访问"""
    print("\n🧪 测试页面访问")
    print("=" * 50)
    
    base_url = "http://localhost:5002"
    pages = [
        ("/register-with-email", "邮箱验证注册页面"),
        ("/forgot-password", "找回密码页面"),
        ("/reset-password?token=test", "重置密码页面")
    ]
    
    all_success = True
    
    for url, name in pages:
        try:
            response = requests.get(f"{base_url}{url}")
            if response.status_code == 200:
                print(f"✅ {name}: 可访问")
            else:
                print(f"❌ {name}: HTTP {response.status_code}")
                all_success = False
        except Exception as e:
            print(f"❌ {name}: 访问失败 - {str(e)}")
            all_success = False
    
    return all_success

def main():
    """主测试函数"""
    print("🎯 百速AI邮箱功能完整测试")
    print("=" * 60)
    
    # 提示启动应用
    input("请确保应用已启动（python run.py），然后按回车继续...")
    
    # 测试页面访问
    if not test_all_pages():
        print("\n❌ 页面访问测试失败，请检查应用是否正常启动")
        return
    
    print("\n" + "=" * 60)
    print("请选择要测试的功能：")
    print("1. 邮箱验证注册流程")
    print("2. 密码重置流程") 
    print("3. 退出")
    
    while True:
        choice = input("\n请输入选择 (1-3): ").strip()
        
        if choice == "1":
            success = test_email_verification_registration()
            if success:
                print("\n🎉 邮箱验证注册测试成功！")
            else:
                print("\n💥 邮箱验证注册测试失败！")
        
        elif choice == "2":
            success = test_password_reset()
            if success:
                print("\n🎉 密码重置测试成功！")
            else:
                print("\n💥 密码重置测试失败！")
        
        elif choice == "3":
            print("\n👋 测试结束")
            break
        
        else:
            print("❌ 无效选择，请输入 1-3")

if __name__ == "__main__":
    main() 