from moviepy.editor import ImageClip, CompositeVideoClip, AudioFileClip, CompositeAudioClip, TextClip
import numpy as np
import json
import os
import sys

# 获取当前脚本的绝对路径
# Get the absolute path of the current script
current_script_path = os.path.abspath(__file__)
# 获取项目根目录 (假设 test1.py 在 test 目录下，项目根目录是 test 目录的上一级)
# Get the project root directory (assuming test1.py is in the test directory, the project root directory is the parent directory of the test directory)
project_root = os.path.dirname(os.path.dirname(current_script_path))
# 将项目根目录添加到 sys.path
# Add the project root directory to sys.path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from workflow import add_time

def generate_video(work_flow_record, result_dir, scream_size = (1280, 720), bg_pic_path='lib/img/background.png', font_path='lib/font/STHeiti Medium.ttc'):
    """
    生成视频的函数

    参数:
    work_flow_record (dict): 工作流记录，包含视频内容信息
    result_dir (str): 结果输出目录
    scream_size (tuple): 屏幕尺寸，默认为 (1280, 720)
    bg_pic_path (str): 背景图片路径，默认为 'lib/img/background.png'

    返回:
    ImageClip: 背景图片剪辑对象
    """
    print(f'*' * 10,'content',f'*' * 10)
    print(work_flow_record['content'][-1]['voice_time'])
    vedio_duration = work_flow_record['content'][-1]['voice_time'][0]+work_flow_record['content'][-1]['voice_time'][1]
    print(f'*' * 10,'vedio_duration',f'*' * 10)
    print(vedio_duration)
    # 初始化背景图片
    bg_clip  = ImageClip(bg_pic_path).with_duration(vedio_duration).resized(scream_size)

    # 生成图片剪辑表
    img_clips = []
    #先单独处理标题图片
    title_img_path = work_flow_record['title_picture_path']
    title_img_clip = ImageClip(title_img_path).with_start(work_flow_record['title_time'][0]).with_duration(work_flow_record['title_time'][1])
    img_clips.append(title_img_clip)

    # 生成图片剪辑
    # 定义透明度动态曲线函数
    def custom_fade(t):
        """透明度动态曲线：
        - 前0.5秒从0到1（淡入）
        - 最后0.5秒从1到0（淡出）
        - 中间保持不透明
        """
        if t < 0.5:  # 淡入阶段
            return t / 0.5
        elif t > (img_clip.duration - 0.5):  # 淡出阶段
            return 1 - (t - (img_clip.duration - 0.5)) / 0.5
        else:  # 保持阶段
            return 1.0
    for index, item in enumerate(work_flow_record['content']):
        for i in range(len(item['picture_path'])):
            img_path = item['picture_path'][i]
            img_clip = ImageClip(img_path).with_start(item['picture_time'][i][0]).with_duration(item['picture_time'][i][1])
            img_clip = img_clip.with_position(('center', 'center')).resized(0.4)
            #img_clip = img_clip.with_opacity(lambda t: custom_fade(t))
            img_clips.append(img_clip)

    # 生成字幕剪辑
    TEXT_STYLE = {
    "font_size": 45,
    "color": "black",
    # "font": "Arial-Bold",  # Windows系统黑体 (已移出)
    "size": (scream_size[0]-150, None)  # 限制文字宽度
    }

    caption_clips = []
    for index, item in enumerate(work_flow_record['content']):
        for i in range(len(item['caption_text'])):
            caption_text = item['caption_text'][i]
            caption_start_time = item['caption_time'][i][0]
            caption_duration_time = item['caption_time'][i][1]
            caption_clip = TextClip(font_path, caption_text, **TEXT_STYLE).with_start(caption_start_time).with_duration(caption_duration_time)
            caption_clip = caption_clip.with_position(('center', scream_size[1]-100))
            caption_clips.append(caption_clip)

    # 合并图片剪辑
    img_concat_clip = CompositeVideoClip([bg_clip]+img_clips+caption_clips, size = scream_size).with_duration(vedio_duration)

    # 生成音频剪辑
    audio_clips = []
    # 单独处理标题音频
    title_audio_path = work_flow_record['title_audio_path']
    title_audio_clip = AudioFileClip(title_audio_path).with_start(work_flow_record['title_time'][0]).with_duration(work_flow_record['title_time'][1])
    audio_clips.append(title_audio_clip)
    # 生成音频剪辑
    for index, item in enumerate(work_flow_record['content']):
        audio_path = item['audio_path']
        audio_start_time = item['voice_time'][0]
        audio_duration_time = item['voice_time'][1]
        audio_clip = AudioFileClip(audio_path).with_start(audio_start_time).with_duration(audio_duration_time)
        audio_clips.append(audio_clip)

    # 合并音频剪辑
    audio_concat_clip = CompositeAudioClip(audio_clips)
    # 合并音频和视频
    final_clip = img_concat_clip.with_audio(audio_concat_clip)

    # 输出视频文件
    output_path = os.path.join(result_dir, "output.mp4")
    final_clip.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")



    




work_flow_record = json.load(open('workstore/work_flow_record.json'))

work_flow_record = add_time(work_flow_record, "workstore/user1/你相信星座运势吗？/audios", 1.0)


result_dir = "workstore/user1/你相信星座运势吗？"
#保存work_flow_record
with open(os.path.join('workstore/user1/你相信星座运势吗？', "1.json"), "w") as f:
    json.dump(work_flow_record, f, ensure_ascii=False)

generate_video(work_flow_record, result_dir)


"""
img_clip = ImageClip('workstore/user1/你相信星座运势吗？/images/0_0.png') # 创建一个红色方块

print("--- 使用 dir(img_clip) ---")
# 打印所有属性和方法名
# 注意：这会列出很多内部方法（通常以下划线开头）和继承的方法

for item in dir(img_clip):
    print(item)

help(img_clip.)

print("\n--- 使用 help(ImageClip) --- (部分示例) ---")
# 显示 ImageClip 类的帮助信息 (可能会很长)
# help(ImageClip)

print("\n--- 使用 help(img_clip.with_duration) --- (示例) ---")
# 显示特定方法的帮助信息
help(img_clip.with_duration)

# 你也可以检查某个属性是否可调用（即是否为方法）
print("\n--- 可调用的方法示例 --- ")
for item_name in dir(img_clip):
    if not item_name.startswith('_'): # 过滤掉私有/魔法方法
        try:
            attr = getattr(img_clip, item_name)
            if callable(attr):
                print(f"{item_name}() is a method")
        except AttributeError:
            pass # 有些属性可能在某些情况下不可访问
"""



