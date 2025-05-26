# 百速一键AI视频生成

一个基于AI技术的自动视频生成系统，可以根据用户输入的提示词，自动生成包含脚本、图片、语音和字幕的完整视频。

## 功能特点

- **一键生成**：只需输入提示词，选择风格，即可自动生成完整视频
- **多种风格**：支持"3D景深"、"黑白矢量图"、"绘本"等多种视觉风格
- **用户系统**：完整的用户注册、登录和充值功能
- **视频管理**：支持视频预览、下载和删除
- **实时状态**：生成过程中实时显示进度和状态

## 技术架构

- **前端**：Vue.js + Element UI
- **后端**：Flask + SQLAlchemy
- **AI服务**：
  - 文本生成：智谱AI GLM大模型
  - 图像生成：智谱AI CogView模型
  - 语音合成：阿里云语音服务

## 安装部署

### 环境要求

- Python 3.8+
- Node.js 14+（如需单独构建前端）
- 智谱AI API密钥
- 阿里云语音服务API密钥

### 安装步骤

1. 克隆代码库

```bash
git clone <仓库地址>
cd VideoMaker
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

3. 配置环境变量

创建`.env`文件，添加以下内容：

```
ZHIPU_API_KEY=你的智谱AI API密钥
DASHSCOPE_API_KEY=你的阿里云语音服务API密钥
FONT_DIR=./lib/font
MUSIC_DIR=./lib/music
SECRET_KEY=自定义密钥（用于Flask会话加密）
```

4. 初始化数据库

```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

5. 启动应用

```bash
python app.py
```

应用将在 http://localhost:5000 运行

## 使用指南

1. 注册/登录账号
2. 在首页输入提示词（如"以很多人都有的心理困扰问题，选择一个主题，做一个分析和如何解决的视频"）
3. 选择视频风格
4. 点击"一键生成视频"按钮
5. 等待视频生成完成（过程中可查看实时状态）
6. 生成完成后可预览、下载或删除视频

## 项目结构

```
VideoMaker/
├── app.py                 # Flask应用入口
├── requirements.txt       # 项目依赖
├── service/               # 核心服务
│   ├── ai_service.py      # AI服务接口
│   ├── work_flow_service.py # 视频生成工作流
│   └── ...
├── static/               # 静态资源
│   ├── css/              # 样式文件
│   ├── js/               # JavaScript文件
│   ├── img/              # 图片资源
│   └── style_config.py   # 风格配置
├── templates/            # 前端模板
│   ├── base.html         # 基础模板
│   ├── index.html        # 首页
│   └── ...
├── lib/                  # 资源库
│   ├── font/             # 字体文件
│   └── music/            # 背景音乐
└── workflow.py           # 工作流定义
```

## 注意事项

- 视频生成过程较为耗时，请耐心等待
- 新注册用户默认赠送3条视频生成额度
- 生成的视频默认保存在`workstore`目录下

## 许可证

[MIT License](LICENSE)