import sys
import os
import json
from zhipuai import ZhipuAI
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service.ai_service import LLMService
from service.script_service import ScriptService
from service.tts_text_service import TTSTextService
from service.picture_prompt_service import PicturePromptService
from utility import parse_json

llm = LLMService()
script_service = ScriptService(llm)

script = script_service.generate("选择一个心理学效应制作一个3分钟的短视频")
print(f'*' * 50,'script',f'*' * 50)
print(script)

"""
print(f'*' * 50,'tts文本',f'*' * 50)
tts_service = TTSTextService(llm)
print(tts_service.generate(script))
"""

script = parse_json(script)

print(f'*' * 50,'picture_prompt',f'*' * 50)
picture_prompt_service = PicturePromptService(llm)
script = picture_prompt_service.generate(script)
print(script)

print(parse_json(script))



