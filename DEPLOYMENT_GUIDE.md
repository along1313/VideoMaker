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

### 方式一：一键部署（推荐）
```bash
chmod +x deploy_scripts/deploy_from_local.sh
./deploy_scripts/deploy_from_local.sh
```

### 方式二：手动部署
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

## 📞 联系支持

如遇到无法解决的问题，请检查：
1. 系统日志: `journalctl -u videomaker -n 100`
2. 应用日志: `tail -100 /root/VideoMaker/logs/app.log`
3. 错误日志: `tail -100 /root/VideoMaker/logs/gunicorn_error.log`

---

**注意**: 所有命令都应该在具有相应权限的情况下执行。部署前请确保备份重要数据。 