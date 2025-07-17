#!/bin/bash
# 快速部署视频生成修复脚本

echo "🚀 开始部署视频生成错误修复..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 错误处理
set -e

# 记录开始时间
START_TIME=$(date)
echo "开始时间: $START_TIME"

# 1. 拉取最新代码
echo -e "${YELLOW}📥 拉取最新代码...${NC}"
git fetch origin
git pull origin master

# 确认最新提交
echo -e "${YELLOW}📋 确认最新提交:${NC}"
git log --oneline -3

# 2. 运行健康检查
echo -e "${YELLOW}🔍 运行服务器健康检查...${NC}"
if python3 server_health_check.py; then
    echo -e "${GREEN}✅ 健康检查通过${NC}"
else
    echo -e "${RED}⚠️ 健康检查发现问题，但继续部署...${NC}"
fi

# 3. 重启服务
echo -e "${YELLOW}🔄 重启VideoMaker服务...${NC}"
systemctl restart videomaker

# 等待服务启动
sleep 5

# 4. 检查服务状态
echo -e "${YELLOW}📊 检查服务状态...${NC}"
if systemctl is-active --quiet videomaker; then
    echo -e "${GREEN}✅ VideoMaker服务运行正常${NC}"
    systemctl status videomaker --no-pager -l
else
    echo -e "${RED}❌ VideoMaker服务启动失败${NC}"
    systemctl status videomaker --no-pager -l
    exit 1
fi

# 5. 检查最新日志
echo -e "${YELLOW}📄 检查最新应用日志:${NC}"
echo "最近的应用日志 (最后10行):"
tail -10 logs/app.log

echo -e "${YELLOW}📄 检查错误日志:${NC}"
echo "最近的错误日志 (最后5行):"
tail -5 logs/error.log

# 6. 简单的连通性测试
echo -e "${YELLOW}🌐 测试服务连通性...${NC}"
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/ | grep -q "200"; then
    echo -e "${GREEN}✅ 本地服务响应正常${NC}"
else
    echo -e "${YELLOW}⚠️ 本地服务响应异常，检查配置...${NC}"
fi

# 记录结束时间
END_TIME=$(date)
echo ""
echo "=========================================="
echo "🎉 部署完成！"
echo "开始时间: $START_TIME"
echo "结束时间: $END_TIME"
echo "=========================================="
echo ""
echo "🔍 验证步骤:"
echo "1. 访问 https://www.baisuai.com/ 检查网站是否正常"
echo "2. 尝试生成视频，观察错误信息是否更具体"
echo "3. 如有问题，运行: tail -50 logs/error.log"
echo ""
echo "✨ 预期改进:"
echo "• 用户现在将看到具体的错误信息"
echo "• 而不是通用的'生成失败，请重试'"
echo "• 例如: '输入内容包含敏感信息，请修改后重试'"
echo ""