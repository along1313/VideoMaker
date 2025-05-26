import os
import requests
import json
from moviepy import ImageClip, CompositeVideoClip, AudioFileClip, CompositeAudioClip, TextClip, ColorClip
from utility import generate_text_image, get_audios_duration, split_text, count_text_chars, generate_covers
from service.ai_service import TTSModelService
from service.script_service import ScriptService
from service.picture_generate_service import PictureGenerateService
from dotenv import load_dotenv
from static.style_config import STYLE_CONFIG
from moviepy import concatenate_audioclips

load_dotenv()
# 字体路径
FONT_PAHT = "lib/font"

def generate_picture(work_flow_record: dict, picture_generate_service: PictureGenerateService, result_dir: str, font_path = None, style = "黑白矢量图"):
    """
    生成图片
    :param work_flow_record: 工作流记录
    :param picture_generate_service: 图片生成服务
    :param result_dir: 结果目录
    :return: 新的工作流记录
    """
    new_work_flow_record = work_flow_record.copy()
    # 在new_work_flow_record中增加style字段
    new_work_flow_record['style'] = style

    # 在new_work_flow_record中content数组每个元素中增加picture_path字段
    new_work_flow_record['content'] = [
        {
            **item,
            "picture_path": []
        }
        for item in work_flow_record['content']
    ]

    # 为new_work_flow_record增加一个"title_picture_path"字段
    new_work_flow_record['title_picture_path'] = []

    # 生成标题图片
    title_text = work_flow_record['title']
    title_image_path = os.path.join(result_dir, "title.png")
    if font_path is not None:
        generate_text_image(title_text, title_image_path, font_path)
    else:
        generate_text_image(title_text, title_image_path)
    new_work_flow_record['title_picture_path'] = title_image_path

    # 生成分镜图片
    content = work_flow_record['content']
    for index, item in enumerate(content):
        prompt_list = item['picture_prompt']
        for prompt_idx, prompt in enumerate(prompt_list):
            image_url = picture_generate_service.generate(prompt, style=style)
            image_path = os.path.join(result_dir, f"{index}_{prompt_idx}.png")
            image_response = requests.get(image_url)
            with open(image_path, "wb") as f:
                f.write(image_response.content)

            new_work_flow_record['content'][index]['picture_path'].append(image_path)
            print(f'生成图片：{image_path}')

    return new_work_flow_record

def generate_audio(work_flow_record: dict, result_dir: str, tts_model: TTSModelService, model_str: str="cosyvoice-v1", voice: str="longmiao", pitch_rate: float=1.0):
    """
    生成音频
    :param work_flow_record: 工作流记录
    :param result_dir: 结果目录
    :return: 新的工作流记录
    """
    new_work_flow_record = work_flow_record.copy()
    # 在new_work_flow_record中content数组每个元素中增加audio_path字段
    new_work_flow_record['content'] = [
        {
            **item,
            "audio_path": ""
        }
        for item in work_flow_record['content']
    ]
    # 为new_work_flow_record增加一个"title_audio_path"字段
    new_work_flow_record['title_audio_path'] = ""
    # 生成标题音频
    title_text = work_flow_record['title']
    title_audio_path = os.path.join(result_dir, "title.mp3")
    audio = tts_model.generate(title_text, model_str=model_str, voice=voice, pitch_rate=pitch_rate)
    with open(title_audio_path, "wb") as f:
        f.write(audio)

    new_work_flow_record['title_audio_path'] = title_audio_path
    print(f'生成音频：{title_audio_path}')

    # 生成音频
    content = work_flow_record['content']
    for index, item in enumerate(content):
        text = item['voice_text']
        audio_path = os.path.join(result_dir, f"{index}.mp3")
        audio = tts_model.generate(text, model_str=model_str, voice=voice, pitch_rate=pitch_rate)
        with open(audio_path, "wb") as f:
            f.write(audio)

        new_work_flow_record['content'][index]['audio_path'] = audio_path
    
    return new_work_flow_record


def add_time(work_flow_record: dict, audios_dir: str, gap = 1.0):
    """
    增加时间
    :param work_flow_record: 工作流记录
    :return: 新的工作流记录
    """

    # 初始化新的工作流记录
    new_work_flow_record = work_flow_record.copy()
    
    # 一次性初始化所有需要的字段，包括字幕文本
    new_work_flow_record['content'] = [
        {
            **item,
            "picture_time": [],
            "caption_time": [],
            "caption_text": split_text(item['voice_text'])
        }
        for item in work_flow_record['content']
    ]
 

    # 获取音频时长列表
    time_list = get_audios_duration(audios_dir)
    start_time = 0

    # 设置标题时间
    new_work_flow_record['title_time'] = [start_time, time_list[0]]
    start_time = start_time + time_list[0] + gap
    for index, item in enumerate(new_work_flow_record['content']):
        # 给音频加上时间
        new_work_flow_record['content'][index]['voice_time'] = [start_time, time_list[index+1]]

        # 给图片加上时间
        picture_start_time = start_time
        picture_time = time_list[index+1]/len(item['picture_path'])
        for _ in range(len(item['picture_path'])):
            new_work_flow_record['content'][index]['picture_time'].append([picture_start_time, picture_time])
            picture_start_time = picture_start_time + picture_time
        # 给最后一个图片加上gap时间，避免画面空白
        new_work_flow_record['content'][index]['picture_time'][-1][1] = new_work_flow_record['content'][index]['picture_time'][-1][1] + gap

        # 给字幕加上时间
        caption_start_time = start_time
        total_chars = count_text_chars(item['caption_text'])
        for i in range(len(item['caption_text'])):
            caption_time = (len(item['caption_text'][i])/total_chars)*time_list[index+1]
            new_work_flow_record['content'][index]['caption_time'].append([caption_start_time, caption_time])
            caption_start_time = caption_start_time + caption_time

        start_time = start_time + time_list[index+1] + gap

    return new_work_flow_record

