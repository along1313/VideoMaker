from service.ai_service import LLMService
from static.style_config import STYLE_CONFIG


class PicturePromptService:
    def __init__(self, llm: LLMService):
        self.llm = llm
        self.system_prompt = """
        从以下JSON格式的文案中，根据"picture_description"中各个分镜描述生成prompt，用于使用图像模型生成插页。
        1. 根据"picture_description"中各个分镜描述，先思考每个分镜用几张图片表现，要求图片内容不要重复或太相近，图片控制在1-3张，去掉重复或者内容相近的图片，然后为每张图片生成prompt用于生成图片。
        2. prompt要能够生成黑白单色粗线条矢量图，不要有动态描述。
        3. 抓住重点，不要描述太多细节，尽量保持画面简单。
        4. 图片中尽量不要出现具体的文字。
        5. 将生成的prompt以以下格式加入到原分镜描述JSON中，不改变原JSON的内容，以"picture_prompt"字段表示，格式如下
        
         {
            "title": "...", # 标题
            "content":[
                {
                    "index": "...", # 分镜编号，从0开始
                    "subtitle": "...", # 分镜名称
                    "picture_description": "...", # 插页描述
                    "picture_prompt": [
                        "prompt1",
                        "prompt2",
                        ...
                    ], # 加入你生成的1-3个插页prompt
                    "voice_text": "..." # 人声朗读文本
                },
                ...
            ]
            "total_count": n # 总条数
        }
        """

    def generate(self, script: str, style: str = None, max_tokens: int=32000, get_only_answer: bool=True) -> str:
        style_config = STYLE_CONFIG.get(style)
        if style_config is None:
            print("未设置风格，使用默认风格")
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": script}
            ]
        else:
            messages = [
                {"role": "system", "content": style_config['img_prompt_system_prompt']},
                {"role": "user", "content": script}
            ]
        return self.llm.generate(messages, max_tokens=max_tokens, get_only_answer=get_only_answer)