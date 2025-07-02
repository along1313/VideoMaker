from re import S
import sys
import os
import json
from dotenv import load_dotenv
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service.ai_service import LLMService, ImageModelService, TTSModelService, VideoModelService
from service.script_service import ScriptService
from service.picture_prompt_service import PicturePromptService
from service.picture_generate_service import PictureGenerateService
from service.voice_generate_service import VoiceGenerateService
from utility import parse_json, func_and_retry_parse_json
from workflow import generate_picture_from_json, generate_audio, add_time, generate_video, generate_cover
from static.style_config import TEMPLATE_CONFIG

text = "生成一个结合实际科普贝叶斯公式的问题"
json_retry_times = 3
result_dir = "test/test_output"
user_id = "test_user"
style = "绘本"
template = "通用"
screan_size = (1280, 720)
title_font_path = "lib/font/字制区喜脉体.ttf"
uploaded_title_picture_path = None
input_title_voice_text = None
kwargs = {}

print(f'#####Work Flow 1 生成视频脚本json####')
llm = LLMService("deepseek-reasoner")
script_service = ScriptService(llm)
work_flow_record = asyncio.run(func_and_retry_parse_json(text, script_service.generate_json_script_from_prompt, json_retry_times))
print(work_flow_record)

user_dir = os.path.join(result_dir, user_id)
os.makedirs(user_dir, exist_ok=True)
    
with open(os.path.join(user_dir, "work_flow_record.json"), "w") as f:
    json.dump(work_flow_record, f, ensure_ascii=False)

if work_flow_record is None:
    print(f'结构化失败, 超过{json_retry_times}次尝试')
    exit()

project_id = work_flow_record['title']
# 创建项目目录
project_dir = os.path.join(result_dir, user_id, project_id)
os.makedirs(project_dir, exist_ok=True)

# 初始化work_flow_record
work_flow_record['title_picture_path'] = ""
work_flow_record['title_voice_text'] = ""
work_flow_record['title_audio_path'] = ""

if template == "通用":
    template_config = TEMPLATE_CONFIG[template]['config']
elif template == "读一本书":
    template_config = TEMPLATE_CONFIG[template]['config']
    work_flow_record['title_picture_path'] = uploaded_title_picture_path
    work_flow_record['title_voice_text'] = f'今天,我们来读{input_title_voice_text}这本书'
elif template == "故事":
    template_config = TEMPLATE_CONFIG[template]['config']
    work_flow_record['title_voice_text'] = work_flow_record['title']
else:
    print(f'模板{template}不存在')
    exit()

print(f'#####Work Flow 2 生成插页####')
    #创建图片目录
image_dir = os.path.join(project_dir, "images")
os.makedirs(image_dir, exist_ok=True)

# 生成图片
image_model = ImageModelService("gemini-2.0-flash-preview-image-generation")
picture_generate_service = PictureGenerateService(image_model)
work_flow_record = asyncio.run(generate_picture_from_json(
    work_flow_record, 
    picture_generate_service, 
    image_dir, 
    style=style,
    title_font_path=title_font_path,
    screen_size=screan_size,      
    **template_config,
    **kwargs
))
print(work_flow_record)
with open(os.path.join(project_dir, "work_flow_record.json"), "w") as f:
    json.dump(work_flow_record, f, ensure_ascii=False)

