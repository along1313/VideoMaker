from pydoc import text
from service.ai_service import LLMService


class AIAgentService:
    def __init__(self):
        self.llm_service = LLMService()
        self.memory = []
        self.tools = []
        

    def run(self, user_prompt: str, max_tokens: int=32000, get_only_answer: bool=True) -> str:
        planner_system_prompt = """
        你是一个智能规划者，你请根据用户的需求，将任务分解为可执行的步骤。
        有以下的工具：
        """

        return self.llm_service.generate(messages, max_tokens, get_only_answer)

    def add_memory(self, message: dict[str, str]):
        self.memory.append(message)
    def add_tools(self, tools: list[Tool]):
        self.tools.extend(tools)
    def add_tool(self, tool: Tool):
        self.tools.append(tool)





class Tool:
    def __init__(self, name: str, description: str, func):
        self.name = name
        self.description = description
        self.func = func
