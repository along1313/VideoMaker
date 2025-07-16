#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试弹窗登录功能的脚本
"""

import requests
import json

# 测试服务器地址
BASE_URL = "http://localhost:5002"

def test_json_login():
    """测试JSON格式的登录请求"""
    print("测试JSON格式登录...")
    
    # 登录数据
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    # 发送JSON登录请求
    response = requests.post(
        f"{BASE_URL}/login",
        json=login_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print("✅ JSON登录成功")
            print(f"用户信息: {data.get('user')}")
            return True
        else:
            print(f"❌ 登录失败: {data.get('message')}")
    else:
        print(f"❌ 请求失败: {response.status_code}")
    
    return False

def test_json_register():
    """测试JSON格式的注册请求"""
    print("\n测试JSON格式注册...")
    
    # 注册数据 - 使用随机用户名避免冲突
    import random
    random_suffix = random.randint(1000, 9999)
    register_data = {
        "username": f"testuser{random_suffix}",
        "email": f"testuser{random_suffix}@example.com",
        "password": "testpass123"
    }
    
    # 发送JSON注册请求
    response = requests.post(
        f"{BASE_URL}/register",
        json=register_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print("✅ JSON注册成功")
            print(f"用户信息: {data.get('user')}")
            return True
        else:
            print(f"❌ 注册失败: {data.get('message')}")
    else:
        print(f"❌ 请求失败: {response.status_code}")
    
    return False

def test_homepage():
    """测试主页是否可以正常访问"""
    print("\n测试主页访问...")
    
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 主页访问成功")
            # 检查是否包含弹窗相关的HTML
            if "showLoginDialog" in response.text and "showRegisterDialog" in response.text:
                print("✅ 弹窗相关代码已添加")
                return True
            else:
                print("❌ 未找到弹窗相关代码")
        else:
            print(f"❌ 主页访问失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
    
    return False

if __name__ == "__main__":
    print("开始测试弹窗登录功能...")
    print("=" * 50)
    
    # 测试主页
    if not test_homepage():
        print("❌ 主页测试失败，请检查服务器是否运行")
        exit(1)
    
    # 测试登录
    test_json_login()
    
    # 测试注册
    test_json_register()
    
    print("\n" + "=" * 50)
    print("测试完成!")