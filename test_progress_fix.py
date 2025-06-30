#!/usr/bin/env python3
"""
测试进度追踪和视频加载修复
"""

import requests
import time
import json

def test_progress_tracking():
    """测试进度追踪功能"""
    print("=== 测试进度追踪功能 ===")
    
    # 模拟登录
    session = requests.Session()
    
    # 登录
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    
    try:
        # 登录
        login_response = session.post('http://localhost:5002/login', data=login_data)
        if login_response.status_code != 200:
            print("❌ 登录失败")
            return False
        
        print("✅ 登录成功")
        
        # 创建测试视频生成任务
        video_data = {
            'prompt': '测试进度追踪的视频',
            'style': '绘本',
            'template': '通用',
            'mode': 'prompt',
            'estimated_credits': 1,
            'is_display_title': 'true',
            'user_name': '测试用户'
        }
        
        # 提交视频生成请求
        response = session.post('http://localhost:5002/api/generate-video-v3', data=video_data)
        
        if response.status_code != 200:
            print(f"❌ 提交视频生成失败: {response.status_code}")
            return False
        
        result = response.json()
        if not result.get('success'):
            print(f"❌ 视频生成请求失败: {result.get('message')}")
            return False
        
        video_id = result['video_id']
        print(f"✅ 视频生成任务已创建，ID: {video_id}")
        
        # 监控进度
        print("📊 开始监控进度...")
        max_attempts = 60  # 最多等待60次，每次2秒
        attempt = 0
        
        while attempt < max_attempts:
            # 获取视频状态
            status_response = session.get(f'http://localhost:5002/api/video-status/{video_id}')
            
            if status_response.status_code != 200:
                print(f"❌ 获取状态失败: {status_response.status_code}")
                break
            
            status_data = status_response.json()
            
            if not status_data.get('success'):
                print(f"❌ 状态查询失败: {status_data.get('message')}")
                break
            
            status = status_data.get('status')
            progress = status_data.get('progress', 0)
            message = status_data.get('message', '')
            current_step = status_data.get('current_step', 1)
            
            print(f"📈 步骤 {current_step}/7 - {message} ({progress}%)")
            
            if status == 'completed':
                print("🎉 视频生成完成！")
                
                # 测试视频信息获取
                info_response = session.get(f'http://localhost:5002/api/video-info/{video_id}')
                if info_response.status_code == 200:
                    info_data = info_response.json()
                    if info_data.get('success') and info_data.get('video_url'):
                        print(f"✅ 视频URL获取成功: {info_data['video_url']}")
                        return True
                    else:
                        print("❌ 视频URL获取失败")
                        return False
                else:
                    print("❌ 获取视频信息失败")
                    return False
                
            elif status in ['failed', 'error']:
                print(f"❌ 视频生成失败: {message}")
                return False
            
            attempt += 1
            time.sleep(2)
        
        print("⏰ 等待超时")
        return False
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {str(e)}")
        return False

def test_video_loading():
    """测试视频加载功能"""
    print("\n=== 测试视频加载功能 ===")
    
    session = requests.Session()
    
    # 登录
    login_data = {
        'username': 'admin',
        'password': 'admin123'
    }
    
    try:
        login_response = session.post('http://localhost:5002/login', data=login_data)
        if login_response.status_code != 200:
            print("❌ 登录失败")
            return False
        
        # 获取我的视频列表
        videos_response = session.get('http://localhost:5002/my-videos')
        if videos_response.status_code != 200:
            print("❌ 获取视频列表失败")
            return False
        
        print("✅ 成功访问我的视频页面")
        
        # 这里可以添加更多的视频加载测试
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试进度追踪和视频加载修复")
    print("=" * 50)
    
    # 测试进度追踪
    progress_test = test_progress_tracking()
    
    # 测试视频加载
    loading_test = test_video_loading()
    
    print("\n" + "=" * 50)
    print("📋 测试结果汇总:")
    print(f"进度追踪功能: {'✅ 通过' if progress_test else '❌ 失败'}")
    print(f"视频加载功能: {'✅ 通过' if loading_test else '❌ 失败'}")
    
    if progress_test and loading_test:
        print("🎉 所有测试通过！")
        return True
    else:
        print("❌ 部分测试失败")
        return False

if __name__ == "__main__":
    main() 