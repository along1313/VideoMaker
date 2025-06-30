#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""gunicorn WSGI服务器配置文件"""

import os
import sys
import time
from dotenv import load_dotenv

# 设置gunicorn工作进程数
workers = 4
# 设置每个工作进程的线程数
threads = 2
# 监听内网端口 - 与nginx配置保持一致
bind = '0.0.0.0:5001'
# 设置守护进程 - systemd管理时设为False
daemon = False
# 设置工作模式
worker_class = 'sync'
# 设置最大并发量
worker_connections = 2000

# 设置进程文件目录
pidfile = 'gunicorn.pid'

# 设置访问日志和错误信息日志路径
accesslog = './logs/gunicorn_access.log'
errorlog = './logs/gunicorn_error.log'

# 设置日志格式
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# 设置gunicorn访问日志级别
loglevel = 'info'

# 设置超时时间
timeout = 300
keepalive = 2

# 最大请求数，防止内存泄漏
max_requests = 1000
max_requests_jitter = 50

def on_starting(server):
    """gunicorn服务器启动时执行的函数"""
    # 加载环境变量
    load_dotenv()
    
    # 检查必要的环境变量
    required_env_vars = ['ZHIPU_API_KEY', 'DASHSCOPE_API_KEY']
    missing_vars = []
    
    for var in required_env_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"警告: 以下环境变量未设置: {', '.join(missing_vars)}")
        print("请检查.env文件配置")
    
    # 确保必要的目录存在
    required_dirs = [
        'logs',
        'workstore',
        'static/audio',
        'static/video', 
        'static/covers',
        'instance'
    ]
    
    for directory in required_dirs:
        os.makedirs(directory, exist_ok=True)
    
    print(f"gunicorn服务器正在启动... 时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"监听地址: {bind}")
    print(f"工作进程数: {workers}")

def on_exit(server):
    """gunicorn服务器关闭时执行的函数"""
    print(f"gunicorn服务器正在关闭... 时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

def worker_init(worker):
    """工作进程初始化"""
    print(f"工作进程 {worker.pid} 已启动")

def worker_exit(server, worker):
    """工作进程退出"""
    print(f"工作进程 {worker.pid} 已退出") 