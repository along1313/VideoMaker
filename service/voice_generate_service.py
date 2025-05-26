from service.ai_service import TTSModelService
import dashscope

class VoiceGenerateService:
    def __init__(self, tts_class, model_str: str="cosyvoice-v1", voice: str="longmiao", pitch_rate: float=1.0):
        self.tts_service = tts_service
        
    def generate(self, text: str):
        tts_model = tts_class()
        return self.tts_service.generate(text)

    def get_synthesizer(self):
        return self.tts_service.get_synthesizer()
        