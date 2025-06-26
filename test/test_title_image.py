#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image
from workflow import generate_title_image_with_background
import asyncio

async def test_title_image_generation():
    """测试标题图片生成功能"""
    
    print("测试标题图片生成功能：")
    print("=" * 50)
    
    # 创建测试背景图片
    test_bg_path = "test_output/test_background.png"
    os.makedirs("test_output", exist_ok=True)
    
    # 创建一个简单的测试背景图片
    bg_image = Image.new('RGB', (1280, 720), color='darkblue')
    bg_image.save(test_bg_path)
    print(f"创建测试背景图片：{test_bg_path}")
    
    # 测试用例
    test_cases = [
        "这是一个测试标题",
        "测试标题文字内容",
        "这是一个很长的测试标题文字内容",
        "短标题",
        "这是一个测试标题文字内容测试标题文字内容测试标题文字内容"
    ]
    
    for i, title_text in enumerate(test_cases):
        print(f"\n测试用例 {i+1}: '{title_text}'")
        
        # 生成标题图片
        output_path = f"test_output/test_title_{i+1}.png"
        
        result = await generate_title_image_with_background(
            title_text=title_text,
            background_image_path=test_bg_path,
            output_path=output_path,
            font_path="lib/font/AlibabaPuHuiTi-3-65-Medium.ttf",
            screen_size=(1280, 720)
        )
        
        if result:
            print(f"  ✓ 成功生成标题图片：{output_path}")
        else:
            print(f"  ✗ 生成标题图片失败")
    
    print("\n" + "=" * 50)
    print("测试完成！请查看 test_output 目录中的图片文件验证效果。")
    print("\n预期效果：")
    print("- 背景图片为深蓝色")
    print("- 标题文字为黄色，带黑色描边")
    print("- 字体大小为屏幕高度的0.2")
    print("- 文字居中显示，支持自动换行")

if __name__ == "__main__":
    asyncio.run(test_title_image_generation()) 