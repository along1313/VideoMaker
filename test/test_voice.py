import sys
import os
import json
import requests
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service.ai_service import LLMService, ImageModelService, TTSModelService
import dashscope
from dashscope.audio.tts_v2 import *

#配置结果存储目录
result_dir = "./workstore"
user_id = "user1"

class TTSModelService:
    def __init__(self):
        self.api_key = os.environ.get("DASHSCOPE_API_KEY")
        dashscope.api_key = self.api_key
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY not found in environment variables")

    def generate(self, text: str, model_str: str="cosyvoice-v1", voice: str="longmiao", pitch_rate: float=1.0):
        synthesizer = SpeechSynthesizer(model=model_str, voice=voice, pitch_rate=pitch_rate)
        audio = synthesizer.call(text)
        return audio

tts_model = TTSModelService()
audio = tts_model.generate("你好，我是小美的小助手")
#保存音频
with open(os.path.join(result_dir, f"{user_id}_audio1.mp3"), "wb") as f:
    f.write(audio)
audio = tts_model.generate("很高兴为您服务")
#保存音频
with open(os.path.join(result_dir, f"{user_id}_audio2.mp3"), "wb") as f:
    f.write(audio)

    

class TTSModelService:
    def __init__(self, model_str: str="cosyvoice-v1", voice: str="longmiao", pitch_rate: float=1.0):
        self.api_key = os.environ.get("DASHSCOPE_API_KEY")
        dashscope.api_key = self.api_key
        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY not found in environment variables")
        self.synthesizer = SpeechSynthesizer(model=model_str, voice=voice, pitch_rate=pitch_rate)
        
    def generate(self, text: str):
        audio = self.synthesizer.call(text)
        return audio

   