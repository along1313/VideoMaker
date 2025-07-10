from zhipuai import ZhipuAI
from openai import OpenAI
from google import genai
from google.genai import types
import wave
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
from static.model_info import ZHIPU_MODELS, DASHSCOPE_MODELS, DEEPSEEK_MODELS, GEMINI_MODELS, MINIMAX_MODELS   
import asyncio
import tempfile
from google.genai import types
from PIL import Image
from io import BytesIO


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
        elif model_str in GEMINI_MODELS:
            self.api_key = os.environ.get("GEMINI_API_KEY")
            if not self.api_key:
                raise ValueError("GEMINI_API_KEY not found in environment variables")
            self.client = genai.Client(api_key=self.api_key)
            self.model_str = model_str
        else:
            raise ValueError("Model not found")
        print(f'LLMService: {self.model_str}')
        
    def generate(self, messages: list[dict[str, str]], get_only_answer: bool=True, **kwargs) -> str:
        if self.model_str in GEMINI_MODELS:
            # 转换 OpenAI 格式的消息为 Gemini 格式
            contents = self._convert_messages_to_gemini_format(messages)
            print(f'Gemini contents: {contents}')
            response = self.client.models.generate_content(
                model=self.model_str,
                contents=contents,
                **kwargs
            )
            return response.text
        else:
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
    
    def _convert_messages_to_gemini_format(self, messages: list[dict[str, str]]) -> list:
        """
        将 OpenAI 格式的消息转换为 Gemini 格式
        """
        gemini_contents = []
        
        for message in messages:
            role = message.get("role", "")
            content = message.get("content", "")
            
            if role == "system":
                # Gemini 通常将 system 消息合并到用户消息中
                gemini_contents.append(f"系统指令: {content}")
            elif role == "user":
                gemini_contents.append(content)
            elif role == "assistant":
                # 如果有助手消息，也添加为内容
                gemini_contents.append(f"助手回复: {content}")
            else:
                # 其他类型的消息直接添加内容
                gemini_contents.append(content)
        
        # 如果有多个内容，合并为一个字符串
        if len(gemini_contents) > 1:
            return "\n\n".join(gemini_contents)
        elif len(gemini_contents) == 1:
            return gemini_contents[0]
        else:
            return ""



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
        elif model_str in GEMINI_MODELS:
            self.api_key = os.environ.get("GEMINI_API_KEY")
            if not self.api_key:
                raise ValueError("GEMINI_API_KEY not found in environment variables")
            self.client = genai.Client(api_key=self.api_key)
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
            
        elif self.model_str in GEMINI_MODELS:
            response = self.client.models.generate_content(
                model=self.model_str,
                contents=f'按如下要求生成一张{size}的图片: {prompt}',
                config=types.GenerateContentConfig(
                    response_modalities=['TEXT', 'IMAGE'],
                )
            )
            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    print(part.text)
                elif part.inline_data is not None:
                    image = Image.open(BytesIO((part.inline_data.data)))
                    return image
        else:
            raise ValueError("Model not found")
        
    async def save_image(self, image_or_url, file_path: str):
        if self.model_str in ZHIPU_MODELS:
            # 如果image_or_url是url，则下载图片
            if isinstance(image_or_url, str):
                response = requests.get(image_or_url)
                image = Image.open(BytesIO(response.content))
                image.save(file_path)
            else:
                image_or_url.save(file_path)
        elif self.model_str in GEMINI_MODELS:
            image_or_url.save(file_path)
        else:
            raise ValueError("Model not found")

    
