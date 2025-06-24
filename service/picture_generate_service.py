from service.ai_service import ImageModelService
from static.style_config import STYLE_CONFIG

class PictureGenerateService:
    def __init__(self, image_model: ImageModelService):
        self.image_model = image_model
        self.system_prompt = "按以下描述生成黑白矢量剪影图, 底色为白色，极简主义风格, 高对比度, 纯黑白色块, 无渐变色, 流畅线条, 平面化设计，轮廓清晰，类SVG格式矢量文件，描述如下："

    async def generate(self, description: str, style: str = None):
        """
        异步生成图片
        :param description: 图片描述
        :param style: 图片风格
        :return: 生成的图片URL
        """
        style_config = STYLE_CONFIG.get(style)
        if style_config is None:
            print(f'未设置风格，使用默认风格')
            prompt = self.system_prompt + description
            size = "1024x1024"
        else:
            prompt = description + style_config['img_generate_system_prompt']
            size = style_config['img_size']

        return await self.image_model.generate(prompt, size)
    
    async def generate_picture_from_json(self, json_text: str, style: str = None, index_number: int = None):
        """
        异构生成图片
        :param json_text: 分镜信息JSON文本
        :param style: 图片风格
        :return: 生成的图片URL
        """
        system_prompt_part1 = """
        请根据以下表示分镜信息的JSON文本中对应的"index"的"voice_text"内容生成与voice_text内容协调的图片，尽量出现剧情人物形象，而不仅仅是景物图片。
        """
        system_prompt_part2 = """
        你现在要生成index:{index_number}对应的voice_text内容。JSON文本为：
        """
        system_prompt_part2 = system_prompt_part2.format(index_number=index_number)

        style_config = STYLE_CONFIG.get(style)  
        if style_config is None:
            print(f'未设置风格，使用默认风格')
            size = "1024x1024"
        else:
            self.system_prompt = style_config['img_generate_system_prompt']
            size = style_config['img_size']
        prompt = system_prompt_part1 + self.system_prompt + system_prompt_part2 + json_text

        return await self.image_model.generate(prompt, size)
    