TEMPLATE_CONFIG = {
    "通用": {
        "description": "可以生成心理学科普，教育，解说等普通视频",
        "config": {
            "template": "通用",
            "tts_model_str": "speech-02-turbo",
            "voice_name": "Chinese (Mandarin)_Wise_Women",
            "is_generate_title_picture": False,
            "is_generate_title_audio": False,
            "title_picture_resize": 1.0
        }
    },
    "读一本书": {
        "description": "用于生成读一本书视频，需要上传书本封面图片和给出书名，并且给出视频文案，仅支持文案模式",
        "config": {
            "template": "读一本书",
            "tts_model_str": "speech-02-turbo",
            "voice_name": "Chinese (Mandarin)_Wise_Women",
            "is_generate_title_picture": False,
            "is_generate_title_audio": True,
            "title_picture_resize": 0.4
        }
    },
    "故事": {
        "description": "用于生成故事类视频，开头有标题画面，并且语音朗读标题",
        "config": {
            "template": "故事",
            "tts_model_str": "speech-02-turbo",
            "voice_name": "Chinese (Mandarin)_Wise_Women",
            "is_generate_title_picture": True,
            "is_generate_title_audio": True,
            "title_picture_resize": 1.0
        }
    },
    "讲经": {
        "description": "用于生成解读经典，玄学等视频, 沉稳男性语音",
        "config": {
            "template": "讲经",
            "tts_model_str": "speech-02-turbo",
            "voice_name": "Chinese (Mandarin)_Lyrical_Voice",
            "is_generate_title_picture": False,
            "is_generate_title_audio": False,
            "title_picture_resize": 1.0,
        }
    }

}

STYLE_CONFIG = {
    "黑白矢量图": {
        "img_prompt_system_prompt": """
        从以下JSON格式的文案中，根据各个分镜的"picture_description"和"voice_text"的内容生成prompt，用于使用图像模型生成插页。
        1. 根据"picture_description"中各个分镜描述和"voice_text"的朗读内容和长度，先思考每个分镜用几张图片表现，要求图片内容不要重复或太相近，图片控制在1-2张，然后为每张图片生成prompt用于生成图片。
        2. prompt要能够生成黑白单色粗线条矢量图，不要有动态描述。
        3. 抓住重点，不要描述太多细节，尽量保持画面简单。
        4. 图片中尽量不要出现具体的文字。
        5. 内容完整，不要有省略。
        6. 生成的prompt不要有不安全或敏感文本。
        7. 将生成的prompt以以下格式加入到原分镜描述JSON中，不改变原JSON的内容，以"picture_prompt"字段表示，格式如下
        
         {
            "title": "...", # 标题
            "content":[
                {
                    "index": "...", # 分镜编号，从0开始
                    "picture_description": "...", # 插页描述
                    "picture_prompt": [
                        "prompt1",
                        ...
                    ], # 加入你生成的1-2个插页prompt
                    "voice_text": "..." # 人声朗读文本
                },
                ...
            ],
            "total_count": n # 总条数
        }
        """,
        "img_generate_system_prompt":"黑白矢量剪影图, 底色为白色，极简主义风格, 高对比度, 纯黑白色块, 无渐变色, 流畅线条, 平面化设计，轮廓清晰，类SVG格式矢量文件，人物为火柴人风格。",
        "img_size": "1024x1024",
        "img_resize": 0.4,
        "text_color": "black",
        "stroke_color": None,
        "is_y_slide": False,
    },
    "绘本": {
        "img_prompt_system_prompt": """
        从以下JSON格式的文案中，根据"picture_description"中各个分镜描述生成英文prompt，用于使用图像模型生成插页。
        1. 根据"picture_description"中各个分镜描述和"voice_text"的内容和长度，先思考每个分镜分别用几张图片表现，要求图片内容不要重复或太相近，图片控制在1-2张，去掉重复或者内容相近的图片，每个分镜的图片数量不一定要一样，然后为每张图片生成prompt用于生成图片。
        2. 描述要完整，保证前后生成一致性。
        3. 画面尽量色彩丰富。
        4. 图片中尽量不要出现具体的文字。
        5. 内容完整不要有省略。
        6. 生成的prompt不要有不安全或敏感文本。
        7. 将生成的prompt以以下格式加入到原分镜描述JSON中，不改变原JSON的内容，以"picture_prompt"字段表示，格式如下
        
         {
            "title": "...", # 标题
            "content":[
                {
                    "index": "...", # 分镜编号，从0开始
                    "picture_description": "...", # 插页描述
                    "picture_prompt": [
                        "prompt1",
                        ...
                    ], # 加入你生成的1-2个插页prompt
                    "voice_text": "..." # 人声朗读文本
                },
                ...
            ],
            "total_count": n # 总条数
        }
        """,
        "img_generate_system_prompt": "生成水彩绘本风格的图片, 柔和的水彩质感，明亮温暖的色调, 童话般的场景, 细腻的笔触细节, 动态元素点缀, 整体保持90%饱和度+70%亮度值, 色彩搭配参考莫兰迪色系调整，不要出现现实的相片风格.",
        "img_size": "1024x1024",
        "img_resize": 1.0,
        "text_color": "white",
        "stroke_color": "black",
        "is_y_slide": True,
    },
    "3D景深": {
        "img_prompt_system_prompt": """
        从给定的JSON格式的文案中，根据"picture_description"中各个分镜描述生成英文prompt，用于使用图像模型生成插页。
        1. 根据"picture_description"中各个分镜描述和"voice_text"的内容和长度，先思考每个分镜分别用几张图片表现，要求图片内容不要重复或太相近，图片控制在1-2张，去掉重复或者内容相近的图片，每个分镜的图片数量不一定要一样，然后为每张图片生成prompt用于生成图片。
        2. 描述要完整，保证前后生成一致性。
        3. 图片中尽量不要出现具体的文字。
        4. 内容完整不要有省略。
        5. 生成的prompt不要有不安全或敏感文本。
        6. 将生成的prompt以以下格式加入到原分镜描述JSON中，不改变原JSON的内容，以"picture_prompt"字段表示，格式如下：
        
         {
            "title": "...", # 标题
            "content":[
                {
                    "index": "...", # 分镜编号，从0开始
                    "picture_description": "...", # 插页描述
                    "picture_prompt": [
                        "prompt1",
                        ...
                    ], # 加入你生成的1-2个插页prompt
                    "voice_text": "..." # 人声朗读文本
                },
                ...
            ],
            "total_count": n # 总条数
        }
        """,
        "img_generate_system_prompt": "A bright and colorful 3D cartoon scene with a paper cutout style。Detailed textures for the characters and environment to enhance the 3D effect,纸片角色边缘用白色描边。",
        "img_size": "1024x1024",
        "img_resize": 1.0,
        "text_color": "white",
        "stroke_color": "black",
        "is_y_slide": True,
    },
    "水墨画": {
        "img_generate_system_prompt": "--niji 5 --style raw 国画风格，柔和毛笔质感，意境淡雅，构图简洁，纯黑白色彩，中国风格，--no cartoon, anime, photograph, realism, 3D render, modern art, texture, shadow, photo, realistic, depth of field, camera",
        "img_size": "1024x1024",
        "img_resize": 1.0,
        "text_color": "white",
        "stroke_color": "black",
        "is_y_slide": True,
    }
}