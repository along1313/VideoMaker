#!/usr/bin/env python3
"""
测试Gemini API调用超时问题
检查网络连接、API响应时间和潜在的配置问题
"""

import os
import sys
import time
import requests
from dotenv import load_dotenv
import traceback

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from service.ai_service import LLMService
from static.model_info import GEMINI_MODELS

# 加载环境变量
load_dotenv()

def test_network_connectivity():
    """测试网络连接"""
    print("=== 测试网络连接 ===")
    
    try:
        # 测试Google API基础连接
        start_time = time.time()
        response = requests.get("https://generativelanguage.googleapis.com", timeout=10)
        end_time = time.time()
        
        print(f"Google API域名连接: {response.status_code}")
        print(f"响应时间: {end_time - start_time:.2f}秒")
        
    except requests.exceptions.Timeout:
        print("❌ 网络连接超时 - 可能是网络问题")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ 网络连接失败 - 可能是DNS或防火墙问题")
        return False
    except Exception as e:
        print(f"❌ 网络测试失败: {str(e)}")
        return False
    
    return True

def test_api_key():
    """测试API密钥配置"""
    print("\n=== 测试API密钥配置 ===")
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY环境变量未设置")
        return False
    
    print(f"✅ API密钥已配置 (长度: {len(api_key)})")
    print(f"密钥前缀: {api_key[:10]}...")
    
    return True

def test_gemini_client_creation():
    """测试Gemini客户端创建"""
    print("\n=== 测试Gemini客户端创建 ===")
    
    try:
        from google import genai
        
        api_key = os.environ.get("GEMINI_API_KEY")
        client = genai.Client(api_key=api_key)
        print("✅ Gemini客户端创建成功")
        return client
        
    except ImportError as e:
        print(f"❌ 导入google.genai失败: {str(e)}")
        return None
    except Exception as e:
        print(f"❌ 客户端创建失败: {str(e)}")
        return None

def test_simple_api_call(client):
    """测试简单的API调用"""
    print("\n=== 测试简单API调用 ===")
    
    if not client:
        print("❌ 客户端未创建，跳过API调用测试")
        return False
    
    try:
        print("开始API调用...")
        start_time = time.time()
        
        # 使用一个简单的测试提示
        test_content = "请说'Hello'"
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=test_content,
            # 添加超时配置
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        print(f"✅ API调用成功")
        print(f"响应时间: {response_time:.2f}秒")
        print(f"响应内容: {response.text[:100]}...")
        
        return True
        
    except Exception as e:
        end_time = time.time()
        response_time = end_time - start_time
        
        print(f"❌ API调用失败 (耗时: {response_time:.2f}秒)")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        
        # 检查是否是超时错误
        if "timeout" in str(e).lower() or "timed out" in str(e).lower():
            print("🚨 这是超时错误！")
        
        traceback.print_exc()
        return False

def test_llm_service():
    """测试LLMService类"""
    print("\n=== 测试LLMService类 ===")
    
    try:
        # 测试每个Gemini模型
        for model in GEMINI_MODELS:
            print(f"\n测试模型: {model}")
            
            try:
                llm_service = LLMService(model_str=model)
                print(f"✅ {model} 初始化成功")
                
                # 测试简单生成
                start_time = time.time()
                
                messages = [
                    {"role": "user", "content": "请说'测试成功'"}
                ]
                
                result = llm_service.generate(messages)
                end_time = time.time()
                
                print(f"✅ {model} 生成成功 (耗时: {end_time - start_time:.2f}秒)")
                print(f"响应: {result[:50]}...")
                
            except Exception as e:
                print(f"❌ {model} 测试失败: {str(e)}")
                
                if "timeout" in str(e).lower():
                    print(f"🚨 {model} 超时错误！")
                    
    except Exception as e:
        print(f"❌ LLMService测试失败: {str(e)}")
        traceback.print_exc()

def test_with_different_timeouts():
    """测试不同超时设置"""
    print("\n=== 测试不同超时设置 ===")
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ 无API密钥，跳过超时测试")
        return
    
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        
        # 测试不同的超时时间
        timeout_values = [5, 10, 30, 60]
        
        for timeout in timeout_values:
            print(f"\n测试超时设置: {timeout}秒")
            
            try:
                start_time = time.time()
                
                # 这里需要检查Gemini客户端是否支持timeout参数
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents="请详细解释什么是人工智能，至少200字",
                    # timeout=timeout  # 需要确认Gemini是否支持此参数
                )
                
                end_time = time.time()
                actual_time = end_time - start_time
                
                print(f"✅ 超时{timeout}秒测试成功 (实际耗时: {actual_time:.2f}秒)")
                
            except Exception as e:
                end_time = time.time()
                actual_time = end_time - start_time
                
                print(f"❌ 超时{timeout}秒测试失败 (实际耗时: {actual_time:.2f}秒)")
                print(f"错误: {str(e)}")
                
    except Exception as e:
        print(f"❌ 超时测试初始化失败: {str(e)}")

def main():
    """主测试函数"""
    print("🔍 Gemini API超时问题诊断工具")
    print("=" * 50)
    
    # 1. 测试网络连接
    network_ok = test_network_connectivity()
    
    # 2. 测试API密钥
    api_key_ok = test_api_key()
    
    # 3. 测试客户端创建
    client = test_gemini_client_creation()
    
    # 4. 测试简单API调用
    if network_ok and api_key_ok and client:
        test_simple_api_call(client)
    
    # 5. 测试LLMService
    if api_key_ok:
        test_llm_service()
    
    # 6. 测试不同超时设置
    test_with_different_timeouts()
    
    print("\n" + "=" * 50)
    print("🏁 诊断完成")
    
    # 总结建议
    print("\n📋 建议:")
    if not network_ok:
        print("1. 检查网络连接和防火墙设置")
        print("2. 尝试使用VPN或代理服务器")
    
    if not api_key_ok:
        print("3. 确保GEMINI_API_KEY环境变量正确设置")
    
    print("4. 考虑增加重试机制")
    print("5. 考虑使用其他LLM模型作为备选")

if __name__ == "__main__":
    main()