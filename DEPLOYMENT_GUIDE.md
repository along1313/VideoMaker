# VideoMaker 统一部署指南

## 📋 概述

VideoMaker 是一个 AI 视频生成平台，本文档提供完整的部署解决方案，包括环境配置、服务部署和维护指南。

> **重要说明**: 此文档已合并原 QUICK_DEPLOY.md，提供一站式部署解决方案。

## 🏗️ 部署架构

```
用户请求 → Nginx (反向代理/SSL) → Gunicorn (WSGI服务器) → Flask应用
```

### 技术栈
- **Web服务器**: Nginx (反向代理、SSL终止、静态文件服务)
- **应用服务器**: Gunicorn (WSGI服务器)
- **应用框架**: Flask
- **进程管理**: systemd
- **数据库**: SQLite
- **版本控制**: Git

## 🚀 快速部署

### 方式一：智能部署（推荐✨）
```bash
chmod +x deploy_scripts/deploy_from_local_optimized.sh
./deploy_scripts/deploy_from_local_optimized.sh
```

**智能部署特点**：
- 🔍 自动检测文件变化类型（静态文件 vs 代码文件）
- ⚡ 只上传有变化的文件，显著提升部署效率
- 📊 详细的变化统计和操作反馈
- 🛡️ 智能跳过不必要的文件传输

### 💡 灵活路径配置

**不同设备部署路径配置**：
由于不同开发者可能使用不同的设备和路径，可以通过环境变量来配置路径：

```bash
# 设置环境变量来适应不同的开发环境
export SSH_KEY_PATH="/your/path/to/keys/sin_key.pem"
export LOCAL_PROJECT_DIR="/your/path/to/VideoMaker"
export SERVER_HOST="43.163.98.206"
export SERVER_USER="root"
export SERVER_PROJECT_DIR="/root/VideoMaker"

# 然后执行部署
./deploy_scripts/deploy_from_local_optimized.sh
```

**常见路径配置示例**：
```bash
# macOS 示例
export SSH_KEY_PATH="/Users/username/keys/sin_key.pem"
export LOCAL_PROJECT_DIR="/Users/username/Projects/VideoMaker"

# Windows WSL 示例
export SSH_KEY_PATH="/mnt/c/Users/username/keys/sin_key.pem"
export LOCAL_PROJECT_DIR="/mnt/c/Users/username/Projects/VideoMaker"

# Linux 示例
export SSH_KEY_PATH="/home/username/keys/sin_key.pem"
export LOCAL_PROJECT_DIR="/home/username/Projects/VideoMaker"
```

**一键配置脚本**：
```bash
# 创建个人配置文件
cat > ~/.videomaker_deploy_config << 'EOF'
export SSH_KEY_PATH="/your/path/to/keys/sin_key.pem"
export LOCAL_PROJECT_DIR="/your/path/to/VideoMaker"
export SERVER_HOST="43.163.98.206"
export SERVER_USER="root"
export SERVER_PROJECT_DIR="/root/VideoMaker"
EOF

# 使用配置文件部署
source ~/.videomaker_deploy_config && ./deploy_scripts/deploy_from_local_optimized.sh
```

### 方式二：传统一键部署
```bash
chmod +x deploy_scripts/deploy_from_local.sh
./deploy_scripts/deploy_from_local.sh
```

**注意**：传统部署会每次上传所有静态文件，适合首次部署或需要强制更新所有文件的场景。

### 方式三：手动部署
```bash
# 1. 提交并推送代码
git add -A && git commit -m "Deploy update" && git push origin master

# 2. 连接服务器部署
ssh -i /path/to/your/key.pem root@your_server_ip "cd /root/VideoMaker && ./deploy.sh"
```

## ⚙️ 环境配置

### 1. 环境变量配置

**必需的环境变量** (在服务器 `/root/VideoMaker/.env` 文件中):
```bash
# 基础配置
FLASK_ENV=production
FLASK_DEBUG=False
PORT=5001

# AI服务API密钥（必需）
ZHIPU_API_KEY=your_zhipu_api_key
DASHSCOPE_API_KEY=your_dashscope_api_key  
MINIMAX_API_KEY=your_minimax_api_key
MINIMAX_GROUP_ID=your_minimax_group_id

# 安全配置
SECRET_KEY=your_random_secret_key
```

