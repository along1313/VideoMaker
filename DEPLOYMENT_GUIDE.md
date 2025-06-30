# VideoMaker 项目部署指南

## 📋 概述

本文档提供了VideoMaker项目在腾讯云服务器上的科学部署方案，包括初始化设置、日常更新和维护操作。

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

## 🚀 部署步骤

### 1. 初次部署（仅需执行一次）

如果是首次在服务器上部署，需要先运行服务器设置脚本：

```bash
# 在本地执行
scp -i /Users/zhusisi/CascadeProjects/keys/sin_key.pem deploy_scripts/server_setup.sh root@43.163.98.206:/root/
ssh -i /Users/zhusisi/CascadeProjects/keys/sin_key.pem root@43.163.98.206 "chmod +x /root/server_setup.sh && /root/server_setup.sh"
```

### 2. 日常部署更新

使用本地部署脚本一键更新：

```bash
# 在项目根目录执行
chmod +x deploy_scripts/deploy_from_local.sh
./deploy_scripts/deploy_from_local.sh
```

### 3. 手动部署（备选方案）

如果自动化脚本出现问题，可以手动执行：

```bash
# 1. 推送代码到Git仓库
git add -A
git commit -m "部署更新"
git push origin master

# 2. 连接服务器并拉取更新
ssh -i /Users/zhusisi/CascadeProjects/keys/sin_key.pem root@43.163.98.206
cd /root/VideoMaker
./deploy.sh
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

## 🐛 故障排除

### 常见问题

1. **服务无法启动**
   ```bash
   # 检查配置文件
   python -c "import gunicorn.config; print('配置文件正常')"
   
   # 检查端口占用
   netstat -tlnp | grep 5001
   
   # 查看详细错误
   journalctl -u videomaker -n 50
   ```

2. **502 Bad Gateway**
   ```bash
   # 检查gunicorn是否运行
   systemctl status videomaker
   
   # 检查端口连接
   curl http://127.0.0.1:5001
   
   # 重启服务
   systemctl restart videomaker
   ```

3. **静态文件404**
   ```bash
   # 检查文件权限
   ls -la /root/VideoMaker/static/
   
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