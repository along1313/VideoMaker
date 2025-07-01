import sys
import os
import json
import requests
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service.ai_service import LLMService, ImageModelService, TTSModelService
import dashscope
from dashscope.audio.tts_v2 import *

text_list = [
    "今天,我们来读《西游记》这本书,这是一本非常有趣的书,它讲述了一个关于西游记的故事",
    "故事发生在唐朝,讲述了一个关于西游记的故事",
    "故事讲述了一只猴子,它非常聪明,它能够解决很多问题",
]

output_dir = "test/test_output"
tts_service = TTSModelService(model_str="gemini-2.5-flash-preview-tts")
for i, text in enumerate(text_list):
    output_path = os.path.join(output_dir, f"test_{i}.mp3")
    data = tts_service.generate(text=text)
    tts_service.save_audio(data, output_path)