### 2. 获取API密钥

- **智谱AI**: https://bigmodel.cn/
- **阿里云通义千问**: https://dashscope.aliyun.com/
- **MiniMax**: https://api.minimax.chat/

### 3. 初次部署设置

**只在首次部署时执行**：
```bash
# 上传并执行服务器初始化脚本
scp -i /path/to/key.pem deploy_scripts/server_setup.sh root@server_ip:/root/
ssh -i /path/to/key.pem root@server_ip "chmod +x /root/server_setup.sh && /root/server_setup.sh"
```

## 🔧 服务管理

### systemd 服务命令

```bash
# 查看服务状态
systemctl status videomaker

# 启动服务
systemctl start videomaker

# 停止服务  
systemctl stop videomaker

# 重启服务
systemctl restart videomaker

# 查看服务日志
journalctl -u videomaker -f

# 查看最近的日志
journalctl -u videomaker -n 50
```

### Nginx 服务命令

```bash
# 检查配置文件语法
nginx -t

# 重新加载配置
systemctl reload nginx

# 重启nginx
systemctl restart nginx

# 查看nginx状态
systemctl status nginx
```

## 📊 监控和日志

### 应用日志位置
- 应用日志: `/root/VideoMaker/logs/app.log`
- Gunicorn访问日志: `/root/VideoMaker/logs/gunicorn_access.log`
- Gunicorn错误日志: `/root/VideoMaker/logs/gunicorn_error.log`
- 系统日志: `journalctl -u videomaker`

### 查看日志命令

```bash
# 实时查看应用日志
tail -f /root/VideoMaker/logs/app.log

# 实时查看访问日志
tail -f /root/VideoMaker/logs/gunicorn_access.log

# 查看错误日志
tail -f /root/VideoMaker/logs/gunicorn_error.log

# 查看系统服务日志
journalctl -u videomaker -f
```

## 🔒 安全配置

### SSL证书
- 证书位置: `/etc/nginx/ssl/baisuai.com_bundle.crt`
- 私钥位置: `/etc/nginx/ssl/baisuai.com.key`

### 防火墙设置
```bash
# 检查防火墙状态
firewall-cmd --state

# 开放HTTP和HTTPS端口
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --reload
```

## 🗄️ 数据备份

### 数据库备份
```bash
# 备份数据库
cp /root/VideoMaker/instance/baisu_video.db /root/VideoMaker/instance/baisu_video.db.backup_$(date +%Y%m%d_%H%M%S)

# 恢复数据库
cp /root/VideoMaker/instance/baisu_video.db.backup_YYYYMMDD_HHMMSS /root/VideoMaker/instance/baisu_video.db
systemctl restart videomaker
```

### 用户数据备份
```bash
# 备份用户工作目录
tar -czf /root/workstore_backup_$(date +%Y%m%d_%H%M%S).tar.gz /root/VideoMaker/workstore/
```

## 🔍 故障排除

### 常见问题诊断

**1. 502 Bad Gateway**
```bash
# 检查服务状态
systemctl status videomaker

# 检查端口监听
netstat -tlnp | grep :5001

# 重启服务
systemctl restart videomaker
```

**2. 端口配置不一致**
```bash
# 检查应用端口配置
grep PORT /root/VideoMaker/.env

# 检查nginx代理配置
grep proxy_pass /www/server/panel/vhost/nginx/videomaker.conf

# 统一端口配置（应该都是5001）
```

**3. API密钥错误**
```bash
# 检查必需的API密钥
grep -E 'MINIMAX_API_KEY|MINIMAX_GROUP_ID|ZHIPU_API_KEY|DASHSCOPE_API_KEY' /root/VideoMaker/.env

# 重启以加载新配置
systemctl restart videomaker
```

**4. 视频生成失败**
```bash
# 查看详细错误日志
tail -50 /root/VideoMaker/logs/app.log | grep ERROR

# 常见错误类型：
# - "MINIMAX_API_KEY and MINIMAX_GROUP_ID must be set"
# - "got multiple values for keyword argument 'voice'"
# - "系统检测到输入或生成内容可能包含不安全或敏感内容"
```