def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
   with wave.open(filename, "wb") as wf:
      wf.setnchannels(channels)
      wf.setsampwidth(sample_width)
      wf.setframerate(rate)
      wf.writeframes(pcm)


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
            self.voice_list = []
        elif model_str in GEMINI_MODELS:
            self.api_key = os.environ.get("GEMINI_API_KEY")
            if not self.api_key:
                raise ValueError("GEMINI_API_KEY not found in environment variables")
            self.client = genai.Client(api_key=self.api_key)
            self.voice_list = ["Zephyr", "Puck", "Charon", "Kore", "Fenrir", "Leda", "Orus", "Aoede", "Callirhoe", "Autonoe", "Enceladus", "Iapetus", "Umbriel", "Algieba", "Despina", "Erinome", "Algenib", "Rasalgethi", "Laomedeia", "Achernar", "Alnilam", "Schedar", "Gacrux", "Pulcherrima", "Achird", "Zubenelgenubi", "Vindemiatrix", "Sadachbia", "Sadaltager", "Sulafar"]
        elif model_str in MINIMAX_MODELS:
            self.api_key = os.environ.get("MINIMAX_API_KEY")
            self.group_id = os.environ.get("MINIMAX_GROUP_ID")
            if not self.api_key or not self.group_id:
                raise ValueError("MINIMAX_API_KEY and MINIMAX_GROUP_ID must be set in environment variables")
            self.voice_list = [
                "Chinese (Mandarin)_Lyrical_Voice",
                "Chinese (Mandarin)_Wise_Women_Voice",
            ]
        else:
            raise ValueError("Model not found")
        self.model_str = model_str

    def generate(self, text: str, style_instructions = "say", voice_name = "Zephyr", **kwargs):
        # @param ["Zephyr", "Puck", "Charon", "Kore", "Fenrir", "Leda", "Orus", "Aoede", "Callirhoe", "Autonoe", "Enceladus", "Iapetus", "Umbriel", "Algieba", "Despina", "Erinome", "Algenib", "Rasalgethi", "Laomedeia", "Achernar", "Alnilam", "Schedar", "Gacrux", "Pulcherrima", "Achird", "Zubenelgenubi", "Vindemiatrix", "Sadachbia", "Sadaltager", "Sulafar"]
        print(f'voice_name: {voice_name}')
        if self.model_str in DASHSCOPE_MODELS:
            if voice_name == "default":
                voice_name = "longmiao"
            synthesizer = SpeechSynthesizer(model=self.model_str, voice= voice_name, **kwargs)
            audio = synthesizer.call(text)
            return audio
        elif self.model_str in GEMINI_MODELS:
            response = self.client.models.generate_content(
                model=self.model_str,
                contents=f'{style_instructions}: {text}',
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice_name,
                            )
                        )
                    ),
                )
                )
            data = response.candidates[0].content.parts[0].inline_data.data
            return data
        elif self.model_str in MINIMAX_MODELS:
            return self._generate_minimax_tts(text, voice_name, **kwargs)
        else:
            raise ValueError("Model not found")
    
    def _generate_minimax_tts(self, text: str, voice_name: str = "Chinese (Mandarin)_Lyrical_Voice", 
                             speed: float = 1, pitch: int = 0, vol: float = 1, 
                             sample_rate: int = 32000, bitrate: int = 128000, **kwargs):
        """
        使用 MiniMax API 生成语音
        
        Args:
            text: 要转换的文本
            voice_name: 语音名称
            speed: 语速 (0.5-2.0)
            pitch: 音调 (-12到12)
            vol: 音量 (0.1-1.0)
            sample_rate: 采样率
            bitrate: 比特率
            
        Returns:
            bytes: 音频数据
        """
        # 设置默认语音
        if voice_name == "default" or voice_name not in self.voice_list:
            voice_name = "Chinese (Mandarin)_Lyrical_Voice"
            
        url = f"https://api.minimax.chat/v1/t2a_v2?GroupId={self.group_id}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_str,
            "text": text,
            "timber_weights": [
                {
                    "voice_id": voice_name,
                    "weight": 1
                }
            ],
            "voice_setting": {
                "voice_id": "",
                "speed": speed,
                "pitch": pitch,
                "vol": vol,
                "latex_read": False
            },
            "audio_setting": {
                "sample_rate": sample_rate,
                "bitrate": bitrate,
                "format": "mp3"
            },
            "language_boost": "auto"
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            
            # 检查响应状态
            if result.get("base_resp", {}).get("status_code") != 0:
                error_msg = result.get("base_resp", {}).get("status_msg", "Unknown error")
                raise ValueError(f"MiniMax API 错误: {error_msg}")
            
            # 获取音频URL并下载
            audio_url = result.get("audio_file")
            if not audio_url:
                raise ValueError("MiniMax API 未返回音频文件URL")
            
            # 下载音频文件
            audio_response = requests.get(audio_url, timeout=60)
            audio_response.raise_for_status()
            
            return audio_response.content
            
        except requests.exceptions.RequestException as e:
            raise ValueError(f"MiniMax API 请求失败: {str(e)}")
        except Exception as e:
            raise ValueError(f"MiniMax TTS 生成失败: {str(e)}")
        
    def save_audio(self, data: bytes, file_path: str):
        # 保存为mp3文件
        if self.model_str in DASHSCOPE_MODELS:
            with open(file_path, "wb") as f:
                f.write(data)
        elif self.model_str in GEMINI_MODELS:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
                temp_wav_path = temp_wav.name
                wave_file(temp_wav_path, data)

            try:
                # 使用moviepy将WAV转换为MP3
                from moviepy import AudioFileClip
                audio_clip = AudioFileClip(temp_wav_path)
                audio_clip.write_audiofile(file_path, codec='mp3')
                audio_clip.close()
            finally:
                # 清理临时文件
                os.unlink(temp_wav_path)
        elif self.model_str in MINIMAX_MODELS:
            # MiniMax 直接返回 MP3 格式的音频数据
            with open(file_path, "wb") as f:
                f.write(data)
        else:
            raise ValueError("Model not found")

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


