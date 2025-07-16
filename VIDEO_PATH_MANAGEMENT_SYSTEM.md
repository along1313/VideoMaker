# 视频路径管理系统

## 概述

本文档详细介绍了VideoMaker项目中实现的统一视频路径管理系统。该系统旨在解决项目中路径管理混乱、维护困难的问题，提供一个科学、统一、易维护的文件路径管理解决方案。

## 系统设计目标

### 1. 统一性
- 所有视频生成相关的路径操作都通过统一的路径管理器处理
- 避免代码中硬编码路径字符串
- 提供统一的路径生成、验证和清理接口

### 2. 科学性
- 规范的目录结构设计
- 安全的项目名称处理
- 完善的错误处理机制

### 3. 易维护性
- 集中式路径管理逻辑
- 清晰的API接口
- 详细的日志记录

## 目录结构设计

### 基础目录结构
```
workstore/                    # 基础工作目录
├── user1/                   # 用户1的工作目录
│   ├── 项目名称1/           # 项目目录
│   │   ├── output.mp4       # 主视频文件
│   │   ├── covers/          # 封面目录
│   │   │   ├── cover_4:3.png    # 4:3比例封面
│   │   │   ├── cover_3:4.png    # 3:4比例封面
│   │   │   └── cover.png        # 默认封面
│   │   ├── images/          # 图片素材目录
│   │   ├── audios/          # 音频素材目录
│   │   ├── temp/            # 临时文件目录
│   │   └── work_flow_record.json  # 工作流记录
│   └── 项目名称2/
└── user2/
    └── ...
```

### 路径命名规范

#### 用户目录
- 格式：`user{user_id}`
- 示例：`user1`、`user123`

#### 项目目录
- 项目名称会经过清理处理：
  - 移除或替换非法字符：`< > : " / \ | ? *`
  - 限制长度为50个字符
  - 移除前后空格
  - 空名称时使用时间戳生成默认名称

#### 文件名称
- 视频文件：`output.mp4`
- 封面文件：
  - 4:3比例：`cover_4:3.png`
  - 3:4比例：`cover_3:4.png`
  - 默认封面：`cover.png`

## 核心组件

### VideoPathManager 类

#### 主要方法

##### 1. 目录管理
```python
def get_user_dir(self, user_id: int) -> Path
def get_project_dir(self, user_id: int, project_name: str) -> Path
def get_project_paths(self, user_id: int, project_name: str) -> Dict[str, Path]
```

##### 2. 路径生成
```python
def get_video_path(self, user_id: int, project_name: str) -> str
def get_cover_path(self, user_id: int, project_name: str, aspect_ratio: str) -> str
def get_web_accessible_path(self, file_path: str) -> str
```

##### 3. 文件管理
```python
def cleanup_project_files(self, user_id: int, project_name: str) -> Dict[str, bool]
def sanitize_project_name(self, project_name: str) -> str
```

##### 4. 信息查询
```python
def get_project_info(self, user_id: int, project_name: str) -> Dict[str, any]
def list_user_projects(self, user_id: int) -> List[Dict[str, any]]
```

## 集成应用

### 1. 视频生成流程

#### 在队列任务完成时更新路径
```python
# 使用统一的路径管理器更新视频路径信息
project_title = current_video.title
user_id_int = int(user_dir_name.replace('user', ''))

# 获取标准化的路径
video_path = path_manager.get_video_path(user_id_int, project_title)
cover_path = path_manager.get_cover_path(user_id_int, project_title, "4:3")

# 检查文件是否存在并更新路径
if os.path.exists(video_path):
    current_video.video_path = video_path
    log_info(f"更新视频路径: {video_path}")
```

### 2. 视频删除流程

#### 使用路径管理器清理文件
```python
def cleanup_video_files(video):
    # 使用路径管理器清理项目文件
    cleanup_result_from_manager = path_manager.cleanup_project_files(user_id, project_id)
    
    if cleanup_result_from_manager['project_dir_removed']:
        cleanup_result['project_dir'] = True
        log_info(f"已使用路径管理器删除项目目录: {project_id}", "video")
```

