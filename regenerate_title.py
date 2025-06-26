import os
import asyncio
from workflow import generate_title_image_with_background

async def regenerate_title_image():
    """
    重新生成标题图片
    """
    # 项目路径
    result_dir = "workstore/user1/三只小猪的智慧"
    
    # 读取工作流记录
    import json
    with open(os.path.join(result_dir, "work_flow_record.json"), "r", encoding="utf-8") as f:
        work_flow_record = json.load(f)
    
    # 获取标题文字
    title_text = work_flow_record['title']
    
    # 获取第一张正文图片作为背景
    background_image_path = work_flow_record['content'][0]['picture_path'][0]
    
    # 输出路径
    title_image_path = os.path.join(result_dir, "images", "title.png")
    
    # 字体路径
    font_path = "lib/font/字制区喜脉体.ttf"
    
    # 屏幕尺寸
    screen_size = (1280, 720)
    
    print(f"正在重新生成标题图片...")
    print(f"标题文字: {title_text}")
    print(f"背景图片: {background_image_path}")
    print(f"输出路径: {title_image_path}")
    
    # 生成标题图片
    result = await generate_title_image_with_background(
        title_text,
        background_image_path,
        title_image_path,
        font_path,
        screen_size
    )
    
    if result:
        print(f"标题图片生成成功: {result}")
    else:
        print("标题图片生成失败")

if __name__ == "__main__":
    asyncio.run(regenerate_title_image()) 