**5. 静态文件404**
```bash
# 检查文件权限
ls -la /root/VideoMaker/static/

# 检查nginx配置
grep "root /root/VideoMaker" /www/server/panel/vhost/nginx/videomaker.conf

# 重新加载nginx
systemctl reload nginx
```

### 性能优化

1. **调整worker数量**
   编辑 `gunicorn.conf.py`:
   ```python
   workers = CPU核心数 * 2 + 1
   ```

2. **内存监控**
   ```bash
   # 查看内存使用
   free -h
   
   # 查看进程内存使用
   ps aux --sort=-%mem | head
   ```

## 📝 维护计划

### 日常维护
- 每日检查服务状态
- 每周清理日志文件
- 每月备份数据库

### 定期任务
```bash
# 添加到crontab
crontab -e

# 每天凌晨2点备份数据库
0 2 * * * cp /root/VideoMaker/instance/baisu_video.db /root/VideoMaker/instance/baisu_video.db.backup_$(date +\%Y\%m\%d)

# 每周清理7天前的日志
0 3 * * 0 find /root/VideoMaker/logs/ -name "*.log" -mtime +7 -delete
```

## 🔄 版本回滚

如果新版本出现问题，可以快速回滚：

```bash
# 1. 停止服务
systemctl stop videomaker

# 2. 回滚到备份版本
cd /root
rm -rf VideoMaker
mv VideoMaker_backup_YYYYMMDD_HHMMSS VideoMaker

# 3. 重启服务
cd VideoMaker
systemctl start videomaker
```

## 🚨 常见部署问题与解决方案

### 问题1：CDN本地化文件缺失导致样式异常

**症状表现**：
- 网站显示不正常，缺少样式和交互效果
- 页面只显示基础HTML内容和箭头图标
- Vue.js应用未正确初始化

**问题原因**：
服务器缺少CDN本地化文件（TailwindCSS、Google Fonts等）

**诊断命令**：
```bash
# 检查CDN本地化文件是否存在
ls -la /root/VideoMaker/static/vendor/tailwindcss/
ls -la /root/VideoMaker/static/vendor/google-fonts/

# 测试文件访问
curl -I https://baisuai.com/static/vendor/vue/vue.min.js
```

**解决方案**：
```bash
# 1. 从本地上传CDN文件
scp -i /path/to/key.pem -r static/vendor/tailwindcss/* root@server:/root/VideoMaker/static/vendor/tailwindcss/
scp -i /path/to/key.pem -r static/vendor/google-fonts/* root@server:/root/VideoMaker/static/vendor/google-fonts/

# 2. 设置正确权限
chown -R www:www /root/VideoMaker/static/vendor/
chmod -R 755 /root/VideoMaker/static/vendor/
```

### 问题2：服务器代码版本过旧

**症状表现**：
- 模板文件中仍使用CDN链接而非本地路径
- 最新功能和修复未生效

**问题原因**：
服务器git代码停留在旧版本，缺少CDN本地化相关提交

**诊断命令**：
```bash
# 检查服务器代码版本
cd /root/VideoMaker && git log --oneline -5

# 检查模板文件中的引用
grep 'tailwindcss' /root/VideoMaker/templates/base.html
```

**解决方案**：
```bash
# 强制更新到最新版本
cd /root/VideoMaker
git stash
git fetch origin  
git reset --hard origin/master
git stash pop  # 恢复本地配置

# 重启服务
systemctl restart videomaker
```

### 问题3：静态文件403 Forbidden错误

**症状表现**：
- 所有静态文件返回403错误
- JavaScript/CSS文件无法加载
- 浏览器控制台显示资源加载失败

**问题原因**：
nginx worker进程以`www`用户运行，无法访问`/root/`目录

**诊断命令**：
```bash
# 检查nginx进程用户
ps aux | grep nginx

# 测试文件访问权限
curl -I https://baisuai.com/static/vendor/vue/vue.min.js

# 检查目录权限
ls -la /root/VideoMaker/static/vendor/
```

**解决方案**：
```bash
# 修复目录权限
chmod 755 /root
chmod -R 755 /root/VideoMaker
chown -R www:www /root/VideoMaker/static/

# 确保所有文件有正确权限
find /root/VideoMaker/static/vendor/ -type f -name '*.js' -o -name '*.css' | xargs chmod 644

# 重新加载nginx
systemctl reload nginx
```

