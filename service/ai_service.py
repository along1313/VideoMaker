from zhipuai import ZhipuAI
from openai import OpenAI
import dashscope
from dashscope.audio.tts_v2 import *
from http import HTTPStatus
from urllib.parse import urlparse, unquote
from pathlib import PurePosixPath
import requests
from dashscope import ImageSynthesis
import os
import time
from dotenv import load_dotenv
from static.model_info import ZHIPU_MODELS, DASHSCOPE_MODELS, DEEPSEEK_MODELS   
import asyncio



load_dotenv()

class LLMService:
    """
    大语言模型服务
    """
    def __init__(self, model_str: str="glm-z1-flash"):
        if model_str in DEEPSEEK_MODELS:
            self.api_key = os.environ.get("DEEPSEEK_API_KEY")
            if not self.api_key:
                raise ValueError("DEEPSEEK_API_KEY not found in environment variables")
            self.client = OpenAI(api_key=self.api_key, base_url="https://api.deepseek.com")
            self.model_str = model_str
        elif model_str in ZHIPU_MODELS:
            self.api_key = os.environ.get("ZHIPU_API_KEY")
            if not self.api_key:
                raise ValueError("ZHIPU_API_KEY not found in environment variables")
            self.client = ZhipuAI(api_key=self.api_key)
            self.model_str = model_str
        else:
            raise ValueError("Model not found")
        print(f'LLMService: {self.model_str}')
        
    def generate(self, messages: list[dict[str, str]], get_only_answer: bool=True, **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=self.model_str,
            messages=messages,
            **kwargs
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
    """
    图像模型服务
    """
    def __init__(self, model_str: str="cogview-3-flash"):
        if model_str in ZHIPU_MODELS:
            self.api_key = os.environ.get("ZHIPU_API_KEY")
            if not self.api_key:
                raise ValueError("ZHIPU_API_KEY not found in environment variables")
            self.client = ZhipuAI(api_key=self.api_key)
            self.model_str = model_str
        elif model_str in DASHSCOPE_MODELS:
            self.api_key = os.environ.get("DASHSCOPE_API_KEY")
            if not self.api_key:
                raise ValueError("DASHSCOPE_API_KEY not found in environment variables")
            self.model_str = model_str
        else:
            raise ValueError("Model not found")
        
    async def generate(self, prompt: str, size ="1024x1024" ,**kwargs):
        """
        异步生成图片
        :param prompt: 图片生成提示词
        :param size: 图片尺寸
        :param **kwargs: 其他参数
        :return: 生成的图片URL
        """
        if self.model_str in ZHIPU_MODELS:
            #如果传入的size参数里面包含*，则将其替换为x
            if "*" in size:
                size = size.replace("*", "x")
            try:
                response = await asyncio.to_thread(
                    self.client.images.generations,
                    model=self.model_str,
                    prompt=prompt,
                    size=size,
                    **kwargs
                )
                print("API response:", response)  # 打印原始响应
                return response.data[0].url
            except Exception as e:
                raise ValueError(f"智谱AI图片生成失败: {str(e)}")
                
        elif self.model_str in DASHSCOPE_MODELS:
            #如果传入的size参数里面包含x，则将其替换为*
            if "x" in size:
                size = size.replace("x", "*")
            try:
                response = await asyncio.to_thread(
                    ImageSynthesis.call,
                    api_key=self.api_key,
                    model=self.model_str, 
                    prompt=prompt, 
                    n=1,
                    size=size,
                    **kwargs
                )
                print("API response:", response)  # 打印原始响应
                if response.status_code == HTTPStatus.OK:
                    urls = []
                    for result in response.output.results:
                        urls.append(result.url)
                    if not urls:
                        raise ValueError(f"API未返回图片URL，原始响应: {response}")
                    return urls[0]
                else:
                    raise ValueError(f'通义千问图片生成失败, status_code: {response.status_code}, code: {response.code}, message: {response.message}')
            except Exception as e:
                raise ValueError(f"通义千问图片生成失败: {str(e)}，原始响应: {response if 'response' in locals() else '无响应'}")
        else:
            raise ValueError("Model not found")

    

class TTSModelService:
    """
    语音模型服务
    """
    def __init__(self, model_str: str= "cosyvoice-v1"):
        if model_str in DASHSCOPE_MODELS:
            self.api_key = os.environ.get("DASHSCOPE_API_KEY")
            if not self.api_key:
                raise ValueError("DASHSCOPE_API_KEY not found in environment variables")
            dashscope.api_key = self.api_key
        else:
            raise ValueError("Model not found")

    def generate(self, text: str, model_str: str="cosyvoice-v1", voice: str="longmiao", pitch_rate: float=1.0):
        synthesizer = SpeechSynthesizer(model=model_str, voice=voice, pitch_rate=pitch_rate)
        audio = synthesizer.call(text)
        return audio

class VideoModelService:
    """
    视频模型服务
    """
    def __init__(self, model_str: str="cogvideox-flash"):
        self.api_key = os.environ.get("ZHIPU_API_KEY")
        if not self.api_key:
            raise ValueError("ZHIPU_API_KEY not found in environment variables")
        self.client = ZhipuAI(api_key=self.api_key)
        self.model_str = model_str
        # 配置参数
        self.max_retries = 48  # 最大重试次数
        self.retry_interval = 5  # 重试间隔（秒）
        self.initial_wait = 30  # 初始等待时间（秒）

    async def generate(self, prompt: str, **kwargs) -> str:
        """
        异步生成视频并返回URL
        
        Args:
            prompt: 视频生成提示词
            **kwargs: 其他参数
            
        Returns:
            str: 生成的视频URL
            
        Raises:
            ValueError: 当视频生成失败时抛出
        """
        try:
            # 发起视频生成请求
            response = self.client.videos.generations(
                model=self.model_str,
                prompt=prompt,
                **kwargs
            )
            video_id = response.id
            print(f'视频生成中，视频id为：{video_id}')
            
            # 初始等待
            await asyncio.sleep(self.initial_wait)
            
            # 轮询检查视频生成状态
            for attempt in range(self.max_retries):
                result = await self._get_status(video_id)
                
                if result.task_status == 'SUCCESS':
                    return result.video_result[0].url
                elif result.task_status == 'FAILED':
                    raise ValueError(f'视频生成失败: {result.error_message if hasattr(result, "error_message") else "未知错误"}')
                
                print(f'视频生成中，已等待{(attempt + 1) * self.retry_interval + self.initial_wait}秒，视频id为：{video_id}')
                await asyncio.sleep(self.retry_interval)
            
            raise ValueError(f'视频生成超时，已等待{self.max_retries * self.retry_interval + self.initial_wait}秒')
            
        except Exception as e:
            raise ValueError(f'视频生成过程中发生错误: {str(e)}')

    async def _get_status(self, video_id: str):
        """
        异步获取视频生成状态
        
        Args:
            video_id: 视频ID
            
        Returns:
            视频生成状态结果
        """
        try:
            return self.client.videos.retrieve_videos_result(id=video_id)
        except Exception as e:
            raise ValueError(f'获取视频状态失败: {str(e)}')


