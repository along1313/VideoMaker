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
from utility import parse_json
from workflow import generate_picture, generate_audio, add_time, generate_video

"""
work_flow_record = json.load(open("workstore/user1/森林深处的星光契约/work_flow_record.json", "r"))
style = "绘本"
result_dir = "workstore/user1"

generate_video(work_flow_record, style, result_dir, "lib/font/STHeiti Medium.ttc" ,"测试", bgm_path="lib/music/bgm.wav")
"""

llm = LLMService()
script_service = ScriptService(llm)
script = script_service.generate_text("选择一个心理学效应生成一个短视频")
print(script)
json_data = script_service.generate_json(script)
print(f'******json_data*****')
print(json_data)
cleaned_json_data = parse_json(json_data)
print(f'******cleaned_json_data*****')
print(cleaned_json_data)

