#!/bin/bash

# VideoMaker 环境变量部署脚本
# 处理 .env 文件的部署，提供多种部署方式

set -e

# 配置信息
SERVER_HOST="${SERVER_HOST:-43.163.98.206}"
SERVER_USER="${SERVER_USER:-root}"
SSH_KEY="${SSH_KEY_PATH:-/Users/zhusisi/CascadeProjects/keys/sin_key.pem}"
SERVER_PROJECT_DIR="${SERVER_PROJECT_DIR:-/root/VideoMaker}"

echo "🔧 VideoMaker 环境变量部署工具"

# 显示使用方法
show_usage() {
    echo "使用方法:"
    echo "  $0 interactive    # 交互式创建 .env 文件"
    echo "  $0 template      # 从模板创建 .env 文件"  
    echo "  $0 upload        # 上传本地 .env 文件"
    echo "  $0 manual        # 手动编辑 .env 文件"
    echo "  $0 check         # 检查服务器 .env 文件"
}

# 交互式创建 .env 文件
interactive_setup() {
    echo "🔧 交互式创建 .env 文件"
    echo "请输入配置信息（回车跳过使用默认值）:"
    
    read -p "数据库URL [sqlite:///instance/baisu_video.db]: " db_url
    db_url=${db_url:-"sqlite:///instance/baisu_video.db"}
    
    read -p "Flask密钥 [随机生成]: " secret_key
    if [ -z "$secret_key" ]; then
        secret_key=$(openssl rand -hex 32)
    fi
    
    read -p "应用端口 [5001]: " port
    port=${port:-5001}
    
    read -p "MiniMax API Key: " minimax_api_key
    read -p "MiniMax Group ID: " minimax_group_id
    read -p "智谱AI API Key: " zhipu_api_key
    read -p "邮件用户名: " mail_username
    read -p "邮件密码: " mail_password
    
    # 创建临时 .env 文件
    cat > /tmp/videomaker.env << ENVEOF
# VideoMaker 应用配置
DATABASE_URL=$db_url
SECRET_KEY=$secret_key
FLASK_ENV=production
PORT=$port
MINIMAX_API_KEY=$minimax_api_key
MINIMAX_GROUP_ID=$minimax_group_id
ZHIPU_API_KEY=$zhipu_api_key
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=$mail_username
MAIL_PASSWORD=$mail_password
VIP_MONTHLY_CREDITS=100
FREE_MONTHLY_CREDITS=3
DEFAULT_CREDITS=10
LOG_LEVEL=INFO
ENVEOF

    # 上传到服务器
    echo "📤 上传 .env 文件到服务器..."
    scp -i "$SSH_KEY" /tmp/videomaker.env "$SERVER_USER@$SERVER_HOST:$SERVER_PROJECT_DIR/.env"
    
    # 设置权限
    ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_HOST" "
        chmod 600 $SERVER_PROJECT_DIR/.env
        chown root:root $SERVER_PROJECT_DIR/.env
    "
    
    # 清理临时文件
    rm /tmp/videomaker.env
    
    echo "✅ .env 文件创建并上传完成"
}

# 从模板创建
template_setup() {
    echo "🔧 从模板创建 .env 文件"
    
    if [ ! -f "env.example" ]; then
        echo "❌ 本地没有找到 env.example 文件"
        exit 1
    fi
    
    echo "📋 请编辑 env.example 文件，将占位符替换为实际值"
    echo "完成后按回车继续..."
    read
    
    # 上传 env.example 作为 .env
    scp -i "$SSH_KEY" env.example "$SERVER_USER@$SERVER_HOST:$SERVER_PROJECT_DIR/.env"
    
    # 设置权限
    ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_HOST" "
        chmod 600 $SERVER_PROJECT_DIR/.env
        chown root:root $SERVER_PROJECT_DIR/.env
    "
    
    echo "✅ .env 文件从模板创建完成"
}

