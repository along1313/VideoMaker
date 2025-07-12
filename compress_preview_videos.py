#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频预览处理脚本
截取static/video目录中视频的前15秒，并压缩以适合主页展示
"""

import os
import sys
from moviepy import VideoFileClip
import glob

def compress_preview_videos(input_dir="static/video", output_dir="static/video/preview", duration=15):
    """
    处理视频文件：截取前15秒并压缩
    
    Args:
        input_dir (str): 输入视频目录
        output_dir (str): 输出目录
        duration (int): 截取时长（秒）
    """
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 支持的视频格式
    video_extensions = ['*.mp4', '*.avi', '*.mov', '*.mkv', '*.wmv', '*.flv']
    
    # 获取所有视频文件
    video_files = []
    for ext in video_extensions:
        video_files.extend(glob.glob(os.path.join(input_dir, ext)))
        video_files.extend(glob.glob(os.path.join(input_dir, ext.upper())))
    
    if not video_files:
        print(f"在 {input_dir} 目录中没有找到视频文件")
        return
    
    print(f"找到 {len(video_files)} 个视频文件")
    print("开始处理...\n")
    
    for i, video_path in enumerate(video_files, 1):
        try:
            filename = os.path.basename(video_path)
            name, ext = os.path.splitext(filename)
            output_path = os.path.join(output_dir, f"{name}_preview{ext}")
            
            print(f"[{i}/{len(video_files)}] 处理: {filename}")
            
            # 检查输出文件是否已存在
            if os.path.exists(output_path):
                print(f"  ⚠️  输出文件已存在，跳过: {output_path}")
                continue
            
            # 加载视频
            with VideoFileClip(video_path) as video:
                # 获取视频信息
                original_duration = video.duration
                original_size = video.size
                
                print(f"  📹 原始时长: {original_duration:.1f}秒, 分辨率: {original_size[0]}x{original_size[1]}")
                
                # 截取前15秒（如果视频长度不足15秒，则使用全部长度）
                clip_duration = min(duration, original_duration)
                clipped_video = video.subclipped(0, clip_duration)
                
                # 压缩设置
                # 1. 降低分辨率到最大720p
                target_height = 720
                if original_size[1] > target_height:
                    scale_factor = target_height / original_size[1]
                    new_width = int(original_size[0] * scale_factor)
                    # 确保宽度是偶数（H.264编码要求）
                    if new_width % 2 != 0:
                        new_width -= 1
                    clipped_video = clipped_video.resized((new_width, target_height))
                    print(f"  📐 调整分辨率到: {new_width}x{target_height}")
                
                # 2. 输出压缩视频
                print(f"  💾 正在保存: {output_path}")
                clipped_video.write_videofile(
                    output_path,
                    codec='libx264',
                    audio_codec='aac',
                    bitrate='1000k',      # 视频比特率1Mbps
                    audio_bitrate='128k', # 音频比特率128kbps
                    fps=24,               # 降低帧率到24fps
                    preset='medium',      # 编码预设：medium平衡质量和速度
                    ffmpeg_params=[
                        '-crf', '28',     # 恒定质量因子：28（较高压缩）
                        '-movflags', '+faststart'  # 优化web播放
                    ],
                    logger=None           # 禁用moviepy日志
                )
                
                # 获取输出文件大小
                output_size = os.path.getsize(output_path)
                original_size_mb = os.path.getsize(video_path) / (1024 * 1024)
                output_size_mb = output_size / (1024 * 1024)
                
                print(f"  ✅ 完成! 时长: {clip_duration:.1f}秒")
                print(f"     原始大小: {original_size_mb:.1f}MB → 压缩后: {output_size_mb:.1f}MB")
                print(f"     压缩率: {((original_size_mb - output_size_mb) / original_size_mb * 100):.1f}%")
                
        except Exception as e:
            print(f"  ❌ 处理失败: {str(e)}")
        
        print()
    
    print("🎉 所有视频处理完成!")

def main():
    """主函数"""
    print("=" * 60)
    print("视频预览处理脚本")
    print("=" * 60)
    print("功能: 截取视频前15秒并压缩以适合主页展示")
    print()
    
    # 检查输入目录是否存在
    input_dir = "static/video"
    if not os.path.exists(input_dir):
        print(f"❌ 输入目录不存在: {input_dir}")
        print("请确保在项目根目录运行此脚本")
        sys.exit(1)
    
    # 检查是否有moviepy
    try:
        from moviepy import VideoFileClip
    except ImportError:
        print("❌ 未安装moviepy库")
        print("请运行: pip install moviepy")
        sys.exit(1)
    
    # 执行处理
    try:
        compress_preview_videos()
    except KeyboardInterrupt:
        print("\n⚠️  用户中断操作")
    except Exception as e:
        print(f"❌ 发生错误: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
