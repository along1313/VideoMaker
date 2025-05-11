
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from service.ai_service import ImageModelService

image_model_service = ImageModelService()
print(image_model_service.generate("按以下描述生成黑白矢量剪影图, 底色为白色，极简主义风格, 高对比度, 纯黑白色块, 无渐变色, 流畅线条, 平面化设计，轮廓清晰，类SVG格式矢量文件，描述如下：星空下双人剪影拥抱，粗线条"))



    