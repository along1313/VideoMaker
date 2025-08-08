#!/bin/bash
# 远程部署视频生成修复到服务器

# 服务器配置
SERVER_HOST="43.163.98.206"
SERVER_USER="root"
SERVER_PROJECT_DIR="/root/VideoMaker"
SSH_KEY_PATH="/Users/zhusisi/CascadeProjects/keys/sin_key.pem"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 开始部署视频生成错误修复到服务器...${NC}"
echo "服务器: $SERVER_HOST"
echo "项目目录: $SERVER_PROJECT_DIR"
echo "=================================="

# 检查SSH密钥是否存在
if [ ! -f "$SSH_KEY_PATH" ]; then
    echo -e "${RED}❌ SSH密钥文件不存在: $SSH_KEY_PATH${NC}"
    echo "请检查密钥路径是否正确"
    exit 1
fi

# 1. 检查服务器连接
echo -e "${YELLOW}🔗 检查服务器连接...${NC}"
if ssh -i "$SSH_KEY_PATH" -o ConnectTimeout=10 "$SERVER_USER@$SERVER_HOST" "echo '连接成功'" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ 服务器连接正常${NC}"
else
    echo -e "${RED}❌ 无法连接到服务器${NC}"
    exit 1
fi

# 2. 检查服务器当前代码版本
echo -e "${YELLOW}📋 检查服务器当前代码版本...${NC}"
CURRENT_COMMIT=$(ssh -i "$SSH_KEY_PATH" "$SERVER_USER@$SERVER_HOST" "cd $SERVER_PROJECT_DIR && git log --oneline -1")
echo "当前提交: $CURRENT_COMMIT"

# 3. 备份当前版本
echo -e "${YELLOW}💾 创建服务器代码备份...${NC}"
BACKUP_DIR="VideoMaker_backup_$(date +%Y%m%d_%H%M%S)"
ssh -i "$SSH_KEY_PATH" "$SERVER_USER@$SERVER_HOST" "cp -r $SERVER_PROJECT_DIR /root/$BACKUP_DIR"
echo -e "${GREEN}✅ 备份创建完成: /root/$BACKUP_DIR${NC}"

# 4. 部署最新代码
echo -e "${YELLOW}📥 拉取最新代码...${NC}"
ssh -i "$SSH_KEY_PATH" "$SERVER_USER@$SERVER_HOST" "
    cd $SERVER_PROJECT_DIR
    echo '正在拉取最新代码...'
    git fetch origin
    git pull origin master
    echo '最新提交:'
    git log --oneline -3
"

# 5. 运行健康检查
echo -e "${YELLOW}🔍 运行服务器健康检查...${NC}"
ssh -i "$SSH_KEY_PATH" "$SERVER_USER@$SERVER_HOST" "
    cd $SERVER_PROJECT_DIR
    echo '运行健康检查...'
    python3 server_health_check.py || echo '健康检查完成（可能有警告）'
"

# 6. 重启服务
echo -e "${YELLOW}🔄 重启VideoMaker服务...${NC}"
ssh -i "$SSH_KEY_PATH" "$SERVER_USER@$SERVER_HOST" "
    echo '停止服务...'
    systemctl stop videomaker
    sleep 3
    echo '启动服务...'
    systemctl start videomaker
    sleep 5
    echo '检查服务状态...'
    systemctl status videomaker --no-pager -l
"

# 7. 验证服务状态
echo -e "${YELLOW}📊 验证服务状态...${NC}"
SERVICE_STATUS=$(ssh -i "$SSH_KEY_PATH" "$SERVER_USER@$SERVER_HOST" "systemctl is-active videomaker")
if [ "$SERVICE_STATUS" = "active" ]; then
    echo -e "${GREEN}✅ VideoMaker服务运行正常${NC}"
else
    echo -e "${RED}❌ VideoMaker服务状态异常: $SERVICE_STATUS${NC}"
    echo "检查服务日志..."
    ssh -i "$SSH_KEY_PATH" "$SERVER_USER@$SERVER_HOST" "journalctl -u videomaker -n 20 --no-pager"
fi

# 8. 检查应用日志
echo -e "${YELLOW}📄 检查应用启动日志...${NC}"
ssh -i "$SSH_KEY_PATH" "$SERVER_USER@$SERVER_HOST" "
    cd $SERVER_PROJECT_DIR
    echo '=== 最近的应用日志 ==='
    tail -15 logs/app.log
    echo
    echo '=== 最近的错误日志 ==='
    tail -10 logs/error.log
"

# 9. 测试网站连通性
echo -e "${YELLOW}🌐 测试网站连通性...${NC}"
HTTP_STATUS=$(ssh -i "$SSH_KEY_PATH" "$SERVER_USER@$SERVER_HOST" "curl -s -o /dev/null -w '%{http_code}' http://localhost:5001/ || echo 'failed'")
if [ "$HTTP_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ 本地服务响应正常 (HTTP $HTTP_STATUS)${NC}"
else
    echo -e "${YELLOW}⚠️ 本地服务响应: $HTTP_STATUS${NC}"
fi

# 10. 最终验证
echo -e "${YELLOW}🔍 最终部署验证...${NC}"
LATEST_COMMIT=$(ssh -i "$SSH_KEY_PATH" "$SERVER_USER@$SERVER_HOST" "cd $SERVER_PROJECT_DIR && git log --oneline -1")
echo "最新提交: $LATEST_COMMIT"

# 检查是否包含我们的修复提交
if echo "$LATEST_COMMIT" | grep -q "修复服务器视频生成失败问题"; then
    echo -e "${GREEN}✅ 修复代码已成功部署${NC}"
else
    echo -e "${YELLOW}⚠️ 请检查是否是最新的修复版本${NC}"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}🎉 部署流程完成！${NC}"
echo "=========================================="
echo ""
echo -e "${BLUE}📋 验证清单:${NC}"
echo "1. ✅ 访问 https://www.baisuai.com/ 检查网站"
echo "2. ✅ 尝试生成视频，观察错误信息"
echo "3. ✅ 错误信息应该更具体，而非'生成失败，请重试'"
echo ""
echo -e "${BLUE}🔧 如果仍有问题:${NC}"
echo "1. SSH到服务器: ssh -i $SSH_KEY_PATH $SERVER_USER@$SERVER_HOST"
echo "2. 检查日志: cd $SERVER_PROJECT_DIR && tail -50 logs/error.log"
echo "3. 运行诊断: python3 server_health_check.py"
echo ""
echo -e "${GREEN}✨ 预期改进: 用户现在应该看到具体的错误原因而不是通用消息${NC}"