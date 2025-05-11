import dashscope
from dashscope.audio.tts_v2 import *

# 若没有将API Key配置到环境变量中，需将your-api-key替换为自己的API Key
dashscope.api_key = "sk-07250dbd106c4f05b96448ab3eb11308"

# 模型
model = "cosyvoice-v1"
# 音色
voice = "longmiao"

# 实例化SpeechSynthesizer，并在构造方法中传入模型（model）、音色（voice）等请求参数
synthesizer = SpeechSynthesizer(model=model, voice=voice)
# 发送待合成文本，获取二进制音频
audio = synthesizer.call("纽约警察局的'破窗治理计划'给出了完美答案：他们在发现第1起破坏事件时立即修复，犯罪率6个月内下降13%。这告诉我们，及时修补'初始破损'能阻断恶性循环。应用到个人生活，当我们发现环境中的'破窗'——无论是房间角落的杂物堆，还是工作中的疏漏——都应该像修复玻璃一样及时处理。")
print('[Metric] requestId: {}, first package delay ms: {}'.format(
    synthesizer.get_last_request_id(),
    synthesizer.get_first_package_delay()))

# 将音频保存至本地
with open('output.mp3', 'wb') as f:
    f.write(audio)