import dashscope
from dashscope.audio.tts_v2 import *
import os
import dotenv
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from service.ai_service import LLMService
from utility import generate_word_image
dotenv.load_dotenv()

# 生成标题图片
title_text = "价格锚定效应：为何我们总被数字操控"
image_dir = os.path.join("workstore", "user1", "images")
image_path = os.path.join(image_dir, f"title.png")
generate_word_image(title_text, image_path)

