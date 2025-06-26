# 百速一键AI视频生成系统 v3.0

## 项目概述

百速一键AI视频生成系统是一个基于Flask的Web应用，支持用户通过选择模板、风格和输入内容，一键生成精美的AI视频。系统集成了多种AI模型，包括大语言模型、图像生成模型和语音合成模型。

## 主要功能

### 🎬 视频生成功能
- **多模板支持**：通用、读一本书、故事三种模板
- **多风格选择**：3D景深、绘本、黑白矢量图等多种风格
- **双输入模式**：提示词模式和文案模式
- **智能生成**：自动生成脚本、图片、语音、视频合成

### 👤 用户系统
- **用户注册/登录**：完整的用户认证系统
- **会员体系**：VIP用户享受更多特权
- **积分系统**：视频生成消耗积分
- **个人中心**：查看历史视频、管理账户

### 🎨 界面特性
- **响应式设计**：支持PC和移动端
- **实时预览**：模板视频悬停播放
- **进度跟踪**：实时显示生成进度
- **现代化UI**：基于Element UI的美观界面

## 技术架构

### 后端技术栈
- **Flask**：Web框架
- **SQLAlchemy**：ORM数据库操作
- **Alembic**：数据库迁移
- **Flask-Login**：用户认证
- **异步处理**：后台任务处理

### 前端技术栈
- **Vue.js 2.6**：前端框架
- **Element UI**：UI组件库
- **Axios**：HTTP客户端
- **原生CSS**：自定义样式

### AI模型集成
- **智谱AI**：大语言模型、图像生成
- **通义千问**：图像生成、语音合成
- **DeepSeek**：大语言模型

## 安装和部署

### 环境要求
- Python 3.8+
- SQLite数据库
- 必要的API密钥

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd VideoMaker
```

2. **创建虚拟环境**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境变量**
创建`.env`文件：
```env
ZHIPU_API_KEY=your_zhipu_api_key
DASHSCOPE_API_KEY=your_dashscope_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
SECRET_KEY=your_secret_key
```

5. **初始化数据库**
```bash
flask db upgrade
```

6. **创建管理员用户**
```bash
python create_admin.py
```

7. **启动服务器**
```bash
python run.py
```

### 访问应用
- 应用地址：http://localhost:5002
- 管理员账户：admin / admin123

## 使用指南

### 1. 用户注册/登录
- 访问首页，点击"注册"或"登录"
- 新用户注册后获得3个免费积分

### 2. 选择模板和风格
- **通用模板**：适合各种内容的通用视频
- **读一本书**：专门为书籍介绍设计的模板
- **故事模板**：适合故事类内容的模板

### 3. 输入内容
- **提示词模式**：输入关键词，AI自动生成完整内容
- **文案模式**：直接输入完整的视频文案
- **读一本书模式**：上传封面图片、输入书名和文案

### 4. 高级设置
- **显示标题**：选择是否在视频右上角显示标题
- **用户名**：VIP用户可自定义显示的用户名

### 5. 生成视频
- 点击"开始生成视频"
- 系统自动执行：脚本生成 → 图片生成 → 语音生成 → 视频合成
- 实时查看生成进度

### 6. 下载和管理
- 生成完成后可预览视频
- 支持下载和删除操作
- 在"我的视频"页面管理所有视频

## 会员特权

### VIP用户特权
- 可自定义用户名（非VIP默认为"百速AI"）
- 视频结尾不添加广告
- 更多积分和功能

### 非VIP用户限制
- 用户名固定为"百速AI"
- 视频结尾自动添加广告
- 部分功能受限

## 项目结构

```
VideoMaker/
├── app.py                 # 主应用文件
├── run.py                 # 启动脚本
├── requirements.txt       # 依赖列表
├── .env                   # 环境变量
├── migrations/            # 数据库迁移文件
├── static/                # 静态文件
│   ├── css/              # 样式文件
│   ├── js/               # JavaScript文件
│   ├── img/              # 图片资源
│   └── video/            # 模板视频
├── templates/             # HTML模板
├── service/               # 业务逻辑服务
│   ├── ai_service.py     # AI模型服务
│   └── work_flow_service.py # 工作流服务
├── lib/                   # 资源文件
│   ├── font/             # 字体文件
│   ├── img/              # 背景图片
│   └── music/            # 背景音乐
├── workstore/             # 生成文件存储
└── logs/                  # 日志文件
```

## API接口

### 视频生成接口
- `POST /api/generate-video-v3`：新版视频生成接口
- `GET /api/video-status/<video_id>`：获取生成状态
- `GET /api/video-info/<video_id>`：获取视频信息
- `POST /api/delete-video/<video_id>`：删除视频

### 用户管理接口
- `POST /api/payment-history`：充值记录
- 用户认证相关接口

## 配置说明

### 风格配置
在`static/style_config.py`中配置：
- 图片风格参数
- 模板配置
- 文字样式设置

### 模型配置
在`static/model_info.py`中配置：
- 支持的AI模型列表
- 模型参数设置

## 开发说明

### 添加新模板
1. 在`static/style_config.py`中添加模板配置
2. 在`templates/index.html`中添加模板选择UI
3. 在`static/video/`中添加模板预览视频

### 添加新风格
1. 在`static/style_config.py`中添加风格配置
2. 准备对应的风格图片资源

### 扩展AI模型
1. 在`service/ai_service.py`中添加新模型支持
2. 在`static/model_info.py`中注册新模型

## 故障排除

### 常见问题
1. **API密钥错误**：检查`.env`文件中的API密钥配置
2. **数据库错误**：运行`flask db upgrade`更新数据库
3. **端口占用**：修改`run.py`中的端口号
4. **模板错误**：检查HTML模板语法

### 日志查看
- 应用日志：`logs/app.log`
- 错误日志：`logs/error.log`
- 视频生成日志：`logs/video.log`

## 更新日志

### v3.0 (2025-06-26)
- ✨ 新增模板选择功能
- ✨ 新增会员体系
- ✨ 新增进度跟踪页面
- ✨ 优化用户界面
- ✨ 新增读一本书模板
- 🔧 修复模板语法错误
- 🔧 优化数据库结构

### v2.0
- 基础视频生成功能
- 用户认证系统
- 积分管理

### v1.0
- 初始版本

## 许可证

本项目采用MIT许可证。

## 联系方式

如有问题或建议，请联系开发团队。 