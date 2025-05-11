
import re
from moviepy import ImageSequenceClip, AudioFileClip
import os
import json
from PIL import Image, ImageDraw, ImageFont

def parse_json(text):
    """
    从包含 Markdown 代码块标记的文本中提取并解析 JSON 数据。
    该函数会优先定位 "```json" 和 "```" 之间的内容，并尝试将其解析为 Python 字典。
    如果未找到标准标记块，会尝试清理首尾的标记并解析。
    即使标记块之后存在其他文本，也能正确提取 JSON 内容。

    Args:
        text (str): 包含 ```json 标记的文本

    Returns:
        text or None: 解析后的 JSON 数据，如果未找到有效的 JSON 或解析失败，则返回 None。
    """
    # 优先使用正则表达式查找 ```json ... ``` 块
    # re.DOTALL 使得 '.' 可以匹配包括换行符在内的任意字符
    match = re.search(r'```json\s*(.*?)\s*```', text, re.IGNORECASE | re.DOTALL)

    if match:
        # 提取捕获组1的内容，即 ```json 和 ``` 之间的文本
        json_text = match.group(1).strip()
        if not json_text: # 如果json_text为空字符串
            print("警告: ```json ... ``` 标记块内部为空。")
            return None
        try:
            # 尝试解析提取出来的 JSON 文本
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            # 如果解析失败，打印错误信息并返回 None
            print(f"JSON 解析错误: {e}。匹配到的内容: '{json_text}'")
            return None
    else:
        # 如果没有找到 ```json ... ``` 标记块，尝试旧的清理逻辑
        # 这部分是为了兼容可能不完全符合 ```json ... ``` 的情况，例如只有 ```json 开头或只有 ``` 结尾
        # 或者根本没有标记，但内容本身是JSON字符串
        cleaned_text = re.sub(r'^```json\s*', '', text, flags=re.IGNORECASE | re.MULTILINE) # 移除开头的```json
        cleaned_text = re.sub(r'\s*```$', '', cleaned_text, flags=re.IGNORECASE | re.MULTILINE) # 移除结尾的```
        cleaned_text = cleaned_text.strip()

        if not cleaned_text: # 如果清理后文本为空
            print("未找到 ```json ... ``` 标记块，且清理后文本为空。")
            return None
        try:
            # 尝试解析清理后的文本
            return json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            # 如果解析失败，打印错误信息并返回 None
            print(f"未找到 ```json ... ``` 标记块，尝试直接解析清理后的文本也失败: {e}。清理后内容: '{cleaned_text}'")
            return None

def get_audios_duration(audio_dir):
    durations = []
    #如果音频文件名是title.mp3，那么将其移到第一个，其他的按文件名数字顺序排列
    audio_files = [f for f in os.listdir(audio_dir) if f.endswith(".mp3") and f.split(".")[0].isdigit()]
    audio_files.sort(key=lambda x: int(x.split(".")[0]))
    # 之后再处理 title.mp3
    if "title.mp3" in os.listdir(audio_dir):
        audio_files.insert(0, "title.mp3")
    audio_paths = [os.path.join(audio_dir, f) for f in audio_files]
    
    for audio_path in audio_paths:
        audio = AudioFileClip(audio_path)
        duration = audio.duration
        durations.append(duration)
        audio.close()
    return durations

def format_time(seconds):
    """
    格式化时间为 SRT 时间轴格式：hh:mm:ss,ms
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def generate_srt(subtitles, durations,output_file, gap=1.0):
    """
    生成 SRT 文件
    :param subtitles: 字幕列表，每个元素为 (start_time, duration, text)
                      start_time: 字幕开始时间（秒）
                      duration: 字幕持续时间（秒）
                      text: 字幕内容
    :param output_file: 输出文件路径
    """
    start = durations[0] + gap
    with open(output_file, 'w', encoding='utf-8') as f:
        for idx, subtitle in enumerate(subtitles, start=1):
            # 计算起始时间和结束时间
            end = start + durations[idx]
            start_time = format_time(start)
            end_time = format_time(end)
            start = end + gap
            
            # 写入 SRT 格式内容
            f.write(f"{idx}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{subtitle}\n\n")

# 提取文本中的str文件部分（srt文本整块连续出现，不考虑不连续的情况），并保存为字幕文件
def extract_srt(subtitle_text):
    """
    从文本中提取连续出现的完整srt字幕块，并写入为标准srt文件
    :param subtitle_text: 输入的原始文本
    """
    import re
    # 匹配以编号开头、时间轴、字幕内容，并以空行分隔的完整srt块
    srt_block_pattern = re.compile(
        r'((?:\d+\n\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}\n(?:.*\n)+?\n)+)',
        re.MULTILINE
    )
    srt_blocks = srt_block_pattern.findall(subtitle_text)
    if srt_blocks:
        # 只写入最长的连续srt块（防止有多个分散的srt片段）
        longest_block = max(srt_blocks, key=len)
        return longest_block
    else:
        # 没有找到srt块时，输出空文件
        print("No srt blocks found in the input text.")
        return ""

def generate_text_image(text, output_file, font_path = "lib/font/STHeiti Medium.ttc", font_size = 60):
    """
    生成文字图片
    :param text: 文字内容
    :param output_file: 输出文件路径
    """
    img = Image.new('RGBA', (1280, 720), color=(255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(font_path, font_size, index=1)

    # 绘制文字
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    draw.text(
        ((1280 - text_width) // 2, (720 - text_height) // 2),  # 居中
        text,
        fill='black',
        font=font
    )

    # 保存图片
    img.save(output_file)


def split_text(text, min_length = 10, max_length = 25):
    """
    将文本合理的截断为指定长度区间的文本，然后输出为数组
    :param text: 输入的文本
    :param min_length: 最小长度
    :param max_length: 最大长度
    :return: 截断后的文本数组
    """
    # 预处理文本：去除换行符并替换为空格，然后去除多余空格
    text = ' '.join(text.replace('\n', ' ').split())
    
    # 初始化结果数组
    result = []
    
    # 如果文本长度小于最大长度，直接返回
    if len(text) <= max_length:
        # 去掉末尾的标点符号
        text = text.strip('，。！？,.!?')
        return [text]
    
    # 当文本还未处理完时，继续处理
    while text:
        # 从最小长度开始尝试查找标点符号
        found_punctuation = False
        for i in range(min_length, min(len(text), max_length + 1)):
            # 检查当前位置是否是标点符号
            if text[i - 1] in '，。！？,.!?':
                # 截取不包含标点符号的部分
                result.append(text[:i - 1].strip())
                text = text[i:].strip()
                found_punctuation = True
                break
        
        # 如果没有找到标点符号，强制截断
        if not found_punctuation:
            cut_length = min(max_length, len(text))
            result.append(text[:cut_length].strip())
            text = text[cut_length:].strip()
        
        # 如果剩余文本长度小于最小长度，直接添加到最后一段
        if len(text) < min_length:
            if result:
                result[-1] = result[-1] + ' ' + text.strip('，。！？,.!?')
            else:
                result.append(text.strip('，。！？,.!?'))
            break
    
    return [item for item in result if item]  # 过滤掉空字符串
    
    
    
