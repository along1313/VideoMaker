import os
import requests
import json
from moviepy import ImageClip, CompositeVideoClip, AudioFileClip, CompositeAudioClip, TextClip, ColorClip
from utility import generate_text_image, get_audios_duration, split_text, count_text_chars, generate_covers, img_y_slide
from service.ai_service import TTSModelService
from service.script_service import ScriptService
from service.picture_generate_service import PictureGenerateService
from dotenv import load_dotenv
from static.style_config import STYLE_CONFIG, TEMPLATE_CONFIG
from moviepy import concatenate_audioclips
import asyncio
import aiohttp
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont
import textwrap

load_dotenv()
# 字体路径
FONT_PAHT = "lib/font"

async def generate_picture_from_json(work_flow_record: dict, 
                         picture_generate_service: PictureGenerateService, 
                         result_dir: str, 
                         title_font_path: str, 
                         style: str = "黑白矢量图",
                         is_generate_title_picture: bool = False,
                         screen_size: tuple = (1280, 720),
                         **kwargs
                        ):
    """
    从JSON异步生成图片
    :param work_flow_record: 工作流记录
    :param picture_generate_service: 图片生成服务
    :param result_dir: 结果目录
    :param title_font_path: 标题字体路径
    :param style: 图片风格
    :param is_generate_title_picture: 是否需要标题图片
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

    # 准备所有需要生成的图片任务
    image_tasks = []
    content = work_flow_record['content']
    
    # 创建异步会话
    async with aiohttp.ClientSession() as session:
        # 收集所有图片生成任务
        for index, item in enumerate(content):
            # 直接使用work_flow_record和index生成图片，不需要picture_prompt
            image_url = await picture_generate_service.generate_picture_from_json(
                work_flow_record, 
                style=style, 
                index_number=index
            )
            image_path = os.path.join(result_dir, f"{index}_0.png")
            # 创建下载任务
            task = download_and_save_image(session, image_url, image_path)
            # 保存任务信息，用于后续更新work_flow_record
            image_tasks.append((index, task))

        # 并发执行所有下载任务
        results = await asyncio.gather(*[task for _, task in image_tasks])
        
        # 更新work_flow_record中的picture_path
        for (index, _), image_path in zip(image_tasks, results):
            if image_path:  # 只添加成功下载的图片路径
                new_work_flow_record['content'][index]['picture_path'].append(image_path)

    # 在所有正文图片生成完毕后，如果需要生成标题图片，使用第一张正文图片作为背景
    if is_generate_title_picture == True:
        title_text = work_flow_record['title']
        title_image_path = os.path.join(result_dir, "title.png")
        
        # 检查是否有正文图片可用
        if (new_work_flow_record['content'] and 
            new_work_flow_record['content'][0]['picture_path'] and 
            len(new_work_flow_record['content'][0]['picture_path']) > 0):
            
            # 使用第一张正文图片作为背景
            background_image_path = new_work_flow_record['content'][0]['picture_path'][0]
            await generate_title_image_with_background(
                title_text, 
                background_image_path, 
                title_image_path, 
                title_font_path,
                screen_size=screen_size
            )
        else:
            # 如果没有正文图片，使用原来的纯文字生成方式
            await generate_text_image_async(title_text, 
                                            title_image_path, 
                                            title_font_path,
                                            img_size=screen_size,
                                            **kwargs)
        
        new_work_flow_record['title_picture_path'] = title_image_path

    return new_work_flow_record

async def generate_text_image_async(text: str, 
                                    save_path: str, 
                                    font_path: str,
                                    font_size_to_width: float = 0.05,
                                    img_size: tuple = (1280, 720),
                                    background_color: tuple = (255, 255, 255, 0),
                                    fill_color: str = 'black'
                                    ) -> str:
    """
    异步生成文字图片
    :param text: 要生成的文字
    :param save_path: 保存路径
    :param font_path: 字体路径
    :return: 保存的图片路径
    """
    try:
        # 使用线程池执行同步的图片生成操作
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            ThreadPoolExecutor(),
            generate_text_image,
            text,
            save_path,
            font_path,
            font_size_to_width=font_size_to_width,
            img_size=img_size,
            background_color=background_color,
            fill_color=fill_color
        )
        return save_path
    except Exception as e:
        print(f'生成文字图片失败：{str(e)}')
        return None

async def download_and_save_image(session: aiohttp.ClientSession, image_url: str, save_path: str) -> str:
    """
    异步下载并保存图片
    :param session: aiohttp会话
    :param image_url: 图片URL
    :param save_path: 保存路径
    :return: 保存的图片路径
    """
    try:
        async with session.get(image_url) as response:
            if response.status == 200:
                content = await response.read()
                # 使用线程池执行文件写入操作
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    ThreadPoolExecutor(),
                    lambda: open(save_path, "wb").write(content)
                )
                print(f'生成图片：{save_path}')
                return save_path
            else:
                print(f'下载图片失败：{image_url}, 状态码：{response.status}')
                return None
    except Exception as e:
        print(f'下载图片出错：{image_url}, 错误：{str(e)}')
        return None

async def generate_title_image_with_background(title_text: str, 
                                              background_image_path: str, 
                                              output_path: str, 
                                              font_path: str,
                                              screen_size: tuple = (1280, 720)) -> str:
    """
    在背景图片上添加标题文字
    :param title_text: 标题文字
    :param background_image_path: 背景图片路径
    :param output_path: 输出图片路径
    :param font_path: 字体路径
    :param screen_size: 屏幕尺寸
    :return: 输出图片路径
    """
    try:
        # 使用线程池执行同步的图片处理操作
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            ThreadPoolExecutor(),
            _generate_title_image_with_background_sync,
            title_text,
            background_image_path,
            output_path,
            font_path,
            screen_size
        )
        print(f'生成标题图片：{output_path}')
        return output_path
    except Exception as e:
        print(f'生成标题图片失败：{str(e)}')
        return None

def _generate_title_image_with_background_sync(title_text: str, 
                                              background_image_path: str, 
                                              output_path: str, 
                                              font_path: str,
                                              screen_size: tuple = (1280, 720)):
    """
    同步版本：在背景图片上添加标题文字
    """
    try:
        # 打开背景图片
        background_image = Image.open(background_image_path).convert("RGBA")
        
        # 计算目标比例
        target_ratio = screen_size[0] / screen_size[1]  # width / height
        
        # 使用utility.py中的crop_image函数进行智能裁剪
        from utility import crop_image, draw_text_on_image
        
        # 智能裁剪：最大化裁剪出与目标比例一致的图片
        cropped_image = crop_image(background_image, target_ratio)
        
        # 等比例缩放到目标尺寸，避免变形
        resized_image = cropped_image.resize(screen_size, Image.Resampling.LANCZOS)
        
        # 在调整后的背景上添加文字
        result_image = draw_text_on_image(
            resized_image,
            title_text,
            font_path=font_path,
            font_size_to_width=0.2,  # 屏幕高度的0.2
            fill_color="yellow",     # 黄色字体
            outline_color="black",   # 黑色描边
            stroke_width=2,          # 描边粗细
            margin=20
        )
        
        # 保存结果
        result_image.save(output_path)
        return output_path
        
    except Exception as e:
        print(f'生成标题图片失败：{str(e)}')
        return None

async def generate_picture(work_flow_record: dict, 
                         picture_generate_service: PictureGenerateService, 
                         result_dir: str, 
                         title_font_path: str, 
                         style: str = "黑白矢量图",
                         is_generate_title_picture: bool = False,
                         screen_size: tuple = (1280, 720),
                         **kwargs
                        ):
    """
    异步生成图片
    :param work_flow_record: 工作流记录
    :param picture_generate_service: 图片生成服务
    :param result_dir: 结果目录
    :param title_font_path: 标题字体路径
    :param style: 图片风格
    :param is_required_title_picture: 是否需要标题图片
    :param title_picture_path: 如果要使用已有标题图片，将is_required_title_picture设为False，提供标题图片路径
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


    # 准备所有需要生成的图片任务
    image_tasks = []
    content = work_flow_record['content']
    
    # 创建异步会话
    async with aiohttp.ClientSession() as session:
        # 收集所有图片生成任务
        for index, item in enumerate(content):
            prompt_list = item['picture_prompt']
            for prompt_idx, prompt in enumerate(prompt_list):
                # 生成图片URL
                image_url = await picture_generate_service.generate(prompt, style=style)
                image_path = os.path.join(result_dir, f"{index}_{prompt_idx}.png")
                # 创建下载任务
                task = download_and_save_image(session, image_url, image_path)
                # 保存任务信息，用于后续更新work_flow_record
                image_tasks.append((index, prompt_idx, task))

        # 并发执行所有下载任务
        results = await asyncio.gather(*[task for _, _, task in image_tasks])
        
        # 更新work_flow_record中的picture_path
        for (index, prompt_idx, _), image_path in zip(image_tasks, results):
            if image_path:  # 只添加成功下载的图片路径
                new_work_flow_record['content'][index]['picture_path'].append(image_path)

    # 在所有正文图片生成完毕后，如果需要生成标题图片，使用第一张正文图片作为背景
    if is_generate_title_picture == True:
        title_text = work_flow_record['title']
        title_image_path = os.path.join(result_dir, "title.png")
        
        # 检查是否有正文图片可用
        if (new_work_flow_record['content'] and 
            new_work_flow_record['content'][0]['picture_path'] and 
            len(new_work_flow_record['content'][0]['picture_path']) > 0):
            
            # 使用第一张正文图片作为背景
            background_image_path = new_work_flow_record['content'][0]['picture_path'][0]
            await generate_title_image_with_background(
                title_text, 
                background_image_path, 
                title_image_path, 
                title_font_path,
                screen_size=screen_size
            )
        else:
            # 如果没有正文图片，使用原来的纯文字生成方式
            await generate_text_image_async(title_text, 
                                            title_image_path, 
                                            title_font_path,
                                            img_size=screen_size,
                                            **kwargs)
        
        new_work_flow_record['title_picture_path'] = title_image_path

    return new_work_flow_record

