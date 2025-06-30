#!/bin/bash

# VideoMaker 项目部署脚本
# 使用方式: ./deploy.sh

set -e  # 出错时停止执行

PROJECT_DIR="/root/VideoMaker"
VENV_DIR="$PROJECT_DIR/venv"
SERVICE_NAME="videomaker"
BACKUP_DIR="${PROJECT_DIR}_backup_$(date +%Y%m%d_%H%M%S)"

echo "🚀 开始部署 VideoMaker 项目更新..."

# 1. 进入项目目录
cd "$PROJECT_DIR"

# 2. 停止服务
echo "📍 停止应用服务..."
systemctl stop "$SERVICE_NAME" || true

# 3. 备份当前状态
echo "📍 备份当前项目状态..."
cp -r "$PROJECT_DIR" "$BACKUP_DIR"
echo "✅ 备份完成: $BACKUP_DIR"

# 4. 清理git状态（保留重要文件）
echo "📍 清理git工作区..."

# 保存重要的配置文件
cp .env .env.backup 2>/dev/null || true
cp gunicorn.conf.py gunicorn.conf.py.backup 2>/dev/null || true

# 备份数据库
cp -r instance/ instance_backup/ 2>/dev/null || true

# 备份工作存储
cp -r workstore/ workstore_backup/ 2>/dev/null || true

# 重置git状态
git stash push -m "Auto stash before deployment $(date)"
git clean -fd

# 5. 拉取最新代码
echo "📍 拉取最新代码..."
git fetch origin
git reset --hard origin/master

# 6. 恢复重要文件
echo "📍 恢复配置文件..."
cp .env.backup .env 2>/dev/null || true
cp gunicorn.conf.py.backup gunicorn.conf.py 2>/dev/null || true

# 如果没有gunicorn配置文件，创建一个
if [ ! -f gunicorn.conf.py ]; then
    echo "📍 创建gunicorn配置文件..."
    cat > gunicorn.conf.py << 'EOF'
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
# 监听内网端口
bind = '0.0.0.0:5001'
# 设置守护进程
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

# 设置gunicorn访问日志格式，错误日志无法通过这个设置
loglevel = 'info'

def on_starting(server):
    """gunicorn服务器启动时执行的函数"""
    # 加载环境变量
    load_dotenv()
    
    # 确保必要的目录存在
    required_dirs = [
        'logs',
        'workstore',
        'static/audio',
        'static/video',
        'static/covers'
    ]
    
    for directory in required_dirs:
        os.makedirs(directory, exist_ok=True)
    
    print(f"gunicorn服务器正在启动... 时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
EOF
fi

# 7. 恢复数据文件
echo "📍 恢复数据文件..."
if [ -d instance_backup ]; then
    rm -rf instance/
    mv instance_backup/ instance/
fi

if [ -d workstore_backup ]; then
    rm -rf workstore/
    mv workstore_backup/ workstore/
fi

# 8. 激活虚拟环境
echo "📍 激活虚拟环境..."
source "$VENV_DIR/bin/activate"

# 9. 更新依赖
echo "📍 更新Python依赖..."
pip install --upgrade pip
pip install -r requirements.txt

# 10. 创建必要目录
echo "📍 创建必要目录..."
mkdir -p logs static/audio static/video static/covers workstore

# 11. 设置文件权限
echo "📍 设置文件权限..."
chown -R root:root "$PROJECT_DIR"
chmod +x run.py
chmod 644 gunicorn.conf.py

# 12. 数据库迁移（如果需要）
echo "📍 执行数据库迁移..."
python -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('数据库初始化完成')
" || true

# 13. 重启服务
echo "📍 重启服务..."
systemctl daemon-reload
systemctl start "$SERVICE_NAME"
systemctl restart nginx

# 14. 检查服务状态
echo "📍 检查服务状态..."
sleep 3

if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "✅ VideoMaker 服务运行正常"
else
    echo "❌ VideoMaker 服务启动失败"
    systemctl status "$SERVICE_NAME"
    exit 1
fi

if systemctl is-active --quiet nginx; then
    echo "✅ Nginx 服务运行正常"
else
    echo "❌ Nginx 服务启动失败"
    systemctl status nginx
    exit 1
fi

# 15. 显示服务状态
echo "📊 当前服务状态："
echo "VideoMaker 服务: $(systemctl is-active $SERVICE_NAME)"
echo "Nginx 服务: $(systemctl is-active nginx)"
echo ""
echo "📝 查看日志命令："
echo "  应用日志: journalctl -u $SERVICE_NAME -f"
echo "  Nginx日志: tail -f /var/log/nginx/error.log"
echo "  应用访问日志: tail -f $PROJECT_DIR/logs/gunicorn_access.log"
echo ""
echo "🎉 部署完成！"
echo "📦 备份位置: $BACKUP_DIR"

# 清理临时文件
rm -f .env.backup gunicorn.conf.py.backup 2>/dev/null || true 