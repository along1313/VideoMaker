#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
百速一键AI视频生成 - 启动脚本
用于初始化环境并启动Web应用
"""

import os
import sys
import time
from dotenv import load_dotenv
from logger import log_info, log_error, log_warning, app_logger

# 加载环境变量
load_dotenv()

# 检查必要的环境变量
required_env_vars = ['ZHIPU_API_KEY', 'DASHSCOPE_API_KEY']
for var in required_env_vars:
    if not os.environ.get(var):
        print(f"错误: 环境变量 {var} 未设置。请在.env文件中配置。")
        sys.exit(1)

# 确保必要的目录存在
required_dirs = [
    'workstore',
    'static/css',
    'static/js',
    'static/img'
]

for directory in required_dirs:
    os.makedirs(directory, exist_ok=True)

# 确保默认图片存在
default_cover_path = os.path.join('static', 'img', 'default-cover.png')
if not os.path.exists(default_cover_path):
    # 创建一个简单的默认封面图片
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new('RGB', (800, 450), color=(52, 152, 219))
        d = ImageDraw.Draw(img)
        
        # 尝试加载字体，如果失败则使用默认字体
        try:
            font_path = os.path.join(os.environ.get("FONT_DIR", "lib/font"), "STHeiti Medium.ttc")
            font = ImageFont.truetype(font_path, 40)
        except:
            font = ImageFont.load_default()
            
        d.text((400, 225), "百速AI视频", fill=(255, 255, 255), font=font, anchor="mm")
        img.save(default_cover_path)
        print(f"已创建默认封面图片: {default_cover_path}")
    except Exception as e:
        print(f"警告: 无法创建默认封面图片: {str(e)}")

# 确保支付图标存在
payment_icons = {
    'alipay.png': (0, 114, 207),  # 蓝色
    'wechat.png': (9, 187, 7)     # 绿色
}

for icon_name, color in payment_icons.items():
    icon_path = os.path.join('static', 'img', icon_name)
    if not os.path.exists(icon_path):
        try:
            from PIL import Image, ImageDraw
            img = Image.new('RGB', (200, 200), color=color)
            d = ImageDraw.Draw(img)
            d.ellipse((50, 50, 150, 150), fill=(255, 255, 255))
            img.save(icon_path)
            print(f"已创建支付图标: {icon_path}")
        except Exception as e:
            print(f"警告: 无法创建支付图标 {icon_name}: {str(e)}")

# 初始化和启动应用
if __name__ == '__main__':
    # 记录应用启动信息
    log_info(f"百速一键AI视频生成应用正在启动... 时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 导入应用实例
        print("正在初始化数据库...")
        log_info("正在初始化数据库...")
        from app import app, db
        
        # 在应用上下文中初始化数据库
        with app.app_context():
            db.create_all()
            print("数据库初始化完成")
            log_info("数据库初始化完成")
            
            # 检查AI服务配置
            print("正在检查AI服务配置...")
            log_info("正在检查AI服务配置...")
            from app import check_ai_services
            check_ai_services()
            print("AI服务检查完成")
            log_info("AI服务检查完成")
            
            # 恢复中断的任务
            print("正在检查并恢复中断的任务...")
            log_info("正在检查并恢复中断的任务...")
            from app import recover_interrupted_tasks
            recover_interrupted_tasks()
            print("任务恢复检查完成")
            log_info("任务恢复检查完成")
        
        # 启动Web服务器
        print("启动百速一键AI视频生成应用...")
        print("请访问 http://localhost:5001 打开网页界面")
        log_info("百速一键AI视频生成应用服务器已启动，监听端口: 5001")
        app.run(debug=True, host='0.0.0.0', port=5001)
    except Exception as e:
        error_message = f"应用启动失败: {str(e)}"
        print(error_message)
        log_error(error_message, exc_info=True)