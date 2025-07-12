#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级视频预览处理脚本
支持命令行参数自定义各种处理选项
"""

import os
import sys
import argparse
from moviepy import VideoFileClip
import glob

def compress_preview_videos(input_dir, output_dir, duration, max_height, bitrate, audio_bitrate, fps, crf):
    """
    处理视频文件：截取指定时长并压缩
    
    Args:
        input_dir (str): 输入视频目录
        output_dir (str): 输出目录
        duration (int): 截取时长（秒）
        max_height (int): 最大高度
        bitrate (str): 视频比特率
        audio_bitrate (str): 音频比特率
        fps (int): 帧率
        crf (int): 质量因子
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
    
    total_original_size = 0
    total_compressed_size = 0
    processed_count = 0
    
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
                
                # 截取指定时长（如果视频长度不足，则使用全部长度）
                clip_duration = min(duration, original_duration)
                clipped_video = video.subclipped(0, clip_duration)
                
                # 压缩设置
                # 1. 降低分辨率
                if original_size[1] > max_height:
                    scale_factor = max_height / original_size[1]
                    new_width = int(original_size[0] * scale_factor)
                    # 确保宽度是偶数（H.264编码要求）
                    if new_width % 2 != 0:
                        new_width -= 1
                    clipped_video = clipped_video.resized((new_width, max_height))
                    print(f"  📐 调整分辨率到: {new_width}x{max_height}")
                
                # 2. 输出压缩视频
                print(f"  💾 正在保存: {output_path}")
                clipped_video.write_videofile(
                    output_path,
                    codec='libx264',
                    audio_codec='aac',
                    bitrate=bitrate,
                    audio_bitrate=audio_bitrate,
                    fps=fps,
                    preset='medium',
                    ffmpeg_params=[
                        '-crf', str(crf),
                        '-movflags', '+faststart'
                    ],
                    logger=None
                )
                
                # 统计文件大小
                original_file_size = os.path.getsize(video_path)
                output_file_size = os.path.getsize(output_path)
                original_size_mb = original_file_size / (1024 * 1024)
                output_size_mb = output_file_size / (1024 * 1024)
                
                total_original_size += original_file_size
                total_compressed_size += output_file_size
                processed_count += 1
                
                print(f"  ✅ 完成! 时长: {clip_duration:.1f}秒")
                print(f"     原始大小: {original_size_mb:.1f}MB → 压缩后: {output_size_mb:.1f}MB")
                print(f"     压缩率: {((original_size_mb - output_size_mb) / original_size_mb * 100):.1f}%")
                
        except Exception as e:
            print(f"  ❌ 处理失败: {str(e)}")
        
        print()
    
    # 显示总体统计
    if processed_count > 0:
        total_original_mb = total_original_size / (1024 * 1024)
        total_compressed_mb = total_compressed_size / (1024 * 1024)
        overall_compression = ((total_original_mb - total_compressed_mb) / total_original_mb * 100)
        
        print("=" * 60)
        print("📊 总体统计")
        print("=" * 60)
        print(f"处理文件数: {processed_count}")
        print(f"总原始大小: {total_original_mb:.1f}MB")
        print(f"总压缩后大小: {total_compressed_mb:.1f}MB")
        print(f"总体压缩率: {overall_compression:.1f}%")
        print(f"节省空间: {total_original_mb - total_compressed_mb:.1f}MB")
    
    print("🎉 所有视频处理完成!")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='视频预览处理脚本 - 截取并压缩视频以适合主页展示',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例用法:
  python compress_preview_videos_advanced.py                    # 使用默认设置
  python compress_preview_videos_advanced.py -d 10             # 截取前10秒
  python compress_preview_videos_advanced.py -h 480 -b 500k    # 480p分辨率，500k比特率
  python compress_preview_videos_advanced.py -i custom_input   # 自定义输入目录
        '''
    )
    
    parser.add_argument('-i', '--input', 
                       default='static/video',
                       help='输入视频目录 (默认: static/video)')
    
    parser.add_argument('-o', '--output',
                       default='static/video/preview',
                       help='输出目录 (默认: static/video/preview)')
    
    parser.add_argument('-d', '--duration',
                       type=int, default=15,
                       help='截取时长(秒) (默认: 15)')
    
    parser.add_argument('-h', '--height',
                       type=int, default=720,
                       help='最大高度像素 (默认: 720)')
    
    parser.add_argument('-b', '--bitrate',
                       default='1000k',
                       help='视频比特率 (默认: 1000k)')
    
    parser.add_argument('-ab', '--audio-bitrate',
                       default='128k',
                       help='音频比特率 (默认: 128k)')
    
    parser.add_argument('-f', '--fps',
                       type=int, default=24,
                       help='输出帧率 (默认: 24)')
    
    parser.add_argument('-c', '--crf',
                       type=int, default=28,
                       help='质量因子 CRF (默认: 28, 范围: 0-51, 越小质量越好)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("高级视频预览处理脚本")
    print("=" * 60)
    print(f"输入目录: {args.input}")
    print(f"输出目录: {args.output}")
    print(f"截取时长: {args.duration}秒")
    print(f"最大高度: {args.height}px")
    print(f"视频比特率: {args.bitrate}")
    print(f"音频比特率: {args.audio_bitrate}")
    print(f"帧率: {args.fps}fps")
    print(f"质量因子: CRF {args.crf}")
    print()
    
    # 检查输入目录是否存在
    if not os.path.exists(args.input):
        print(f"❌ 输入目录不存在: {args.input}")
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
        compress_preview_videos(
            args.input, args.output, args.duration, args.height,
            args.bitrate, args.audio_bitrate, args.fps, args.crf
        )
    except KeyboardInterrupt:
        print("\n⚠️  用户中断操作")
    except Exception as e:
        print(f"❌ 发生错误: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
