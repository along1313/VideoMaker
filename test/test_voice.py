import sys
import os
import json
import requests
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service.ai_service import LLMService, ImageModelService, TTSModelService
from service.script_service import ScriptService
from service.tts_text_service import TTSTextService
from service.picture_prompt_service import PicturePromptService
from service.picture_generate_service import PictureGenerateService
from service.voice_generate_service import VoiceGenerateService
from utility import parse_markdown_json

#配置结果存储目录
result_dir = "./workstore"
user_id = "user1"

# 实例化模型
llm = LLMService()
image_model = ImageModelService()
tts_model = TTSModelService()


# 生成视频脚本
print(f'*' * 20,'script',f'*' * 20)
script_service = ScriptService(llm)
script = script_service.generate("选择一个心理学效应制作一个7分钟的短视频")
print(script)

# 生成TTS文本
print(f'*' * 20,'tts文本',f'*' * 20)
tts_service = TTSTextService(llm)
tts_texts = tts_service.generate(script)
print(tts_texts)

# 生成语音
print(f'*' * 20,'voice',f'*' * 20)
voice_generate_service = VoiceGenerateService(tts_model)
tts_text_array = json.loads(parse_markdown_json(tts_texts))['TTS_text']

print(type(tts_text_array))
for i, text in enumerate(tts_text_array):
    print(f"Processing {i} {text}...", end=" ")
    print(f"Processing {i} {type(text)}")

   