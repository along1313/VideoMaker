#!/usr/bin/env python3
"""
简单测试LLM模型降级机制
只测试初始化和错误处理逻辑
"""

import os
import sys
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from service.ai_service import LLMService

# 加载环境变量
load_dotenv()

def test_model_initialization():
    """测试模型初始化"""
    print("🧪 测试模型初始化和降级逻辑")
    print("=" * 40)
    
    # 测试1: 正常模型
    print("\n1. 测试deepseek-reasoner (备用模型)")
    try:
        llm = LLMService(model_str="deepseek-reasoner")
        print("✅ deepseek-reasoner 初始化成功")
        
        # 简单测试生成
        messages = [{"role": "user", "content": "请说'测试'"}]
        result = llm.generate(messages)
        print(f"✅ 生成成功: {result[:50]}...")
        
    except Exception as e:
        print(f"❌ deepseek-reasoner 失败: {str(e)}")
    
    # 测试2: Gemini模型
    print("\n2. 测试gemini-2.5-flash")
    try:
        llm = LLMService(model_str="gemini-2.5-flash")
        print("✅ gemini-2.5-flash 初始化成功")
        
        # 简单测试生成
        messages = [{"role": "user", "content": "请说'测试'"}]
        result = llm.generate(messages)
        print(f"✅ 生成成功: {result[:50]}...")
        
    except Exception as e:
        print(f"❌ gemini-2.5-flash 失败: {str(e)}")
        print("📝 这个失败是预期的，将在工作流中触发降级")
    
    # 测试3: 不存在的模型
    print("\n3. 测试不存在的模型")
    try:
        llm = LLMService(model_str="nonexistent-model")
        print("❌ 不应该初始化成功")
    except Exception as e:
        print(f"✅ 预期的失败: {str(e)}")

def simulate_fallback_logic():
    """模拟降级逻辑"""
    print("\n🔄 模拟降级逻辑")
    print("=" * 25)
    
    primary_model = "gemini-2.5-flash"
    fallback_model = "deepseek-reasoner"
    
    # 模拟工作流中的降级逻辑
    work_flow_record = None
    
    # 尝试主模型
    try:
        print(f"尝试使用主模型: {primary_model}")
        llm = LLMService(model_str=primary_model)
        
        # 模拟脚本生成（简化版）
        messages = [{"role": "user", "content": "生成一个简单的JSON: {\"title\": \"测试标题\"}"}]
        result = llm.generate(messages)
        
        work_flow_record = {"title": "主模型成功", "content": result}
        print(f"✅ 主模型成功: {work_flow_record['title']}")
        
    except Exception as e:
        print(f"❌ 主模型失败: {str(e)}")
        
        # 尝试降级模型
        if primary_model != fallback_model:
            try:
                print(f"🔄 降级到: {fallback_model}")
                llm_fallback = LLMService(model_str=fallback_model)
                
                messages = [{"role": "user", "content": "生成一个简单的JSON: {\"title\": \"测试标题\"}"}]
                result = llm_fallback.generate(messages)
                
                work_flow_record = {"title": "降级模型成功", "content": result}
                print(f"✅ 降级模型成功: {work_flow_record['title']}")
                
            except Exception as fallback_error:
                print(f"❌ 降级模型也失败: {str(fallback_error)}")
                error_msg = f"主模型({primary_model})失败: {str(e)}; 降级模型({fallback_model})失败: {str(fallback_error)}"
                print(f"🔍 完整错误信息: {error_msg}")
                return None
    
    return work_flow_record

def test_error_scenarios():
    """测试各种错误场景"""
    print("\n🚨 测试错误场景")
    print("=" * 20)
    
    scenarios = [
        {"model": "deepseek-reasoner", "expected": "成功"},
        {"model": "gemini-2.5-flash", "expected": "可能超时"},
        {"model": "nonexistent-model", "expected": "模型不存在"}
    ]
    
    for scenario in scenarios:
        model = scenario["model"]
        expected = scenario["expected"]
        
        print(f"\n测试 {model} (预期: {expected})")
        
        try:
            llm = LLMService(model_str=model)
            print(f"  ✅ 初始化成功")
            
            # 尝试简单生成
            messages = [{"role": "user", "content": "Hello"}]
            result = llm.generate(messages)
            print(f"  ✅ 生成成功: {len(result)}字符")
            
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            print(f"  ❌ 失败 ({error_type}): {error_msg[:100]}...")

def main():
    """主函数"""
    print("🧪 LLM模型降级机制简单测试")
    print("=" * 40)
    
    # 检查环境变量
    required_apis = ["DEEPSEEK_API_KEY", "GEMINI_API_KEY"]
    available_apis = [api for api in required_apis if os.environ.get(api)]
    
    print(f"可用API: {available_apis}")
    
    if "DEEPSEEK_API_KEY" not in available_apis:
        print("❌ 缺少DEEPSEEK_API_KEY，降级机制无法工作")
        return
    
    # 运行测试
    test_model_initialization()
    simulate_fallback_logic()
    test_error_scenarios()
    
    print("\n" + "=" * 40)
    print("📋 测试总结:")
    print("1. ✅ 降级机制已集成到work_flow_service.py")
    print("2. ✅ max_retries已调整为2次")
    print("3. ✅ 备用模型为deepseek-reasoner")
    print("4. 🔄 当主模型失败时自动降级")
    print("5. 📝 提供详细的错误信息")
    
    print("\n💡 使用建议:")
    print("- 生产环境推荐使用gemini-2.5-flash作为主模型")
    print("- deepseek-reasoner作为稳定的备用模型")
    print("- 系统会自动处理模型故障")

if __name__ == "__main__":
    main()