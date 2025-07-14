#!/bin/bash

# VideoMaker 优化版本部署脚本
# 只在文件有变化时才上传，提高部署效率

set -e  # 出错时停止执行

# 配置信息 (从环境变量读取，如果没有则使用默认值)
SERVER_HOST="${SERVER_HOST:-43.163.98.206}"
SERVER_USER="${SERVER_USER:-root}"
SSH_KEY="${SSH_KEY_PATH:-/Users/zhusisi/CascadeProjects/keys/sin_key.pem}"
LOCAL_PROJECT_DIR="${LOCAL_PROJECT_DIR:-/Users/zhusisi/CascadeProjects/VideoMaker}"
SERVER_PROJECT_DIR="${SERVER_PROJECT_DIR:-/root/VideoMaker}"

echo "📋 优化部署配置:"
echo "  服务器: $SERVER_HOST"
echo "  用户: $SERVER_USER"
echo "  SSH密钥: $SSH_KEY"
echo "  本地目录: $LOCAL_PROJECT_DIR"
echo "  服务器目录: $SERVER_PROJECT_DIR"
echo ""

echo "🚀 智能部署 VideoMaker 到服务器..."

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

# 2. 检查与上次部署的差异
echo "📍 分析文件变化..."
CURRENT_COMMIT=$(git rev-parse HEAD)

# 获取服务器上的当前commit
SERVER_COMMIT=$(ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_HOST" "cd $SERVER_PROJECT_DIR && git rev-parse HEAD 2>/dev/null || echo 'none'")

if [ "$SERVER_COMMIT" = "$CURRENT_COMMIT" ]; then
    echo "✅ 服务器代码已是最新版本，无需部署"
    exit 0
fi

echo "  本地版本: $CURRENT_COMMIT"
echo "  服务器版本: $SERVER_COMMIT"

# 检查变化的文件类型
if [ "$SERVER_COMMIT" != "none" ]; then
    CHANGED_FILES=$(git diff --name-only "$SERVER_COMMIT" HEAD 2>/dev/null || git diff --name-only HEAD~1 HEAD)
    STATIC_CHANGES=$(echo "$CHANGED_FILES" | grep "^static/" | wc -l)
    CODE_CHANGES=$(echo "$CHANGED_FILES" | grep -v "^static/" | grep -E "\.(py|html|js|css|json)$" | wc -l)
    
    echo "  📊 变化统计:"
    echo "    静态文件变化: $STATIC_CHANGES 个"
    echo "    代码文件变化: $CODE_CHANGES 个"
else
    STATIC_CHANGES=1  # 首次部署，需要上传所有文件
    CODE_CHANGES=1
    echo "  📊 首次部署，将上传所有文件"
fi

# 3. 推送最新代码到Git仓库
echo "📍 推送最新代码到Git仓库..."
git add -A
git commit -m "Deploy: $(date '+%Y-%m-%d %H:%M:%S')" 2>/dev/null || echo "没有新的修改需要提交"
git push origin master

# 4. 上传部署脚本到服务器
echo "📍 上传部署脚本到服务器..."
scp -i "$SSH_KEY" deploy_scripts/deploy.sh "$SERVER_USER@$SERVER_HOST:$SERVER_PROJECT_DIR/"

# 5. 智能上传静态文件（仅在有变化时）
if [ "$STATIC_CHANGES" -gt 0 ]; then
    echo "📍 检测到静态文件变化，正在上传..."
    
    # 创建服务器上的必要目录
    ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_HOST" "
        mkdir -p $SERVER_PROJECT_DIR/static/video/preview
        mkdir -p $SERVER_PROJECT_DIR/static/img
        mkdir -p $SERVER_PROJECT_DIR/static/audio
    "

    # 上传视频模板文件
    if [ -d "static/video" ] && [ "$(find static/video -maxdepth 1 -name '*.mp4' | wc -l)" -gt 0 ]; then
        echo "  📁 上传视频模板文件..."
        scp -i "$SSH_KEY" static/video/*.mp4 "$SERVER_USER@$SERVER_HOST:$SERVER_PROJECT_DIR/static/video/" 2>/dev/null || echo "    跳过：无视频模板文件"
    fi

    # 上传预览视频文件
    if [ -d "static/video/preview" ] && [ "$(find static/video/preview -name '*.mp4' | wc -l)" -gt 0 ]; then
        echo "  📁 上传预览视频文件..."
        scp -i "$SSH_KEY" static/video/preview/*.mp4 "$SERVER_USER@$SERVER_HOST:$SERVER_PROJECT_DIR/static/video/preview/" 2>/dev/null || echo "    跳过：无预览视频文件"
    fi

    # 上传图片文件
    if [ -d "static/img" ] && [ "$(find static/img -name '*.png' -o -name '*.jpg' | wc -l)" -gt 0 ]; then
        echo "  📁 上传图片文件..."
        scp -i "$SSH_KEY" static/img/*.png static/img/*.jpg "$SERVER_USER@$SERVER_HOST:$SERVER_PROJECT_DIR/static/img/" 2>/dev/null || echo "    跳过：无图片文件"
    fi

    # 上传音频文件（如果存在）
    if [ -f "static/audio/end_voice.mp3" ]; then
        echo "  📁 上传音频文件..."
        scp -i "$SSH_KEY" static/audio/end_voice.mp3 "$SERVER_USER@$SERVER_HOST:$SERVER_PROJECT_DIR/static/audio/"
    fi

    # 设置文件权限
    ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_HOST" "
        chown -R www:www $SERVER_PROJECT_DIR/static/
        chmod -R 755 $SERVER_PROJECT_DIR/static/
    "
    
    echo "✅ 静态文件上传完成"
else
    echo "⏭️  静态文件无变化，跳过上传"
fi

# 6. 在服务器上执行部署
echo "📍 在服务器上执行部署..."
ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_HOST" "cd $SERVER_PROJECT_DIR && chmod +x deploy.sh && ./deploy.sh"

# 7. 检查部署结果
echo "📍 检查部署结果..."
DEPLOYMENT_STATUS=$(ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_HOST" "systemctl is-active videomaker" 2>/dev/null || echo "failed")

if [ "$DEPLOYMENT_STATUS" = "active" ]; then
    echo "✅ 部署成功！服务状态: $DEPLOYMENT_STATUS"
    echo "🌐 访问地址: https://baisuai.com"
    
    # 显示简要的服务信息
    echo ""
    echo "📊 服务状态:"
    ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_HOST" "
        echo '  服务状态:' \$(systemctl is-active videomaker)
        echo '  Nginx状态:' \$(systemctl is-active nginx)
        echo '  最新提交:' \$(cd $SERVER_PROJECT_DIR && git log --oneline -1)
    "
else
    echo "❌ 部署失败！服务状态: $DEPLOYMENT_STATUS"
    echo "📋 错误日志:"
    ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_HOST" "
        echo '=== 服务状态 ==='
        systemctl status videomaker --no-pager -l
        echo ''
        echo '=== 最近日志 ==='
        journalctl -u videomaker -n 10 --no-pager
    "
    exit 1
fi

echo ""
echo "🎉 部署完成！" 