#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workflow import generate_picture_from_json
from service.picture_generate_service import PictureGenerateService

async def test_generate_picture_from_json():
    """测试generate_picture_from_json函数"""
    
    print("测试generate_picture_from_json函数：")
    print("=" * 60)
    
    # 创建测试目录
    test_dir = "test_output/test_json_picture"
    os.makedirs(test_dir, exist_ok=True)
    
    # 模拟工作流记录
    work_flow_record = {
        "title": "测试标题：从JSON生成图片",
        "content": [
            {
                "voice_text": "这是第一段内容，用于测试JSON图片生成功能。",
                "json_text": "{\"scene\": \"办公室\", \"objects\": [\"电脑\", \"文件\", \"咖啡杯\"], \"style\": \"现代简约\"}"
            },
            {
                "voice_text": "这是第二段内容，继续测试JSON图片生成功能。",
                "json_text": "{\"scene\": \"户外公园\", \"objects\": [\"长椅\", \"树木\", \"小鸟\"], \"style\": \"自然风光\"}"
            },
            {
                "voice_text": "这是第三段内容，完成JSON图片生成功能测试。",
                "json_text": "{\"scene\": \"图书馆\", \"objects\": [\"书架\", \"书籍\", \"台灯\"], \"style\": \"学术氛围\"}"
            }
        ]
    }
    
    # 创建图片生成服务（这里需要根据实际的PictureGenerateService接口调整）
    # 注意：这里只是示例，实际使用时需要真实的API密钥和配置
    picture_generate_service = PictureGenerateService()
    
    try:
        # 测试生成图片
        result = await generate_picture_from_json(
            work_flow_record=work_flow_record,
            picture_generate_service=picture_generate_service,
            result_dir=test_dir,
            title_font_path="lib/font/AlibabaPuHuiTi-3-65-Medium.ttf",
            style="黑白矢量图",
            is_generate_title_picture=True,
            screen_size=(1280, 720)
        )
        
        print(f"✓ 成功生成工作流记录")
        print(f"  结果目录：{test_dir}")
        
        # 检查生成的文件
        if result and result.get('content'):
            print(f"\n生成的图片文件：")
            for i, item in enumerate(result['content']):
                if item.get('picture_path'):
                    for j, path in enumerate(item['picture_path']):
                        print(f"  - content[{i}] picture[{j}]: {path}")
                else:
                    print(f"  - content[{i}]: 未生成图片")
        
        # 检查标题图片
        if result.get('title_picture_path'):
            print(f"\n标题图片：{result['title_picture_path']}")
        else:
            print(f"\n标题图片：未生成")
            
        # 检查style字段
        print(f"\n样式：{result.get('style', '未设置')}")
        
    except Exception as e:
        print(f"✗ 测试失败：{str(e)}")
        print("注意：这可能是由于缺少API密钥或网络连接问题导致的")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("\n预期结果：")
    print("- 每个content项生成一张图片（0_0.png, 1_0.png, 2_0.png）")
    print("- 图片路径保存在picture_path数组中")
    print("- 如果启用标题图片，会使用第一张图片作为背景生成title.png")
    print("- 文件名格式保持与generate_picture兼容")

if __name__ == "__main__":
    asyncio.run(test_generate_picture_from_json()) 