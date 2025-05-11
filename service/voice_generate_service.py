from service.ai_service import TTSModelService
import dashscope

class VoiceGenerateService:
    def __init__(self, tts_service: TTSModelService):
        self.tts_service = tts_service
        
    def generate(self, text: str):
        return self.tts_service.generate(text)

    def get_synthesizer(self):
        return self.tts_service.get_synthesizer()
        