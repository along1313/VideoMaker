#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
邮箱验证API测试脚本
演示如何使用邮箱验证功能
"""

import requests
import json
import time

def test_verification_api():
    """测试邮箱验证API"""
    base_url = "http://localhost:5002"
    
    print("🧪 测试邮箱验证API流程")
    print("="*50)
    
    # 测试邮箱
    test_email = input("请输入测试邮箱: ").strip()
    if not test_email:
        print("❌ 请输入有效邮箱")
        return
    
    # 第1步：发送验证码
    print(f"\n📤 步骤1: 发送验证码到 {test_email}")
    
    response = requests.post(f"{base_url}/api/send-verification-code", 
                           json={"email": test_email})
    
    if response.status_code == 200:
        result = response.json()
        if result['success']:
            print(f"✅ {result['message']}")
        else:
            print(f"❌ {result['message']}")
            return
    else:
        print(f"❌ 请求失败: {response.status_code}")
        return
    
    # 第2步：用户输入验证码
    print(f"\n📥 步骤2: 验证邮箱验证码")
    verification_code = input("请输入收到的验证码: ").strip()
    
    response = requests.post(f"{base_url}/api/verify-email-code",
                           json={"email": test_email, "code": verification_code})
    
    if response.status_code == 200:
        result = response.json()
        if result['success']:
            print(f"✅ {result['message']}")
        else:
            print(f"❌ {result['message']}")
            return
    else:
        print(f"❌ 验证失败: {response.status_code}")
        return
    
    # 第3步：完成注册
    print(f"\n👤 步骤3: 完成注册")
    username = input("请输入用户名: ").strip()
    password = input("请输入密码: ").strip()
    
    response = requests.post(f"{base_url}/register-with-verification",
                           json={
                               "email": test_email,
                               "username": username, 
                               "password": password
                           })
    
    if response.status_code == 200:
        result = response.json()
        if result['success']:
            print(f"🎉 {result['message']}")
            print(f"🔗 跳转到: {result.get('redirect', '/')}")
        else:
            print(f"❌ {result['message']}")
    else:
        print(f"❌ 注册失败: {response.status_code}")

if __name__ == "__main__":
    print("🚀 百速AI邮箱验证API测试")
    print("请确保应用正在运行 (python run.py)")
    print()
    
    try:
        test_verification_api()
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到应用，请确保应用正在运行")
    except KeyboardInterrupt:
        print("\n👋 测试已取消") 