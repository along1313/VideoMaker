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
from utility import parse_json, func_and_retry_parse_json
from workflow import generate_picture_from_json, generate_audio, add_time, generate_video, generate_cover
from static.style_config import TEMPLATE_CONFIG


async def run_work_flow_v3(
    text: str, 
    result_dir: str, 
    user_id: str, 
    style: str, 
    template: str,
    llm_model_str: str = "deepseek-reasoner", 
    image_model_str: str = "cogview-3-flash", 
    tts_model_str: str = "cosyvoice-v1", 
    is_prompt_mode = True,
    json_retry_times = 3,
    uploaded_title_picture_path = None,
    input_title_voice_text = None,
    screan_size = (1280,720), 
    title_font_path = "lib/font/字制区喜脉体.ttf", 
    caption_text_font_path = "lib/font/STHeiti Medium.ttc",
    cover_font_path= "lib/font/字制区喜脉体.ttf", 
    bg_pic_path = None,
    bgm_path = "lib/music/bgm.wav", 
    user_name = "百速AI",
    is_display_title = True,
    is_need_ad_end = False,
    **kwargs
):
    """
    1. 生成视频脚本json
    2. 生成插页
    3. 生成音频
    4. 添加时间
    5. 生成视频
    """
    
    print(f'#####Work Flow 1 生成视频脚本json####')
    llm = LLMService(model_str=llm_model_str)
    script_service = ScriptService(llm)
    if is_prompt_mode == True:
        work_flow_record = await func_and_retry_parse_json(text, script_service.generate_json_script_from_prompt, json_retry_times)
    else:
        work_flow_record = await func_and_retry_parse_json(text, script_service.generate_json_script_from_text, json_retry_times)
    
    print(work_flow_record)
    
    # 确保用户目录存在
    user_dir = os.path.join(result_dir, user_id)
    os.makedirs(user_dir, exist_ok=True)
    
    with open(os.path.join(user_dir, "work_flow_record.json"), "w") as f:
        json.dump(work_flow_record, f, ensure_ascii=False)

    if work_flow_record is None:
        print(f'结构化失败, 超过{json_retry_times}次尝试')
        return
    
    
    ###########整理项目##########
    # 使用项目标题作为项目ID
    project_id = work_flow_record['title']
    # 创建项目目录
    project_dir = os.path.join(result_dir, user_id, project_id)
    os.makedirs(project_dir, exist_ok=True)
    
    # 初始化work_flow_record
    work_flow_record['title_picture_path'] = ""
    work_flow_record['title_voice_text'] = ""
    work_flow_record['title_audio_path'] = ""

    if template == "通用":
        template_config = TEMPLATE_CONFIG[template]['config'].copy()
    elif template == "读一本书":
        template_config = TEMPLATE_CONFIG[template]['config'].copy()
        work_flow_record['title_picture_path'] = uploaded_title_picture_path
        work_flow_record['title_voice_text'] = f'今天,我们来读{input_title_voice_text}这本书'
    elif template == "故事":
        template_config = TEMPLATE_CONFIG[template]['config'].copy()
        work_flow_record['title_voice_text'] = work_flow_record['title']
    elif template == "讲经":
        template_config = TEMPLATE_CONFIG[template]['config'].copy()
    else:
        print(f'模板{template}不存在')
        return
    
    # 确保 voice_name 参数被传递
    template_config['voice_name'] = template_config.get('voice_name', 'default')

    print(f'#####Work Flow 2 生成插页####')
      #创建图片目录
    image_dir = os.path.join(project_dir, "images")
    os.makedirs(image_dir, exist_ok=True)
    
    # 生成图片
    image_model = ImageModelService(model_str=image_model_str)
    picture_generate_service = PictureGenerateService(image_model)
    work_flow_record = await generate_picture_from_json(
        work_flow_record, 
        picture_generate_service, 
        image_dir, 
        style=style,
        title_font_path=title_font_path,
        screen_size=screan_size,      
        **template_config,
        **kwargs
    )
    print(work_flow_record)
    with open(os.path.join(project_dir, "work_flow_record.json"), "w") as f:
        json.dump(work_flow_record, f, ensure_ascii=False)

    print(f'#####Work Flow 3 生成音频####')
    # 创建音频目录
    audio_dir = os.path.join(project_dir, "audios")
    os.makedirs(audio_dir, exist_ok=True)

    tts_model = TTSModelService(model_str=tts_model_str)
    work_flow_record = generate_audio(
        work_flow_record, 
        audio_dir, 
        tts_model,
        **template_config,
        **kwargs
    )
    print(work_flow_record)
    with open(os.path.join(project_dir, "work_flow_record.json"), "w") as f:
        json.dump(work_flow_record, f, ensure_ascii=False)

    print(f'#####Work Flow 4 添加时间####')
    work_flow_record = add_time(work_flow_record, audio_dir, gap=1.0)
    print(work_flow_record)
    with open(os.path.join(project_dir, "work_flow_record.json"), "w") as f:
        json.dump(work_flow_record, f, ensure_ascii=False)

    
    print(f'#####Work Flow 5 视频生成####')
    # 生成视频
    generate_video(work_flow_record=work_flow_record, 
                   style=style, 
                   template=template,
                   result_dir=project_dir, 
                   user_name=user_name, 
                   font_path=caption_text_font_path, 
                   screan_size=screan_size, 
                   bg_pic_path=bg_pic_path,
                   bgm_path=bgm_path,
                   is_display_title=is_display_title,
                   is_need_ad_end=is_need_ad_end)   
    print(f'视频生成完成')

    print(f'#####Work Flow 6 封面生成####')
    # 创建封面目录
    cover_dir = os.path.join(project_dir, "covers")
    os.makedirs(cover_dir, exist_ok=True)
    # 生成封面
    work_flow_record = generate_cover(work_flow_record, project_dir, font_path=cover_font_path)
    print (f'封面生成完成')


