# 🚨 紧急部署指令 - 修复服务器视频生成失败问题

## 📋 问题描述
服务器上的视频生成功能显示"生成失败，请重试"，需要应用最新的错误处理修复。

## 🚀 部署步骤

### 1️⃣ 连接到服务器
```bash
ssh -i /path/to/key.pem root@43.163.98.206
cd /root/VideoMaker
```

### 2️⃣ 备份当前版本（可选但推荐）
```bash
# 创建备份
cp -r /root/VideoMaker /root/VideoMaker_backup_$(date +%Y%m%d_%H%M%S)
```

### 3️⃣ 拉取最新修复
```bash
# 拉取最新代码
git fetch origin
git pull origin master

# 确认最新提交
git log --oneline -3
# 应该看到最新的提交: "修复服务器视频生成失败问题"
```

### 4️⃣ 运行健康检查
```bash
# 运行新的健康检查脚本
python3 server_health_check.py

# 检查输出，查看是否有配置问题
```

### 5️⃣ 重启服务
```bash
# 重启VideoMaker服务
systemctl restart videomaker

# 检查服务状态
systemctl status videomaker

# 查看启动日志（新增了AI服务检查）
tail -50 logs/app.log
```

### 6️⃣ 验证修复效果
```bash
# 检查错误日志
tail -50 logs/error.log

# 访问网站测试
curl -I https://www.baisuai.com/
```

## 🔍 新增功能说明

### ✅ 增强的错误处理
- **前端**：现在显示具体错误信息而非通用"生成失败"
- **后端**：根据错误类型返回针对性提示

### ✅ AI服务健康检查
- **启动检查**：应用启动时自动检查AI服务配置
- **环境变量验证**：检查必要的API Keys是否设置

### ✅ 服务器诊断工具
- **新脚本**：`server_health_check.py`
- **全面检查**：环境变量、权限、模块、数据库等

## 🛠️ 故障排除

### 如果拉取失败：
```bash
# 强制重置到远程版本
git reset --hard origin/master
```

### 如果健康检查发现问题：
```bash
# 检查环境变量
env | grep -E "(ZHIPU|DEEPSEEK|QWEN|COSYVOICE)_API_KEY"

# 检查Python模块
pip3 install -r requirements.txt

# 检查权限
chmod -R 755 workstore logs static templates
```

### 如果服务启动失败：
```bash
# 查看详细错误
journalctl -u videomaker -f

# 手动启动测试
cd /root/VideoMaker
source .venv/bin/activate
python3 run.py
```

## 📊 验证清单

执行部署后，请验证以下项目：

- [ ] `git log`显示最新提交（修复服务器视频生成失败问题）
- [ ] `python3 server_health_check.py`运行成功
- [ ] `systemctl status videomaker`显示active (running)
- [ ] 访问 https://www.baisuai.com/ 正常
- [ ] 尝试生成视频，观察是否显示具体错误信息（而非通用"生成失败"）

## 🆘 紧急联系

如果部署过程中遇到问题：
1. 先检查 `logs/error.log` 中的最新错误信息
2. 运行 `python3 server_health_check.py` 获取详细诊断
3. 将具体错误信息反馈，以便进一步协助

## 📝 预期改进效果

部署后，用户在视频生成失败时将看到：
- ❌ **之前**："生成失败，请重试"
- ✅ **现在**："输入内容包含敏感信息，请修改后重试" 或其他具体错误

这将大大提高问题定位和解决效率！