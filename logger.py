#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
日志模块 - 为百速一键AI视频生成项目提供日志功能
"""

import os
import logging
from logging.handlers import RotatingFileHandler
import time
from datetime import datetime

# 创建日志目录
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# 配置日志格式
formatter = logging.Formatter(
    '[%(asctime)s] [%(levelname)s] [%(module)s:%(lineno)d] - %(message)s'
)

# 创建不同级别的日志文件
def setup_logger(name, log_file, level=logging.INFO):
    """设置并返回指定名称和级别的日志记录器"""
    handler = RotatingFileHandler(
        os.path.join(LOG_DIR, log_file), 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    handler.setFormatter(formatter)
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    
    # 同时输出到控制台
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

# 创建主日志记录器
app_logger = setup_logger('app', 'app.log')
# 创建视频生成专用日志记录器
video_logger = setup_logger('video', 'video.log')
# 创建错误日志记录器
error_logger = setup_logger('error', 'error.log', level=logging.ERROR)

# 便捷日志记录函数
def log_info(message, logger_name='app'):
    """记录信息级别日志"""
    if logger_name == 'app':
        app_logger.info(message)
    elif logger_name == 'video':
        video_logger.info(message)

def log_error(message, exc_info=None):
    """记录错误级别日志，可选择是否包含异常信息"""
    error_logger.error(message, exc_info=exc_info)
    app_logger.error(message)

def log_warning(message):
    """记录警告级别日志"""
    app_logger.warning(message)

def log_debug(message):
    """记录调试级别日志"""
    app_logger.debug(message)

def log_video_task(task_id, message, status=None, progress=None):
    """记录视频任务相关日志"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    log_entry = f"[任务 {task_id}] {message}"
    
    if status:
        log_entry += f" - 状态: {status}"
    if progress is not None:
        log_entry += f" - 进度: {progress}%"
        
    video_logger.info(log_entry)
    
    # 对于错误状态，同时记录到错误日志
    if status == 'failed':
        error_logger.error(log_entry)

# 测试代码
if __name__ == "__main__":
    log_info("测试应用日志")
    log_video_task("test-task-id", "开始生成视频", "processing", 0)
    log_error("测试错误日志")