def generate_video(work_flow_record, style, result_dir, font_path, user_name = None, screan_size = (1280, 720), bg_pic_path = None, bgm_path = None):
    """
    生成视频的函数

    参数:
    work_flow_record (dict): 工作流记录，包含视频内容信息
    result_dir (str): 结果输出目录
    screan_size (tuple): 屏幕尺寸，默认为 (1280, 720)
    bg_pic_path (str): 背景图片路径，默认为 'lib/img/background.png'

    返回:
    ImageClip: 背景图片剪辑对象
    """

    config = STYLE_CONFIG.get(style)
    if config is None:
        config = STYLE_CONFIG['黑白矢量图']
    
    video_duration = work_flow_record['content'][-1]['voice_time'][0]+work_flow_record['content'][-1]['voice_time'][1]

    # 初始化背景图片
    if bg_pic_path is None:
        bg_clip = ColorClip(size=screan_size, color=(255, 255, 255), duration=video_duration)
    else:
        bg_clip  = ImageClip(bg_pic_path).with_duration(video_duration).resized(screan_size)

    # 生成图片剪辑表
    img_clips = []
    #先单独处理标题图片
    title_img_path = work_flow_record['title_picture_path']
    title_img_clip = ImageClip(title_img_path).with_start(work_flow_record['title_time'][0]).with_duration(work_flow_record['title_time'][1])
    img_clips.append(title_img_clip)

    # 生成图片剪辑   
    for index, item in enumerate(work_flow_record['content']):
        for i in range(len(item['picture_path'])):
            img_path = item['picture_path'][i]
            img_clip = ImageClip(img_path).with_start(item['picture_time'][i][0]).with_duration(item['picture_time'][i][1])
            img_clip = img_clip.with_position(('center', 'center')).resized(config['img_resize'])
            img_clips.append(img_clip)
    
    #生成用户名
    caption_clips = []
    if user_name is not None:
        user_name_text = f"@{user_name}"
        user_name_clip = TextClip(font=font_path, text = user_name_text, font_size=35, color=config["text_color"], stroke_color = config['stroke_color'], stroke_width = 1).with_position((25, 50)).with_duration(video_duration)
        caption_clips.append(user_name_clip)
    # 生成字幕剪辑
    TEXT_STYLE = {
    "font_size": 45,
    "color": config["text_color"],
    "stroke_color": config["stroke_color"],
    "size": (screan_size[0]-50, None)  # 限制文字宽度
    }

    
    for index, item in enumerate(work_flow_record['content']):
        for i in range(len(item['caption_text'])):
            caption_text = item['caption_text'][i]
            caption_start_time = item['caption_time'][i][0]
            caption_duration_time = item['caption_time'][i][1]
            caption_clip = TextClip(font_path, caption_text, stroke_width = 1, **TEXT_STYLE).with_start(caption_start_time).with_duration(caption_duration_time)
            caption_clip = caption_clip.with_position(('center', screan_size[1]-100))
            caption_clips.append(caption_clip)

    # 合并图片剪辑
    img_concat_clip = CompositeVideoClip([bg_clip]+img_clips+caption_clips, size = screan_size).with_duration(video_duration)

    # 生成音频剪辑
    audio_clips = []
    # 单独处理标题音频
    title_audio_path = work_flow_record['title_audio_path']
    title_audio_clip = AudioFileClip(title_audio_path).with_start(work_flow_record['title_time'][0]).with_duration(work_flow_record['title_time'][1])
    audio_clips.append(title_audio_clip)
    # 生成音频剪辑
    for index, item in enumerate(work_flow_record['content']):
        audio_path = item['audio_path']
        audio_start_time = item['voice_time'][0]
        audio_duration_time = item['voice_time'][1]
        audio_clip = AudioFileClip(audio_path).with_start(audio_start_time).with_duration(audio_duration_time)
        audio_clips.append(audio_clip)
        
    loop_bgm_clip = None
    # 增加背景音乐
    if bgm_path is not None:
        bgm_clip = AudioFileClip(bgm_path)
        num_repeats = int(video_duration / bgm_clip.duration) + 1
        loop_bgm_clip = concatenate_audioclips([bgm_clip] * num_repeats).subclipped(0, video_duration).with_volume_scaled(0.1)


    # 合并音频剪辑
    audio_concat_clip = CompositeAudioClip(audio_clips)
    if loop_bgm_clip is not None:
        audio_concat_clip = CompositeAudioClip([audio_concat_clip, loop_bgm_clip])
    # 合并音频和视频
    final_clip = img_concat_clip.with_audio(audio_concat_clip)

    # 输出视频文件
    output_path = os.path.join(result_dir, "output.mp4")
    final_clip.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")

def generate_cover(work_flow_record, project_dir, **kwargs):   
    text = work_flow_record['title']
    cover_image_path = os.path.join(project_dir, "images", "0_0.png")
    cover_dir = os.path.join(project_dir, "covers")
    generate_covers(cover_image_path, cover_dir, text, **kwargs)

"""   
project_dir = "workstore/user1/魔法花田与星光披风"
with open(os.path.join(project_dir, "work_flow_record.json"), "r") as f:
    work_flow_record = json.load(f)
generate_cover(work_flow_record, project_dir, font_path="lib/font/字制区喜脉体.ttf")
  """