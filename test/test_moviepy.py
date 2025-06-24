from moviepy import ImageClip, CompositeVideoClip, AudioFileClip, CompositeAudioClip, TextClip
import numpy as np
import json
import os
import sys
from dotenv import load_dotenv

def img_y_slide(image_clip, screen_size, pan_speed, int_direction = "up"):
    """
    图片剪辑垂直平移
    :param image_clip: 图片剪辑
    :param screen_size: 屏幕大小
    :param pan_speed: 平移速度
    :param int_direction: 初始运动方向，"up"表示初始镜头向上（图片向下），"down"表示初始镜头向下（图片向上）
    :return: 平移后的图片剪辑
    """
    image_clip = image_clip.resized(width=screen_size[0])
    image_width, image_height = image_clip.size
    panable_height = image_height - screen_size[1]
    
    # 计算时间节点
    t1 = panable_height / 2 / pan_speed
    t2 = t1 + panable_height / pan_speed
    t3 = t2 + panable_height / 2 / pan_speed
    
    # 根据方向设置初始位置
    if int_direction == "up":
        # 初始镜头向上（图片向下）：从图片顶部开始
        initial_y = 0
    elif int_direction == "down":
        # 初始镜头向下（图片向上）：从图片底部开始
        initial_y = -panable_height
    else:
        # 默认使用原来的逻辑（中间开始）
        initial_y = -panable_height / 2
    
    def get_y_position(t):
        if int_direction == "up":
            # 镜头向上运动：图片向下移动
            if t < t1:
                return initial_y - pan_speed * t
            elif t < t2:
                return -panable_height / 2 + pan_speed * (t - t1)
            elif t < t3:
                return 0 - pan_speed * (t - t2)
            else:
                return -panable_height / 2
        elif int_direction == "down":
            # 镜头向下运动：图片向上移动
            if t < t1:
                return initial_y + pan_speed * t
            elif t < t2:
                return -panable_height / 2 - pan_speed * (t - t1)
            elif t < t3:
                return 0 + pan_speed * (t - t2)
            else:
                return -panable_height / 2
        else:
            # 原来的逻辑（从中间开始）
            if t < t1:
                return initial_y + pan_speed * t
            elif t < t2:
                return 0 - pan_speed * (t - t1)
            elif t < t3:
                return -panable_height + pan_speed * (t - t2)
            else:
                return -panable_height / 2
    
    image_clip = image_clip.with_position(lambda t: (0, get_y_position(t)))
    return image_clip


image_path = "workstore/user1/博弈论基石/images/0_0.png"
image_duration = 20
output_path = "test/test_output/output.mp4"
screen_size = (1024, 720)
pan_speed = 50

image_clip = ImageClip(image_path).with_duration(image_duration)

"""

image_width, image_height = image_clip.size

# 计算可平移的高度范围
panable_height = image_height - screen_size[1]


speed = panable_height / pan_duration

image_clip = image_clip.resized(width=screen_size[0])

initial_y = 0

def get_y_position(t):
    
    #根据时间 t 计算图像的垂直位置，实现往复平移效果。
    #y 坐标表示视频帧顶部边缘相对于图像顶部边缘的偏移。
    
    y_offset = speed * t

    if t < pan_duration:
        return initial_y - y_offset
    else:
        return  panable_height * -1
        
    
image_clip = image_clip.with_position(lambda t: (0, get_y_position(t)))
"""

semi_transparent_gray = (100, 100, 100, 128)

# 创建带有半透明灰色背景的 TextClip
subtitle_clip = TextClip(
    text = "这是一个半透明背景的字幕",
    font_size=50,
    color='white',
    bg_color=semi_transparent_gray, # 在这里设置背景色和透明度
    font='lib/font/NotoSansSC-Regular.ttf', # 确保您的系统有此字体或使用其他字体
    stroke_color='black', # 可选的描边
    stroke_width=0 # 可选的描边宽度
).with_duration(13).with_position(("center", "center")) # 放置在视频底部中心

user_name_clip = TextClip(
    font='lib/font/NotoSansSC-Regular.ttf', 
    text = '第二个测试字幕', font_size=35, color='white', stroke_color = 'black', stroke_width = 1).with_position((25, 50)).with_duration(15)

image_clip = img_y_slide(image_clip, screen_size, pan_speed)

# 测试不同滑动方向的示例（注释掉，需要时可以启用）
# image_clip_up = img_y_slide(image_clip, screen_size, pan_speed, int_direction="up")    # 镜头向上（图片向下）
# image_clip_down = img_y_slide(image_clip, screen_size, pan_speed, int_direction="down")  # 镜头向下（图片向上）

final_video = CompositeVideoClip([image_clip, subtitle_clip, user_name_clip], size=(screen_size[0], screen_size[1]))

final_video.write_videofile(output_path, fps=30)

print(f'视频生成完成')




