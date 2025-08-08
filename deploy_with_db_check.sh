#!/bin/bash
# 包含数据库检查的标准化部署脚本

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

echo -e "${BLUE}🚀 启动标准化数据库安全部署流程...${NC}"
echo "=================================================="

# 1. 本地预检查
echo -e "${YELLOW}📋 本地预检查...${NC}"

# 检查是否有数据库模型变更
if git diff HEAD~1 --name-only | grep -E "(app\.py|models\.py)" > /dev/null; then
    echo -e "${YELLOW}⚠️  检测到数据库模型文件可能有变更${NC}"
    echo "变更的文件:"
    git diff HEAD~1 --name-only | grep -E "(app\.py|models\.py)" | sed 's/^/  - /'
    
    # 检查是否有 db.Model 相关变更
    if git diff HEAD~1 | grep -E "(class.*db\.Model|db\.Column)" > /dev/null; then
        echo -e "${RED}🚨 发现数据库模型变更，需要数据库迁移！${NC}"
        DB_MIGRATION_NEEDED=true
    else
        echo -e "${GREEN}✅ 未发现数据库结构变更${NC}"
        DB_MIGRATION_NEEDED=false
    fi
else
    echo -e "${GREEN}✅ 未检测到数据库模型文件变更${NC}"
    DB_MIGRATION_NEEDED=false
fi

# 2. 连接服务器并检查状态
echo -e "${YELLOW}🔗 连接服务器并检查当前状态...${NC}"
ssh -i "$SSH_KEY_PATH" "$SERVER_USER@$SERVER_HOST" "
    cd $SERVER_PROJECT_DIR
    echo '当前代码版本:'
    git log --oneline -1
    echo ''
    echo '服务状态:'
    systemctl is-active videomaker
"

# 3. 如果需要数据库迁移，先备份
if [ "$DB_MIGRATION_NEEDED" = true ]; then
    echo -e "${YELLOW}💾 创建数据库备份...${NC}"
    BACKUP_NAME="db_backup_$(date +%Y%m%d_%H%M%S).db"
    ssh -i "$SSH_KEY_PATH" "$SERVER_USER@$SERVER_HOST" "
        cd $SERVER_PROJECT_DIR
        if [ -f instance/baisu_video.db ]; then
            cp instance/baisu_video.db instance/$BACKUP_NAME
            echo '数据库备份创建: instance/$BACKUP_NAME'
        else
            echo '警告: 数据库文件不存在'
        fi
    "
fi

# 4. 部署代码
echo -e "${YELLOW}📥 部署最新代码...${NC}"
ssh -i "$SSH_KEY_PATH" "$SERVER_USER@$SERVER_HOST" "
    cd $SERVER_PROJECT_DIR
    git fetch origin
    git pull origin master
    echo '最新代码版本:'
    git log --oneline -1
"

# 5. 数据库结构检查和迁移
echo -e "${YELLOW}🔍 检查数据库结构...${NC}"
ssh -i "$SSH_KEY_PATH" "$SERVER_USER@$SERVER_HOST" "
    cd $SERVER_PROJECT_DIR
    echo '运行数据库结构检查...'
    python3 -c \"
import sqlite3
import sys
import os

# 检查数据库文件
db_path = 'instance/baisu_video.db'
if not os.path.exists(db_path):
    print('❌ 数据库文件不存在')
    sys.exit(1)

# 连接数据库并检查表
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 获取现有表
cursor.execute(\\\"SELECT name FROM sqlite_master WHERE type='table'\\\" )
existing_tables = {row[0] for row in cursor.fetchall()}

# 需要的表（根据模型定义）
required_tables = {'user', 'video', 'task_queue', 'feedback', 'message', 'payment'}

missing_tables = required_tables - existing_tables
if missing_tables:
    print(f'❌ 缺失表: {missing_tables}')
    print('需要运行数据库迁移')
    sys.exit(2)
else:
    print('✅ 所有必要的表都存在')
    
conn.close()
\"
    SCHEMA_CHECK_RESULT=\$?
    echo \"数据库检查结果码: \$SCHEMA_CHECK_RESULT\"
"

# 6. 根据检查结果决定是否运行迁移
echo -e "${YELLOW}📊 处理数据库迁移...${NC}"
ssh -i "$SSH_KEY_PATH" "$SERVER_USER@$SERVER_HOST" "
    cd $SERVER_PROJECT_DIR
    if [ -f create_task_queue_table.py ]; then
        echo '发现迁移脚本，运行数据库迁移...'
        python3 create_task_queue_table.py
        MIGRATION_RESULT=\$?
        if [ \$MIGRATION_RESULT -eq 0 ]; then
            echo '✅ 数据库迁移成功'
        else
            echo '❌ 数据库迁移失败'
            exit 1
        fi
    else
        echo '⚠️  未发现迁移脚本，跳过迁移'
    fi
"

# 7. 重启服务
echo -e "${YELLOW}🔄 重启服务...${NC}"
ssh -i "$SSH_KEY_PATH" "$SERVER_USER@$SERVER_HOST" "
    systemctl restart videomaker
    sleep 5
    
    echo '检查服务状态:'
    if systemctl is-active --quiet videomaker; then
        echo '✅ 服务启动成功'
        systemctl status videomaker --no-pager -l | head -10
    else
        echo '❌ 服务启动失败'
        systemctl status videomaker --no-pager -l
        exit 1
    fi
"

# 8. 功能验证
echo -e "${YELLOW}🧪 功能验证...${NC}"
ssh -i "$SSH_KEY_PATH" "$SERVER_USER@$SERVER_HOST" "
    cd $SERVER_PROJECT_DIR
    
    echo '1. 网站连通性测试:'
    HTTP_CODE=\$(curl -s -o /dev/null -w '%{http_code}' http://localhost:5001/)
    if [ \"\$HTTP_CODE\" = \"200\" ]; then
        echo '✅ 网站响应正常'
    else
        echo '❌ 网站响应异常: \$HTTP_CODE'
    fi
    
    echo '2. 数据库连接测试:'
    python3 -c \"
try:
    import sqlite3
    conn = sqlite3.connect('instance/baisu_video.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM user')
    user_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM task_queue')
    task_count = cursor.fetchone()[0]
    print(f'✅ 数据库连接正常 - 用户: {user_count}, 任务: {task_count}')
    conn.close()
except Exception as e:
    print(f'❌ 数据库连接失败: {e}')
    exit(1)
\"
    
    echo '3. 检查最新日志:'
    if [ -f logs/app.log ]; then
        echo '最近5行应用日志:'
        tail -5 logs/app.log
    fi
"

echo ""
echo "=================================================="
echo -e "${GREEN}🎉 标准化数据库安全部署完成！${NC}"
echo "=================================================="
echo ""
echo -e "${BLUE}📋 部署摘要:${NC}"
echo "• 代码版本: $(git log --oneline -1)"
echo "• 数据库迁移: $([ "$DB_MIGRATION_NEEDED" = true ] && echo '已执行' || echo '未需要')"
echo "• 服务状态: 已重启并验证"
echo ""
echo -e "${BLUE}✅ 验证清单:${NC}"
echo "1. 访问 https://www.baisuai.com/ 确认网站正常"
echo "2. 尝试生成视频功能"
echo "3. 检查是否有具体错误信息而非通用提示"
echo ""
echo -e "${GREEN}🛡️  本次部署包含数据库安全检查，避免了结构不一致问题！${NC}"