#!/bin/bash

# VideoMaker 本地到服务器部署脚本
# 使用方式: ./deploy_from_local.sh

set -e  # 出错时停止执行

# 配置信息
SERVER_HOST="43.163.98.206"
SERVER_USER="root"
SSH_KEY="/Users/zhusisi/CascadeProjects/keys/sin_key.pem"
LOCAL_PROJECT_DIR="/Users/zhusisi/CascadeProjects/VideoMaker"
SERVER_PROJECT_DIR="/root/VideoMaker"

echo "🚀 从本地部署 VideoMaker 到服务器..."

# 1. 检查本地项目状态
echo "📍 检查本地项目状态..."
cd "$LOCAL_PROJECT_DIR"

if [[ $(git status --porcelain) ]]; then
    echo "⚠️  发现未提交的本地修改，是否继续部署？(y/N)"
    read -r response
    if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "❌ 部署已取消"
        exit 1
    fi
fi

# 2. 推送最新代码到Git仓库
echo "📍 推送最新代码到Git仓库..."
git add -A
git commit -m "Deploy: $(date '+%Y-%m-%d %H:%M:%S')" 2>/dev/null || echo "没有新的修改需要提交"
git push origin master

# 3. 上传部署脚本到服务器
echo "📍 上传部署脚本到服务器..."
scp -i "$SSH_KEY" deploy_scripts/deploy.sh "$SERVER_USER@$SERVER_HOST:$SERVER_PROJECT_DIR/"

# 4. 在服务器上执行部署
echo "📍 在服务器上执行部署..."
ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_HOST" "cd $SERVER_PROJECT_DIR && chmod +x deploy.sh && ./deploy.sh"

# 5. 检查部署结果
echo "📍 检查部署结果..."
DEPLOYMENT_STATUS=$(ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_HOST" "systemctl is-active videomaker" 2>/dev/null || echo "failed")

if [ "$DEPLOYMENT_STATUS" = "active" ]; then
    echo "✅ 部署成功！服务正在运行"
    echo "🌐 网站地址: https://baisuai.com"
    
    # 显示服务状态
    echo ""
    echo "📊 服务器状态："
    ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_HOST" "
        echo 'VideoMaker 服务: $(systemctl is-active videomaker)'
        echo 'Nginx 服务: $(systemctl is-active nginx)'
        echo '服务器负载: $(uptime)'
        echo '磁盘使用: $(df -h $SERVER_PROJECT_DIR | tail -1)'
    "
else
    echo "❌ 部署失败！"
    echo "查看服务器日志："
    ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_HOST" "
        echo '=== VideoMaker 服务状态 ==='
        systemctl status videomaker --no-pager
        echo ''
        echo '=== 最近的应用日志 ==='
        journalctl -u videomaker --no-pager -n 20
    "
    exit 1
fi

echo ""
echo "🎉 部署完成！"
echo ""
echo "📝 常用管理命令："
echo "  查看应用日志: ssh -i $SSH_KEY $SERVER_USER@$SERVER_HOST 'journalctl -u videomaker -f'"
echo "  重启应用: ssh -i $SSH_KEY $SERVER_USER@$SERVER_HOST 'systemctl restart videomaker'"
echo "  查看服务状态: ssh -i $SSH_KEY $SERVER_USER@$SERVER_HOST 'systemctl status videomaker'" 