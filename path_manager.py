#!/usr/bin/env python3
"""
视频路径管理模块
统一管理视频生成过程中的所有路径，包括：
- 用户目录结构
- 项目目录结构
- 视频文件路径
- 封面文件路径
- 临时文件路径
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class VideoPathManager:
    """视频路径管理器"""
    
    def __init__(self, base_workstore_dir: str = "workstore"):
        """
        初始化路径管理器
        
        Args:
            base_workstore_dir: 基础工作目录，默认为 'workstore'
        """
        self.base_workstore_dir = Path(base_workstore_dir)
        self.base_workstore_dir.mkdir(exist_ok=True)
    
    def get_user_dir(self, user_identifier) -> Path:
        """
        获取用户目录路径
        
        Args:
            user_identifier: 用户ID(int)或用户名(str)
            
        Returns:
            用户目录路径
        """
        # 如果是整数，使用原来的命名方式（向后兼容）
        if isinstance(user_identifier, int):
            user_dir = self.base_workstore_dir / f"user{user_identifier}"
        else:
            # 如果是字符串（用户名），直接使用用户名作为目录名
            user_dir = self.base_workstore_dir / str(user_identifier)
        user_dir.mkdir(exist_ok=True)
        return user_dir
    
    def sanitize_project_name(self, project_name: str) -> str:
        """
        清理项目名称，确保可以作为文件夹名
        """
        # 移除所有不可见字符（包括换行、回车、制表符等）
        sanitized = re.sub(r'[\r\n\t]', '', project_name)
        # 移除或替换不能用作文件夹名的字符，包括全角引号、单引号（保留空格）
        sanitized = re.sub(r'[<>:"/\\|?*""''\']', '_', sanitized)
        sanitized = sanitized.strip('_')
        # 限制长度
        if len(sanitized) > 50:
            sanitized = sanitized[:50]
        # 如果为空，使用默认名称
        if not sanitized:
            sanitized = f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return sanitized
    
    def get_project_dir(self, user_identifier, project_name: str) -> Path:
        """
        获取项目目录路径
        
        Args:
            user_identifier: 用户ID(int)或用户名(str)
            project_name: 项目名称
            
        Returns:
            项目目录路径
        """
        user_dir = self.get_user_dir(user_identifier)
        sanitized_name = self.sanitize_project_name(project_name)
        project_dir = user_dir / sanitized_name
        project_dir.mkdir(exist_ok=True)
        return project_dir
    
    def get_project_paths(self, user_identifier, project_name: str) -> Dict[str, Path]:
        """
        获取项目的所有相关路径
        
        Args:
            user_identifier: 用户ID(int)或用户名(str)
            project_name: 项目名称
            
        Returns:
            包含所有路径的字典
        """
        project_dir = self.get_project_dir(user_identifier, project_name)
        
        # 创建子目录
        subdirs = {
            'images': project_dir / "images",
            'audios': project_dir / "audios", 
            'covers': project_dir / "covers",
            'temp': project_dir / "temp"
        }
        
        for subdir in subdirs.values():
            subdir.mkdir(exist_ok=True)
        
        paths = {
            'project_dir': project_dir,
            'video_file': project_dir / "output.mp4",
            'cover_4_3': subdirs['covers'] / "cover_4:3.png",
            'cover_3_4': subdirs['covers'] / "cover_3:4.png",
            'cover_default': subdirs['covers'] / "cover.png",
            'workflow_record': project_dir / "work_flow_record.json",
            **subdirs
        }
        
        return paths
    
    def get_video_path(self, user_identifier, project_name: str) -> str:
        """
        获取视频文件的相对路径（用于存储到数据库）
        """
        paths = self.get_project_paths(user_identifier, project_name)
        abs_path = str(paths['video_file'].resolve())
        rel_path = os.path.relpath(abs_path, os.getcwd())
        return rel_path
    
    def get_cover_path(self, user_identifier, project_name: str, aspect_ratio: str = "4:3") -> str:
        """
        获取封面文件的相对路径（用于存储到数据库）
        """
        paths = self.get_project_paths(user_identifier, project_name)
        if aspect_ratio == "4:3":
            cover_path = paths['cover_4_3']
        elif aspect_ratio == "3:4":
            cover_path = paths['cover_3_4']
        else:
            cover_path = paths['cover_default']
        abs_path = str(cover_path.resolve())
        rel_path = os.path.relpath(abs_path, os.getcwd())
        return rel_path
    
    def get_web_accessible_path(self, file_path: str) -> str:
        """
        将文件系统路径转换为web可访问路径
        
        Args:
            file_path: 文件系统路径
            
        Returns:
            web可访问路径
        """
        # 确保路径以 workstore 开头
        if not file_path.startswith('workstore/'):
            if file_path.startswith('/'):
                file_path = file_path[1:]
            file_path = f"workstore/{file_path}"
        
        # 标准化路径分隔符
        web_path = file_path.replace('\\', '/')
        
        # 确保路径以 / 开头
        if not web_path.startswith('/'):
            web_path = f"/{web_path}"
        
        return web_path
    
    def cleanup_project_files(self, user_identifier, project_name: str) -> Dict[str, bool]:
        """
        清理项目的所有文件
        
        Args:
            user_id: 用户ID
            project_name: 项目名称
            
        Returns:
            清理结果字典
        """
        import shutil
        
        result = {
            'project_dir_removed': False,
            'files_removed': [],
            'errors': []
        }
        
        try:
            project_dir = self.get_project_dir(user_identifier, project_name)
            
            if project_dir.exists():
                shutil.rmtree(project_dir)
                result['project_dir_removed'] = True
                result['files_removed'].append(str(project_dir))
            
        except Exception as e:
            result['errors'].append(f"清理项目文件失败: {str(e)}")
        
        return result
    
    def get_project_info(self, user_identifier, project_name: str) -> Dict[str, any]:
        """
        获取项目信息
        
        Args:
            user_identifier: 用户ID(int)或用户名(str)
            project_name: 项目名称
            
        Returns:
            项目信息字典
        """
        paths = self.get_project_paths(user_identifier, project_name)
        
        info = {
            'project_name': project_name,
            'sanitized_name': self.sanitize_project_name(project_name),
            'project_dir': str(paths['project_dir']),
            'video_exists': paths['video_file'].exists(),
            'cover_exists': paths['cover_4_3'].exists(),
            'project_size': 0,
            'files_count': 0
        }
        
        # 计算项目大小和文件数量
        if paths['project_dir'].exists():
            for file_path in paths['project_dir'].rglob('*'):
                if file_path.is_file():
                    info['files_count'] += 1
                    info['project_size'] += file_path.stat().st_size
        
        return info
    
    def list_user_projects(self, user_identifier) -> List[Dict[str, any]]:
        """
        列出用户的所有项目
        
        Args:
            user_id: 用户ID
            
        Returns:
            项目列表
        """
        user_dir = self.get_user_dir(user_identifier)
        projects = []
        
        if user_dir.exists():
            for project_path in user_dir.iterdir():
                if project_path.is_dir():
                    project_info = self.get_project_info(user_identifier, project_path.name)
                    projects.append(project_info)
        
        return projects


# 全局路径管理器实例
path_manager = VideoPathManager() 