### 问题4：端口配置不一致

**症状表现**：
- 502 Bad Gateway错误
- 服务无法正常访问

**诊断命令**：
```bash
# 检查应用实际监听端口
netstat -tlnp | grep python

# 检查nginx代理配置
grep proxy_pass /www/server/panel/vhost/nginx/videomaker.conf

# 检查环境变量配置
grep PORT /root/VideoMaker/.env
```

**解决方案**：
确保以下配置一致：
- nginx配置：`proxy_pass http://127.0.0.1:5001;`
- gunicorn配置：`bind = '0.0.0.0:5001'`
- 环境变量：PORT=5001（如果设置）

### 问题5：服务启动失败

**症状表现**：
- systemctl status显示failed状态
- 应用无法启动

**诊断命令**：
```bash
# 检查服务状态和错误信息
systemctl status videomaker -l
journalctl -u videomaker -n 50

# 检查Python环境和依赖
source /root/VideoMaker/.venv/bin/activate
pip check
```

**解决方案**：
```bash
# 重新安装依赖
cd /root/VideoMaker
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 重启服务
systemctl daemon-reload
systemctl restart videomaker
```

### 问题6：虚拟环境路径错误

**症状表现**：
- 部署脚本报错：`/root/VideoMaker/venv/bin/activate: No such file or directory`
- 虚拟环境激活失败
- 依赖包无法正确加载

**问题原因**：
部署脚本中的虚拟环境路径与实际路径不一致。服务器上使用的是 `.venv` 目录，但脚本中配置的是 `venv`。

**诊断命令**：
```bash
# 检查服务器上的虚拟环境目录
ssh -i /path/to/key.pem root@server_ip "cd /root/VideoMaker && ls -la | grep venv"

# 常见的虚拟环境目录名：
# .venv (推荐，隐藏目录) - 服务器实际使用的目录
# venv (传统命名) - 部署脚本默认配置
# env (简短命名)
```

**解决方案**：

**方案1：修正部署脚本中的路径（推荐）**
```bash
# 编辑 deploy.sh 文件，将第9行和第129行：
VENV_DIR="$PROJECT_DIR/venv"
source "$VENV_DIR/bin/activate"

# 改为：
VENV_DIR="$PROJECT_DIR/.venv"
source "$VENV_DIR/bin/activate"
```

**方案2：手动激活正确的虚拟环境**
```bash
ssh -i /path/to/key.pem root@server_ip "
    cd /root/VideoMaker
    source .venv/bin/activate  # 注意使用正确的目录名
    pip install -r requirements.txt
    systemctl restart videomaker
"
```

**方案3：智能路径检测（最佳实践）**
```bash
# 在 deploy.sh 中添加智能检测逻辑
if [ -d "$PROJECT_DIR/.venv" ]; then
    VENV_DIR="$PROJECT_DIR/.venv"
elif [ -d "$PROJECT_DIR/venv" ]; then
    VENV_DIR="$PROJECT_DIR/venv"
else
    echo "❌ 虚拟环境目录未找到"
    exit 1
fi
```

**预防措施**：
1. 在项目根目录创建 `.python-version` 文件标记Python版本
2. 统一使用 `.venv` 作为虚拟环境目录名（现代最佳实践）
3. 在部署脚本中添加虚拟环境路径检测逻辑
4. 确保本地开发环境和服务器环境使用相同的虚拟环境目录名

### 部署后验证清单

**必须验证的项目**：
```bash
# 1. 服务状态检查
systemctl is-active videomaker
systemctl is-active nginx

# 2. CDN本地化文件访问测试
curl -o /dev/null -s -w "%{http_code}" https://baisuai.com/static/vendor/vue/vue.min.js
curl -o /dev/null -s -w "%{http_code}" https://baisuai.com/static/vendor/tailwindcss/tailwindcss.min.js
curl -o /dev/null -s -w "%{http_code}" https://baisuai.com/static/vendor/element-ui/index.js

# 3. 网站功能测试
curl -s https://baisuai.com/ | grep -c "home-container"

# 4. 日志检查
tail -20 /root/VideoMaker/logs/app.log
journalctl -u videomaker -n 10
```

