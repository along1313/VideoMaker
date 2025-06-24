from re import S
import sys
import os
import json
from dotenv import load_dotenv
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service.ai_service import LLMService, ImageModelService, TTSModelService, VideoModelService
from service.script_service import ScriptService
from service.picture_prompt_service import PicturePromptService
from service.picture_generate_service import PictureGenerateService
from service.voice_generate_service import VoiceGenerateService
from utility import parse_json, func_and_retry_parse_json
from workflow import generate_picture, generate_audio, add_time, generate_video, generate_cover


async def run_work_flow_v2(
    text, 
    result_dir, 
    user_id, 
    style: str, 
    llm_model_str = "glm-z1-flash", 
    image_model_str ="cogview-3-flash", 
    tts_model_str = "cosyvoice-v1", 
    is_already_have_script = False,
    json_retry_times = 3,
    is_generate_title_picture = False,
    title_picture_path = None,
    screan_size = (1280,720), 
    title_font_path = "lib/font/AlibabaPuHuiTi-3-65-Medium.ttf", 
    is_generate_title_audio = False,
    title_audio_text = None,
    caption_text_font_path = "lib/font/AlibabaPuHuiTi-3-55-Regular.ttf",
    cover_font_path= "lib/font/AlibabaPuHuiTi-3-115-Black.ttf", 
    bg_pic_path = None,
    bgm_path = "lib/music/bgm.wav", 
    user_name = "百速AI",
    
    **kwargs
    ):
    """
    1. 生成视频脚本
    2. 生成插页prompt
    3. 生成图片
    4. 生成音频
    5. 添加时间
    6. 生成视频
    7. 生成封面

    :param text: 用户输入的文本
    :param result_dir: 结果目录
    :param user_id: 用户ID
    :param style: 风格
    :param llm_model_str: LLM模型
    :param image_model_str: 图片模型
    :param tts_model_str: TTS模型
    :param is_already_have_script: 是否已经提供脚本
    :param is_generate_title_picture: 是否生成标题图片
    :param title_picture_path: 标题图片路径
    :param screan_size: 屏幕大小
    :param title_font_path: 标题字体路径
    :param cover_font_path: 封面字体路径
    """

    llm = LLMService(model_str=llm_model_str)
    image_model = ImageModelService(model_str=image_model_str)
    tts_model = TTSModelService(model_str=tts_model_str)
    

    print(f'#####Work Flow 1 生成视频脚本####')
    # 生成视频脚本
    script_service = ScriptService(llm)

    if is_already_have_script == False:
        # 如果用户没有提供脚本，则生成脚本
        text = script_service.generate_text(text)
        print(text)
    
    work_flow_record = await func_and_retry_parse_json(text, script_service.generate_json, json_retry_times)

    if work_flow_record is None:
        print(f'结构化失败, 超过{json_retry_times}次尝试')
        return

    print(work_flow_record) # 打印work_flow_record
  
    # 使用项目标题作为项目ID
    project_id = work_flow_record['title']
    # 创建项目目录
    project_dir = os.path.join(result_dir, user_id, project_id)
    os.makedirs(project_dir, exist_ok=True)

    # 将work_flow_record保存到文件中
    with open(os.path.join(project_dir, "work_flow_record.json"), "w") as f:
        json.dump(work_flow_record, f, ensure_ascii=False)


    print(f'#####Work Flow 2 插页prompt生成####')
    picture_prompt_service = PicturePromptService(llm)
    work_flow_record = await func_and_retry_parse_json(work_flow_record, picture_prompt_service.generate, json_retry_times, style=style)
    if work_flow_record is None:
        print(f'结构化失败, 超过{json_retry_times}次尝试')
        return
    print(work_flow_record) #   打印work_flow_record

    print(f'#####Work Flow 3 图片生成####')
    #创建图片目录
    image_dir = os.path.join(project_dir, "images")
    os.makedirs(image_dir, exist_ok=True)

    # 生成图片
    picture_generate_service = PictureGenerateService(image_model)
    work_flow_record = await generate_picture(
        work_flow_record, 
        picture_generate_service, 
        image_dir, 
        style=style,
        is_generate_title_picture=is_generate_title_picture,
        title_picture_path=title_picture_path,
        title_font_path=title_font_path,
        img_size=screan_size,
        **kwargs
    )
    print(work_flow_record)
    # 将work_flow_record保存到文件中
    with open(os.path.join(project_dir, "work_flow_record.json"), "w") as f:
        json.dump(work_flow_record, f, ensure_ascii=False)


    
    print(f'#####Work Flow 4 音频生成####')
        
    # 创建音频目录
    audio_dir = os.path.join(project_dir, "audios")
    os.makedirs(audio_dir, exist_ok=True)

    # 生成语音
    work_flow_record = generate_audio(
        work_flow_record, 
        audio_dir, 
        tts_model,
        is_generate_title_audio=is_generate_title_audio,
        title_audio_text=title_audio_text
    )
    print(work_flow_record)
    # 将work_flow_record保存到文件中
    with open(os.path.join(project_dir, "work_flow_record.json"), "w") as f:
        json.dump(work_flow_record, f, ensure_ascii=False)

    print(f'#####Work Flow 5 时间添加####')
    # 增加时间
    work_flow_record = add_time(work_flow_record, audio_dir, gap=1.0)
    print(work_flow_record)
    # 将work_flow_record保存到文件中
    with open(os.path.join(project_dir, "work_flow_record.json"), "w") as f:
        json.dump(work_flow_record, f, ensure_ascii=False)
    

    print(f'#####Work Flow 6 视频生成####')
    # 生成视频
    generate_video(work_flow_record=work_flow_record, 
                   style=style, 
                   result_dir=project_dir, 
                   user_name=user_name, 
                   font_path=caption_text_font_path, 
                   screan_size=screan_size, 
                   bg_pic_path=bg_pic_path,
                   bgm_path=bgm_path,
                   is_display_title=True)   
    print(f'视频生成完成')

    print(f'#####Work Flow 7 封面生成####')
    # 创建封面目录
    cover_dir = os.path.join(project_dir, "covers")
    os.makedirs(cover_dir, exist_ok=True)
    # 生成封面
    work_flow_record = generate_cover(work_flow_record, project_dir, font_path=cover_font_path)
    print (f'封面生成完成')

    


    




    pass


