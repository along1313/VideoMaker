from moviepy.editor import AudioFileClip, ImageClip, VideoFileClip, CompositeVideoClip
from moviepy import ImageSequenceClip, AudioFileClip
import os
import json
import sys
import requests
import time
import dashscope
from PIL import Image
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utility import *
from service.ai_service import LLMService
from service.segment_srt_service import SegmentSRTService
from moviepy.video.tools.segmenting import ColorClip


# 计算出每个音频文件的时长
durations = get_audios_duration("workstore/user1/audios")
print(f"音频时长：{durations}")

# 读取字幕
subtitle_path = os.path.join("workstore", "user1", "subtitles", "subtitle.json")
with open(subtitle_path, "r") as f:
    subtitle = json.load(f)["display_text"]
print(f"字幕json文件读取完成：{subtitle_path}")

# 将subtitle转换成字幕文件,subtitle变量是一个带字幕的数组
gap = 1.0 # 每个字幕之间的间隔
subtitle_dir = os.path.join("workstore", "user1", "subtitles")
subtitle_path = os.path.join(subtitle_dir, f"subtitle.srt")

# 调用generate_srt生成字幕文件
generate_srt(subtitle, durations, subtitle_path, gap)
print(f"字幕文件生成完成：{subtitle_path}")

# 读取subtitle.srt文件
with open(subtitle_path, "r") as f:
    subtitle = f.read()


"""
# 调用SegmentSrtService生成字幕文件
llm = LLMService("glm-z1-air")
segment_srt_service = SegmentSRTService(llm)
segmented_srt = segment_srt_service.segment(subtitle)
print(f"分割后的字幕：{segmented_srt}")

# 提取srt文件
segmented_srt = extract_srt(segmented_srt)

segmented_srt_path = os.path.join(subtitle_dir, f"segmented.srt")
with open(segmented_srt_path, "w", encoding="utf-8") as f:
    f.write(segmented_srt)
print(f"分割后的字幕文件生成完成：{segmented_srt_path}")
"""

# 生成标题图片
title_text = "价格锚定效应：为何我们总被数字操控"
image_dir = os.path.join("workstore", "user1", "images")
image_path = os.path.join(image_dir, f"title.png")
generate_word_image(title_text, image_path)

duration = 0

for t in durations:
    duration += t
    duration += gap

print(f"视频总时长：{duration}")

imageclips = []

background = ImageClip("background.png", duration=duration)
imageclips.append(background)
# 获取workstore/user1/images目录下除了title.png之外的图片的路径，并按文件名数字大小排列
image_files = [f for f in os.listdir(image_dir) if f.endswith(".png") and f != "title.png"]
image_files.sort(key=lambda x: int(x.split(".")[0]))
image_paths = [os.path.join(image_dir, f) for f in image_files]

overlay_image = ImageClip("workstore/user1/images/title.png")
overlay_image = overlay_image.set_start(0).set_duration(durations[0] + gap).set_position("center")
imageclips.append(overlay_image)

start = durations[0] + gap

for t in durations[1:]:
    overlay_image = ImageClip(image_paths.pop(0))
    overlay_image = overlay_image.set_start(start).set_duration(t + gap).set_position("center")
    imageclips.append(overlay_image)
    start += t + gap

final = CompositeVideoClip(
    [imageclips],
    size=(1280, 720)
)

video_path = os.path.join("workstore", "user1", "video.mp4")
final.write_videofile(video_path, fps=24)
print(f"视频生成完成：{video_path}")














