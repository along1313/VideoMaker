#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
停止生成功能测试脚本
测试停止API和相关功能的完整性
"""

import requests
import time
import json
from dotenv import load_dotenv

load_dotenv()

def test_stop_functionality():
    """测试停止生成功能的完整流程"""
    
    print("🧪 开始测试停止生成功能...")
    
    # 创建会话
    session = requests.Session()
    base_url = 'http://localhost:5002'
    
    # 1. 测试登录
    print("\n📍 步骤1: 测试用户登录...")
    login_data = {
        'username': 'admin',  # 使用admin账户测试
        'password': 'admin123'
    }
    
    login_response = session.post(f'{base_url}/login', data=login_data)
    
    if login_response.status_code != 200:
        print("❌ 登录失败，请检查用户名和密码")
        return False
    
    # 检查登录是否成功
    if 'login' in login_response.url:
        print("❌ 登录失败，账户或密码错误")
        return False
    
    print("✅ 登录成功")
    
    # 2. 启动视频生成任务
    print("\n📍 步骤2: 启动视频生成任务...")
    
    generation_data = {
        'prompt': '测试停止功能的简短视频',
        'style': '绘本',
        'template': '通用',
        'mode': 'prompt',
        'estimated_credits': '1',
        'is_display_title': 'false'
    }
    
    generate_response = session.post(f'{base_url}/api/generate-video-v3', data=generation_data)
    
    if generate_response.status_code != 200:
        print(f"❌ 启动生成失败: {generate_response.status_code}")
        return False
    
    generate_data = generate_response.json()
    
    if not generate_data.get('success'):
        print(f"❌ 启动生成失败: {generate_data.get('message')}")
        return False
    
    video_id = generate_data['video_id']
    print(f"✅ 视频生成任务已启动，视频ID: {video_id}")
    
    # 3. 等待一段时间让生成开始
    print("\n📍 步骤3: 等待生成开始...")
    time.sleep(5)
    
    # 4. 检查生成状态
    print("\n📍 步骤4: 检查生成状态...")
    status_response = session.get(f'{base_url}/api/video-status/{video_id}')
    
    if status_response.status_code == 200:
        status_data = status_response.json()
        if status_data.get('success'):
            print(f"✅ 当前状态: {status_data.get('status')}")
            print(f"   进度: {status_data.get('progress')}%")
            print(f"   消息: {status_data.get('message')}")
            print(f"   步骤: {status_data.get('current_step')}")
        else:
            print(f"❌ 获取状态失败: {status_data.get('message')}")
    else:
        print(f"❌ 状态请求失败: {status_response.status_code}")
    
    # 5. 测试停止功能
    print(f"\n📍 步骤5: 测试停止功能 (视频ID: {video_id})...")
    
    stop_response = session.post(f'{base_url}/api/stop-generation/{video_id}')
    
    if stop_response.status_code != 200:
        print(f"❌ 停止请求失败: {stop_response.status_code}")
        print(f"   响应内容: {stop_response.text}")
        return False
    
    stop_data = stop_response.json()
    
    if stop_data.get('success'):
        print("✅ 停止生成成功!")
        print(f"   消息: {stop_data.get('message')}")
        print(f"   任务已取消: {stop_data.get('task_cancelled')}")
        print(f"   返还额度: {stop_data.get('credits_returned')}")
        print(f"   当前余额: {stop_data.get('current_credits')}")
        
        # 显示清理结果
        files_cleaned = stop_data.get('files_cleaned', {})
        print(f"   文件清理结果:")
        print(f"     视频文件: {'✅' if files_cleaned.get('video_file') else '❌'}")
        print(f"     封面文件: {'✅' if files_cleaned.get('cover_file') else '❌'}")
        print(f"     项目目录: {'✅' if files_cleaned.get('project_dir') else '❌'}")
        
        if files_cleaned.get('errors'):
            print(f"   清理错误: {files_cleaned['errors']}")
        
    else:
        print(f"❌ 停止生成失败: {stop_data.get('message')}")
        return False
    
    # 6. 验证视频记录是否已删除
    print("\n📍 步骤6: 验证视频记录是否已删除...")
    
    # 再次检查状态应该返回404或视频不存在
    verify_response = session.get(f'{base_url}/api/video-status/{video_id}')
    
    if verify_response.status_code == 404:
        print("✅ 视频记录已正确删除")
    elif verify_response.status_code == 200:
        verify_data = verify_response.json()
        if not verify_data.get('success'):
            print("✅ 视频记录已正确删除")
        else:
            print("⚠️  视频记录可能仍然存在")
    
    print("\n🎉 停止生成功能测试完成!")
    return True

def test_api_endpoints():
    """测试相关API端点的可达性"""
    
    print("\n🔍 测试API端点可达性...")
    
    session = requests.Session()
    base_url = 'http://localhost:5002'
    
    # 测试主页
    try:
        response = session.get(base_url)
        if response.status_code == 200:
            print("✅ 主页可访问")
        else:
            print(f"❌ 主页访问失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 无法连接到服务器: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 百速AI视频生成 - 停止功能测试")
    print("=" * 60)
    
    # 首先测试服务器连接
    if not test_api_endpoints():
        print("\n❌ 服务器连接失败，请确保应用正在运行")
        exit(1)
    
    # 测试停止功能
    try:
        success = test_stop_functionality()
        
        if success:
            print("\n" + "=" * 60)
            print("✅ 所有测试通过！停止功能工作正常")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("❌ 部分测试失败，请检查日志")
            print("=" * 60)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        
    print("\n📝 测试说明:")
    print("   - 确保应用在 localhost:5002 运行")
    print("   - 确保有admin/admin123账户")
    print("   - 测试会启动一个真实的生成任务然后停止")
    print("   - 停止成功后会清理所有相关文件") 