### 3. Web路径处理

#### 前端路径转换
```python
def getCoverUrl(coverPath):
    if not coverPath:
        return '/static/img/default-cover.png'
    return path_manager.get_web_accessible_path(coverPath)
```

## 错误处理

### 1. 项目名称处理
- 自动清理非法字符
- 长度限制保护
- 空名称默认值

### 2. 文件操作错误
- 详细的错误信息记录
- 失败操作的回滚机制
- 用户友好的错误提示

### 3. 路径安全检查
- 防止路径遍历攻击
- 确保操作在指定目录内
- 标准化路径处理

## 性能优化

### 1. 目录创建
- 按需创建目录结构
- 避免重复创建操作
- 使用系统缓存

### 2. 路径计算
- 路径计算结果缓存
- 批量路径操作优化
- 减少文件系统调用

## 日志记录

### 1. 操作日志
```python
log_info(f"更新视频路径: {video_path}")
log_warning(f"视频文件不存在: {video_path}")
log_error(f"删除项目目录失败: {str(e)}")
```

### 2. 调试信息
- 路径生成过程记录
- 文件操作状态跟踪
- 错误详细信息

## 使用示例

### 1. 基本使用
```python
from path_manager import path_manager

# 获取用户项目路径
paths = path_manager.get_project_paths(user_id=1, project_name="我的视频项目")

# 生成Web可访问路径
web_path = path_manager.get_web_accessible_path(paths['video_file'])

# 清理项目文件
result = path_manager.cleanup_project_files(user_id=1, project_name="我的视频项目")
```

### 2. 批量操作
```python
# 获取用户所有项目
projects = path_manager.list_user_projects(user_id=1)

# 批量清理过期项目
for project in projects:
    if should_cleanup(project):
        path_manager.cleanup_project_files(user_id=1, project_name=project['project_name'])
```

## 配置参数

### 1. 基础配置
```python
# 基础工作目录
base_workstore_dir = "workstore"

# 项目名称长度限制
max_project_name_length = 50

# 支持的封面比例
supported_aspect_ratios = ["4:3", "3:4", "default"]
```

### 2. 安全配置
```python
# 禁止的文件名字符
forbidden_chars = r'[<>:"/\\|?*]'

# 最大目录深度
max_directory_depth = 5
```

## 迁移指南

### 1. 从旧系统迁移
1. 备份现有数据
2. 运行路径标准化脚本
3. 更新数据库路径记录
4. 验证文件访问正常

### 2. 数据完整性检查
```python
# 检查路径一致性
def verify_path_consistency():
    videos = Video.query.all()
    for video in videos:
        expected_path = path_manager.get_video_path(video.user_id, video.title)
        if video.video_path != expected_path:
            log_warning(f"路径不一致: {video.id}")
```

## 最佳实践

### 1. 开发建议
- 始终使用路径管理器获取路径
- 避免硬编码路径字符串
- 及时处理路径操作错误

### 2. 维护建议
- 定期清理临时文件
- 监控磁盘使用情况
- 备份重要项目数据

### 3. 扩展建议
- 支持更多文件类型
- 实现路径压缩功能
- 添加文件版本管理

## 故障排除

### 1. 常见问题
- **路径不存在**：检查目录创建权限
- **文件无法访问**：验证Web服务器配置
- **清理失败**：检查文件占用情况

### 2. 调试方法
```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 检查项目信息
info = path_manager.get_project_info(user_id, project_name)
print(json.dumps(info, indent=2))
```

## 版本历史

### v1.0.0 (2025-01-15)
- 初始版本发布
- 基础路径管理功能
- 统一的API接口
- 完整的错误处理机制

## 贡献指南

欢迎对路径管理系统进行改进！请遵循以下原则：

1. 保持API的向后兼容性
2. 添加完整的单元测试
3. 更新相关文档
4. 遵循代码规范

## 许可证

该路径管理系统遵循项目的整体许可证协议。 