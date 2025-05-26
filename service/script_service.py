from service.ai_service import LLMService


class ScriptService:
    def __init__(self, llm: LLMService):
        self.llm = llm
        self.system_prompt = """
        你是一个专业的文案写手，擅长根据用户需求创作优质的小视频文案。视频形式为人声朗读配上播放静态插图，配以字幕。
        1. 如果用户没有特别指定，人声朗读文本总字数在2000字左右。
        2. 文案人声朗读文本内容组成一篇连贯的，结构完整的文章，结构起承转合，有娓娓道来的开篇，有过渡，有结尾，有总结，有点题。文章核心观点/情节突出，有价值导向，语言表达准确、简洁、有节奏感。
        3. 每个分镜间的人声朗读文本要连贯。
        4. 分镜插页设计要适合用单张或者多张静态图表现,与人声内容要连系紧密。
        5. 语言要温馨，能引起共鸣，不要使用生僻字，不要包含英文。
        6. 请确保朗读文字总时长跟要求的视频时长基本一致。
        7. 请以JSON格式提供你的回复，结构如下：
        {
            "title": "...", # 标题
            "content":[
                {
                    "index": "...", # 分镜编号，从0开始
                    "picture_description": "...", # 插页描述
                    "voice_text": "..." # 人声朗读文本
                },
                ...
            ],
            "total_count": n # 总条数
        }
        """
    
    def generate(self, user_prompt: str, max_tokens: int=32000, get_only_answer: bool=True) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        content = self.llm.generate(messages, max_tokens=max_tokens, get_only_answer=get_only_answer)
        return content

    def generate_text(self, user_prompt: str, **config) -> str:
        system_prompt = """
        你是一个顶尖的作家，擅长根据用户提供的内容或者需求创作完整的优质视频文案。视频形式为人声朗读讲述配上播放静态插图，配以字幕。你需要给出完整的文案，而非提纲，要求如下：
        1. 如果用户给的是需求，你需要根据用户需求创作完整的视频文案，如果用户没有特别指定字数，创造的朗读内容总字数在2000字左右，文案总字数不限。
        2. 如果用户给的是原始文案，字数少于2000字，补上缺失的部分，扩写内容；如果用户给的文案字数大于2000字，补充缺失内容，不做任何修改，直接输出。
        3. 文案内容需包含所有的人声朗读内容，而不是仅仅是提纲，
        4. 如果用户对风格没有指定，你创作的部分需根据用户需求的题材选择合适的风格。
        5. 你创作的部分，文案结构要完整，有起承转合，有娓娓道来的开篇，有过渡，有结尾，有总结，有点题。文章核心观点/情节突出，有价值导向，语言表达准确、简洁、有节奏感。
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        content = self.llm.generate(messages, **config)
        return content

    def generate_json(self, user_prompt: str, **config) -> str:
        system_prompt = """
        请根据用户的文案，转换为完整的分镜供后续流程制作使用，不要大幅修改或者省略表达。视频形式为人声朗读配上播放静态插图，配以字幕。要求如下：
        1. 每个项目内容都要完整，不要有省略，如果文案有缺失或者不完整的部分请补充完整。
        2. 总分镜条数不要超过12条，不是一定要12条，不要用重复的内容凑成12条。
        3. 标题为视频标题，而非文案的标题，如果文案中没有标题，请自行设计。
        4. 插页图片描述可以根据文案发挥想象，详细描述，保持前后描述统一。
        5. 人声朗读文本为纯朗读文本，不要出现除朗读文本外多余的文字。
        6. 去除文案中的引号符号，避免在JSON中出现问题。
        7. 请以JSON格式提供你的回复，结构如下：
        {
            "title": "...", # 视频标题，不要超过10个字
            "content":[
                {
                    "index": "...", # 分镜编号，从0开始
                    "picture_description": "...", # 分镜描述
                    "voice_text": "..." # 人声朗读文本
                },
                ...
            ],
            "total_count": n # 总条数
        }
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        content = self.llm.generate(messages, **config)
        return content


