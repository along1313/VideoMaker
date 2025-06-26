import re
from moviepy import ImageSequenceClip, AudioFileClip, ImageClip
from moviepy.audio.AudioClip import AudioClip
import numpy as np
import os
import json
from PIL import Image, ImageDraw, ImageFont
import textwrap

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
    if text is None or text.strip() == "":
        print("警告: 输入文本为空。")
        return None
        
    # 优先使用正则表达式查找 ```json ... ``` 块
    # 使用非贪婪匹配确保只匹配到第一个完整的JSON块
    match = re.search(r'```json\s*([\s\S]*?)\s*```', text, re.IGNORECASE)

    if match:
        # 提取捕获组1的内容，即 ```json 和 ``` 之间的文本
        json_text = match.group(1).strip()
        if not json_text: # 如果json_text为空字符串
            print("警告: ```json ... ``` 标记块内部为空。")
            return None
        try:
            # 尝试先将文本转换为Python对象，再通过json.dumps确保正确的JSON格式
            parsed_data = json.loads(json_text)
            formatted_json = json.dumps(parsed_data, ensure_ascii=False)
            return json.loads(formatted_json)
        except json.JSONDecodeError as e:
            # 如果解析失败，尝试清理可能的注释或额外文本
            try:
                # 查找最后一个右花括号的位置
                last_brace_pos = json_text.rstrip().rfind('}')
                if last_brace_pos > 0:
                    # 只保留到最后一个右花括号的内容
                    cleaned_json = json_text[:last_brace_pos+1].strip()
                    parsed_data = json.loads(cleaned_json)
                    formatted_json = json.dumps(parsed_data, ensure_ascii=False)
                    print("成功通过清理额外内容解析JSON。")
                    return json.loads(formatted_json)
            except json.JSONDecodeError:
                pass  # 如果清理后仍然失败，继续执行下面的代码
                
            print(f"JSON 解析错误: {e}。匹配到的内容: '{json_text}...'")
            return None
    else:
        # 如果没有找到 ```json ... ``` 标记块，尝试旧的清理逻辑
        cleaned_text = re.sub(r'^```json\s*', '', text, flags=re.IGNORECASE | re.MULTILINE)
        cleaned_text = re.sub(r'\s*```$', '', cleaned_text, flags=re.IGNORECASE | re.MULTILINE)
        cleaned_text = cleaned_text.strip()

        if not cleaned_text:
            print("未找到 ```json ... ``` 标记块，且清理后文本为空。")
            return None
            
        # 尝试查找JSON的开始和结束位置
        try:
            # 查找第一个左花括号和最后一个右花括号的位置
            first_brace = cleaned_text.find('{')
            last_brace = cleaned_text.rfind('}')
            
            if first_brace >= 0 and last_brace > first_brace:
                # 提取可能的JSON部分
                json_part = cleaned_text[first_brace:last_brace+1].strip()
                parsed_data = json.loads(json_part)
                formatted_json = json.dumps(parsed_data, ensure_ascii=False)
                print("成功通过提取花括号内容解析JSON。")
                return json.loads(formatted_json)
        except json.JSONDecodeError:
            pass  # 如果提取花括号内容失败，继续尝试解析整个文本
            
        try:
            # 尝试直接解析清理后的文本
            parsed_data = json.loads(cleaned_text)
            formatted_json = json.dumps(parsed_data, ensure_ascii=False)
            return json.loads(formatted_json)
        except json.JSONDecodeError as e:
            print(f"未找到 ```json ... ``` 标记块，尝试直接解析清理后的文本也失败: {e}。清理后内容前100字符: '{cleaned_text[:100]}...'")
            return None

def get_audios_duration(audio_dir):
    durations = []
    #如果音频文件名是title.mp3，那么将其移到第一个，其他的按文件名数字顺序排列
    audio_files = [f for f in os.listdir(audio_dir) if f.endswith(".mp3") and f.split(".")[0].isdigit()]
    audio_files.sort(key=lambda x: int(x.split(".")[0]))
    # 之后再处理 title.mp3
    if "title.mp3" in os.listdir(audio_dir):
        audio_files.insert(0, "title.mp3")
    else:
        durations.append(0)
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

