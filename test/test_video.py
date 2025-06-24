import sys
import os
import json
import requests
import time
import dashscope
from zhipuai import ZhipuAI
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service.ai_service import LLMService, ImageModelService, TTSModelService, VideoModelService
from service.script_service import ScriptService
from service.picture_prompt_service import PicturePromptService
from service.picture_generate_service import PictureGenerateService
from service.voice_generate_service import VoiceGenerateService
from utility import parse_json
from workflow import generate_picture, generate_audio, add_time, generate_video
from static.style_config import STYLE_CONFIG
import base64

img_path = "workstore/1/三只小猪/images/0_0.png"
with open(img_path, "rb") as f:
    img_data = base64.b64encode(f.read()).decode("utf-8")

video_model_service = VideoModelService()
prompt = "让图片中的景物有微风吹过的效果，人物细微的活动"
response = asyncio.run(video_model_service.generate(prompt, image_url=img_data))
print(response)