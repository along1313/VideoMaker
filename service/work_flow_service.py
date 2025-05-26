from re import S
import sys
import os
import json
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service.ai_service import LLMService, ImageModelService, TTSModelService
from service.script_service import ScriptService
from service.picture_prompt_service import PicturePromptService
from service.picture_generate_service import PictureGenerateService
from service.voice_generate_service import VoiceGenerateService
from utility import parse_json
from workflow import generate_picture, generate_audio, add_time, generate_video, generate_cover


def run_work_flow(text, result_dir, user_id, style: str, llm: LLMService, image_model: ImageModelService, tts_model: TTSModelService, screan_size = (1280,720), font_path = None, cover_font_path= None, bgm_path = None, user_name = None):
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
    llm = LLMService()
    image_model = ImageModelService()
    tts_model = TTSModelService()
    result_dir = "./workstore"
    user_id = "user1"
    project_id = ""
    style = "绘本"
    text = "创作一个买火柴的小女孩的原作故事的视频"
    run_work_flow(text, result_dir, user_id, style, llm, image_model, tts_model, user_name="童话天地")


    

























 










