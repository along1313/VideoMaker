import dashscope
from dashscope.audio.tts_v2 import *
import os
import dotenv
import sys
from zhipuai import ZhipuAI

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from service.ai_service import ImageModelService
dotenv.load_dotenv()

api_key = os.environ.get("ZHIPU_API_KEY")
client = ZhipuAI(api_key=api_key)
response = client.images.generations(
    model="cogview-3-flash",
    prompt='一只可爱的小狗',
    size="1280x720",
    style="painting"
        )
print(response.data[0].url)

"""
image_generate_service = ImageModelService()

url = image_generate_service.generate("一只可爱的小狗", size = "1280x720")
print(url)
"""
