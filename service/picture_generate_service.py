from service.ai_service import ImageModelService
from static.style_config import STYLE_CONFIG

class PictureGenerateService:
    def __init__(self, image_model: ImageModelService):
        self.image_model = image_model
        self.system_prompt = "按以下描述生成黑白矢量剪影图, 底色为白色，极简主义风格, 高对比度, 纯黑白色块, 无渐变色, 流畅线条, 平面化设计，轮廓清晰，类SVG格式矢量文件，描述如下："

    def generate(self, description: str, style: str = None):
        style_config = STYLE_CONFIG.get(style)
        if style_config is None:
            print(f'未设置风格，使用默认风格')
            prompt = self.system_prompt + description
            size = "1024x1024"
        else:
            prompt = style_config['img_generate_system_prompt'] + description
            size = style_config['img_size']

        return self.image_model.generate(prompt, size)
        
    