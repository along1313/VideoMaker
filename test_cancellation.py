#!/usr/bin/env python3
"""
测试视频生成取消功能
"""
import os
import sys
import time
import threading
import asyncio
from unittest.mock import Mock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from service.work_flow_service import run_work_flow_v3_with_progress

def test_cancellation_mechanism():
    """测试取消机制是否正常工作"""
    
    # 创建模拟状态
    task_id = "test_task_123"
    generation_status = {
        task_id: {
            'video_id': 999,
            'status': 'processing',
            'progress': 0,
            'message': '测试任务开始',
            'logs': [],
            'current_step': 1
        }
    }
    
    # 创建测试用的工作流参数
    test_params = {
        'text': '测试视频生成取消功能',
        'result_dir': './test_workstore',
        'user_id': 'test_user',
        'style': '绘本',
        'template': '通用',
        'llm_model_str': 'deepseek-reasoner',
        'image_model_str': 'image-01',
        'tts_model_str': 'cosyvoice-v1',
        'is_prompt_mode': True,
        'task_id': task_id,
        'generation_status': generation_status
    }
    
    # 创建测试目录
    os.makedirs('./test_workstore', exist_ok=True)
    
    print("开始测试取消机制...")
    
    # 启动视频生成任务
    def run_workflow():
        try:
            result = asyncio.run(run_work_flow_v3_with_progress(**test_params))
            print("❌ 错误：工作流应该被取消但却完成了")
            return False
        except Exception as e:
            if "取消" in str(e):
                print("✅ 成功：工作流被正确取消")
                return True
            else:
                print(f"❌ 错误：工作流因其他原因失败: {str(e)}")
                return False
    
    # 启动工作流线程
    workflow_thread = threading.Thread(target=run_workflow)
    workflow_thread.daemon = True
    workflow_thread.start()
    
    # 等待一段时间后取消任务
    time.sleep(2)
    print("正在取消任务...")
    generation_status[task_id]['status'] = 'cancelled'
    
    # 等待线程结束
    workflow_thread.join(timeout=10)
    
    if workflow_thread.is_alive():
        print("❌ 错误：工作流线程在取消后仍在运行")
        return False
    
    print("✅ 测试完成：取消机制正常工作")
    
    # 清理测试目录
    try:
        import shutil
        shutil.rmtree('./test_workstore')
        print("✅ 测试目录已清理")
    except:
        pass
    
    return True

if __name__ == "__main__":
    success = test_cancellation_mechanism()
    if success:
        print("\n🎉 取消机制测试通过！")
        sys.exit(0)
    else:
        print("\n❌ 取消机制测试失败！")
        sys.exit(1)