**预期结果**：
- 所有服务状态：active
- 所有CDN文件：200状态码
- 网站包含Vue应用容器
- 日志无ERROR级别错误

## 📞 联系支持

如遇到无法解决的问题，请检查：
1. 系统日志: `journalctl -u videomaker -n 100`
2. 应用日志: `tail -100 /root/VideoMaker/logs/app.log`
3. 错误日志: `tail -100 /root/VideoMaker/logs/gunicorn_error.log`

---

## 🎯 部署策略选择指南

### 智能部署 vs 传统部署

| 场景 | 推荐方式 | 原因 |
|------|----------|------|
| 🔄 日常代码更新 | 智能部署 | 自动跳过静态文件，速度快 |
| 🖼️ 静态文件更新 | 智能部署 | 自动检测并只上传变化的文件 |
| 🚀 首次部署 | 传统部署 | 确保所有文件都正确上传 |
| 🔧 强制全量更新 | 传统部署 | 无条件上传所有静态文件 |
| 🐛 部署脚本调试 | 手动部署 | 便于逐步排查问题 |

### 部署效果验证

**验证智能部署是否生效**：
```bash
# 查看部署日志，应包含以下信息：
# ✅ "静态文件变化: 0 个" (当静态文件未变化时)
# ✅ "⏭️ 静态文件无变化，跳过上传" 
# ✅ "📊 变化统计" 显示具体的文件变化数量
```

**验证部署结果**：
```bash
# 检查关键文件是否正确部署
curl -I https://baisuai.com/sitemap.xml    # 站点地图
curl -I https://baisuai.com/robots.txt     # 爬虫规则  
curl -I https://baisuai.com/favicon.ico    # 网站图标

# 验证服务状态
ssh -i /path/to/key.pem root@server_ip "systemctl status videomaker nginx"
```

### 虚拟环境最佳实践

**推荐配置**：
```bash
# 1. 统一使用 .venv 作为虚拟环境目录名
python3 -m venv .venv

# 2. 在 .gitignore 中排除虚拟环境
echo ".venv/" >> .gitignore

# 3. 在部署脚本中添加路径检测
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ 虚拟环境未找到"
    exit 1
fi
```

### 🔧 部署脚本路径配置

**deploy.sh 脚本关键配置**：
```bash
# 默认配置（需要根据实际情况修改）
PROJECT_DIR="/root/VideoMaker"
VENV_DIR="$PROJECT_DIR/.venv"  # 注意：应该是 .venv 而不是 venv
SERVICE_NAME="videomaker"
```

**常见路径配置问题及解决方案**：

1. **虚拟环境路径不匹配**：
   - 问题：脚本中是 `venv` 但服务器上是 `.venv`
   - 解决：修改 `deploy.sh` 第9行为 `VENV_DIR="$PROJECT_DIR/.venv"`

2. **SSH密钥路径错误**：
   - 问题：不同设备上密钥路径不同
   - 解决：使用环境变量或创建符号链接

3. **项目目录路径不统一**：
   - 问题：本地和服务器项目路径不同
   - 解决：通过环境变量或配置文件统一管理

**部署脚本智能路径检测**：
```bash
# 在 deploy.sh 中添加以下检测逻辑
detect_venv_path() {
    if [ -d "$PROJECT_DIR/.venv" ]; then
        VENV_DIR="$PROJECT_DIR/.venv"
        echo "✅ 发现虚拟环境: .venv"
    elif [ -d "$PROJECT_DIR/venv" ]; then
        VENV_DIR="$PROJECT_DIR/venv"
        echo "✅ 发现虚拟环境: venv"
    elif [ -d "$PROJECT_DIR/env" ]; then
        VENV_DIR="$PROJECT_DIR/env"
        echo "✅ 发现虚拟环境: env"
    else
        echo "❌ 虚拟环境目录未找到"
        echo "请确保以下目录之一存在："
        echo "  - $PROJECT_DIR/.venv"
        echo "  - $PROJECT_DIR/venv"
        echo "  - $PROJECT_DIR/env"
        exit 1
    fi
}

# 在脚本中调用检测函数
detect_venv_path
```

---

**注意**: 所有命令都应该在具有相应权限的情况下执行。部署前请确保备份重要数据。 