def run_work_flow_v1(text, result_dir, user_id, style: str, llm: LLMService, image_model: ImageModelService, tts_model: TTSModelService, screan_size = (1280,720), font_path = None, cover_font_path= None, bgm_path = None, user_name = None):
    # 配置字体和背景目录
    if font_path is None:
        font_path = os.path.join(os.environ.get("FONT_DIR"), "STHeiti Medium.ttc")

    if cover_font_path is None:
        cover_font_path = os.path.join(os.environ.get("FONT_DIR"), "字制区喜脉体.ttf")

    if bgm_path is None:
        bgm_path = os.path.join(os.environ.get("MUSIC_DIR"), "bgm.wav")

    n_retry = 0

    print(f'#####Work Flow 1 生成视频脚本####')
    # 生成视频脚本
    script_service = ScriptService(llm)
    script = script_service.generate_text(text)
    print(script)
    work_flow_record = script_service.generate_json(script)
    
    print(work_flow_record) # 打印work_flow_record

    # 尝试parse_json(work_flow_record)，如果失败则重新work_flow_record = script_service.generate_json(script)，一共尝试3次
    while n_retry < 3:
        try:
            parsed_record = parse_json(work_flow_record)
            if parsed_record is None:
                # 如果parse_json返回None，说明解析失败
                raise Exception("解析返回None")
            work_flow_record = parsed_record
            break
        except Exception as e:
            n_retry += 1
            print(f'结构化失败: {str(e)}, retry {n_retry} times')
            work_flow_record = script_service.generate_json(script)

    if n_retry >= 3:
        print(f'结构化失败, 超过3次尝试')
        return
    else:
        n_retry = 0
    # 使用项目标题作为项目ID
    project_id = work_flow_record['title']

    # 创建项目目录
    project_dir = os.path.join(result_dir, user_id, project_id)
    os.makedirs(project_dir, exist_ok=True)

    # 将work_flow_record保存到文件中
    with open(os.path.join(project_dir, "work_flow_record.json"), "w") as f:
        json.dump(work_flow_record, f, ensure_ascii=False)

    print(f'#####Work Flow 2 插页prompt生成####')

    # 生成插页prompt
    picture_prompt_service = PicturePromptService(llm)
    work_flow_record = picture_prompt_service.generate(work_flow_record, style)
    print(work_flow_record) #   打印work_flow_record
    # 尝试parse_json(work_flow_record)，如果失败则重新work_flow_record = picture_prompt_service.generate(work_flow_record, style)，一共尝试3次
    while n_retry < 3:
        try:
            parsed_record = parse_json(work_flow_record)
            if parsed_record is None:
                # 如果parse_json返回None，说明解析失败
                raise Exception("解析返回None")
            work_flow_record = parsed_record
            break
        except Exception as e:
            n_retry += 1
            print(f'结构化失败: {str(e)}, retry {n_retry} times')
            # 从项目目录中读取work_flow_record.json
            with open(os.path.join(project_dir, "work_flow_record.json"), "r") as f:
                work_flow_record = json.load(f)
            work_flow_record = picture_prompt_service.generate(work_flow_record, style)
    if n_retry >= 3:
        print(f'结构化失败, 超过3次尝试')
        return
    else:
        n_retry = 0
    # 将work_flow_record保存到文件中
    with open(os.path.join(project_dir, "work_flow_record.json"), "w") as f:
        json.dump(work_flow_record, f, ensure_ascii=False)
    print(work_flow_record) # 打印work_flow_record

    print(f'#####Work Flow 3 图片生成####')

    #创建图片目录
    image_dir = os.path.join(project_dir, "images")
    os.makedirs(image_dir, exist_ok=True)

    # 生成图片
    picture_generate_service = PictureGenerateService(image_model)
    work_flow_record = generate_picture(work_flow_record, picture_generate_service, image_dir, style=style)
    print(work_flow_record)
    # 将work_flow_record保存到文件中
    with open(os.path.join(project_dir, "work_flow_record.json"), "w") as f:
        json.dump(work_flow_record, f, ensure_ascii=False)


    print(f'#####Work Flow 4 音频生成####')

        
    # 创建音频目录
    audio_dir = os.path.join(project_dir, "audios")
    os.makedirs(audio_dir, exist_ok=True)

    # 生成语音
    work_flow_record = generate_audio(work_flow_record, audio_dir, tts_model)
    print(work_flow_record)
    # 将work_flow_record保存到文件中
    with open(os.path.join(project_dir, "work_flow_record.json"), "w") as f:
        json.dump(work_flow_record, f, ensure_ascii=False)

    
    print(f'#####Work Flow 5 时间添加####')
    # 增加时间
    work_flow_record = add_time(work_flow_record, audio_dir, gap=1.0)
    print(work_flow_record)
    # 将work_flow_record保存到文件中
    with open(os.path.join(project_dir, "work_flow_record.json"), "w") as f:
        json.dump(work_flow_record, f, ensure_ascii=False)

    print(f'#####Work Flow 6 视频生成####')
    # 生成视频
    generate_video(work_flow_record, style, project_dir, user_name=user_name, font_path=font_path, screan_size=screan_size, bgm_path=bgm_path)
    print(f'视频生成完成')

    print(f'#####Work Flow 7 封面生成####')
    # 创建封面目录
    cover_dir = os.path.join(project_dir, "covers")
    os.makedirs(cover_dir, exist_ok=True)
    # 生成封面
    work_flow_record = generate_cover(work_flow_record, project_dir, font_path=cover_font_path)
    print (f'封面生成完成')


