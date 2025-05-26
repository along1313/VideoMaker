
import re
from moviepy import ImageSequenceClip, AudioFileClip
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

def generate_text_image(text, output_file, font_path = "lib/font/STHeiti Medium.ttc", font_size = 60, screan_size = (1280, 720)):
    """
    生成文字图片
    :param text: 文字内容
    :param output_file: 输出文件路径
    """
    img = Image.new('RGBA', screan_size, color=(255, 255, 255, 0))
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

def draw_text_on_image(image, text, font_path=None, font_size=128, fill_color="yellow", outline_color="black", stroke_width=2, margin=20):
    """
    在图片上绘制带描边的文字，并自动换行
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

    draw = ImageDraw.Draw(image)

    try:
        if font_path:
            font = ImageFont.truetype(font_path, font_size)
        else:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()

    width, height = image.size

    # 自动换行 - 改进版本，考虑中文字符宽度
    # 检测文本中是否包含中文字符
    has_chinese = any('\u4e00' <= char <= '\u9fff' for char in text)
    
    if has_chinese:
        # 中文字符宽度计算 - 使用实际文本中的字符计算平均宽度
        # 取样本字符计算平均宽度，包括中文和英文
        sample_chars = text[:min(20, len(text))]  # 使用前20个字符作为样本
        if sample_chars:
            sample_widths = [font.getlength(char) for char in sample_chars]
            avg_char_width = sum(sample_widths) / len(sample_widths)
        else:
            # 如果没有足够的样本，使用一个中文字符的宽度作为参考
            avg_char_width = font.getlength('中')
    else:
        # 英文字符宽度计算 - 使用英文字母的平均宽度
        avg_char_width = sum(font.getlength(chr(i)) for i in range(65, 91)) / 26
    
    # 计算每行最大字符数，考虑边距
    max_char_per_line = max(1, int((width - 2 * margin) / avg_char_width))
    lines = textwrap.wrap(text, width=max_char_per_line)

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
    marks = '，。！？——,!?-'
    # 初始化结果数组
    result = []
    
    # 如果文本长度小于最大长度，直接返回
    if len(text) <= max_length:
        # 去掉末尾的标点符号
        text = text.strip(marks)
        return [text]
    
    # 当文本还未处理完时，继续处理
    while text:
        # 从最小长度开始尝试查找标点符号
        found_punctuation = False
        for i in range(min_length, min(len(text), max_length + 1)):
            # 检查当前位置是否是标点符号
            if text[i - 1] in marks:
                # 截取不包含标点符号的部分
                result.append(text[:i - 1].strip(marks))
                text = text[i:].strip()
                found_punctuation = True
                break
        
        # 如果没有找到标点符号，强制截断
        if not found_punctuation:
            cut_length = min(max_length, len(text))
            result.append(text[:cut_length].strip())
            text = text[cut_length:].strip(marks)
        
        # 如果剩余文本长度小于最小长度，直接添加到最后一段
        if len(text) < min_length:
            if result:
                result[-1] = result[-1] + ' ' + text.strip(marks)
            else:
                result.append(text.strip(marks))
            break
    
    return [item for item in result if item]  # 过滤掉空字符串
    

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
    