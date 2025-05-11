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

#读取workstore/work_flow_record.json
with open("workstore/work_flow_record.json", "r") as f:
    work_flow_record = json.load(f)

work_flow_record = add_time(work_flow_record, "workstore/user1/你相信星座运势吗？/audios", 1.0)
print(work_flow_record)

#将work_flow_record保存到文件中
with open("workstore/user1/你相信星座运势吗？/work_flow_record_add.json", "w") as f:
    json.dump(work_flow_record, f, ensure_ascii=False)