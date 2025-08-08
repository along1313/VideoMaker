
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


output_path = "test/test_image00007.png"

print(f"开始生成图片...")
image_generate_service = ImageModelService("image-01")

print(f"调用API生成图片...")
image_url = asyncio.run(image_generate_service.generate("Studio Ghibli style, Hayao Miyazaki aesthetic, soft watercolor textures, pastel color palette (muted greens, golds, lavenders), highly detailed hand-drawn background, gentle dappled sunlight, peaceful and whimsical atmosphere, magical yet nostalgic, calm wind movement, 2D animation masterpiece, --ar 16:9 --style raw --no photorealistic, sharp edges, 3D render, text, signaturea. 一个女孩坐在石头上"))

if image_url:
    print(f"获取到图片数据: {image_url}")
    print(f"数据类型: {type(image_url)}")
    
    # 使用service的save_image方法保存
    print(f"保存图片到: {output_path}")
    try:
        await_result = asyncio.run(image_generate_service.save_image(image_url, output_path))
        print(f"图片保存完成")
    except Exception as e:
        print(f"图片保存失败: {e}")
else:
    print("未获取到图片数据")

print(f"图片保存完成，检查文件是否存在: {os.path.exists(output_path)}")
print(f"文件大小: {os.path.getsize(output_path) if os.path.exists(output_path) else '文件不存在'}")


    