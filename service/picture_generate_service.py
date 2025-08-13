import json
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
    
    async def generate_picture_from_json_old(self, work_flow_record: dict, style: str = None, index_number: int = None):
        """
        从工作流记录生成图片
        :param work_flow_record: 工作流记录字典
        :param style: 图片风格
        :param index_number: 内容索引
        :return: 生成的图片URL
        """
        system_prompt_part1 = """
        请根据以下视频脚本JSON文本中,对应的"index"中的"image_description"内容，生成与此分镜对应的“image_description”内容一致的图片。
        请注意，你首先根据index编号提取image_description内容，然后再参考整个本JSON脚本文本主体内容，生成与提取的“image_description”一致的图片。
        如果"main_character_description"字段不为空，请参考其中描述的主要角色，以及角色出场的场景编号。
        图片风格要求为：
        """
        system_prompt_part2 = """
        你现在要生成index:{index_number}对应的“image_description”内容。JSON文本为：
        """
        system_prompt_part2 = system_prompt_part2.format(index_number=index_number)

        style_config = STYLE_CONFIG.get(style)  
        if style_config is None:
            print(f'未设置风格，使用默认风格')
            size = "1024x1024"
        else:
            self.system_prompt = style_config['img_generate_system_prompt']
            size = style_config['img_size']
        
        # 将工作流记录转换为JSON字符串
        json_text_str = json.dumps(work_flow_record, ensure_ascii=False, indent=2)
        
        prompt = system_prompt_part1 + self.system_prompt + system_prompt_part2 + json_text_str

        return await self.image_model.generate(prompt, size)
    
    async def save_image(self, image_or_url, file_path: str):
        return await self.image_model.save_image(image_or_url, file_path)
    
    async def generate_picture_from_json(self, work_flow_record: dict, style: str = None, index_number: int = None):
        """
        从工作流记录生成图片
        :param work_flow_record: 工作流记录字典
        :param style: 图片风格
        :param index_number: 内容索引
        :return: 生成的图片URL
        """

        style_config = STYLE_CONFIG.get(style)  
        if style_config is None:
            print(f'未设置风格，使用默认风格')
            size = "1024x1024"
        else:
            self.system_prompt = style_config['img_generate_system_prompt']
            size = style_config['img_size']

        prompt_image_description = work_flow_record['content'][index_number]['image_description']

        prompt_main_character_description = ""
        for main_character in work_flow_record['main_character_description']:
            if index_number in main_character['index']:
                prompt_main_character_description += main_character['description'] + "\n"
        if prompt_main_character_description != "":
            prompt = self.system_prompt + "\n" + "画面描述: " + prompt_image_description + "\n" + "人物描述: " + prompt_main_character_description           
        else:
            prompt = self.system_prompt + "\n" + "画面描述: " + prompt_image_description
        print(f'####test_prompt####')
        print(prompt)
        return await self.image_model.generate(prompt, size)
    
    async def save_image(self, image_or_url, file_path: str):
        return await self.image_model.save_image(image_or_url, file_path)