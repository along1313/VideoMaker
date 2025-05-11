import os
import requests
from utility import generate_text_image, get_audios_duration, split_text
from service.ai_service import TTSModelService
from service.script_service import ScriptService
from service.picture_generate_service import PictureGenerateService

def generate_picture(work_flow_record: dict, picture_generate_service: PictureGenerateService, result_dir: str, style = "黑白矢量图"):
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
    generate_text_image(title_text, title_image_path)
    new_work_flow_record['title_picture_path'] = title_image_path

    # 生成分镜图片
    content = work_flow_record['content']
    for index, item in enumerate(content):
        prompt_list = item['picture_prompt']
        for prompt_idx, prompt in enumerate(prompt_list):
            image_url = picture_generate_service.generate(prompt)
            image_path = os.path.join(result_dir, f"{index}_{prompt_idx}.png")
            image_response = requests.get(image_url)
            with open(image_path, "wb") as f:
                f.write(image_response.content)

            new_work_flow_record['content'][index]['picture_path'].append(image_path)

    return new_work_flow_record

def generate_audio(work_flow_record: dict, result_dir: str, model_str: str="cosyvoice-v1", voice: str="longmiao", pitch_rate: float=1.0):
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
    # 每次生成音频都需要重新实例化tts_model和voice_generate_service
    tts_model = TTSModelService(model_str=model_str, voice=voice, pitch_rate=pitch_rate)
    audio = tts_model.generate(title_text)
    with open(title_audio_path, "wb") as f:
        f.write(audio)

    new_work_flow_record['title_audio_path'] = title_audio_path

    # 生成音频
    content = work_flow_record['content']
    for index, item in enumerate(content):
        text = item['voice_text']
        audio_path = os.path.join(result_dir, f"{index}.mp3")
        # 每次生成音频都需要重新实例化tts_model和voice_generate_service
        tts_model = TTSModelService(model_str=model_str, voice=voice, pitch_rate=pitch_rate)
        audio = tts_model.generate(text)
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

        # 给字幕加上时间
        caption_start_time = start_time
        for i in range(len(item['caption_text'])):
            caption_time = (len(item['caption_text'][i])/len(item['voice_text']))*time_list[index+1]
            new_work_flow_record['content'][index]['caption_time'].append([caption_start_time, caption_time])
            caption_start_time = caption_start_time + caption_time

        start_time = start_time + time_list[index+1] + gap

    return new_work_flow_record
        
