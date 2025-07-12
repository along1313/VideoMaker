import sys
import os
import json
import requests
import time
import base64
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service.ai_service import LLMService, ImageModelService, TTSModelService
import dashscope
from dashscope.audio.tts_v2 import *
from static.model_info import MINIMAX_MODELS


text_list = [
    "第一品 法会因由分",
    "如是我闻，一时，佛在舍卫国祗树给孤独园，与大比丘众千二百五十人俱。尔时，世尊食时，著衣持钵，",
    "入舍卫大城乞食。于其城中，次第乞已，还至本处。饭食讫，收衣钵，洗足已，敷座而坐。",
]

output_dir = "test/test_output"
tts_service = TTSModelService(model_str="speech-02-turbo")
for i, text in enumerate(text_list):
    output_path = os.path.join(output_dir, f"test_{i}.mp3")
    data = tts_service.generate(text=text, voice_name="default")
    tts_service.save_audio(data, output_path)
    print(f"生成第{i}段音频")

"""
import requests

group_id = os.getenv("MINIMAX_GROUP_ID")
api_key = os.getenv("MINIMAX_API_KEY")

url = f"https://api.minimax.chat/v1/t2a_v2?GroupId={group_id}"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
payload = {
  "model": "speech-02-turbo",
  "text": "如是我闻，一时，佛在舍卫国祗树给孤独园，与大比丘众千二百五十人俱。尔时，世尊食时，著衣持钵，",
  "timber_weights": [
    {
      "voice_id": "Chinese (Mandarin)_Lyrical_Voice",
      "weight": 1
    }
  ],
  "voice_setting": {
    "voice_id": "",
    "speed": 1,
    "pitch": 0,
    "vol": 1,
    "latex_read": False
  },
  "audio_setting": {
    "sample_rate": 32000,
    "bitrate": 128000,
    "format": "mp3"
  },
  "language_boost": "auto"
}

response = requests.post(url, headers=headers, json=payload)
result = response.json()
audio_hex = result["data"]["audio"]
audio_bytes = bytes.fromhex(audio_hex)
with open("test/test_output/output_1.mp3", "wb") as f:
    f.write(audio_bytes)
    """
