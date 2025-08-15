#!/usr/bin/env python3
"""
测试LLM模型降级机制
验证当主模型失败时能否自动降级到deepseek-reasoner
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from service.work_flow_service import run_work_flow_v3_with_progress

# 加载环境变量
load_dotenv()

async def test_model_fallback():
    """测试模型降级机制"""
    print("🧪 测试LLM模型降级机制")
    print("=" * 50)
    
    # 测试参数
    test_params = {
        "text": "请介绍人工智能的基本概念",
        "result_dir": "test_output",
        "user_id": "test_user",
        "style": "绘本",
        "template": "通用",
        "voice": "语音1（男）",
        "is_prompt_mode": True,
        "json_retry_times": 2,
        "task_id": "test_task_123",
        "generation_status": {"test_task_123": {"status": "processing", "logs": []}}
    }
    
    # 创建测试目录
    os.makedirs("test_output", exist_ok=True)
    
    # 测试场景1: 正常模型工作
    print("\n📱 测试场景1: 使用正常工作的模型")
    print("-" * 40)
    
    try:
        result = await run_work_flow_v3_with_progress(
            **test_params,
            llm_model_str="deepseek-reasoner"  # 使用稳定的模型
        )
        if result:
            print("✅ 正常模型测试成功")
        else:
            print("❌ 正常模型测试失败")
    except Exception as e:
        print(f"❌ 正常模型测试异常: {str(e)}")
    
    # 测试场景2: 使用可能失败的Gemini模型（测试降级）
    print("\n🔄 测试场景2: 使用Gemini模型（可能触发降级）")
    print("-" * 40)
    
    try:
        result = await run_work_flow_v3_with_progress(
            **test_params,
            llm_model_str="gemini-2.5-flash"  # 可能超时的模型
        )
        if result:
            print("✅ Gemini模型或降级模型测试成功")
        else:
            print("❌ Gemini模型和降级模型都失败")
    except Exception as e:
        print(f"❌ Gemini模型测试异常: {str(e)}")
        # 检查是否包含降级信息
        if "降级模型" in str(e):
            print("🔍 检测到降级尝试，符合预期")
        else:
            print("⚠️ 未检测到降级尝试")
    
    # 测试场景3: 使用不存在的模型（必然触发降级）
    print("\n🚨 测试场景3: 使用不存在的模型（必然触发降级）")
    print("-" * 40)
    
    try:
        result = await run_work_flow_v3_with_progress(
            **test_params,
            llm_model_str="nonexistent-model"  # 不存在的模型
        )
        if result:
            print("✅ 降级到deepseek-reasoner成功")
        else:
            print("❌ 降级失败")
    except Exception as e:
        error_msg = str(e)
        print(f"❌ 测试异常: {error_msg}")
        
        # 分析错误信息
        if "降级模型" in error_msg and "deepseek-reasoner" in error_msg:
            print("✅ 检测到正确的降级机制运行")
        elif "Model not found" in error_msg:
            print("⚠️ 模型未找到错误，这是预期的第一步")
        else:
            print("❓ 未检测到预期的降级机制")

def test_individual_model_initialization():
    """测试单独的模型初始化"""
    print("\n🔧 测试单独模型初始化")
    print("-" * 30)
    
    from service.ai_service import LLMService
    
    test_models = [
        "deepseek-reasoner",
        "gemini-2.5-flash", 
        "nonexistent-model"
    ]
    
    for model in test_models:
        try:
            print(f"测试模型: {model}")
            llm = LLMService(model_str=model)
            print(f"✅ {model} 初始化成功")
        except Exception as e:
            print(f"❌ {model} 初始化失败: {str(e)}")

async def test_error_message_format():
    """测试错误信息格式"""
    print("\n📝 测试错误信息格式")
    print("-" * 25)
    
    # 模拟一个简单的降级测试
    from service.ai_service import LLMService
    
    primary_model = "gemini-2.5-flash"
    fallback_model = "deepseek-reasoner"
    
    try:
        print(f"尝试使用主模型: {primary_model}")
        llm = LLMService(model_str=primary_model)
        
        # 模拟一个可能失败的调用
        messages = [{"role": "user", "content": "测试" * 1000}]  # 长文本可能导致超时
        result = llm.generate(messages)
        print(f"✅ 主模型成功: {len(result)}字符")
        
    except Exception as primary_error:
        print(f"❌ 主模型失败: {str(primary_error)}")
        
        try:
            print(f"🔄 尝试降级模型: {fallback_model}")
            llm_fallback = LLMService(model_str=fallback_model)
            
            messages = [{"role": "user", "content": "请简单说'测试成功'"}]  # 简化请求
            result = llm_fallback.generate(messages)
            print(f"✅ 降级模型成功: {result}")
            
        except Exception as fallback_error:
            print(f"❌ 降级模型也失败: {str(fallback_error)}")
            print(f"🔍 组合错误信息: 主模型({primary_model})失败: {str(primary_error)}; 降级模型({fallback_model})失败: {str(fallback_error)}")

async def main():
    """主测试函数"""
    print("🧪 LLM模型降级机制测试套件")
    print("=" * 50)
    
    # 检查环境
    required_keys = ["DEEPSEEK_API_KEY", "GEMINI_API_KEY"]
    missing_keys = [key for key in required_keys if not os.environ.get(key)]
    
    if missing_keys:
        print(f"❌ 缺少环境变量: {', '.join(missing_keys)}")
        print("某些测试可能无法运行")
    
    # 1. 测试单独模型初始化
    test_individual_model_initialization()
    
    # 2. 测试错误信息格式
    await test_error_message_format()
    
    # 3. 测试完整工作流降级机制
    await test_model_fallback()
    
    print("\n" + "=" * 50)
    print("🏁 测试完成")
    
    print("\n💡 预期行为:")
    print("1. 当主模型失败时，自动尝试deepseek-reasoner")
    print("2. 降级成功时，继续完成任务")
    print("3. 降级也失败时，提供详细错误信息")
    print("4. 错误日志清晰显示降级过程")

if __name__ == "__main__":
    asyncio.run(main())