# 上传本地 .env 文件
upload_setup() {
    echo "🔧 上传本地 .env 文件"
    
    if [ ! -f ".env" ]; then
        echo "❌ 本地没有找到 .env 文件"
        exit 1
    fi
    
    echo "⚠️  注意: 这将上传本地的 .env 文件到服务器"
    read -p "继续？(y/N): " confirm
    
    if [[ ! "$confirm" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "❌ 操作已取消"
        exit 1
    fi
    
    # 上传文件
    scp -i "$SSH_KEY" .env "$SERVER_USER@$SERVER_HOST:$SERVER_PROJECT_DIR/.env"
    
    # 设置权限
    ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_HOST" "
        chmod 600 $SERVER_PROJECT_DIR/.env
        chown root:root $SERVER_PROJECT_DIR/.env
    "
    
    echo "✅ .env 文件上传完成"
}

# 手动编辑
manual_setup() {
    echo "🔧 手动编辑服务器 .env 文件"
    
    # 检查服务器是否有 .env 文件
    ENV_EXISTS=$(ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_HOST" "test -f $SERVER_PROJECT_DIR/.env && echo 'yes' || echo 'no'")
    
    if [ "$ENV_EXISTS" = "no" ]; then
        echo "📋 服务器没有 .env 文件，从模板创建..."
        scp -i "$SSH_KEY" env.example "$SERVER_USER@$SERVER_HOST:$SERVER_PROJECT_DIR/.env"
    fi
    
    echo "🖊️  在服务器上编辑 .env 文件..."
    ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_HOST" "
        cd $SERVER_PROJECT_DIR
        nano .env
        chmod 600 .env
        chown root:root .env
    "
    
    echo "✅ .env 文件编辑完成"
}

# 检查现有配置
check_setup() {
    echo "🔍 检查服务器 .env 文件"
    
    ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_HOST" "
        cd $SERVER_PROJECT_DIR
        
        if [ -f .env ]; then
            echo '✅ .env 文件存在'
            echo '📋 文件信息:'
            ls -la .env
            echo ''
            echo '📝 配置检查 (隐藏敏感值):'
            
            # 检查关键配置
            echo 'DATABASE_URL: '$(grep -q 'DATABASE_URL' .env && echo '✅ 已配置' || echo '❌ 未配置')
            echo 'SECRET_KEY: '$(grep -q 'SECRET_KEY' .env && echo '✅ 已配置' || echo '❌ 未配置')
            echo 'MINIMAX_API_KEY: '$(grep -q 'MINIMAX_API_KEY' .env && echo '✅ 已配置' || echo '❌ 未配置')
            echo 'MINIMAX_GROUP_ID: '$(grep -q 'MINIMAX_GROUP_ID' .env && echo '✅ 已配置' || echo '❌ 未配置')
            echo 'ZHIPU_API_KEY: '$(grep -q 'ZHIPU_API_KEY' .env && echo '✅ 已配置' || echo '❌ 未配置')
            echo 'MAIL_USERNAME: '$(grep -q 'MAIL_USERNAME' .env && echo '✅ 已配置' || echo '❌ 未配置')
        else
            echo '❌ .env 文件不存在'
            echo '请选择一种方法创建 .env 文件'
        fi
    "
}

# 主函数
main() {
    if [ $# -eq 0 ]; then
        show_usage
        echo ""
        echo "请选择部署方式:"
        echo "1) interactive - 交互式创建（推荐新部署）"
        echo "2) template    - 从模板创建"
        echo "3) upload      - 上传本地文件"
        echo "4) manual      - 手动编辑"
        echo "5) check       - 检查现有配置"
        echo ""
        read -p "请选择 (1-5): " choice
        
        case $choice in
            1) interactive_setup ;;
            2) template_setup ;;
            3) upload_setup ;;
            4) manual_setup ;;
            5) check_setup ;;
            *) echo "❌ 无效选择"; exit 1 ;;
        esac
    else
        case $1 in
            interactive) interactive_setup ;;
            template) template_setup ;;
            upload) upload_setup ;;
            manual) manual_setup ;;
            check) check_setup ;;
            *) show_usage; exit 1 ;;
        esac
    fi
    
    echo ""
    echo "🎉 环境变量配置完成！"
    echo "💡 建议运行: ./deploy_env.sh check 验证配置"
}

main "$@"
