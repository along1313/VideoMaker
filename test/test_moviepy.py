import os
import pytest
from moviepy import VideoFileClip, ImageClip, TextClip, CompositeVideoClip, vfx

@pytest.mark.parametrize("video_path,image_path,font_path", [
    ("static/video/故事.mp4", "static/img/logo.png", "lib/font/NotoSansSC-Medium.ttf"),
])
def test_moviepy_basic_workflow(video_path, image_path, font_path):
    # 检查测试资源是否存在
    assert os.path.exists(video_path), f"视频文件不存在: {video_path}"
    assert os.path.exists(image_path), f"图片文件不存在: {image_path}"
    assert os.path.exists(font_path), f"字体文件不存在: {font_path}"

    # 1. 加载视频
    video = VideoFileClip(video_path).subclipped(0, 5)  # 取前5秒

    # 2. 加载图片并设置时长
    logo = ImageClip(image_path).with_duration(5).with_position(("right", "bottom"))

    # 3. 创建文本剪辑
    text = TextClip(
        font=font_path,
        text="MoviePy v2 测试",
        font_size=50,
        color="white"
    ).with_duration(5).with_position(("center", "top"))

    # 4. 应用淡入淡出效果
    text = text.with_effects([vfx.FadeIn(1), vfx.FadeOut(1)])

    # 5. 合成视频
    final = CompositeVideoClip([video, logo, text])

    # 6. 导出（仅测试生成，不保存到磁盘）
    # final.write_videofile("test_output.mp4", fps=video.fps)  # 如需导出，取消注释

    # 7. 简单断言
    assert final.duration == pytest.approx(5, 0.1)
    assert final.size == video.size

    # 8. 预览（可选，调试用）
    # final.preview(fps=video.fps)


