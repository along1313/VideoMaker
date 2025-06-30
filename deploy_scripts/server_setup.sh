#!/bin/bash

# VideoMaker 项目服务器部署脚本
# 使用方式: chmod +x server_setup.sh && ./server_setup.sh

set -e  # 出错时停止执行

PROJECT_NAME="VideoMaker"
PROJECT_DIR="/root/VideoMaker"
VENV_DIR="$PROJECT_DIR/venv"
SERVICE_NAME="videomaker"
NGINX_CONF="/etc/nginx/sites-available/videomaker"
SYSTEMD_SERVICE="/etc/systemd/system/${SERVICE_NAME}.service"

echo "🚀 开始部署 VideoMaker 项目..."

# 1. 停止现有服务
echo "📍 停止现有服务..."
pkill -f gunicorn || true
systemctl stop nginx || true

# 2. 备份现有项目
if [ -d "$PROJECT_DIR" ]; then
    echo "📍 备份现有项目..."
    cp -r "$PROJECT_DIR" "${PROJECT_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
fi

# 3. 确保依赖安装
echo "📍 检查系统依赖..."
yum update -y
yum install -y python3 python3-pip python3-venv git nginx supervisor

# 4. 创建系统服务文件
echo "📍 创建systemd服务文件..."
cat > "$SYSTEMD_SERVICE" << EOF
[Unit]
Description=VideoMaker Gunicorn Application
After=network.target

[Service]
Type=notify
User=root
Group=root
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/gunicorn -c gunicorn.conf.py run:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

# 5. 配置nginx
echo "📍 配置nginx..."
mkdir -p /etc/nginx/sites-available /etc/nginx/sites-enabled

cat > "$NGINX_CONF" << EOF
server {
    listen 80;
    server_name baisuai.com www.baisuai.com _;

    # 将HTTP请求重定向到HTTPS
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name baisuai.com www.baisuai.com;

    # SSL配置
    ssl_certificate /etc/nginx/ssl/baisuai.com_bundle.crt;
    ssl_certificate_key /etc/nginx/ssl/baisuai.com.key;
    ssl_session_timeout 5m;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:HIGH:!aNULL:!MD5:!RC4:!DHE;
    ssl_prefer_server_ciphers on;

    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    # 客户端上传限制
    client_max_body_size 100M;

    # 静态文件
    location /static/ {
        alias $PROJECT_DIR/static/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    # 媒体文件
    location /workstore/ {
        alias $PROJECT_DIR/workstore/;
        expires 1d;
    }

    # 应用程序
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

# 启用nginx配置
ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# 6. 重新加载systemd并启动服务
echo "📍 重新加载systemd配置..."
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl enable nginx

echo "✅ 服务器设置完成！"
echo "📝 接下来请运行项目部署脚本来部署代码。" 