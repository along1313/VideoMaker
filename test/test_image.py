
import sys
import os
import json
import asyncio
import base64
from PIL import Image
from io import BytesIO
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from service.ai_service import ImageModelService, TTSModelService
from service.picture_generate_service import PictureGenerateService
from static.style_config import STYLE_CONFIG


output_path = "test/test_image00008.png"
work_flow_record = json.load(open("test/test_work_flow_record.json", "r", encoding="utf-8"))

print(f"开始生成图片...")
image_generate_service = ImageModelService("cogview-3-flash")
picture_generate_service = PictureGenerateService(image_generate_service)

image_url = asyncio.run(picture_generate_service.generate_picture_from_json(work_flow_record, "宫崎骏", 7))
print(f"图片生成完成，正在保存到: {output_path}")
asyncio.run(picture_generate_service.save_image(image_url, output_path))