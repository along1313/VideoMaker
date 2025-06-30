# 🚀 VideoMaker 快速部署指南

## 立即部署

### 方式一：一键部署（推荐）
```bash
./deploy_scripts/deploy_from_local.sh
```

### 方式二：手动部署
```bash
# 1. 提交并推送代码
git add -A && git commit -m "Deploy update" && git push origin master

# 2. 连接服务器部署
ssh -i /Users/zhusisi/CascadeProjects/keys/sin_key.pem root@43.163.98.206 "cd /root/VideoMaker && ./deploy.sh"
```

## 快速检查

### 服务状态检查
```bash
ssh -i /Users/zhusisi/CascadeProjects/keys/sin_key.pem root@43.163.98.206 "systemctl status videomaker nginx"
```

### 查看日志
```bash
ssh -i /Users/zhusisi/CascadeProjects/keys/sin_key.pem root@43.163.98.206 "journalctl -u videomaker -n 20"
```

## 常用命令

### 重启服务
```bash
ssh -i /Users/zhusisi/CascadeProjects/keys/sin_key.pem root@43.163.98.206 "systemctl restart videomaker"
```

### 备份数据库
```bash
ssh -i /Users/zhusisi/CascadeProjects/keys/sin_key.pem root@43.163.98.206 "cp /root/VideoMaker/instance/baisu_video.db /root/VideoMaker/instance/baisu_video.db.backup_\$(date +%Y%m%d_%H%M%S)"
```

## 故障排除

### 如果部署失败
1. 检查服务器连接：`ping 43.163.98.206`
2. 检查SSH密钥：`ssh -i /Users/zhusisi/CascadeProjects/keys/sin_key.pem root@43.163.98.206 "echo 'Connected'"` 
3. 查看详细日志：参考完整部署指南 `DEPLOYMENT_GUIDE.md`

### 如果网站无法访问
1. 检查服务状态：`systemctl status videomaker nginx`
2. 检查端口：`netstat -tlnp | grep :5001`
3. 重启服务：`systemctl restart videomaker nginx`

## 网站地址
- 🌐 生产网站：https://baisuai.com
- 📊 服务器IP：43.163.98.206

---
更多详细信息请参考：[完整部署指南](DEPLOYMENT_GUIDE.md) 