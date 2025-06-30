#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
密码重置功能测试脚本
"""

import requests
import json

def test_password_reset_flow():
    """测试完整的密码重置流程"""
    base_url = "http://localhost:5002"
    test_email = "inter_trade@msn.com"  # test5用户的邮箱
    
    print("🧪 测试密码重置流程")
    print("=" * 50)
    
    # 步骤1：发送重置邮件
    print(f"📤 步骤1: 发送密码重置邮件到 {test_email}")
    response = requests.post(f"{base_url}/api/send-reset-email", 
                           json={"email": test_email})
    
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"响应: {result}")
        if result['success']:
            print(f"✅ {result['message']}")
            return True
        else:
            print(f"❌ {result['message']}")
            return False
    else:
        print(f"❌ 请求失败: HTTP {response.status_code}")
        print(f"响应内容: {response.text}")
        return False

if __name__ == "__main__":
    test_password_reset_flow()
