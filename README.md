# 百速一键AI视频生成系统 v3.0

## 项目概述

百速一键AI视频生成系统是一个基于Flask的Web应用，支持用户通过选择模板、风格和输入内容，一键生成精美的AI视频。系统集成了多种AI模型，包括大语言模型、图像生成模型和语音合成模型。

## 主要功能

### 🎬 视频生成功能
- **多模板支持**：通用、读一本书、故事、讲经四种模板
- **多风格选择**：3D景深、绘本、黑白矢量图、水墨画等多种风格
- **双输入模式**：提示词模式和文案模式
- **智能生成**：自动生成脚本、图片、语音、视频合成

### 👤 用户系统
- **用户注册/登录**：完整的用户认证系统
- **会员体系**：VIP用户享受更多特权
- **积分系统**：视频生成消耗积分
- **个人中心**：查看历史视频、管理账号

### 🎨 界面特性
- **响应式设计**：支持PC和移动端
- **实时预览**：模板视频悬停播放
- **进度跟踪**：实时显示生成进度
- **现代化UI**：基于Element UI的美观界面

## 新增功能
- 新增"讲经"模板，适合解读经典、玄学等内容，自动使用高质量TTS模型
- 新增"水墨画"风格，生成国画风格插图，风格图片位于 static/img/水墨画.png

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
- **MiniMax**：高质量TTS（讲经模板专用）

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
MINIMAX_API_KEY=your_minimax_api_key
MINIMAX_GROUP_ID=your_minimax_group_id
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
- 管理员账号：admin / admin123

## 使用指南

1. 注册/登录账号
2. 在首页输入提示词或文案，选择模板（如"讲经"）和风格（如"水墨画"）
3. 点击"一键生成视频"按钮
4. 等待视频生成完成（过程可查看实时进度）
5. 生成完成后可预览、下载或删除视频

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
3. 在`static/video/`中添加模板预览视频或图片

### 添加新风格
1. 在`static/style_config.py`中添加风格配置
2. 准备对应的风格图片资源

### 扩展AI模型
1. 在`service/ai_service.py`中添加新模型支持
2. 在`static/model_info.py`中注册新模型

## 常见问题
1. **API密钥错误**：检查`.env`文件中的API密钥配置
2. **数据库错误**：运行`flask db upgrade`更新数据库
3. **端口占用**：修改`run.py`中的端口号
4. **模板错误**：检查HTML模板语法

## 日志查看
- 应用日志：`logs/app.log`
- 错误日志：`logs/error.log`
- 视频生成日志：`logs/video.log`

## 许可协议

本项目采用MIT许可协议。

## 联系方式

如有问题或建议，请联系开发团队。