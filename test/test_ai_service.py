import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service.ai_service import LLMService



llm = LLMService(model_str="deepseek-reasoner")

messages = [
    {"role": "system", "content": "你是一个专业的文案写手，擅长根据用户需求创作优质的视频文案。视频形式为人声朗读配上播放静态插图，配以字幕。"},
    {"role": "user", "content": "创作一个白雪公主故事的视频"}
]

response = llm.generate(messages,get_only_answer=False)
print(response)