def generate_text_image(text, 
                        output_path, 
                        font_path = "lib/font/AlibabaPuHuiTi-3-65-Medium.ttf", 
                        font_size_to_width = 0.05, 
                        img_size = (1280, 720),
                        background_color=(255, 255, 255, 0),
                        fill_color='black',
                        ):
    """
    生成文字图片
    :param text: 文字内容
    :param output_file: 输出文件路径
    """
    font_size = int(img_size[0] * font_size_to_width)
    img = Image.new('RGBA', img_size, color=background_color)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(font_path, font_size, index=1)

    # 绘制文字
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    draw.text(
        ((img_size[0] - text_width) // 2, (img_size[1] - text_height) // 2),  # 居中
        text,
        fill=fill_color,
        font=font
    )

    # 保存图片
    img.save(output_path)

def crop_image(image, target_ratio):
    """
    根据目标比例裁剪图片中心区域（尽可能大）
    :param image: 原始图片对象
    :param target_ratio: 目标比例 (width / height)
    :return: 裁剪后的图片
    """
    width, height = image.size
    img_ratio = width / height

    if img_ratio > target_ratio:
        # 图片太宽，按高度裁剪宽度
        new_width = int(height * target_ratio)
        left = (width - new_width) // 2
        top = 0
        right = left + new_width
        bottom = height
    else:
        # 图片太高，按宽度裁剪高度
        new_height = int(width / target_ratio)
        top = (height - new_height) // 2
        left = 0
        right = width
        bottom = top + new_height

    return image.crop((left, top, right, bottom))

def draw_text_on_image(image, text, font_path=None, font_size_to_width=0.15, fill_color="yellow", outline_color="black", stroke_width=2, margin=20):
    """
    在图片上绘制带描边的文字，并自动换行，保证所有文字都在图片内
    :param image: PIL Image 对象
    :param text: 要绘制的文字
    :param font_path: 字体文件路径
    :param font_size: 字号大小
    :param fill_color: 文字填充颜色
    :param outline_color: 描边颜色
    :param stroke_width: 描边粗细
    :param margin: 边距
    :return: 修改后的图像
    """

    font_size = int(image.size[0] * font_size_to_width)
    draw = ImageDraw.Draw(image)

    try:
        if font_path:
            font = ImageFont.truetype(font_path, font_size)
        else:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()

    width, height = image.size

    # 动态测量宽度，超宽即换行
    lines = []
    current_line = ""
    for char in text:
        test_line = current_line + char
        line_width = draw.textlength(test_line, font=font)
        if line_width > (width - 2 * margin) and current_line:
            lines.append(current_line)
            current_line = char
        else:
            current_line = test_line
    if current_line:
        lines.append(current_line)

    # 计算总文本高度
    line_heights = [draw.textbbox((0, 0), line, font=font)[3] - draw.textbbox((0, 0), line, font=font)[1] for line in lines]
    total_text_height = sum(line_heights)
    
    # 居中 y 坐标
    y = (height - total_text_height) // 2

    for line in lines:
        line_width = draw.textlength(line, font=font)
        x = (width - line_width) // 2

        # 绘制描边：多个方向偏移绘制 outline_color 颜色的文字
        for dx in range(-stroke_width, stroke_width + 1):
            for dy in range(-stroke_width, stroke_width + 1):
                if dx != 0 or dy != 0:  # 不在中心点绘制
                    draw.text((x + dx, y + dy), line, fill=outline_color, font=font)

        # 最后绘制主文字
        draw.text((x, y), line, fill=fill_color, font=font)
        y += line_heights.pop(0)

    return image

def generate_covers(input_path, output_dir, text, **keywords):
    """
    生成四种封面图：4:3、3:4 各两张
    :param input_path: 输入图片路径
    :param output_prefix: 输出文件名前缀
    :param text: 添加的文字内容
    """
    image = Image.open(input_path).convert("RGBA")
    # 检查image的分辨率，如果没有任何边长大于800像素，则将图片等比例放大，达到长边等于800像素
    width, height = image.size
    if max(width, height) <= 800:
        scale_factor = 800 / max(width, height)
        image = image.resize((int(width * scale_factor), int(height * scale_factor)))


    ratios = {
        "4:3": 4/3,
        "3:4": 3/4
    }
    for name, ratio in ratios.items():
        cropped = crop_image(image, ratio)
        with_text = draw_text_on_image(cropped, text=text, **keywords)
        with_text.save(f"{output_dir}/cover_{name}.png")
        print(f"已生成 {output_dir}/cover_{name}.png")


 


def split_text(text, min_length=8, max_length=25):
    """
    优先按句号/问号/感叹号切分字幕，尽量不在句号中间断开
    """
    # 预处理
    text = ' '.join(text.replace('\n', ' ').split())
    # 1. 先按"。！？!?切句
    sentences = re.split(r'([。！？!?])', text)
    # 合并标点
    chunks = []
    for i in range(0, len(sentences)-1, 2):
        chunk = sentences[i] + sentences[i+1]
        chunks.append(chunk)
    if len(sentences) % 2 == 1:
        chunks.append(sentences[-1])

    # 2. 对每个句子做二次切分
    result = []
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        if len(chunk) <= max_length:
            result.append(chunk)
        else:
            # 优先按逗号、顿号、分号等切分
            subs = re.split(r'([，,、；;])', chunk)
            temp = ''
            for sub in subs:
                if not sub:
                    continue
                if len(temp) + len(sub) <= max_length:
                    temp += sub
                else:
                    if temp:
                        result.append(temp)
                    temp = sub
            if temp:
                result.append(temp)
            # 最后还超长就强制截断
            i = 0
            while i < len(result):
                seg = result[i]
                while len(seg) > max_length:
                    result.insert(i+1, seg[max_length:])
                    seg = seg[:max_length]
                result[i] = seg
                i += 1
    # 合并过短的
    merged = []
    for seg in result:
        if merged and len(merged[-1]) < min_length:
            merged[-1] += seg
        else:
            merged.append(seg)
    return [s.strip() for s in merged if s.strip()]
    

def count_text_chars(text_array):
    """
    计算文本数组中所有字符的总数
    
    :param text_array: 包含多个文本字符串的数组
    :return: 所有文本字符串的字符总数
    """
    # 初始化计数器
    total_chars = 0
    
    # 遍历数组中的每个文本元素，累加字符长度
    for text in text_array:
        if text:  # 确保文本不为空
            total_chars += len(text)
    
    return total_chars
    
async def func_and_retry_parse_json(text, func, n_retry = 3, **kwargs):
    """
    尝试解析JSON，如果失败则重试
    :param text: 将被解析的文本
    :param func: 尝试处理文本为json格式的函数
    :param n_retry: 重试次数
    :param **kwargs: 传递给func的其他参数
    :return: 解析后的JSON
    """
    # 第一次调用时传入所有参数
    work_flow_record = func(text, **kwargs)
    for i in range(n_retry):
        try:          
            return parse_json(work_flow_record)
        except Exception as e:
            print(f'结构化失败: {str(e)}, retry {i+1} times')
            # 重试时使用上一次生成的结果作为输入
            work_flow_record = func(work_flow_record, **kwargs)
    return None

def make_blank_audio(duration, output_path, fps=44100):
    """
    生成指定时长的静音音频文件
    
    :param duration: 音频时长（秒）
    :param output_path: 输出文件路径
    :param fps: 采样率，默认为44100Hz（CD音质）
    :return: 生成的音频文件路径，如果失败则返回None
    """
    try:
        # 创建一个静音音频片段
        silent_audio = AudioClip(
            make_frame=lambda t: np.zeros((1,)),  # 单声道静音
            duration=duration,
            fps=fps
        )
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # 保存为MP3文件
        silent_audio.write_audiofile(
            output_path,
            codec='libmp3lame',
            bitrate='192k',
            logger=None  # 禁用进度条输出
        )
        
        return output_path
    except Exception as e:
        print(f"生成静音音频失败: {str(e)}")
        return None
    
def img_y_slide(image_clip, screen_size, pan_speed, int_direction = "up"):
    """
    图片剪辑垂直平移
    :param image_clip: 图片剪辑
    :param screen_size: 屏幕大小
    :param pan_speed: 平移速度
    :param int_direction: 初始运动方向，"up"表示初始镜头向上（图片向下），"down"表示初始镜头向下（图片向上）
    :return: 平移后的图片剪辑
    """
    image_clip = image_clip.resized(width=screen_size[0])
    image_width, image_height = image_clip.size
    panable_height = image_height - screen_size[1]
    
    # 计算时间节点
    t1 = panable_height / 2 / pan_speed
    t2 = t1 + panable_height / pan_speed
    t3 = t2 + panable_height / 2 / pan_speed
    
    # 根据方向设置初始位置
    if int_direction == "up":
        # 初始镜头向上（图片向下）：从图片顶部开始
        initial_y = 0
    elif int_direction == "down":
        # 初始镜头向下（图片向上）：从图片底部开始
        initial_y = -panable_height
    else:
        # 默认使用原来的逻辑（中间开始）
        initial_y = -panable_height / 2
    
    def get_y_position(t):
        if int_direction == "up":
            # 镜头向上运动：图片向下移动
            if t < t1:
                return initial_y - pan_speed * t
            elif t < t2:
                return -panable_height / 2 + pan_speed * (t - t1)
            elif t < t3:
                return 0 - pan_speed * (t - t2)
            else:
                return -panable_height / 2
        elif int_direction == "down":
            # 镜头向下运动：图片向上移动
            if t < t1:
                return initial_y + pan_speed * t
            elif t < t2:
                return -panable_height / 2 - pan_speed * (t - t1)
            elif t < t3:
                return 0 + pan_speed * (t - t2)
            else:
                return -panable_height / 2
        else:
            # 原来的逻辑（从中间开始）
            if t < t1:
                return initial_y + pan_speed * t
            elif t < t2:
                return 0 - pan_speed * (t - t1)
            elif t < t3:
                return -panable_height + pan_speed * (t - t2)
            else:
                return -panable_height / 2
    
    image_clip = image_clip.with_position(lambda t: (0, get_y_position(t)))
    return image_clip