def run_work_flow_with_script(script, result_dir, user_id, style: str, llm: LLMService, image_model: ImageModelService, tts_model: TTSModelService, screan_size = (1280,720), font_path = None, cover_font_path= None, bgm_path = None, user_name = None):
    # 配置字体和背景目录
    if font_path is None:
        font_path = os.path.join(os.environ.get("FONT_DIR"), "STHeiti Medium.ttc")

    if cover_font_path is None:
        cover_font_path = os.path.join(os.environ.get("FONT_DIR"), "字制区喜脉体.ttf")

    if bgm_path is None:
        bgm_path = os.path.join(os.environ.get("MUSIC_DIR"), "bgm.wav")

    n_retry = 0

    print(f'#####Work Flow 1 生成视频脚本####')
    # 生成视频脚本
    script_service = ScriptService(llm)
    work_flow_record = script_service.generate_json(script)
    
    print(work_flow_record) # 打印work_flow_record

    # 尝试parse_json(work_flow_record)，如果失败则重新work_flow_record = script_service.generate_json(script)，一共尝试3次
    while n_retry < 3:
        try:
            parsed_record = parse_json(work_flow_record)
            if parsed_record is None:
                # 如果parse_json返回None，说明解析失败
                raise Exception("解析返回None")
            work_flow_record = parsed_record
            break
        except Exception as e:
            n_retry += 1
            print(f'结构化失败: {str(e)}, retry {n_retry} times')
            work_flow_record = script_service.generate_json(script)

    if n_retry >= 3:
        print(f'结构化失败, 超过3次尝试')
        return
    else:
        n_retry = 0
    # 使用项目标题作为项目ID
    project_id = work_flow_record['title']

    # 创建项目目录
    project_dir = os.path.join(result_dir, user_id, project_id)
    os.makedirs(project_dir, exist_ok=True)

    # 将work_flow_record保存到文件中
    with open(os.path.join(project_dir, "work_flow_record.json"), "w") as f:
        json.dump(work_flow_record, f, ensure_ascii=False)

    print(f'#####Work Flow 2 插页prompt生成####')

    # 生成插页prompt
    picture_prompt_service = PicturePromptService(llm)
    work_flow_record = picture_prompt_service.generate(work_flow_record, style)
    print(work_flow_record) #   打印work_flow_record
    # 尝试parse_json(work_flow_record)，如果失败则重新work_flow_record = picture_prompt_service.generate(work_flow_record, style)，一共尝试3次
    while n_retry < 3:
        try:
            parsed_record = parse_json(work_flow_record)
            if parsed_record is None:
                # 如果parse_json返回None，说明解析失败
                raise Exception("解析返回None")
            work_flow_record = parsed_record
            break
        except Exception as e:
            n_retry += 1
            print(f'结构化失败: {str(e)}, retry {n_retry} times')
            # 从项目目录中读取work_flow_record.json
            with open(os.path.join(project_dir, "work_flow_record.json"), "r") as f:
                work_flow_record = json.load(f)
            work_flow_record = picture_prompt_service.generate(work_flow_record, style)
    if n_retry >= 3:
        print(f'结构化失败, 超过3次尝试')
        return
    else:
        n_retry = 0
    # 将work_flow_record保存到文件中
    with open(os.path.join(project_dir, "work_flow_record.json"), "w") as f:
        json.dump(work_flow_record, f, ensure_ascii=False)
    print(work_flow_record) # 打印work_flow_record

    print(f'#####Work Flow 3 图片生成####')

    #创建图片目录
    image_dir = os.path.join(project_dir, "images")
    os.makedirs(image_dir, exist_ok=True)

    # 生成图片
    picture_generate_service = PictureGenerateService(image_model)
    work_flow_record = generate_picture(work_flow_record, picture_generate_service, image_dir, style=style)
    print(work_flow_record)
    # 将work_flow_record保存到文件中
    with open(os.path.join(project_dir, "work_flow_record.json"), "w") as f:
        json.dump(work_flow_record, f, ensure_ascii=False)


    print(f'#####Work Flow 4 音频生成####')

        
    # 创建音频目录
    audio_dir = os.path.join(project_dir, "audios")
    os.makedirs(audio_dir, exist_ok=True)

    # 生成语音
    work_flow_record = generate_audio(work_flow_record, audio_dir, tts_model)
    print(work_flow_record)
    # 将work_flow_record保存到文件中
    with open(os.path.join(project_dir, "work_flow_record.json"), "w") as f:
        json.dump(work_flow_record, f, ensure_ascii=False)

    
    print(f'#####Work Flow 5 时间添加####')
    # 增加时间
    work_flow_record = add_time(work_flow_record, audio_dir, gap=1.0)
    print(work_flow_record)
    # 将work_flow_record保存到文件中
    with open(os.path.join(project_dir, "work_flow_record.json"), "w") as f:
        json.dump(work_flow_record, f, ensure_ascii=False)

    print(f'#####Work Flow 6 视频生成####')
    # 生成视频
    generate_video(work_flow_record, style, project_dir, user_name=user_name, font_path=font_path, screan_size=screan_size, bgm_path=bgm_path)
    print(f'视频生成完成')

    print(f'#####Work Flow 7 封面生成####')
    # 创建封面目录
    cover_dir = os.path.join(project_dir, "covers")
    os.makedirs(cover_dir, exist_ok=True)
    # 生成封面
    work_flow_record = generate_cover(work_flow_record, project_dir, font_path=cover_font_path)
    print (f'封面生成完成')






# 实例化模型
# 只在直接运行此文件时才会执行下面的测试代码
if __name__ == '__main__':
    llm_str = "glm-z1-flash"
    image_model_str = "cogview-3-flash"
    tts_model_str = "cosyvoice-v1"
    result_dir = "./workstore"
    user_id = "user1"
    style = "绘本"
    text = "创作一个丑小鸭的故事"
    asyncio.run(run_work_flow_v2(
        text, 
        result_dir, 
        user_id, 
        style, 
        llm_str, 
        image_model_str, 
        tts_model_str, 
        user_name="百速AI"))


    

























 










