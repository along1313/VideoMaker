# 百速AI 邮件服务配置指南

## 📧 使用 baisuai.com 域名发送邮件

是的，完全可以使用您的域名 `baisuai.com` 来发送邮件！下面提供几种实现方案：

## 🚀 推荐方案：腾讯企业邮箱

### 优势
- ✅ 国内服务，稳定可靠
- ✅ 免费版支持50个邮箱
- ✅ 完善的反垃圾邮件机制
- ✅ 配置简单

### 配置步骤

#### 1. 开通腾讯企业邮箱
1. 访问 [腾讯企业邮箱](https://exmail.qq.com/)
2. 注册并添加域名 `baisuai.com`
3. 创建邮箱账号：`noreply@baisuai.com`

#### 2. DNS 配置
在您的域名服务商（如阿里云、腾讯云）添加以下记录：

```bash
# MX 记录 (邮件交换记录)
@    MX    5     mxbiz1.qq.com.
@    MX    10    mxbiz2.qq.com.

# SPF 记录 (防止垃圾邮件)
@    TXT   "v=spf1 include:spf.mail.qq.com ~all"

# DKIM 记录 (提高送达率)
tencent-verification._domainkey    TXT    "腾讯提供的DKIM值"

# DMARC 记录 (可选，提高安全性)
_dmarc    TXT    "v=DMARC1; p=quarantine; rua=mailto:admin@baisuai.com"
```

#### 3. 环境变量配置

创建 `.env` 文件并配置：

```bash
# 腾讯企业邮箱配置
MAIL_SERVER=smtp.exmail.qq.com
MAIL_PORT=465
MAIL_USE_SSL=True
MAIL_USE_TLS=False
MAIL_USERNAME=noreply@baisuai.com
MAIL_PASSWORD=你的邮箱密码
MAIL_DEFAULT_SENDER=百速AI <noreply@baisuai.com>
```

## 🔧 备选方案：阿里云邮件推送

### 优势
- ✅ 专业的邮件发送服务
- ✅ 高送达率保证
- ✅ 按量付费，成本可控
- ✅ 详细的发送统计

### 配置步骤

#### 1. 开通服务
1. 访问 [阿里云邮件推送](https://dm.console.aliyun.com/)
2. 开通服务并实名认证
3. 添加发信域名：`baisuai.com`

#### 2. DNS 配置
```bash
# 域名验证记录
_dm._domainkey.baisuai.com    TXT    "阿里云提供的DKIM值"

# SPF 记录
@    TXT    "v=spf1 include:spf1.dm.aliyun.com -all"

# MX 记录 (如果需要收信)
@    MX    10    mx1.dm.aliyun.com.
@    MX    20    mx2.dm.aliyun.com.
```

#### 3. 环境变量配置
```bash
# 阿里云邮件推送配置
ALIYUN_ACCESS_KEY=你的AccessKey
ALIYUN_ACCESS_SECRET=你的AccessSecret
ALIYUN_REGION=cn-hangzhou
MAIL_DEFAULT_SENDER=百速AI <noreply@baisuai.com>
```

## 🛠️ 安装依赖

添加到 `requirements.txt`：

```bash
# 邮件服务
Flask-Mail==0.9.1
itsdangerous==2.1.2

# 阿里云邮件推送 (如果使用)
aliyun-python-sdk-core==2.13.36
aliyun-python-sdk-dm==3.3.1
```

## 📝 创建邮箱账号建议

建议创建以下邮箱账号：

```bash
noreply@baisuai.com      # 系统发送邮件 (验证码、通知等)
admin@baisuai.com        # 管理员邮箱
support@baisuai.com      # 客服邮箱
marketing@baisuai.com    # 营销邮件 (可选)
```

## 🔒 安全配置

### 1. SPF 记录
防止其他人伪造您的域名发送邮件：
```bash
@    TXT    "v=spf1 include:spf.mail.qq.com ~all"
```

### 2. DKIM 记录
提高邮件的可信度和送达率：
```bash
tencent-verification._domainkey    TXT    "腾讯提供的公钥"
```

### 3. DMARC 记录
定义邮件认证失败的处理策略：
```bash
_dmarc    TXT    "v=DMARC1; p=quarantine; rua=mailto:admin@baisuai.com"
```

## 🎯 DNS 配置验证

配置完成后，使用以下工具验证：

1. **MX 记录查询**
   ```bash
   nslookup -type=MX baisuai.com
   ```

2. **SPF 记录查询**
   ```bash
   nslookup -type=TXT baisuai.com
   ```

3. **在线工具验证**
   - [MX Toolbox](https://mxtoolbox.com/)
   - [SPF Record Checker](https://www.kitterman.com/spf/validate.html)

## 📧 邮件模板测试

配置完成后，测试邮件发送：

```python
# 测试脚本
from service.email_service import email_service
from app import app

with app.app_context():
    # 发送测试邮件
    result = email_service.send_verification_email(
        user_email="test@example.com",
        verification_code="123456",
        username="测试用户"
    )
    print(f"邮件发送结果: {result}")
```

## ⚠️ 注意事项

1. **域名验证**：大部分邮件服务商需要验证域名所有权
2. **实名认证**：国内服务商可能需要实名认证
3. **发送限制**：免费版本通常有发送数量限制
4. **预热期**：新域名需要逐步建立发信声誉
5. **监控**：定期检查邮件送达率和退信率

## 🚀 最佳实践

1. **使用专用发信子域名**
   ```bash
   mail.baisuai.com  # 专门用于发送邮件
   ```

2. **设置邮件头信息**
   ```python
   Message-ID: <unique-id@baisuai.com>
   Return-Path: noreply@baisuai.com
   Reply-To: support@baisuai.com
   ```

3. **邮件内容优化**
   - 避免垃圾邮件关键词
   - 保持文本/HTML比例平衡
   - 提供退订链接

4. **发送频率控制**
   - 避免短时间大量发送
   - 建立用户参与度
   - 监控投诉率

## 📞 技术支持

如果在配置过程中遇到问题：

1. **腾讯企业邮箱**：[官方文档](https://work.weixin.qq.com/help)
2. **阿里云邮件推送**：[官方文档](https://help.aliyun.com/product/29412.html)
3. **DNS 配置**：联系您的域名服务商技术支持

---

**配置完成后，您就可以使用 `@baisuai.com` 的邮箱地址发送专业的系统邮件了！** 🎉 