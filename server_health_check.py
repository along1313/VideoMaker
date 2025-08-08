#!/usr/bin/env python3
"""
服务器健康检查脚本
用于在服务器部署后检查各种服务和配置的状态
"""

import os
import sys
import json
import requests
from pathlib import Path

def check_environment_variables():
    """检查关键环境变量"""
    print("=== 检查环境变量 ===")
    
    required_vars = [
        'ZHIPU_API_KEY',
        'DEEPSEEK_API_KEY', 
        'QWEN_API_KEY',
        'COSYVOICE_API_KEY',
        'SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
            print(f"❌ {var}: 未设置")
        else:
            # 只显示前4个字符以保护敏感信息
            masked_value = value[:4] + "*" * (len(value) - 4) if len(value) > 4 else "****"
            print(f"✅ {var}: {masked_value}")
    
    if missing_vars:
        print(f"\n⚠️  警告：缺少 {len(missing_vars)} 个环境变量")
        return False
    else:
        print("\n✅ 所有环境变量已正确设置")
        return True

def check_file_permissions():
    """检查文件权限"""
    print("\n=== 检查文件权限 ===")
    
    check_paths = [
        'workstore',
        'logs',
        'instance',
        'static',
        'templates'
    ]
    
    for path in check_paths:
        if os.path.exists(path):
            if os.access(path, os.R_OK | os.W_OK):
                print(f"✅ {path}: 读写权限正常")
            else:
                print(f"❌ {path}: 权限不足")
                return False
        else:
            print(f"⚠️  {path}: 目录不存在")
    
    return True

def check_python_modules():
    """检查Python模块"""
    print("\n=== 检查Python模块 ===")
    
    required_modules = [
        'flask',
        'flask_sqlalchemy',
        'flask_login',
        'moviepy',
        'requests',
        'openai',
        'zhipuai',
        'PIL',
        'numpy'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}: 已安装")
        except ImportError:
            missing_modules.append(module)
            print(f"❌ {module}: 未安装")
    
    if missing_modules:
        print(f"\n⚠️  警告：缺少 {len(missing_modules)} 个Python模块")
        print("请运行: pip install -r requirements.txt")
        return False
    
    return True

def check_ai_services():
    """检查AI服务连通性"""
    print("\n=== 检查AI服务连通性 ===")
    
    # 这里只做基本的配置检查，避免实际调用API
    services = {
        'ZHIPU_API_KEY': '智谱AI',
        'DEEPSEEK_API_KEY': 'DeepSeek',
        'QWEN_API_KEY': '通义千问',
        'COSYVOICE_API_KEY': 'CosyVoice'
    }
    
    for key, name in services.items():
        if os.getenv(key):
            print(f"✅ {name}: API Key已配置")
        else:
            print(f"❌ {name}: API Key未配置")
    
    return True

def check_database():
    """检查数据库"""
    print("\n=== 检查数据库 ===")
    
    db_path = 'instance/baisu_video.db'
    if os.path.exists(db_path):
        print(f"✅ 数据库文件存在: {db_path}")
        
        # 检查文件大小
        size = os.path.getsize(db_path)
        print(f"📊 数据库大小: {size} bytes")
        
        if size > 0:
            print("✅ 数据库非空")
            return True
        else:
            print("⚠️  数据库为空，可能需要初始化")
            return False
    else:
        print(f"❌ 数据库文件不存在: {db_path}")
        return False

def check_service_health():
    """检查服务健康状态"""
    print("\n=== 检查服务健康状态 ===")
    
    try:
        # 尝试导入关键模块
        sys.path.insert(0, os.getcwd())
        
        from service.ai_service import LLMService, ImageModelService, TTSModelService
        print("✅ AI服务模块导入成功")
        
        # 尝试实例化服务（不实际调用API）
        try:
            llm = LLMService(model_str="deepseek-reasoner")
            print("✅ LLM服务实例化成功")
        except Exception as e:
            print(f"❌ LLM服务实例化失败: {str(e)}")
        
        try:
            image_model = ImageModelService(model_str="image-01")
            print("✅ 图片生成服务实例化成功")
        except Exception as e:
            print(f"❌ 图片生成服务实例化失败: {str(e)}")
        
        try:
            tts_model = TTSModelService(model_str="cosyvoice-v1")
            print("✅ TTS服务实例化成功")
        except Exception as e:
            print(f"❌ TTS服务实例化失败: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 服务模块导入失败: {str(e)}")
        return False

def generate_report():
    """生成健康检查报告"""
    print("\n" + "="*50)
    print("服务器健康检查报告")
    print("="*50)
    
    checks = [
        ("环境变量", check_environment_variables),
        ("文件权限", check_file_permissions),
        ("Python模块", check_python_modules),
        ("AI服务", check_ai_services),
        ("数据库", check_database),
        ("服务健康", check_service_health)
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"❌ {name}检查失败: {str(e)}")
            results[name] = False
    
    print("\n" + "="*50)
    print("检查结果摘要:")
    print("="*50)
    
    total_checks = len(results)
    passed_checks = sum(1 for r in results.values() if r)
    
    for name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")
    
    print(f"\n总体状态: {passed_checks}/{total_checks} 项检查通过")
    
    if passed_checks == total_checks:
        print("🎉 所有检查通过！服务器状态良好")
        return True
    else:
        print("⚠️  存在问题，请检查上述失败项目")
        return False

if __name__ == "__main__":
    print("百速AI视频生成系统 - 服务器健康检查")
    print("="*50)
    
    success = generate_report()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)