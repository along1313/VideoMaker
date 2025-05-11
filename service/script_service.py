from service.ai_service import LLMService


class ScriptService:
    def __init__(self, llm: LLMService):
        self.llm = llm
        self.system_prompt = """
        你是一个专业的文案写手，擅长根据用户需求创作优质的小视频文案。视频形式为人声朗读配上播放静态插图，配以字幕。
        1. 如果用户没有特别指定，小视频时长默认为3分钟左右。
        2. 每个分镜间的人声朗读文本要连贯。
        3. 分镜插页设计要适合用单张或者多张静态图表现,与人声内容要连系紧密。
        4. 语言要温馨，能引起共鸣，不要使用生僻字，不要包含英文。
        5. 请确保朗读文字总时长跟要求的视频时长基本一致。
        6. 请以JSON格式提供你的回复，结构如下：
        {
            "title": "...", # 标题
            "content":[
                {
                    "index": "...", # 分镜编号，从0开始
                    "subtitle": "...", # 分镜名称
                    "picture_description": "...", # 插页描述
                    "voice_text": "..." # 人声朗读文本
                },
                ...
            ]
            "total_count": n # 总条数
        }
        """
    
    def generate(self, user_prompt: str, max_tokens: int=12000, get_only_answer: bool=True) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        content = self.llm.generate(messages, max_tokens=max_tokens, get_only_answer=get_only_answer)
        return content

