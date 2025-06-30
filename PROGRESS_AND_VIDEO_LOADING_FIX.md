# 进度追踪和视频加载问题修复总结

## 问题描述

在 `http://localhost:5002/generate/19` 页面发现两个主要问题：

1. **进度节点不更新**：进度状态一直停留在"正在撰写脚本"状态，只有在最后完成时才显示"视频生成完成！"并更新到"结束"节点
2. **视频加载失败**：生成完成后，最下面的视频区域一直显示"正在加载视频..."，视频无法正常加载

## 问题分析

### 1. 进度追踪问题

**原因分析：**
- 系统有两套视频生成API：旧版 `generate_video_task` 和新版 `generate_video_v3`
- 新版API使用 `run_work_flow_v3` 函数，但缺少进度状态回调机制
- 前端通过 `/api/video-status/<video_id>` 获取状态，但只有旧版API有完整的状态追踪

**核心问题：**
- `run_work_flow_v3` 函数没有实现进度状态更新
- `generation_status` 字典中缺少 `current_step` 字段
- 前端无法获取到正确的工作流步骤信息

### 2. 视频加载问题

**原因分析：**
- 模板中硬编码了视频URL，依赖后端传递的 `video.video_url` 属性
- 生成完成后没有动态获取视频信息
- 视频路径构建可能存在问题

## 解决方案

### 1. 进度追踪修复

#### 1.1 创建带进度追踪的工作流函数

在 `service/work_flow_service.py` 中添加 `run_work_flow_v3_with_progress` 函数：

```python
async def run_work_flow_v3_with_progress(
    # ... 参数列表 ...
    task_id = None,
    generation_status = None,
    **kwargs
):
    def update_progress(step, message, progress):
        """更新进度状态"""
        if task_id and generation_status and task_id in generation_status:
            generation_status[task_id]['current_step'] = step
            generation_status[task_id]['progress'] = progress
            generation_status[task_id]['message'] = message
            generation_status[task_id]['logs'].append(f"步骤{step}: {message}")
    
    # 在每个工作流步骤中调用 update_progress
    update_progress(1, '正在撰写脚本', 10)
    # ... 脚本生成逻辑 ...
    
    update_progress(2, '正在制作图片', 30)
    # ... 图片生成逻辑 ...
    
    # ... 其他步骤 ...
```

#### 1.2 修改新版API使用带进度追踪的函数

在 `app.py` 的 `generate_video_v3` 函数中：

```python
# 初始化状态记录
task_id = str(uuid.uuid4())
generation_status[task_id] = {
    'video_id': video_id,
    'status': 'processing',
    'progress': 0,
    'message': '初始化生成任务...',
    'logs': ['任务开始: 初始化生成环境'],
    'current_step': 1
}

# 调用带进度追踪的工作流
loop.run_until_complete(run_work_flow_v3_with_progress(
    # ... 参数 ...
    task_id=task_id,
    generation_status=generation_status
))
```

#### 1.3 更新状态API返回进度信息

在 `video_status` API中添加 `current_step` 字段：

```python
return jsonify({
    'success': True,
    'status': task_data.get('status', 'unknown'),
    'progress': task_data.get('progress', 0),
    'message': task_data.get('message', ''),
    'logs': task_data.get('logs', []),
    'current_step': task_data.get('current_step', 1)  # 新增
})
```

#### 1.4 优化前端进度显示逻辑

在 `templates/generate.html` 中改进状态检查逻辑：

```javascript
function checkGenerationStatus() {
    fetch('/api/video-status/' + videoId)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (data.status === 'completed') {
                    showComplete();
                } else if (data.status === 'processing') {
                    // 更新进度状态
                    if (data.current_step !== undefined) {
                        setStep(data.current_step);
                    }
                    if (data.message) {
                        statusText.textContent = data.message;
                    }
                    setTimeout(checkGenerationStatus, 2000);
                }
                // ... 其他状态处理
            }
        });
}
```

### 2. 视频加载修复

#### 2.1 动态视频加载

修改模板，移除硬编码的视频元素：

```html
<div class="video-wrapper">
    <div id="video-container">
        <div class="video-loading">
            <i class="fas fa-video"></i>
            <p>正在加载视频...</p>
        </div>
    </div>
</div>
```

#### 2.2 在完成时动态获取视频信息

修改 `showComplete` 函数：

```javascript
function showComplete() {
    // ... 更新进度显示 ...
    
    // 获取视频信息并加载视频
    fetch('/api/video-info/' + videoId)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.video_url) {
                const videoContainer = document.getElementById('video-container');
                videoContainer.innerHTML = `
                    <video controls>
                        <source src="${data.video_url}" type="video/mp4">
                        您的浏览器不支持视频播放。
                    </video>
                `;
            }
        });
}
```

## 实现的步骤映射

工作流步骤与前端显示的对应关系：

| 步骤 | 后端工作流 | 前端显示 | 进度 |
|------|------------|----------|------|
| 1 | 生成视频脚本 | 正在撰写脚本 | 10% |
| 2 | 生成图片 | 正在制作图片 | 30% |
| 3 | 生成音频 | 正在录制语音 | 50% |
| 4 | 添加时间轴 | 正在剪辑视频 | 70% |
| 5 | 生成视频 | 正在剪辑视频 | 85% |
| 6 | 生成封面 | 正在制作封面 | 95% |
| 7 | 完成 | 视频生成完成！ | 100% |

## 测试验证

创建了 `test_progress_fix.py` 测试脚本，用于验证：

1. **进度追踪功能**：
   - 提交视频生成请求
   - 监控进度状态变化
   - 验证每个步骤的正确显示

2. **视频加载功能**：
   - 检查视频信息API
   - 验证视频URL的正确性
   - 确保视频能够正常加载

## 预期效果

修复后的系统应该能够：

1. **实时进度更新**：
   - 用户可以看到具体的工作流步骤
   - 进度条和状态文字实时更新
   - 每个步骤都有对应的视觉反馈

2. **正常视频加载**：
   - 生成完成后自动加载视频
   - 视频可以正常播放
   - 提供下载和其他操作选项

3. **更好的用户体验**：
   - 清晰的进度指示
   - 及时的状态反馈
   - 流畅的界面交互

## 注意事项

1. **性能考虑**：轮询间隔设置为2秒，平衡了实时性和服务器负载
2. **错误处理**：添加了完善的错误处理机制，确保异常情况下的用户体验
3. **兼容性**：保持了与现有系统的兼容性，不影响其他功能
4. **调试信息**：添加了控制台日志，便于调试和问题排查

## 文件修改清单

- `app.py`: 修改 `generate_video_v3` 和 `video_status` API
- `service/work_flow_service.py`: 添加 `run_work_flow_v3_with_progress` 函数
- `templates/generate.html`: 优化前端进度显示和视频加载逻辑
- `test_progress_fix.py`: 新增测试脚本

通过这些修复，用户在视频生成页面将能够看到实时的进度更新，并在完成后正常观看生成的视频。 