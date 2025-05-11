import sys
import os
import json
import requests
import time
import dashscope
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service.ai_service import LLMService, ImageModelService, TTSModelService
from service.script_service import ScriptService
from service.picture_prompt_service import PicturePromptService
from service.picture_generate_service import PictureGenerateService
from service.voice_generate_service import VoiceGenerateService
from utility import parse_json
from workflow import generate_picture, generate_audio, add_time

#配置结果存储目录
result_dir = "./workstore"
user_id = "user1"
project_id = ""

# 实例化模型
llm = LLMService()
image_model = ImageModelService()


#####Work Flow 1 视频生成####


# 生成视频脚本
print(f'*' * 20,'script',f'*' * 20)
script_service = ScriptService(llm)
work_flow_record = script_service.generate("选择一个心理学效应制作一个3分钟的短视频")
print(work_flow_record)

work_flow_record = parse_json(work_flow_record)

# 将work_flow_record保存到文件中
with open(os.path.join(result_dir, "work_flow_record.json"), "w") as f:
    json.dump(work_flow_record, f, ensure_ascii=False)

# 使用项目标题作为项目ID
project_id = work_flow_record['title']

"""
# 生成TTS文本
print(f'*' * 20,'tts文本',f'*' * 20)
tts_service = TTSTextService(llm)
tts_texts = tts_service.generate(script)
print(tts_texts)
"""

# 创建项目目录
project_dir = os.path.join(result_dir, user_id, project_id)
os.makedirs(project_dir, exist_ok=True)


#####Work Flow 2 插页prompt生成####

# 生成插页prompt
print(f'*' * 20,'picture_prompt',f'*' * 20)
picture_prompt_service = PicturePromptService(llm)
work_flow_record = picture_prompt_service.generate(work_flow_record)
print(work_flow_record)

work_flow_record = parse_json(work_flow_record)
# 将work_flow_record保存到文件中
with open(os.path.join(result_dir, "work_flow_record.json"), "w") as f:
    json.dump(work_flow_record, f, ensure_ascii=False)




#####Work Flow 3 图片生成####

#创建图片目录
image_dir = os.path.join(project_dir, "images")
os.makedirs(image_dir, exist_ok=True)


# 生成图片
print(f'*' * 20,'picture',f'*' * 20)
picture_generate_service = PictureGenerateService(image_model)
work_flow_record = generate_picture(work_flow_record, picture_generate_service, image_dir)
print(work_flow_record)
# 将work_flow_record保存到文件中
with open(os.path.join(result_dir, "work_flow_record.json"), "w") as f:
    json.dump(work_flow_record, f, ensure_ascii=False)


#####Work Flow 4 音频生成####

    
# 创建音频目录
audio_dir = os.path.join(project_dir, "audios")
os.makedirs(audio_dir, exist_ok=True)

# 生成语音
print(f'*' * 20,'voice',f'*' * 20)
work_flow_record = generate_audio(work_flow_record, audio_dir, pitch_rate=0.8)
print(work_flow_record)
# 将work_flow_record保存到文件中
with open(os.path.join(result_dir, "work_flow_record.json"), "w") as f:
    json.dump(work_flow_record, f, ensure_ascii=False)


#####Work Flow 5 音频时间添加####
# 增加时间
print(f'*' * 20,'time',f'*' * 20)
work_flow_record = add_time(work_flow_record, audio_dir, gap=1.0)
print(work_flow_record)
# 将work_flow_record保存到文件中
with open(os.path.join(result_dir, "work_flow_record.json"), "w") as f:
    json.dump(work_flow_record, f, ensure_ascii=False)

 










