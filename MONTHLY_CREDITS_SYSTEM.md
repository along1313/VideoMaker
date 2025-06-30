# 月度免费额度系统说明

## 📋 系统概述

本系统实现了为非VIP用户定期刷新免费视频制作额度的功能。

## 🎯 业务逻辑

### 用户分类
- **新注册用户**: 获得3条免费额度，非VIP身份
- **普通用户**: 非VIP用户，生成视频时：
  - 用户名强制显示为"百速AI" 
  - 视频末尾包含广告
- **VIP用户**: 订阅会员，生成视频时：
  - 可自定义用户名显示
  - 视频末尾无广告

### VIP判断规则
VIP状态通过 `vip_expires_at` 字段判断：
- 如果字段为空：非VIP用户
- 如果当前时间 < 到期时间：VIP用户  
- 如果当前时间 >= 到期时间：VIP已过期，视为普通用户

### 月度免费额度刷新
每月1日自动为所有非VIP用户刷新3条免费额度：
- ✅ 仅对非VIP用户生效
- ✅ 每月只能刷新一次
- ✅ 用户登录时自动检查并刷新
- ✅ 管理员可手动触发批量刷新

## 🔧 技术实现

### 数据库字段
```sql
-- User表新增字段
last_free_credits_refresh DATETIME  -- 记录上次免费额度刷新时间
vip_expires_at DATETIME             -- VIP到期时间
```

### 核心方法
```python
# 检查是否需要刷新免费额度
def should_refresh_free_credits(self):
    # 检查是否跨月且当前为1日
    
# 刷新月度免费额度
def refresh_monthly_free_credits(self):
    # 仅对非VIP用户，且满足刷新条件时执行
    
# 检查当前VIP状态
@property
def is_current_vip(self):
    # 基于vip_expires_at字段动态判断
```

## 🚀 部署和使用

### 1. 自动化任务设置

#### Linux/macOS (使用crontab)
```bash
# 编辑定时任务
crontab -e

# 添加每月1日0点0分执行刷新脚本
0 0 1 * * cd /path/to/VideoMaker && python refresh_monthly_credits.py

# 查看定时任务
crontab -l
```

#### Windows (使用任务计划程序)
1. 打开"任务计划程序"
2. 创建基本任务
3. 设置触发器：每月第1天
4. 设置操作：启动程序 `python`
5. 参数：`refresh_monthly_credits.py`
6. 起始位置：项目根目录

### 2. 手动刷新方式

#### 管理员界面刷新
1. 登录管理员账户
2. 进入"用户管理"页面 (`/admin/users`)
3. 点击"刷新月度额度"按钮

#### 命令行刷新
```bash
# 测试刷新逻辑
python refresh_monthly_credits.py --test

# 执行批量刷新
python refresh_monthly_credits.py
```

#### API刷新
```http
POST /admin/refresh-monthly-credits
Authorization: Admin Required
```

## 📊 监控和日志

### 刷新记录查看
- 登录日志中会记录用户获得月度刷新的信息
- 脚本执行时会输出详细的刷新统计

### 示例日志输出
```
🚀 开始月度免费额度刷新...
✅ 用户 user1 刷新成功，当前额度: 6
⭐ 用户 admin 是VIP，跳过刷新
⏭️ 用户 user2 本月已刷新过，跳过

📊 刷新完成统计:
   总用户数: 15
   刷新成功: 8
   跳过用户: 7
✨ 月度免费额度刷新完成！
```

## 🔐 安全考虑

1. **权限控制**: 只有管理员可以手动触发批量刷新
2. **防重复刷新**: 系统记录刷新时间，防止同月多次刷新
3. **VIP保护**: VIP用户不会被误刷新免费额度
4. **数据完整性**: 使用数据库事务确保操作原子性

## 📅 业务场景

### 典型用户生命周期
1. **新用户注册** → 获得3条免费额度
2. **首次生成视频** → 扣除1条额度，视频显示"百速AI"并有广告
3. **月初自动刷新** → 重新获得3条免费额度
4. **购买VIP会员** → 可自定义显示名称，视频无广告
5. **VIP到期后** → 恢复普通用户状态，继续享受月度免费额度

### 运营优势
- 🎁 **用户留存**: 月度免费额度鼓励用户持续使用
- 💰 **转化驱动**: 免费用户看到品牌标识，促进VIP转化
- 📈 **活跃度提升**: 定期额度刷新带来流量高峰
- 🔄 **自动化运营**: 无需人工干预的月度用户激活

## 🛠️ 故障排除

### 常见问题

**Q: 用户投诉没有收到月度免费额度**
A: 检查用户是否为VIP、是否已经刷新过、系统时间是否正确

**Q: 定时任务没有执行**
A: 检查crontab配置、脚本路径、Python环境路径

**Q: 刷新脚本报错**
A: 检查数据库连接、日志文件权限、依赖包安装

### 调试命令
```bash
# 测试单个用户刷新逻辑
python -c "
from app import app, db, User
with app.app_context():
    user = User.query.filter_by(username='testuser').first()
    print(f'VIP状态: {user.is_current_vip}')
    print(f'是否需要刷新: {user.should_refresh_free_credits()}')
"

# 检查系统时间
date

# 验证crontab任务
crontab -l | grep refresh_monthly_credits
``` 