def generate_audio(
        work_flow_record: dict, 
        result_dir: str, 
        tts_model: TTSModelService, 
        model_str: str="cosyvoice-v1", 
        voice: str="longmiao", 
        pitch_rate: float=1.0,
        is_generate_title_audio: bool=False,
        **kwargs
        ):
    """
    生成音频
    :param work_flow_record: 工作流记录
    :param result_dir: 结果目录
    :param tts_model: TTS模型
    :param model_str: TTS模型名称
    :param voice: 语音名称
    :param pitch_rate: 语调
    :param is_generate_title_audio: 是否需要标题音频
    :param **kwargs: 其他参数（会被忽略）
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

    if is_generate_title_audio == True and work_flow_record.get('title_voice_text') is not None:
        # 生成标题音频
        title_text = work_flow_record['title_voice_text']
        title_audio_path = os.path.join(result_dir, "title.mp3")
        audio = tts_model.generate(title_text, voice=voice, pitch_rate=pitch_rate)
        tts_model.save_audio(audio, title_audio_path)

        new_work_flow_record['title_audio_path'] = title_audio_path
        print(f'生成音频：{title_audio_path}')

    # 生成音频
    content = work_flow_record['content']
    for index, item in enumerate(content):
        text = item['voice_text']
        audio_path = os.path.join(result_dir, f"{index}.mp3")
        audio = tts_model.generate(text, voice=voice, pitch_rate=pitch_rate)
        tts_model.save_audio(audio, audio_path)

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
    # 如果标题音频时长为0，则第一幅图片从0开始
    if time_list[0] == 0:
        start_time = 0
    else:
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

def generate_video(
    work_flow_record, 
    style, 
    template,
    result_dir, 
    font_path, 
    user_name = None, 
    screan_size = (1280, 720), 
    bg_pic_path = None, 
    bgm_path = None, 
    is_display_title = True, 
    is_need_ad_end = False,):
    """
    生成视频的函数

    参数:
    work_flow_record (dict): 工作流记录，包含视频内容信息
    result_dir (str): 结果输出目录
    screan_size (tuple): 屏幕尺寸，默认为 (1280, 720)
    bg_pic_path (str): 背景图片路径，默认为 'lib/img/background.png'
    slide_direction (str): 图片滑动方向，"up"表示初始镜头向上，"down"表示初始镜头向下

    返回:
    ImageClip: 背景图片剪辑对象
    """

    config = STYLE_CONFIG.get(style)
    if config is None:
        config = STYLE_CONFIG['绘本']
        print(f'没有找到{style}风格，使用绘本风格')

    template_config = TEMPLATE_CONFIG.get(template)
    if template_config is None:
        template_config = TEMPLATE_CONFIG['通用']
        print(f'没有找到{template}模板，使用通用模板')
    
    video_duration = work_flow_record['content'][-1]['voice_time'][0]+work_flow_record['content'][-1]['voice_time'][1]

    # 初始化背景图片
    if bg_pic_path is None:
        bg_clip = ColorClip(size=screan_size, color=(255, 255, 255), duration=video_duration)
    else:
        bg_clip  = ImageClip(bg_pic_path).with_duration(video_duration).resized(screan_size)

    # 生成图片剪辑表
    img_clips = []
    if work_flow_record['title_time'][1] > 0:
        #先单独处理标题图片
        if work_flow_record['title_picture_path'] is not None:
            title_img_path = work_flow_record['title_picture_path']
            title_img_clip = ImageClip(title_img_path).with_start(work_flow_record['title_time'][0]).with_duration(work_flow_record['title_time'][1]+1).resized(template_config['config']['title_picture_resize']).with_position(('center', 'center'))
            img_clips.append(title_img_clip)

    # 生成图片剪辑
    int_direction = "up"
    for index, item in enumerate(work_flow_record['content']):
        for i in range(len(item['picture_path'])):
            img_path = item['picture_path'][i]
            img_clip = ImageClip(img_path).with_start(item['picture_time'][i][0]).with_duration(item['picture_time'][i][1])
            if config['is_y_slide'] == True:
                img_clip = img_y_slide(img_clip, screan_size, pan_speed=15, int_direction=int_direction)
            else:
                img_clip = img_clip.with_position(('center', 'center')).resized(config['img_resize'])
            img_clips.append(img_clip)
            if int_direction == "up":
                int_direction = "down"
            else:
                int_direction = "up"
    
    #生成用户名文字
    caption_clips = []
    if user_name is not None:
        user_name_text = f"@{user_name}"
        user_name_clip = TextClip(
            font=font_path, 
            text = user_name_text, 
            font_size=int(screan_size[1]*0.05),  # 修复：转换为整数
            color=config["text_color"], 
            stroke_color = config['stroke_color'], 
            stroke_width = 1,
            ).with_position((int(screan_size[0]*0.025), int(screan_size[1]*0.05))).with_duration(video_duration)  # 修复：位置转换为整数
        caption_clips.append(user_name_clip)
    #生成标题文字
    if is_display_title == True:
        title_text = work_flow_record['title']
        
        # 创建标题文字剪辑
        title_clip = TextClip(
            font=font_path, 
            text=title_text, 
            font_size=int(screan_size[1]*0.05),  # 修复：转换为整数
            color=config["text_color"], 
            stroke_color=config['stroke_color'], 
            stroke_width=1,
        ).with_duration(video_duration)
        
        # 获取文字的实际尺寸
        text_width = title_clip.w
        text_height = title_clip.h
        
        # 计算合适的X坐标位置
        # 确保文字不会超出屏幕右边界，留出一定边距
        margin_x = int(screan_size[0] * 0.025)  # 修复：转换为整数
        max_x = screan_size[0] - margin_x - text_width
        
        # 如果文字太长，调整字体大小
        if max_x < margin_x:  # 如果文字太宽，缩小字体
            scale_factor = (screan_size[0] - 2 * margin_x) / text_width
            new_font_size = int(screan_size[1] * 0.035 * scale_factor)
            title_clip = TextClip(
                font=font_path, 
                text=title_text, 
                font_size=new_font_size, 
                color=config["text_color"], 
                stroke_color=config['stroke_color'], 
                stroke_width=1,
            ).with_duration(video_duration)
            # 重新计算位置
            text_width = title_clip.w
            max_x = screan_size[0] - margin_x - text_width
        
        # 设置Y坐标位置（顶部留出边距）
        margin_y = int(screan_size[1] * 0.05)  # 修复：转换为整数
        y_position = margin_y
        
        # 设置最终位置
        title_clip = title_clip.with_position((int(max_x), int(y_position)))  # 修复：位置转换为整数
        caption_clips.append(title_clip)
    # 生成字幕剪辑
    TEXT_STYLE = {
    "color": config["text_color"],
    "stroke_color": config["stroke_color"], # 限制文字宽度
    }

    
    for index, item in enumerate(work_flow_record['content']):
        for i in range(len(item['caption_text'])):
            caption_text = item['caption_text'][i]
            caption_start_time = item['caption_time'][i][0]
            caption_duration_time = item['caption_time'][i][1]
            caption_clip = TextClip(
                font_path, 
                caption_text, 
                font_size=int(screan_size[1]*0.05),  # 修复：转换为整数
                bg_color= (100, 100, 100, 128),
                stroke_width = 0, 
                **TEXT_STYLE
                ).with_start(caption_start_time).with_duration(caption_duration_time)
            caption_clip = caption_clip.with_position(('center', int(screan_size[1]-100)))  # 修复：Y位置转换为整数
            caption_clips.append(caption_clip)

    # 生成音频剪辑
    audio_clips = []
    # 单独处理标题音频
    if work_flow_record.get('title_audio_path') != "":
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

    # 一次性合并所有视频元素（背景、图片、字幕）
    all_video_clips = [bg_clip] + img_clips + caption_clips
    
    # 处理广告结尾
    if is_need_ad_end == True:
        ad_end_audio_clip = AudioFileClip("static/audio/end_voice.mp3").with_start(video_duration+1)
        ad_end_img_clip = ImageClip("static/img/end_img.jpg").with_start(video_duration).with_duration(ad_end_audio_clip.duration+1).resized(screan_size)
        all_video_clips.append(ad_end_img_clip)
        # 将广告音频也添加到音频剪辑中
        audio_concat_clip = CompositeAudioClip([audio_concat_clip, ad_end_audio_clip])
        # 更新视频总时长
        video_duration = video_duration + ad_end_audio_clip.duration+1

    # 最后一次性合并所有视频和音频元素
    final_clip = CompositeVideoClip(all_video_clips, size=screan_size).with_duration(video_duration).with_audio(audio_concat_clip)

    # 输出视频文件
    output_path = os.path.join(result_dir, "output.mp4")
    final_clip.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")

def generate_cover(work_flow_record, project_dir, **kwargs):   
    text = work_flow_record['title']
    cover_image_path = os.path.join(project_dir, "images", "0_0.png")
    cover_dir = os.path.join(project_dir, "covers")
    generate_covers(cover_image_path, cover_dir, text, **kwargs)

