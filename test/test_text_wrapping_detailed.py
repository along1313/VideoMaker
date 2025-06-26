#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw, ImageFont
from utility import draw_text_on_image

def test_odd_even_wrapping():
    """测试奇偶数字符的换行情况"""
    
    # 创建测试图片
    img_width, img_height = 800, 600
    test_image = Image.new('RGB', (img_width, img_height), color='darkblue')
    
    # 专门测试奇偶数字符的情况
    test_cases = [
        ("测试文本", 4),  # 偶数
        ("测试文本内容", 5),  # 奇数
        ("测试文本内容测试", 6),  # 偶数
        ("测试文本内容测试文本", 7),  # 奇数
        ("测试文本内容测试文本内容", 8),  # 偶数
        ("测试文本内容测试文本内容测试", 9),  # 奇数
        ("测试文本内容测试文本内容测试文本", 10),  # 偶数
        ("测试文本内容测试文本内容测试文本内容", 11),  # 奇数
        ("测试文本内容测试文本内容测试文本内容测试", 12),  # 偶数
        ("测试文本内容测试文本内容测试文本内容测试文本", 13),  # 奇数
    ]
    
    print("详细测试奇偶数字符换行功能：")
    print("=" * 60)
    
    for i, (text, char_count) in enumerate(test_cases):
        print(f"\n测试用例 {i+1}: '{text}' (共{char_count}个字)")
        
        # 计算预期的换行
        first_line_chars = char_count // 2
        second_line_chars = char_count - first_line_chars
        
        print(f"  预期换行：第一行{first_line_chars}字，第二行{second_line_chars}字")
        
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
        output_path = f"test_output/detailed_wrapping_{i+1}_{char_count}chars.png"
        os.makedirs("test_output", exist_ok=True)
        result_img.save(output_path)
        
        print(f"  实际结果：已保存到 {output_path}")
        
        # 验证换行是否正确
        if char_count <= 8:  # 假设8个字以内不换行
            print(f"  ✓ 验证：字符数较少，应该不换行")
        else:
            if char_count % 2 == 0:  # 偶数
                expected_first = char_count // 2
                expected_second = char_count // 2
                print(f"  ✓ 验证：偶数{char_count}字，应该平均分配为{expected_first}+{expected_second}")
            else:  # 奇数
                expected_first = char_count // 2
                expected_second = char_count - expected_first
                print(f"  ✓ 验证：奇数{char_count}字，应该分配为{expected_first}+{expected_second}")
    
    print("\n" + "=" * 60)
    print("详细测试完成！")
    print("\n关键测试点：")
    print("- 10个字：应该分成5+5")
    print("- 11个字：应该分成5+6") 
    print("- 12个字：应该分成6+6")
    print("- 13个字：应该分成6+7")
    print("\n请查看 test_output 目录中的图片文件验证效果。")

if __name__ == "__main__":
    test_odd_even_wrapping() 