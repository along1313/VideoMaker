#!/usr/bin/env python3
"""
测试修复后的Gemini LLM调用
验证重试机制和超时处理是否正常工作
"""

import os
import sys
import time
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from service.ai_service import LLMService
from static.model_info import GEMINI_MODELS

# 加载环境变量
load_dotenv()

def test_gemini_models():
    """测试修复后的Gemini模型"""
    print("🔧 测试修复后的Gemini LLM调用")
    print("=" * 50)
    
    # 测试每个可用的Gemini模型
    for model in GEMINI_MODELS:
        print(f"\n📱 测试模型: {model}")
        print("-" * 30)
        
        try:
            # 创建LLM服务实例
            llm_service = LLMService(model_str=model)
            
            # 准备测试消息
            messages = [
                {
                    "role": "system", 
                    "content": "你是一个AI助手，请简洁回答问题。"
                },
                {
                    "role": "user", 
                    "content": "请用一句话解释什么是人工智能？"
                }
            ]
            
            print("发送测试请求...")
            start_time = time.time()
            
            # 调用生成方法
            result = llm_service.generate(messages)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            print(f"✅ {model} 测试成功！")
            print(f"总耗时: {total_time:.2f}秒")
            print(f"响应长度: {len(result)}字符")
            print(f"响应预览: {result[:100]}...")
            
        except Exception as e:
            print(f"❌ {model} 测试失败")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {str(e)}")

def test_long_content():
    """测试长内容生成（可能触发超时）"""
    print(f"\n🕐 测试长内容生成（检验超时处理）")
    print("-" * 40)
    
    try:
        # 使用最快的模型
        llm_service = LLMService(model_str="gemini-2.5-flash")
        
        messages = [
            {
                "role": "user",
                "content": """请详细解释以下概念，每个概念至少200字：
                1. 机器学习
                2. 深度学习  
                3. 神经网络
                4. 自然语言处理
                5. 计算机视觉
                请确保回答详细且专业。"""
            }
        ]
        
        print("发送长内容生成请求...")
        start_time = time.time()
        
        result = llm_service.generate(messages)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"✅ 长内容生成成功！")
        print(f"总耗时: {total_time:.2f}秒")
        print(f"响应长度: {len(result)}字符")
        print(f"响应预览: {result[:200]}...")
        
    except Exception as e:
        print(f"❌ 长内容生成失败")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")

def test_model_performance():
    """比较不同模型的性能"""
    print(f"\n⚡ 模型性能对比测试")
    print("-" * 30)
    
    test_content = "请简单介绍Python编程语言的特点。"
    results = {}
    
    for model in GEMINI_MODELS:
        try:
            print(f"测试 {model}...")
            
            llm_service = LLMService(model_str=model)
            
            messages = [{"role": "user", "content": test_content}]
            
            start_time = time.time()
            result = llm_service.generate(messages)
            end_time = time.time()
            
            results[model] = {
                "success": True,
                "time": end_time - start_time,
                "length": len(result),
                "preview": result[:50] + "..."
            }
            
        except Exception as e:
            results[model] = {
                "success": False,
                "error": str(e)
            }
    
    # 输出结果
    print("\n📊 性能对比结果:")
    for model, result in results.items():
        print(f"\n{model}:")
        if result["success"]:
            print(f"  ✅ 成功")
            print(f"  ⏱️  耗时: {result['time']:.2f}秒")
            print(f"  📝 长度: {result['length']}字符")
            print(f"  👀 预览: {result['preview']}")
        else:
            print(f"  ❌ 失败: {result['error']}")

def main():
    """主测试函数"""
    print("🧪 Gemini修复验证测试")
    print("=" * 50)
    
    # 检查环境
    if not os.environ.get("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY环境变量未设置")
        return
    
    # 1. 基础模型测试
    test_gemini_models()
    
    # 2. 长内容测试
    test_long_content()
    
    # 3. 性能对比
    test_model_performance()
    
    print("\n" + "=" * 50)
    print("🏁 所有测试完成")
    print("\n💡 建议:")
    print("1. 如果测试通过，超时问题已解决")
    print("2. 建议在生产环境中使用 gemini-2.5-flash (速度快)")
    print("3. 对于复杂任务可使用 gemini-2.5-pro (质量高)")
    print("4. 重试机制会自动处理网络问题")

if __name__ == "__main__":
    main()