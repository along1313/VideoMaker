# 数据库变更部署指南

## 问题背景

本次生产故障的根本原因：代码中新增了 `TaskQueue` 数据库模型，但部署时没有同步更新数据库结构，导致 `INSERT INTO task_queue` 操作失败。

## 标准化解决方案

### 1. 使用 Flask-Migrate 管理数据库版本

#### 初始化 Migrate（一次性设置）
```bash
# 安装 Flask-Migrate
pip install Flask-Migrate

# 在 app.py 中添加
from flask_migrate import Migrate
migrate = Migrate(app, db)

# 初始化迁移仓库
flask db init
```

#### 生成迁移文件
```bash
# 每次修改模型后生成迁移
flask db migrate -m "添加TaskQueue表"
```

#### 部署时应用迁移
```bash
# 在服务器上执行
flask db upgrade
```

### 2. 改进的部署脚本

已创建 `deploy_with_db_check.sh` 包含以下安全检查：

```bash
# 使用新的安全部署脚本
./deploy_with_db_check.sh
```

### 3. 标准化工作流程

#### 开发阶段
1. **修改数据库模型后立即生成迁移**
   ```bash
   # 每次修改 app.py 中的 db.Model 后
   flask db migrate -m "描述变更内容"
   git add migrations/
   git commit -m "添加数据库迁移: 描述变更"
   ```

2. **本地测试迁移**
   ```bash
   flask db upgrade  # 确保迁移脚本正确
   ```

#### 部署阶段
1. **使用安全部署脚本**
   ```bash
   ./deploy_with_db_check.sh
   ```

2. **脚本自动执行以下步骤：**
   - 检测代码中的数据库模型变更
   - 自动备份现有数据库
   - 部署代码更新
   - 运行数据库迁移（如需要）
   - 重启服务并验证

### 4. 预防措施清单

#### ✅ 代码层面
- [ ] 新增/修改 `db.Model` 后立即生成迁移文件
- [ ] 迁移文件与代码变更一起提交
- [ ] 本地测试迁移的前向和回滚操作

#### ✅ 部署层面  
- [ ] 使用包含数据库检查的部署脚本
- [ ] 部署前自动备份数据库
- [ ] 部署后验证数据库结构完整性
- [ ] 监控服务启动日志

#### ✅ 监控层面
- [ ] 添加数据库结构健康检查
- [ ] 监控 SQLite 相关错误
- [ ] 设置关键功能可用性监控

### 5. 应急恢复流程

如果部署后发现数据库问题：

```bash
# 1. 立即回滚到备份
ssh user@server "cd /path && cp instance/db_backup_YYYYMMDD_HHMMSS.db instance/baisu_video.db"

# 2. 重启服务
ssh user@server "systemctl restart videomaker"

# 3. 验证回滚成功
ssh user@server "curl -I http://localhost:5001"
```

### 6. 最佳实践建议

#### 数据库版本控制
```python
# app.py 中添加版本检查
def check_database_version():
    """检查数据库版本与代码兼容性"""
    try:
        # 检查关键表是否存在
        required_tables = ['user', 'video', 'task_queue', 'feedback']
        # ... 检查逻辑
    except Exception as e:
        log_error(f"数据库版本检查失败: {e}")
        return False
    return True

# 应用启动时调用
@app.before_first_request  
def startup_checks():
    if not check_database_version():
        raise RuntimeError("数据库版本不兼容，需要运行迁移")
```

#### 渐进式部署
1. **蓝绿部署**：维护两套环境，切换流量
2. **灰度发布**：先在少量用户上测试
3. **回滚准备**：每次部署前准备快速回滚方案

## 本次故障总结

### 故障原因
- ❌ 代码引入了 `TaskQueue` 模型但未同步数据库结构
- ❌ 部署流程缺少数据库一致性检查
- ❌ 没有自动化的数据库迁移机制

### 解决方案
- ✅ 创建了数据库迁移脚本自动检查和创建缺失表
- ✅ 建立了包含数据库检查的标准化部署流程
- ✅ 添加了数据库备份和恢复机制

### 预防效果
使用新的部署流程可以：
- 🛡️ **自动检测**数据库模型变更
- 🛡️ **强制备份**避免数据丢失
- 🛡️ **验证完整性**确保部署成功
- 🛡️ **快速回滚**出现问题时及时恢复

## 后续建议

1. **立即行动**：将 `deploy_with_db_check.sh` 设为标准部署脚本
2. **定期检查**：每周运行数据库健康检查
3. **团队培训**：确保所有开发者了解数据库变更流程
4. **监控升级**：添加数据库结构异常告警

通过这套标准化流程，可以有效避免类似的生产环境数据库不一致问题！