async def run_work_flow_v3_with_progress(
    text: str, 
    result_dir: str, 
    user_id: str,  #使用用户的id作为项目目录的名称
    style: str, 
    template: str,
    llm_model_str: str = "deepseek-reasoner", 
    image_model_str: str = "cogview-3-flash", 
    tts_model_str: str = "cosyvoice-v1", 
    is_prompt_mode = True,
    json_retry_times = 3,
    uploaded_title_picture_path = None,
    input_title_voice_text = None,
    screan_size = (1280,720), 
    title_font_path = "lib/font/字制区喜脉体.ttf", 
    caption_text_font_path = "lib/font/STHeiti Medium.ttc",
    cover_font_path= "lib/font/字制区喜脉体.ttf", 
    bg_pic_path = None,
    bgm_path = "lib/music/bgm.wav", 
    user_name = "百速AI",
    is_display_title = True,
    is_need_ad_end = False,
    task_id = None,
    generation_status = None,
    **kwargs
):
    """
    带进度追踪的工作流v3
    1. 生成视频脚本json
    2. 生成插页
    3. 生成音频
    4. 添加时间
    5. 生成视频
    """
    # 动态选择 tts_model_str 和 voice_name
    template_config = TEMPLATE_CONFIG.get(template, {}).get('config', {})
    tts_model_str = template_config.get('tts_model_str', tts_model_str)
    voice_name = template_config.get('voice_name', 'default')
    
    def update_progress(step, message, progress):
        """更新进度状态"""
        if task_id and generation_status and task_id in generation_status:
            generation_status[task_id]['current_step'] = step
            generation_status[task_id]['progress'] = progress
            generation_status[task_id]['message'] = message
            generation_status[task_id]['logs'].append(f"步骤{step}: {message}")
            print(f"[进度更新] 步骤{step}: {message} ({progress}%)")

    def check_cancellation():
        """检查任务是否被用户取消"""
        if task_id and generation_status and task_id in generation_status:
            if generation_status[task_id].get('status') == 'cancelled':
                print(f"[工作流] 检测到任务被取消，任务ID: {task_id}")
                raise Exception("任务被用户主动取消")

    def cleanup_partial_files(project_dir):
        """清理部分生成的文件"""
        try:
            if os.path.exists(project_dir):
                import shutil
                shutil.rmtree(project_dir)
                print(f"[清理] 已删除部分生成的项目目录: {project_dir}")
        except Exception as e:
            print(f"[清理] 清理部分文件失败: {str(e)}")

    print(f"llm_model_str: {llm_model_str}")
    print(f"image_model_str: {image_model_str}")
    print(f"tts_model_str: {tts_model_str}")
    print(f"template: {template}")
    print(f"style: {style}")

    try:
        # 检查取消状态 - 开始前
        check_cancellation()
        
        update_progress(1, '正在撰写脚本', 10)
        print(f'#####Work Flow 1 生成视频脚本json####')
        
        # 实例化服务
        llm = LLMService(model_str=llm_model_str)
        script_service = ScriptService(llm)
        
        # 生成脚本
        if is_prompt_mode == True:
            work_flow_record = await func_and_retry_parse_json(text, script_service.generate_json_script_from_prompt, json_retry_times)
        else:
            work_flow_record = await func_and_retry_parse_json(text, script_service.generate_json_script_from_text, json_retry_times)
        
        # 检查取消状态 - 脚本生成后
        check_cancellation()
        
        print(work_flow_record)
        
        # 确保用户目录存在
        user_dir = os.path.join(result_dir, user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        with open(os.path.join(user_dir, "work_flow_record.json"), "w") as f:
            json.dump(work_flow_record, f, ensure_ascii=False)

        if work_flow_record is None:
            print(f'结构化失败, 超过{json_retry_times}次尝试')
            return
        
        ###########整理项目##########
        # 使用项目标题作为项目ID
        project_id = work_flow_record['title']
        # 创建项目目录
        project_dir = os.path.join(result_dir, user_id, project_id)
        os.makedirs(project_dir, exist_ok=True)
        
        # 初始化work_flow_record
        work_flow_record['title_picture_path'] = ""
        work_flow_record['title_voice_text'] = ""
        work_flow_record['title_audio_path'] = ""

        if template == "通用" or template == "讲经":
            template_config = TEMPLATE_CONFIG[template]['config'].copy()
        elif template == "读一本书":
            template_config = TEMPLATE_CONFIG[template]['config'].copy()
            work_flow_record['title_picture_path'] = uploaded_title_picture_path
            work_flow_record['title_voice_text'] = f'今天,我们来读{input_title_voice_text}这本书'
        elif template == "故事":
            template_config = TEMPLATE_CONFIG[template]['config'].copy()
            work_flow_record['title_voice_text'] = work_flow_record['title']
        else:
            print(f'模板{template}不存在')
            return
        
        # 确保 voice_name 参数被传递
        template_config['voice_name'] = voice_name
        
        # 保存工作流记录
        with open(os.path.join(project_dir, "work_flow_record.json"), "w") as f:
            json.dump(work_flow_record, f, ensure_ascii=False)

        # 检查取消状态 - 图片生成前
        check_cancellation()
        
        update_progress(2, '正在制作图片', 30)
        print(f'#####Work Flow 2 图片生成####')
        # 创建图片目录
        image_dir = os.path.join(project_dir, "images")
        os.makedirs(image_dir, exist_ok=True)

        # 生成图片
        image_model = ImageModelService(model_str=image_model_str)
        picture_generate_service = PictureGenerateService(image_model)
        work_flow_record = await generate_picture_from_json(
            work_flow_record, 
            picture_generate_service, 
            image_dir, 
            style=style,
            title_font_path=title_font_path,
            screen_size=screan_size,      
            **template_config,
            **kwargs
        )
        
        with open(os.path.join(project_dir, "work_flow_record.json"), "w") as f:
            json.dump(work_flow_record, f, ensure_ascii=False)

        # 检查取消状态 - 音频生成前
        check_cancellation()
        
        update_progress(3, '正在录制语音', 50)
        print(f'#####Work Flow 3 生成音频####')
        # 创建音频目录
        audio_dir = os.path.join(project_dir, "audios")
        os.makedirs(audio_dir, exist_ok=True)

        tts_model = TTSModelService(model_str=tts_model_str)
        work_flow_record = await asyncio.to_thread(
            generate_audio,
            work_flow_record, 
            audio_dir, 
            tts_model,
            **template_config,
            **kwargs
        )
        
        with open(os.path.join(project_dir, "work_flow_record.json"), "w") as f:
            json.dump(work_flow_record, f, ensure_ascii=False)

        # 检查取消状态 - 时间轴处理前
        check_cancellation()
        
        #update_progress(4, '正在处理素材', 70)
        print(f'#####Work Flow 4 添加时间####')
        work_flow_record = add_time(work_flow_record, audio_dir, gap=1.0)
        
        with open(os.path.join(project_dir, "work_flow_record.json"), "w") as f:
            json.dump(work_flow_record, f, ensure_ascii=False)

        # 检查取消状态 - 视频生成前
        check_cancellation()
        
        update_progress(4, '正在剪辑视频', 85)
        print(f'#####Work Flow 5 视频生成####')
        # 生成视频
        generate_video(work_flow_record=work_flow_record, 
                       style=style, 
                       template=template,
                       result_dir=project_dir, 
                       user_name=user_name, 
                       font_path=caption_text_font_path, 
                       screan_size=screan_size, 
                       bg_pic_path=bg_pic_path,
                       bgm_path=bgm_path,
                       is_display_title=is_display_title,
                       is_need_ad_end=is_need_ad_end)   
        print(f'视频生成完成')

        # 检查取消状态 - 封面生成前
        check_cancellation()
        
        update_progress(5, '正在制作封面', 95)
        print(f'#####Work Flow 6 封面生成####')
        # 创建封面目录
        cover_dir = os.path.join(project_dir, "covers")
        os.makedirs(cover_dir, exist_ok=True)

        # 生成封面
        work_flow_record = generate_cover(work_flow_record, project_dir, font_path=cover_font_path)
        print(f'封面生成完成')

        update_progress(6, '视频生成完成！', 100)
        print(f'#####Work Flow 完成####')
        
        return work_flow_record
        
    except Exception as e:
        error_message = str(e)
        if "取消" in error_message:
            print(f"[工作流] 任务被用户取消: {error_message}")
            # 清理部分生成的文件
            if 'project_dir' in locals():
                cleanup_partial_files(project_dir)
        else:
            print(f"[工作流] 生成过程中发生错误: {error_message}")
        
        if task_id and generation_status and task_id in generation_status:
            if "取消" in error_message:
                generation_status[task_id]['status'] = 'cancelled'
                generation_status[task_id]['message'] = '用户主动停止生成'
            else:
                generation_status[task_id]['status'] = 'failed'
                generation_status[task_id]['message'] = f'生成失败: {error_message}'
        raise e

