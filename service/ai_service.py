from zhipuai import ZhipuAI
import dashscope
from dashscope.audio.tts_v2 import *
import os
from dotenv import load_dotenv



load_dotenv()
class LLMService:
    def __init__(self, model_str: str="glm-z1-flash"):
        self.api_key = os.environ.get("ZHIPU_API_KEY")
        if not self.api_key:
            raise ValueError("ZHIPU_API_KEY not found in environment variables")
        self.client = ZhipuAI(api_key=self.api_key)
        self.model_str = model_str
        
    def generate(self, messages: list[dict[str, str]], max_tokens: int=32000, get_only_answer: bool=True) -> str:
        response = self.client.chat.completions.create(
            model=self.model_str,
            messages=messages,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content

        # 去除回答中的思考部分
        if get_only_answer:
            idx = content.find("</think>")
            if idx == -1:
                return content
            return content[idx+len("</think>"):].strip()
        return content

class ImageModelService:
    def __init__(self, model_str: str="cogview-3-flash"):
        self.api_key = os.environ.get("ZHIPU_API_KEY")
        if not self.api_key:
            raise ValueError("ZHIPU_API_KEY not found in environment variables")
        self.client = ZhipuAI(api_key=self.api_key)
        self.model_str = model_str
        
    def generate(self, prompt: str):
        response = self.client.images.generations(
            model=self.model_str,
            prompt=prompt,
        )
        return response.data[0].url

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

    def get_api_key(self):
        return dashscope.api_key

    def get_synthesizer(self):
        return self.synthesizer

        
        

