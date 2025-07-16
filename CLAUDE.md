# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Starting the Application
```bash
python run.py                    # Start development server on port 5002
```

### Production Deployment
```bash
gunicorn -c gunicorn.conf.py app:app    # Start production server with gunicorn
```

### Database Operations
```bash
flask db upgrade                 # Apply database migrations
python create_admin.py          # Create admin user
```

### Testing
```bash
python test/test_work_flow_by_step.py    # Test video generation workflow
python test_stop_functionality.py       # Test video generation stopping
```

### Dependencies
```bash
pip install -r requirements.txt         # Install Python dependencies
npm install                             # Install frontend dependencies (minimal)
```

## Architecture Overview

### Core Application Structure
- **app.py**: Main Flask application with user management, video generation API endpoints, and database models
- **run.py**: Application startup script that initializes environment and database
- **workflow.py**: Core video generation workflow orchestrator
- **gunicorn.conf.py**: Production server configuration

### Service Layer (`service/`)
- **ai_service.py**: AI model integrations (LLM, Image Generation, TTS)
- **work_flow_service.py**: Video generation workflow management with progress tracking
- **script_service.py**: Content script generation and processing
- **picture_generate_service.py**: Image generation service
- **email_service.py**: Email notifications and verification

### Data Models (in app.py)
- **User**: User authentication and VIP management
- **Video**: Video records with status tracking
- **TaskQueue**: Background task management
- **Message**: User messaging system

### Video Generation Workflow
1. **Input Processing**: User provides content (prompt or script) and selects template/style
2. **Script Generation**: AI generates structured content script
3. **Asset Creation**: Parallel generation of images, audio, and covers
4. **Video Assembly**: MoviePy composites final video with transitions and effects
5. **Storage**: Videos stored in `workstore/{user_id}/{title}/` structure

### Template System
- **Templates**: 通用 (General), 读一本书 (Book Reading), 故事 (Story), 讲经 (Scripture)
- **Styles**: 3D景深, 绘本, 黑白矢量图, 水墨画 (various artistic styles)
- **Configuration**: `static/style_config.py` and `static/model_info.py`

### AI Model Integration
- **智谱AI (ZhipuAI)**: Primary LLM and image generation
- **通义千问 (Dashscope)**: Alternative image generation and TTS
- **DeepSeek**: Additional LLM support
- **MiniMax**: High-quality TTS for scripture template

### File Storage Structure
```
workstore/
├── {user_id}/
│   └── {video_title}/
│       ├── work_flow_record.json
│       ├── output.mp4
│       ├── audios/
│       ├── images/
│       └── covers/
```

### Environment Configuration
Required environment variables in `.env`:
- `ZHIPU_API_KEY`: 智谱AI API key
- `DASHSCOPE_API_KEY`: 阿里云通义千问 API key
- `DEEPSEEK_API_KEY`: DeepSeek API key (optional)
- `MINIMAX_API_KEY`: MiniMax TTS API key (optional)
- `SECRET_KEY`: Flask secret key

### Background Processing
- Asynchronous video generation using threading
- Task queue system with status tracking
- Progress updates via WebSocket-style polling
- Automatic recovery of interrupted tasks on startup

### Database Schema
- SQLite database with Flask-Migrate for versioning
- User authentication with Flask-Login
- VIP system with credit-based usage limits
- Video generation history and status tracking

## Development Notes

### Testing Video Generation
Use test files in `test/` directory to validate workflow components individually before testing full generation pipeline.

### Adding New Templates
1. Update `TEMPLATE_CONFIG` in `static/style_config.py`
2. Add template preview files in `static/video/`
3. Update frontend template selection in `templates/index.html`

### Adding New AI Models
1. Extend service classes in `service/ai_service.py`
2. Update model configuration in `static/model_info.py`
3. Add API credentials to environment variables

### Deployment
Use deployment scripts in `deploy_scripts/` for production deployment. The application runs behind nginx with gunicorn workers.