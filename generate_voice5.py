#!/usr/bin/env python3
"""
生成语音5（男）的音频文件
使用TTSModelService生成"百速AI，百倍速度进行创作"的英文男声
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from service.ai_service import TTSModelService

# 加载环境变量
load_dotenv()

async def generate_voice5():
    """生成语音5（男）的音频文件"""
    try:
        print("开始生成语音5（男）音频文件...")
        
        # 创建TTS服务实例，使用MiniMax的speech-02-turbo模型
        tts_service = TTSModelService(model_str="speech-02-turbo")
        
        # 要生成的文本
        text = "百速AI，百倍速度进行创作。"
        
        # 使用English_Diligent_Man语音
        voice_name = "English_Diligent_Man"
        
        print(f"使用语音: {voice_name}")
        print(f"生成文本: {text}")
        
        # 生成音频
        audio_data = tts_service.generate(
            text=text,
            voice_name=voice_name
        )
        
        # 确保输出目录存在
        output_dir = "static/audio"
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存音频文件
        output_path = os.path.join(output_dir, "语音5（男）.mp3")
        
        if isinstance(audio_data, bytes):
            # 如果返回的是字节数据，直接写入文件
            with open(output_path, "wb") as f:
                f.write(audio_data)
        elif hasattr(audio_data, 'content'):
            # 如果是响应对象，提取内容
            with open(output_path, "wb") as f:
                f.write(audio_data.content)
        else:
            # 如果是文件路径，复制文件
            import shutil
            shutil.copy(audio_data, output_path)
        
        print(f"音频文件已保存到: {output_path}")
        
        # 检查文件大小
        file_size = os.path.getsize(output_path)
        print(f"文件大小: {file_size} bytes")
        
        if file_size > 0:
            print("✅ 语音5（男）音频文件生成成功！")
            return True
        else:
            print("❌ 生成的音频文件为空")
            return False
            
    except Exception as e:
        print(f"❌ 生成语音文件失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(generate_voice5())
    sys.exit(0 if success else 1)