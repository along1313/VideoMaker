#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw, ImageFont
from utility import draw_text_on_image

def test_text_wrapping():
    """测试文字换行功能"""
    
    # 创建测试图片
    img_width, img_height = 800, 600
    test_image = Image.new('RGB', (img_width, img_height), color='darkblue')
    
    # 测试用例
    test_cases = [
        "这是一个测试文本",  # 8个字
        "这是一个测试文本内容",  # 9个字
        "这是一个测试文本内容测试",  # 10个字
        "这是一个测试文本内容测试文本",  # 11个字
        "这是一个测试文本内容测试文本内容",  # 12个字
        "这是一个测试文本内容测试文本内容测试",  # 13个字
        "这是一个测试文本内容测试文本内容测试文本",  # 14个字
        "这是一个测试文本内容测试文本内容测试文本内容",  # 15个字
    ]
    
    print("测试文字换行功能：")
    print("=" * 50)
    
    for i, text in enumerate(test_cases):
        print(f"\n测试用例 {i+1}: '{text}' (共{len(text)}个字)")
        
        # 创建测试图片副本
        test_img = test_image.copy()
        
        # 应用文字换行
        result_img = draw_text_on_image(
            test_img, 
            text, 
            font_path="lib/font/AlibabaPuHuiTi-3-65-Medium.ttf",
            font_size_to_width=0.08,
            fill_color="yellow",
            outline_color="black",
            stroke_width=2,
            margin=50
        )
        
        # 保存结果
        output_path = f"test_output/test_wrapping_{i+1}_{len(text)}chars.png"
        os.makedirs("test_output", exist_ok=True)
        result_img.save(output_path)
        
        # 分析换行结果
        if len(text) <= 8:  # 假设8个字以内不换行
            print(f"  预期：不换行，实际：已保存到 {output_path}")
        else:
            # 计算预期的换行
            first_line_chars = len(text) // 2
            second_line_chars = len(text) - first_line_chars
            print(f"  预期：第一行{first_line_chars}字，第二行{second_line_chars}字")
            print(f"  实际：已保存到 {output_path}")
    
    print("\n" + "=" * 50)
    print("测试完成！请查看 test_output 目录中的图片文件验证效果。")

if __name__ == "__main__":
    test_text_wrapping() 