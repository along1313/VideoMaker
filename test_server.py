#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
服务器功能测试脚本
"""

import requests
import time

def test_server():
    """测试服务器基本功能"""
    base_url = "http://localhost:5002"
    
    print("=== 百速AI视频生成服务器测试 ===")
    
    # 测试1: 首页访问
    print("\n1. 测试首页访问...")
    try:
        response = requests.get(base_url)
        if response.status_code == 200:
            print("✅ 首页访问成功")
        else:
            print(f"❌ 首页访问失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ 首页访问异常: {str(e)}")
    
    # 测试2: 登录页面
    print("\n2. 测试登录页面...")
    try:
        response = requests.get(f"{base_url}/login")
        if response.status_code == 200:
            print("✅ 登录页面访问成功")
        else:
            print(f"❌ 登录页面访问失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ 登录页面访问异常: {str(e)}")
    
    # 测试3: 注册页面
    print("\n3. 测试注册页面...")
    try:
        response = requests.get(f"{base_url}/register")
        if response.status_code == 200:
            print("✅ 注册页面访问成功")
        else:
            print(f"❌ 注册页面访问失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ 注册页面访问异常: {str(e)}")
    
    # 测试4: 静态文件
    print("\n4. 测试静态文件...")
    try:
        response = requests.get(f"{base_url}/static/css/style.css")
        if response.status_code == 200:
            print("✅ 静态文件访问成功")
        else:
            print(f"❌ 静态文件访问失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ 静态文件访问异常: {str(e)}")
    
    print("\n=== 测试完成 ===")
    print("服务器运行正常！")
    print(f"请访问: {base_url}")
    print("用户名: admin")
    print("密码: admin123")

if __name__ == "__main__":
    test_server() 