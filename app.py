import os
import json
import uuid
import traceback
import io
import zipfile
import secrets
from datetime import datetime, timedelta
from urllib.parse import unquote
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, send_from_directory, flash, send_file, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import threading
import time
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
from flask import abort, flash, request, jsonify, render_template, redirect, url_for, session, send_from_directory
import requests
import os
from dateutil.relativedelta import relativedelta
from functools import wraps
from sqlalchemy import or_
import socket
import json
from flask_migrate import Migrate
import humanize
from babel.dates import format_timedelta
from datetime import datetime, timedelta
import asyncio

# 导入日志模块
from logger import log_info, log_error, log_warning, log_video_task

# 导入核心服务
from service.ai_service import LLMService, ImageModelService, TTSModelService
from service.work_flow_service import run_work_flow_v3_with_progress
from service.email_service import email_service
from static.style_config import STYLE_CONFIG
from path_manager import path_manager

# 初始化Flask应用
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_for_baisu_ai_video')
# 使用绝对路径
db_path = os.path.abspath(os.path.join('instance', 'baisu_video.db'))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SECURE'] = False  # 开发环境设为False，生产环境设为True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # 会话有效期7天

# 初始化数据库
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# 初始化邮件服务
email_service.init_app(app)

# 初始化登录管理器
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 全局变量存储生成状态
generation_status = {}

def migrate_video_paths():
    """迁移旧的视频路径到新的统一路径格式"""
    try:
        with app.app_context():
            # 检查是否需要迁移（只在有实际需要迁移的视频时才输出日志）
            needs_migration = False
            videos = Video.query.all()
            for video in videos:
                if video.video_path:
                    user = User.query.get(video.user_id)
                    if user:
                        path_parts = video.video_path.split('/')
                        if len(path_parts) >= 2 and path_parts[1] != user.username:
                            needs_migration = True
                            break
            
            if not needs_migration:
                return
                
            log_info("开始迁移视频路径...")
            
            migrated_count = 0
            
            for video in videos:
                try:
                    # 获取用户信息
                    user = User.query.get(video.user_id)
                    if not user:
                        continue
                        
                    # 检查视频路径是否需要迁移
                    if video.video_path:
                        # 如果路径包含数字用户ID或"user"前缀，需要迁移
                        path_parts = video.video_path.split('/')
                        if len(path_parts) >= 2:
                            user_dir = path_parts[1]  # workstore/user_dir/project/...
                            expected_user_dir = user.username
                            
                            if user_dir != expected_user_dir:
                                log_info(f"迁移视频 {video.id}: {user_dir} -> {expected_user_dir}")
                                
                                # 构建新的视频路径
                                new_video_path = video.video_path.replace(f"workstore/{user_dir}/", f"workstore/{expected_user_dir}/")
                                
                                # 检查新路径是否存在
                                if os.path.exists(new_video_path):
                                    video.video_path = new_video_path
                                    
                                    # 同时更新封面路径
                                    if video.cover_path:
                                        new_cover_path = video.cover_path.replace(f"workstore/{user_dir}/", f"workstore/{expected_user_dir}/")
                                        if os.path.exists(new_cover_path):
                                            video.cover_path = new_cover_path
                                    
                                    migrated_count += 1
                                    log_info(f"成功迁移视频 {video.id} 的路径")
                                else:
                                    log_warning(f"新路径不存在，跳过迁移视频 {video.id}: {new_video_path}")
                    
                except Exception as e:
                    log_error(f"迁移视频 {video.id} 失败: {str(e)}")
                    
            # 提交所有更改
            db.session.commit()
            log_info(f"视频路径迁移完成，共迁移 {migrated_count} 个视频")
            
    except Exception as e:
        log_error(f"迁移视频路径失败: {str(e)}")


def recover_interrupted_tasks():
    """服务器启动时恢复中断的任务"""
    try:
        with app.app_context():
            log_info("检查服务器启动时是否有中断的任务需要恢复...")
            
            # 先尝试迁移旧的视频路径
            migrate_video_paths()
            
            # 查找所有处于processing状态的任务
            interrupted_tasks = TaskQueue.query.filter_by(status='processing').all()
            
            if not interrupted_tasks:
                log_info("没有发现中断的任务")
                return
            
            log_info(f"发现 {len(interrupted_tasks)} 个中断的任务，开始恢复...")
            
            for task in interrupted_tasks:
                try:
                    # 重置任务状态为waiting
                    task.status = 'waiting'
                    task.started_at = None
                    
                    # 如果已经创建了视频记录，将其状态重置为pending
                    if task.video_id:
                        video = Video.query.get(task.video_id)
                        if video:
                            video.status = 'pending'
                            log_info(f"重置视频ID {task.video_id} 状态为pending")
                    
                    db.session.commit()
                    log_info(f"恢复任务 {task.id}，用户 {task.user_id}，标题: {task.title[:30]}...")
                    
                    # 启动任务处理
                    import threading
                    thread = threading.Thread(target=process_next_queue_task, args=(task.user_id,))
                    thread.daemon = True
                    thread.start()
                    
                    log_info(f"任务 {task.id} 已重新启动")
                    
                except Exception as e:
                    log_error(f"恢复任务 {task.id} 失败: {str(e)}")
                    # 如果恢复失败，标记为失败状态
                    task.status = 'failed'
                    task.completed_at = datetime.utcnow()
                    if task.video_id:
                        video = Video.query.get(task.video_id)
                        if video:
                            video.status = 'failed'
                    db.session.commit()
            
            log_info("任务恢复完成")
            
    except Exception as e:
        log_error(f"恢复中断任务时发生错误: {str(e)}")

def process_next_queue_task(user_id):
    """处理用户队列中的下一个任务"""
    try:
        with app.app_context():
            # 查找用户队列中等待的任务
            next_task = TaskQueue.query.filter_by(
                user_id=user_id,
                status='waiting'
            ).order_by(TaskQueue.created_at).first()
            
            if not next_task:
                # 没有等待的任务，结束
                return
            
            # 获取用户信息并检查当前额度
            user = User.query.get(user_id)
            if not user:
                return
            user_name = user.username  # 用用户名作为目录名
            
            # 检查用户当前额度是否足够（额度<=0时不处理任务）
            if user.credits <= 0:
                log_warning(f"用户 {user.username} 当前额度不足({user.credits})，暂停处理队列任务")
                return
            
            # 创建视频记录
            video = Video(
                title=next_task.title,
                user_id=user_id,
                style=next_task.style,
                prompt=next_task.prompt,
                status='pending',
                mode=next_task.mode,
                credits_used=next_task.estimated_credits
            )
            db.session.add(video)
            db.session.commit()
            
            # 更新任务状态
            next_task.status = 'processing'
            next_task.video_id = video.id
            next_task.started_at = datetime.utcnow()
            db.session.commit()
            
            log_info(f"开始处理用户 {user.username} 的队列任务，任务ID: {next_task.id}, 视频ID: {video.id}")
            
            # 启动视频生成任务
            import threading
            import uuid
            
            task_id = str(uuid.uuid4())
            generation_status[task_id] = {
                'video_id': video.id,
                'user_id': user_id,
                'status': 'processing',
                'progress': 0,
                'message': '初始化生成任务...',
                'logs': ['任务开始: 初始化生成环境'],
                'current_step': 1
            }
            
            def queue_task():
                try:
                    result_dir = 'workstore'
                    user_dir_name = user_name
                    
                    # 更新视频状态为处理中
                    with app.app_context():
                        current_video = Video.query.get(video.id)
                        if current_video:
                            current_video.status = 'processing'
                            db.session.commit()
                    
                    # 调用视频生成流程
                    from service.work_flow_service import run_work_flow_v3_with_progress
                    
                    def status_callback(message):
                        if task_id in generation_status:
                            generation_status[task_id]['message'] = message
                    
                    # 生成视频
                    import asyncio
                    result = asyncio.run(run_work_flow_v3_with_progress(
                        text=next_task.prompt,
                        result_dir=result_dir,
                        user_id=user_dir_name,  # 传用户名
                        style=next_task.style,
                        template=next_task.template,
                        tts_model_str=next_task.tts_model_str,
                        is_prompt_mode=(next_task.mode == 'prompt'),
                        uploaded_title_picture_path=next_task.book_cover_path,
                        input_title_voice_text=next_task.book_title,
                        user_name=next_task.user_name,
                        is_display_title=next_task.is_display_title,
                        task_id=task_id,
                        generation_status=generation_status
                    ))
                    
                    # 任务完成后的处理
                    with app.app_context():
                        current_video = Video.query.get(video.id)
                        task = TaskQueue.query.get(next_task.id)
                        if current_video and task:
                            # 自动获取最终项目名（目录名）
                            user_dir = os.path.join('workstore', user_name)
                            project_dirs = [d for d in os.listdir(user_dir) if os.path.isdir(os.path.join(user_dir, d))]
                            project_dirs.sort(key=lambda d: os.path.getmtime(os.path.join(user_dir, d)), reverse=True)
                            if project_dirs:
                                final_project_title = project_dirs[0]
                                sanitized_title = path_manager.sanitize_project_name(final_project_title)
                                video_path = path_manager.get_video_path(user_name, sanitized_title)
                                cover_path = path_manager.get_cover_path(user_name, sanitized_title, "4:3")
                                current_video.title = final_project_title  # 保证数据库title和目录一致
                                if os.path.exists(video_path):
                                    current_video.video_path = video_path
                                    log_info(f"更新视频路径: {video_path}")
                                else:
                                    current_video.video_path = video_path
                                    log_warning(f"视频文件不存在: {video_path}")
                                if os.path.exists(cover_path):
                                    current_video.cover_path = cover_path
                                    log_info(f"更新封面路径: {cover_path}")
                                else:
                                    current_video.cover_path = cover_path
                                    log_warning(f"封面文件不存在: {cover_path}")
                            else:
                                log_warning(f"未找到任何项目目录，无法更新视频路径")
                            current_video.status = 'completed'
                            task.status = 'completed'
                            task.completed_at = datetime.utcnow()
                            db.session.commit()
                            log_info(f"队列任务完成，任务ID: {next_task.id}, 视频ID: {video.id}")
                
                except Exception as e:
                    log_error(f'队列视频生成任务失败: {str(e)}', 'video')
                    with app.app_context():
                        current_video = Video.query.get(video.id)
                        task = TaskQueue.query.get(next_task.id)
                        if current_video:
                            current_video.status = 'failed'
                            db.session.commit()
                        if task:
                            task.status = 'failed'
                            task.completed_at = datetime.utcnow()
                            db.session.commit()
                    
                    if task_id in generation_status:
                        generation_status[task_id]['status'] = 'failed'
                        generation_status[task_id]['message'] = f'生成失败: {str(e)}'
                
                finally:
                    # 处理下一个队列任务
                    process_next_queue_task(user_id)
            
            thread = threading.Thread(target=queue_task)
            thread.daemon = True
            thread.start()
    
    except Exception as e:
        log_error(f"处理队列任务失败: {str(e)}")

# 管理员权限装饰器
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)  # 禁止访问
        return f(*args, **kwargs)
    return decorated_function

# 用户模型
class User(UserMixin, db.Model):
    """用户模型，存储用户信息"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    credits = db.Column(db.Integer, default=3)  # 新用户赠送3条视频额度
    is_admin = db.Column(db.Boolean, default=False)  # 是否为管理员
    is_active = db.Column(db.Boolean, default=True)  # 账户是否启用
    is_vip = db.Column(db.Boolean, default=False)  # 是否为会员（已弃用，通过vip_expires_at判断）
    vip_expires_at = db.Column(db.DateTime, nullable=True)  # VIP到期时间
    last_free_credits_refresh = db.Column(db.DateTime, nullable=True)  # 上次免费额度刷新时间
    last_login_ip = db.Column(db.String(50))  # 最后登录IP
    last_login_at = db.Column(db.DateTime)  # 最后登录时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # 邮箱验证相关字段
    is_email_verified = db.Column(db.Boolean, default=False)  # 邮箱验证状态
    email_verification_token = db.Column(db.String(100))      # 验证令牌
    email_verification_sent_at = db.Column(db.DateTime)       # 验证邮件发送时间
    password_reset_token = db.Column(db.String(100))          # 密码重置令牌
    password_reset_sent_at = db.Column(db.DateTime)           # 重置邮件发送时间
    login_logs = db.relationship('UserLoginLog', backref='user', lazy=True)  # 登录日志
    videos = db.relationship('Video', backref='user', lazy=True)  # 视频
    payments = db.relationship('Payment', backref='user', lazy=True)  # 充值记录
    
    def is_administrator(self):
        return self.is_admin
    
    @property
    def is_current_vip(self):
        """检查用户是否是当前有效的VIP"""
        if not self.vip_expires_at:
            return False
        return datetime.utcnow() < self.vip_expires_at
    
    def should_refresh_free_credits(self):
        """检查是否需要刷新免费额度（每月1日）"""
        if not self.last_free_credits_refresh:
            # 如果从未刷新过，需要刷新
            return True
        
        current_date = datetime.utcnow()
        last_refresh_date = self.last_free_credits_refresh
        
        # 检查是否已经跨月，且当前日期是1日
        if (current_date.month != last_refresh_date.month or 
            current_date.year != last_refresh_date.year) and current_date.day == 1:
            return True
        
        return False
    
    def refresh_monthly_free_credits(self):
        """刷新月度免费额度（仅对非VIP用户）"""
        if not self.is_current_vip and self.should_refresh_free_credits():
            self.credits += 3  # 增加3条免费额度
            self.last_free_credits_refresh = datetime.utcnow()
            return True
        return False
    
    def set_password(self, password):
        """设置密码哈希"""
        # 使用兼容性更好的pbkdf2算法
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)

# 视频模型
class Video(db.Model):
    """视频模型，存储生成的视频信息"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    style = db.Column(db.String(50), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    video_path = db.Column(db.String(200), nullable=True)
    cover_path = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    mode = db.Column(db.String(20), default='prompt')  # prompt(提示词模式) 或 script(文案模式)
    credits_used = db.Column(db.Integer, default=1)  # 实际扣除的额度数量
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 用户登录日志模型
class UserLoginLog(db.Model):
    """用户登录日志"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    login_ip = db.Column(db.String(50), nullable=False)
    user_agent = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 充值记录模型
class Payment(db.Model):
    """充值记录模型，存储用户充值信息"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    credits = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='completed')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 留言模型
class Message(db.Model):
    """留言模型，存储用户留言信息"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False)  # 邮箱
    wechat = db.Column(db.String(100), nullable=True)  # 微信号
    qq = db.Column(db.String(50), nullable=True)  # QQ号
    phone = db.Column(db.String(20), nullable=True)  # 手机号码
    content = db.Column(db.Text, nullable=False)  # 留言内容
    is_read = db.Column(db.Boolean, default=False)  # 是否已读
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 创建时间
    replied_at = db.Column(db.DateTime, nullable=True)  # 回复时间
    # 移除重复的 user 关系，因为已经在 User 模型中定义了 backref

# 任务队列模型
class TaskQueue(db.Model):
    """任务队列模型，存储等待处理的视频生成任务"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    video_id = db.Column(db.Integer, db.ForeignKey('video.id'), nullable=True)  # 关联的视频ID，如果任务已开始
    title = db.Column(db.String(200), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    style = db.Column(db.String(50), nullable=False)
    template = db.Column(db.String(50), nullable=False, default='通用')
    mode = db.Column(db.String(20), default='prompt')  # prompt(提示词模式) 或 script(文案模式)
    estimated_credits = db.Column(db.Integer, default=1)  # 预估消耗的额度
    is_display_title = db.Column(db.Boolean, default=True)
    user_name = db.Column(db.String(100), nullable=True)  # 用户名显示
    tts_model_str = db.Column(db.String(50), default='cosyvoice-v1')
    book_title = db.Column(db.String(200), nullable=True)  # 书本标题（仅读书模板使用）
    book_cover_path = db.Column(db.String(200), nullable=True)  # 书本封面路径
    status = db.Column(db.String(20), default='waiting')  # waiting, processing, completed, failed, cancelled
    queue_position = db.Column(db.Integer, default=0)  # 队列位置
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, nullable=True)  # 开始处理时间
    completed_at = db.Column(db.DateTime, nullable=True)  # 完成时间
    
    # 关系
    user = db.relationship('User', backref='task_queue', lazy=True)
    video = db.relationship('Video', backref='task_queue_item', lazy=True)

@login_manager.user_loader
def load_user(user_id):
    """加载用户"""
    return User.query.get(int(user_id))

# 视频生成后台任务
def generate_video_task(prompt, style, user_id, video_id, mode='prompt'):
    """视频生成后台任务"""
    # 初始化状态记录
    task_id = str(uuid.uuid4())
    generation_status[task_id] = {
        'video_id': video_id,
        'status': 'processing',
        'progress': 0,
        'message': '初始化生成任务...',
        'logs': ['任务开始: 初始化生成环境']
    }
    
    log_video_task(task_id, f"开始视频生成任务 - 用户ID:{user_id}, 视频ID:{video_id}, 风格:{style}", "processing", 0)
    
    try:
        # 使用应用上下文更新视频状态为处理中
        with app.app_context():
            video = Video.query.get(video_id)
            if video:
                video.status = 'processing'
                db.session.commit()
                log_info(f"更新视频ID:{video_id}状态为processing", "video")
        
        # 自定义状态输出函数，用于捕获生成过程中的状态
        def status_callback(message):
            generation_status[task_id]['logs'].append(message)
            if '生成视频脚本' in message:
                generation_status[task_id]['progress'] = 10
                generation_status[task_id]['message'] = '正在生成视频脚本...' 
            elif '插页prompt生成' in message:
                generation_status[task_id]['progress'] = 30
                generation_status[task_id]['message'] = '正在生成图像提示词...'
            elif '图片生成' in message:
                generation_status[task_id]['progress'] = 50
                generation_status[task_id]['message'] = '正在生成场景图像...'
            elif '音频生成' in message:
                generation_status[task_id]['progress'] = 70
                generation_status[task_id]['message'] = '正在生成语音...'
            elif '时间添加' in message:
                generation_status[task_id]['progress'] = 80
                generation_status[task_id]['message'] = '正在处理时间轴...'
            elif '视频生成' in message:
                generation_status[task_id]['progress'] = 90
                generation_status[task_id]['message'] = '正在合成视频...'
            elif '封面生成' in message:
                generation_status[task_id]['progress'] = 95
                generation_status[task_id]['message'] = '正在生成封面...'
        
        # 重定向print输出到状态回调
        original_print = print
        def custom_print(*args, **kwargs):
            message = ' '.join(map(str, args))
            status_callback(message)
            original_print(*args, **kwargs)
        
        # 替换print函数
        import builtins
        builtins.print = custom_print
        
        # 实例化模型
        llm = LLMService()
        image_model = ImageModelService()
        tts_model = TTSModelService()
        
        # 设置结果目录
        result_dir = "./workstore"
        
        # 获取用户名用于目录命名
        with app.app_context():
            user = User.query.get(user_id)
            user_name = user.username if user else str(user_id)
        
        # 调用统一的工作流函数
        log_info(f"[任务 {task_id}] 开始生成视频，模式: {mode}")
        
        # 使用异步工作流函数
        import asyncio
        result = asyncio.run(run_work_flow_v3_with_progress(
            text=prompt,
            result_dir=result_dir,
            user_id=user_name,
            style=style,
            template="通用",  # 默认模板
            llm_model_str="deepseek-reasoner",
            image_model_str="cogview-3-flash",
            tts_model_str="cosyvoice-v1",
            is_prompt_mode=(mode == 'prompt'),
            status_callback=status_callback
        ))
        
        # 恢复原始print函数
        builtins.print = original_print
        
        # 更新视频信息
        with app.app_context():
            video = Video.query.get(video_id)
            if video:
                # 获取项目ID（标题）
                project_dir = os.path.join(result_dir, str(user_id))
                project_folders = [f for f in os.listdir(project_dir) if os.path.isdir(os.path.join(project_dir, f))]
                project_folders.sort(key=lambda x: os.path.getmtime(os.path.join(project_dir, x)), reverse=True)
                
                if project_folders:
                    project_id = project_folders[0]
                    video_file = os.path.join(project_dir, project_id, "output.mp4")
                    cover_file = os.path.join(project_dir, project_id, "covers", "cover.png")
                    
                    if os.path.exists(video_file):
                        video.video_path = video_file
                        video.title = project_id
                        video.status = 'completed'
                        
                        if os.path.exists(cover_file):
                            video.cover_path = cover_file
                    else:
                        video.status = 'failed'
                else:
                    video.status = 'failed'
                
                db.session.commit()
        
        # 更新状态
        generation_status[task_id]['status'] = 'completed'
        generation_status[task_id]['progress'] = 100
        generation_status[task_id]['message'] = '视频生成完成！'
        
    except Exception as e:
        # 处理异常
        error_msg = f"视频生成失败: {str(e)}"
        log_error(error_msg, exc_info=True)
        log_video_task(task_id, error_msg, "failed")
        
        # 确保task_id变量在作用域内才更新状态
        if task_id in generation_status:
            generation_status[task_id]['status'] = 'failed'
            generation_status[task_id]['message'] = f'生成失败: {str(e)}'
        
        # 更新视频状态
        with app.app_context():
            try:
                video = Video.query.get(video_id)
                if video:
                    video.status = 'failed'
                    db.session.commit()
                    log_info(f"更新视频ID:{video_id}状态为failed", "video")
            except Exception as db_error:
                log_error(f"更新视频状态失败: {str(db_error)}")

# 路由：首页
@app.route('/')
def index():
    """首页路由"""
    styles = {}
    for style_name in STYLE_CONFIG.keys():
        style_img = f"/static/img/{style_name}.png"
        styles[style_name] = style_img
    
    return render_template('index.html', styles=styles)

# Google Search Console验证文件
@app.route('/google0d5274732e0bb492.html')
def google_verification():
    """Google Search Console验证文件"""
    return "google-site-verification: google0d5274732e0bb492.html"

# Favicon和网站图标路由
@app.route('/favicon.ico')
def favicon():
    """Favicon.ico 文件"""
    return send_from_directory('.', 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/favicon.png')
def favicon_png():
    """Favicon PNG 文件"""
    return send_from_directory('.', 'favicon.png', mimetype='image/png')

@app.route('/apple-touch-icon.png')
def apple_touch_icon():
    """Apple Touch Icon 文件"""
    return send_from_directory('.', 'apple-touch-icon.png', mimetype='image/png')

@app.route('/site.webmanifest')
def site_webmanifest():
    """网站清单文件"""
    return send_from_directory('.', 'site.webmanifest', mimetype='application/manifest+json')

@app.route('/favicon-<int:size>x<int:size2>.png')
def favicon_sized(size, size2):
    """不同尺寸的favicon PNG文件"""
    if size == size2 and f'favicon-{size}x{size}.png' in os.listdir('.'):
        return send_from_directory('.', f'favicon-{size}x{size}.png', mimetype='image/png')
    return abort(404)

@app.route('/sitemap.xml')
def sitemap():
    """站点地图文件"""
    return send_from_directory('.', 'sitemap.xml', mimetype='application/xml')

@app.route('/robots.txt')
def robots():
    """搜索引擎爬虫规则文件"""
    return send_from_directory('.', 'robots.txt', mimetype='text/plain')

# 路由：登录
@app.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if current_user.is_authenticated:
        if request.content_type == 'application/json':
            return jsonify({'success': False, 'message': '用户已登录'})
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # 支持表单数据和JSON数据
        if request.content_type == 'application/json':
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
        else:
            username = request.form.get('username')
            password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            if not user.is_active:
                if request.content_type == 'application/json':
                    return jsonify({'success': False, 'message': '账户已被禁用'})
                return render_template('login.html', error='账户已被禁用')
            
            # 记录登录日志
            login_log = UserLoginLog(
                user_id=user.id,
                login_ip=request.remote_addr,
                user_agent=request.user_agent.string
            )
            db.session.add(login_log)
            
            # 更新用户最后登录信息
            user.last_login_ip = request.remote_addr
            user.last_login_at = datetime.utcnow()
            
            # 检查并刷新月度免费额度
            if user.refresh_monthly_free_credits():
                log_info(f"用户 {user.username} 获得了月度免费额度刷新，当前额度: {user.credits}")
            
            db.session.commit()
            
            # 登录用户
            login_user(user, remember=True)
            
            # 对于JSON请求，返回用户信息
            if request.content_type == 'application/json':
                return jsonify({
                    'success': True,
                    'message': '登录成功',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'isAuthenticated': True,
                        'isVip': user.is_vip,
                        'credits': user.credits,
                        'vipExpireAt': user.vip_expires_at.isoformat() if user.vip_expires_at else None
                    }
                })
            
            # 获取下一个页面
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('index')
            
            return redirect(next_page)
        
        # 登录失败
        if request.content_type == 'application/json':
            return jsonify({'success': False, 'message': '用户名或密码错误'})
        return render_template('login.html', error='用户名或密码错误')
    
    return render_template('login.html')

# 路由：注册
@app.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if current_user.is_authenticated:
        if request.content_type == 'application/json':
            return jsonify({'success': False, 'message': '用户已登录'})
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # 支持表单数据和JSON数据
        if request.content_type == 'application/json':
            data = request.get_json()
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
        else:
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
        
        # 用户名合法性校验
        import re
        username_pattern = r'^[A-Za-z0-9_-]+$'
        if not re.match(username_pattern, username or ''):
            if request.content_type == 'application/json':
                return jsonify({'success': False, 'message': '用户名仅支持字母、数字、-、_'})
            return render_template('register.html', error='用户名仅支持字母、数字、-、_')
        
        # 检查用户名和邮箱是否已存在
        if User.query.filter_by(username=username).first():
            if request.content_type == 'application/json':
                return jsonify({'success': False, 'message': '用户名已存在'})
            return render_template('register.html', error='用户名已存在')
        
        if User.query.filter_by(email=email).first():
            if request.content_type == 'application/json':
                return jsonify({'success': False, 'message': '邮箱已存在'})
            return render_template('register.html', error='邮箱已存在')
        
        # 创建新用户
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        # 自动登录
        login_user(user)
        
        # 对于JSON请求，返回用户信息
        if request.content_type == 'application/json':
            return jsonify({
                'success': True,
                'message': '注册成功',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'isAuthenticated': True,
                    'isVip': user.is_vip,
                    'credits': user.credits,
                    'vipExpireAt': user.vip_expires_at.isoformat() if user.vip_expires_at else None
                }
            })
        
        return redirect(url_for('index'))
    
    return render_template('register.html')

# ================================
# 邮箱验证相关API
# ================================

@app.route('/api/send-verification-code', methods=['POST'])
def send_verification_code():
    """发送邮箱验证码"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({'success': False, 'message': '请输入邮箱地址'})
        
        # 检查邮箱格式
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return jsonify({'success': False, 'message': '邮箱格式不正确'})
        
        # 检查邮箱是否已注册
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'success': False, 'message': '该邮箱已被注册'})
        
        # 检查发送频率限制（60秒内只能发送一次）
        current_time = datetime.utcnow()
        session_key = f'verification_email_sent_{email}'
        last_sent = session.get(session_key)
        
        if last_sent:
            last_sent_time = datetime.fromisoformat(last_sent)
            if (current_time - last_sent_time).total_seconds() < 60:
                remaining = 60 - int((current_time - last_sent_time).total_seconds())
                return jsonify({'success': False, 'message': f'请等待{remaining}秒后再发送'})
        
        # 生成验证码
        verification_code = email_service.generate_verification_code()
        
        # 存储验证码到session（10分钟有效期）
        verification_data = {
            'code': verification_code,
            'email': email,
            'expires_at': (current_time + timedelta(minutes=10)).isoformat()
        }
        session[f'verification_code_{email}'] = verification_data
        session[session_key] = current_time.isoformat()
        
        # 发送验证码邮件
        success = email_service.send_verification_email(email, verification_code)
        
        if success:
            log_info(f"验证码已发送至邮箱: {email}")
            return jsonify({'success': True, 'message': '验证码已发送，请查收邮件'})
        else:
            return jsonify({'success': False, 'message': '邮件发送失败，请稍后重试'})
        
    except Exception as e:
        log_error(f"发送验证码失败: {str(e)}")
        return jsonify({'success': False, 'message': '发送失败，请稍后重试'})

@app.route('/api/verify-email-code', methods=['POST'])
def verify_email_code():
    """验证邮箱验证码"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        code = data.get('code', '').strip()
        
        if not email or not code:
            return jsonify({'success': False, 'message': '请输入邮箱和验证码'})
        
        # 获取存储的验证码
        verification_data = session.get(f'verification_code_{email}')
        if not verification_data:
            return jsonify({'success': False, 'message': '验证码已过期，请重新发送'})
        
        # 检查过期时间
        expires_at = datetime.fromisoformat(verification_data['expires_at'])
        if datetime.utcnow() > expires_at:
            session.pop(f'verification_code_{email}', None)
            return jsonify({'success': False, 'message': '验证码已过期，请重新发送'})
        
        # 验证验证码
        if verification_data['code'] != code:
            return jsonify({'success': False, 'message': '验证码错误'})
        
        # 验证成功，标记验证状态
        session[f'email_verified_{email}'] = True
        log_info(f"邮箱验证成功: {email}")
        
        return jsonify({'success': True, 'message': '邮箱验证成功'})
        
    except Exception as e:
        log_error(f"验证邮箱失败: {str(e)}")
        return jsonify({'success': False, 'message': '验证失败，请稍后重试'})

@app.route('/register-with-verification', methods=['POST'])
def register_with_verification():
    """邮箱验证注册"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '').strip()
        
        # 用户名合法性校验
        import re
        username_pattern = r'^[A-Za-z0-9_-]+$'
        if not re.match(username_pattern, username or ''):
            return jsonify({'success': False, 'message': '用户名仅支持字母、数字、-、_'})
        
        if not all([username, email, password]):
            return jsonify({'success': False, 'message': '请填写完整信息'})
        
        # 验证邮箱是否已验证
        if not session.get(f'email_verified_{email}'):
            return jsonify({'success': False, 'message': '请先验证邮箱'})
        
        # 检查用户名和邮箱是否已存在
        if User.query.filter_by(username=username).first():
            return jsonify({'success': False, 'message': '用户名已存在'})
        
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': '邮箱已被注册'})
        
        # 创建新用户
        user = User(
            username=username,
            email=email,
            is_email_verified=True  # 邮箱已验证
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # 清除验证相关的session
        session.pop(f'verification_code_{email}', None)
        session.pop(f'email_verified_{email}', None)
        session.pop(f'verification_email_sent_{email}', None)
        
        # 发送欢迎邮件
        email_service.send_welcome_email(email, username)
        
        # 自动登录
        login_user(user, remember=True)
        
        log_info(f"用户注册成功: {username} ({email})")
        return jsonify({'success': True, 'message': '注册成功！', 'redirect': url_for('index')})
        
    except Exception as e:
        db.session.rollback()
        log_error(f"注册失败: {str(e)}")
        return jsonify({'success': False, 'message': '注册失败，请稍后重试'})

@app.route('/api/send-reset-email', methods=['POST'])
def send_reset_email():
    """发送密码重置邮件"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({'success': False, 'message': '请输入邮箱地址'})
        
        # 检查用户是否存在
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'success': False, 'message': '该邮箱未注册'})
        
        # 生成重置令牌
        reset_token = secrets.token_urlsafe(32)
        user.password_reset_token = reset_token
        user.password_reset_sent_at = datetime.utcnow()
        db.session.commit()
        
        # 发送重置邮件
        success = email_service.send_password_reset_email(email, reset_token, user.username)
        
        if success:
            return jsonify({'success': True, 'message': '重置邮件已发送，请查收'})
        else:
            return jsonify({'success': False, 'message': '邮件发送失败，请稍后重试'})
            
    except Exception as e:
        print(f'发送重置邮件错误: {str(e)}')
        return jsonify({'success': False, 'message': '操作失败，请稍后重试'})

@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    """重置密码"""
    try:
        data = request.get_json()
        token = data.get('token')
        new_password = data.get('password')
        
        if not token or not new_password:
            return jsonify({'success': False, 'message': '参数不完整'})
        
        # 验证重置令牌
        user = User.query.filter_by(password_reset_token=token).first()
        if not user:
            return jsonify({'success': False, 'message': '重置链接无效或已过期'})
        
        # 检查令牌是否过期（30分钟有效期）
        if user.password_reset_sent_at:
            time_diff = datetime.utcnow() - user.password_reset_sent_at
            if time_diff.total_seconds() > 1800:  # 30分钟
                return jsonify({'success': False, 'message': '重置链接已过期，请重新申请'})
        
        # 更新密码
        user.password_hash = generate_password_hash(new_password)
        user.password_reset_token = None
        user.password_reset_sent_at = None
        db.session.commit()
        
        return jsonify({'success': True, 'message': '密码重置成功！'})
        
    except Exception as e:
        print(f'重置密码错误: {str(e)}')
        return jsonify({'success': False, 'message': '重置失败，请稍后重试'})

# ================================
# 页面路由
# ================================

@app.route('/register-with-email')
def register_with_email():
    """邮箱验证注册页面"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('register_with_email.html')

@app.route('/forgot-password')
def forgot_password():
    """找回密码页面"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('forgot_password.html')

@app.route('/reset-password')
def reset_password_page():
    """重置密码页面"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    token = request.args.get('token')
    if not token:
        flash('重置链接无效', 'error')
        return redirect(url_for('forgot_password'))
    
    return render_template('reset_password.html')

# 路由：登出
@app.route('/logout')
@login_required
def logout():
    """用户登出"""
    logout_user()
    return redirect(url_for('index'))

# 路由：用户中心
@app.route('/profile')
@login_required
def profile():
    """用户中心"""
    return render_template('profile.html')

# 路由：我的视频
@app.route('/my-videos')
@login_required
def my_videos():
    """我的视频页面"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        videos_pagination = Video.query.filter_by(user_id=current_user.id)\
            .order_by(Video.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        # 将视频数据转换为JSON格式
        videos_list = []
        for video in videos_pagination.items:
            video_data = {
                'id': video.id,
                'title': video.title or '未命名视频',
                'video_path': video.video_path or '',
                'cover_path': video.cover_path or '',
                'status': video.status or 'unknown',
                'created_at': video.created_at.isoformat() if video.created_at else '',
                'style': video.style or '默认'
            }
            videos_list.append(video_data)
        
        # 将视频列表转换为JSON字符串
        import json
        videos_json = json.dumps(videos_list, ensure_ascii=False)
        
        log_info(f"用户 {current_user.username} 查看我的视频页面，共 {len(videos_list)} 个视频")
        
        return render_template('my_videos.html', 
                             videos=videos_pagination,
                             videos_json=videos_json,
                             error=None)
    
    except Exception as e:
        log_error(f"我的视频页面加载失败: {str(e)}")
        return render_template('my_videos.html', 
                             videos=None,
                             videos_json='[]',
                             error=f'加载视频列表失败: {str(e)}')

@app.route('/my-tasks')
@login_required
def my_tasks():
    """统一的任务管理页面"""
    # 查找用户当前正在处理的任务
    current_processing_task = TaskQueue.query.filter_by(
        user_id=current_user.id, 
        status='processing'
    ).first()
    
    # 创建当前任务的视频对象（用于进度显示）
    current_video = None
    if current_processing_task and current_processing_task.video_id:
        current_video = Video.query.get(current_processing_task.video_id)
    
    # 如果没有当前视频，创建一个假的video对象用于模板兼容
    if not current_video:
        class MockVideo:
            def __init__(self):
                self.id = 0
                self.title = "任务管理中心"
                self.status = "idle"
        current_video = MockVideo()
    
    return render_template('generate.html', video=current_video)

@app.route('/generate/<int:video_id>')
@login_required
def generate_page(video_id):
    """视频生成进度页面"""
    video = Video.query.get_or_404(video_id)
    if video.user_id != current_user.id:
        abort(403)
    return render_template('generate.html', video=video)

# 路由：充值
@app.route('/recharge', methods=['GET', 'POST'])
@login_required
def recharge():
    """充值页面"""
    if request.method == 'POST':
        amount = float(request.form.get('amount', 0))
        
        # 简单的充值逻辑，实际应对接支付系统
        if amount > 0:
            # 计算充值额度，假设1元=1条视频
            credits = int(amount)
            
            # 创建充值记录
            payment = Payment(user_id=current_user.id, amount=amount, credits=credits)
            db.session.add(payment)
            
            # 更新用户额度
            current_user.credits += credits
            db.session.commit()
            
            return redirect(url_for('profile'))
    
    return render_template('recharge.html')

# API：生成视频
@app.route('/api/generate-video', methods=['POST'])
@login_required
def generate_video_api():
    """生成视频API"""
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        style = data.get('style')
        mode = data.get('mode', 'prompt')
        
        if not prompt or not style:
            return jsonify({'success': False, 'message': '请提供提示词和风格'})
        
        # 检查用户积分
        if current_user.credits <= 0:
            return jsonify({'success': False, 'message': '积分不足，请充值'})
        
        # 创建视频记录
        video = Video(
            title=prompt[:30] if prompt else 'AI视频',
            user_id=current_user.id,
            style=style,
            prompt=prompt,
            status='pending',
            mode=mode
        )
        db.session.add(video)
        db.session.commit()
        
        # 扣除积分
        current_user.credits -= 1
        db.session.commit()
        
        # 启动后台任务
        thread = threading.Thread(
            target=generate_video_task,
            args=(prompt, style, current_user.id, video.id, mode)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'video_id': video.id,
            'message': '视频生成任务已启动'
        })
        
    except Exception as e:
        log_error(f'生成视频API错误: {str(e)}', 'api')
        return jsonify({'success': False, 'message': '生成失败，请重试'})

@app.route('/api/generate-video-v3', methods=['POST'])
@login_required
def generate_video_v3():
    """新版视频生成API - 统一队列管理"""
    try:
        prompt = request.form.get('prompt')
        style = request.form.get('style')
        template = request.form.get('template')
        mode = request.form.get('mode')
        is_display_title = request.form.get('is_display_title') == 'true' or request.form.get('is_display_title') == 'True'
        user_name = request.form.get('user_name')
        # 处理用户名为空的情况
        if not user_name or user_name.strip() == '' or user_name.strip().lower() == 'null':
            user_name = None

        if not prompt or not style or not template:
            return jsonify({'success': False, 'message': '请提供完整信息'})
        
        # 计算需要扣除的额度（文案模式根据字数计算）
        estimated_credits = int(request.form.get('estimated_credits', 1))
        credits_to_deduct = 1  # 默认扣除1条
        
        if mode == 'script' and prompt:
            # 每超过2000字多扣1条额度
            char_count = len(prompt)
            credits_to_deduct = max(1, (char_count - 1) // 2000 + 1)
            
            # 验证前端计算的额度是否正确
            if estimated_credits != credits_to_deduct:
                log_warning(f"前端计算的额度({estimated_credits})与后端计算的额度({credits_to_deduct})不一致")
        
        # 检查用户积分
        if current_user.credits < credits_to_deduct:
            return jsonify({
                'success': False, 
                'message': f'积分不足！需要{credits_to_deduct}条额度，当前剩余{current_user.credits}条'
            })

        # 会员逻辑 - 使用新的VIP检查方法
        is_vip = current_user.is_current_vip
        if not is_vip:
            # 对于非VIP用户，如果user_name为None，则保持None（不显示用户名）
            # 只有在用户设置了用户名的情况下，才强制改为'百速AI'
            if user_name is not None:
                user_name = '百速AI'
            is_need_ad_end = True
        else:
            is_need_ad_end = False

        # 读一本书模板特殊处理
        uploaded_title_picture_path = None
        input_title_voice_text = None
        if template == '读一本书':
            book_title = request.form.get('book_title')
            input_title_voice_text = book_title
            book_cover = request.files.get('book_cover')
            if book_cover:
                save_dir = os.path.join('workstore', 'covers')
                os.makedirs(save_dir, exist_ok=True)
                save_path = os.path.join(save_dir, f'{current_user.id}_{int(time.time())}.png')
                book_cover.save(save_path)
                uploaded_title_picture_path = save_path

        # 扣除积分（提前扣除，避免重复扣除）
        current_user.credits -= credits_to_deduct
        db.session.commit()
        log_info(f"用户 {current_user.username} 生成视频扣除了 {credits_to_deduct} 条额度，剩余 {current_user.credits} 条")

        # 所有任务都先创建TaskQueue记录
        task_queue = TaskQueue(
            user_id=current_user.id,
            title=prompt[:30] if prompt else 'AI视频',
            prompt=prompt,
            style=style,
            template=template,
            mode=mode,
            estimated_credits=credits_to_deduct,
            is_display_title=is_display_title,
            user_name=user_name,
            tts_model_str=request.form.get('tts_model_str', 'cosyvoice-v1'),
            book_title=request.form.get('book_title') if template == '读一本书' else None,
            book_cover_path=uploaded_title_picture_path if template == '读一本书' else None,
            status='waiting'
        )
        db.session.add(task_queue)
        db.session.commit()
        
        log_info(f"用户 {current_user.username} 的任务已加入队列，任务ID: {task_queue.id}")
        
        # 检查是否有正在处理的任务
        existing_processing_task = TaskQueue.query.filter_by(
            user_id=current_user.id,
            status='processing'
        ).first()
        
        # 如果没有正在处理的任务，立即开始处理这个任务
        if not existing_processing_task:
            # 在后台线程中处理任务
            import threading
            thread = threading.Thread(target=process_next_queue_task, args=(current_user.id,))
            thread.daemon = True
            thread.start()
            
            # 返回成功信息，统一跳转到任务中心
            return jsonify({
                'success': True,
                'message': '任务已开始处理',
                'redirect_url': '/my-tasks'
            })
        else:
            # 返回队列信息，统一跳转到任务中心
            queue_position = TaskQueue.query.filter_by(user_id=current_user.id, status='waiting').count()
            return jsonify({
                'success': True,
                'message': f'您有视频正在生成中，新任务已加入队列（排队位置：{queue_position}）',
                'redirect_url': '/my-tasks'
            })

    except Exception as e:
        log_error(f"视频生成失败: {str(e)}")
        return jsonify({'success': False, 'message': '生成失败，请重试'})

@app.route('/api/video-status/<int:video_id>')
@login_required
def video_status(video_id):
    """获取视频生成状态"""
    try:
        # 检查视频存在性和所有权
        video = Video.query.get_or_404(video_id)
        if video.user_id != current_user.id:
            log_warning(f"用户 {current_user.username} 尝试访问非自己的视频 ID: {video_id}")
            return jsonify({
                'success': False,
                'message': '无权查看该视频'
            }), 403
    except Exception as e:
        log_error(f"查询视频状态出错 - 视频ID: {video_id}, 错误: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'查询视频状态出错: {str(e)}'
        }), 500
    
    # 查找对应的任务状态
    task_status = None
    try:
        # 寻找对应的生成任务状态
        for task_id, task_data in generation_status.items():
            if task_data.get('video_id') == video_id:
                log_info(f"返回视频状态 - 视频ID: {video_id}, 状态: {task_data.get('status', 'unknown')}, 进度: {task_data.get('progress', 0)}%", "video")
                return jsonify({
                    'success': True,
                    'status': task_data.get('status', 'unknown'),
                    'progress': task_data.get('progress', 0),
                    'message': task_data.get('message', ''),
                    'logs': task_data.get('logs', []),
                    'current_step': task_data.get('current_step', 1)
                })
        
        # 如果没有找到任务状态，返回数据库中的状态
        log_info(f"返回数据库中的视频状态 - 视频ID: {video_id}, 状态: {video.status}", "video")
        return jsonify({
            'success': True,
            'status': video.status,
            'progress': 100 if video.status == 'completed' else 0,
            'message': '视频生成完成' if video.status == 'completed' else '等待处理',
            'logs': []
        })
    except Exception as e:
        log_error(f"获取视频状态失败 - 视频ID: {video_id}, 错误: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取视频状态失败: {str(e)}'
        }), 500

# 任务队列API接口
@app.route('/api/task-queue')
@login_required
def get_task_queue():
    """获取用户的任务队列"""
    try:
        # 获取等待中和处理中的任务
        waiting_tasks = TaskQueue.query.filter_by(
            user_id=current_user.id
        ).filter(TaskQueue.status.in_(['waiting', 'processing'])).order_by(TaskQueue.created_at).all()
        
        # 获取已完成的任务
        completed_tasks = TaskQueue.query.filter_by(
            user_id=current_user.id
        ).filter(TaskQueue.status.in_(['completed', 'failed', 'cancelled'])).order_by(TaskQueue.completed_at.desc()).limit(20).all()
        
        def serialize_task(task):
            return {
                'id': task.id,
                'title': task.title,
                'prompt': task.prompt,
                'style': task.style,
                'template': task.template,
                'estimated_credits': task.estimated_credits,
                'status': task.status,
                'video_id': task.video_id,
                'created_at': task.created_at.isoformat() if task.created_at else None,
                'started_at': task.started_at.isoformat() if task.started_at else None,
                'completed_at': task.completed_at.isoformat() if task.completed_at else None
            }
        
        return jsonify({
            'success': True,
            'waiting_tasks': [serialize_task(task) for task in waiting_tasks],
            'completed_tasks': [serialize_task(task) for task in completed_tasks]
        })
    
    except Exception as e:
        log_error(f"获取任务队列失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取任务队列失败: {str(e)}'
        }), 500

@app.route('/api/task-queue/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    """更新任务信息"""
    try:
        task = TaskQueue.query.filter_by(id=task_id, user_id=current_user.id).first()
        if not task:
            return jsonify({'success': False, 'message': '任务不存在'}), 404
        
        if task.status != 'waiting':
            return jsonify({'success': False, 'message': '只能编辑等待中的任务'}), 400
        
        data = request.get_json()
        
        # 更新任务信息
        if 'prompt' in data:
            task.prompt = data['prompt']
        if 'template' in data:
            task.template = data['template']
        if 'style' in data:
            task.style = data['style']
        if 'mode' in data:
            task.mode = data['mode']
        if 'tts_model_str' in data:
            task.tts_model_str = data['tts_model_str']
        if 'is_display_title' in data:
            task.is_display_title = data['is_display_title']
        if 'book_title' in data:
            task.book_title = data['book_title']
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': '任务更新成功'})
    
    except Exception as e:
        db.session.rollback()
        log_error(f"更新任务失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'更新任务失败: {str(e)}'
        }), 500

@app.route('/api/task-queue/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    """删除任务"""
    try:
        task = TaskQueue.query.filter_by(id=task_id, user_id=current_user.id).first()
        if not task:
            return jsonify({'success': False, 'message': '任务不存在'}), 404
        
        if task.status == 'processing':
            return jsonify({'success': False, 'message': '不能删除正在处理的任务'}), 400
        
        # 如果是已完成的任务，还需要检查是否有关联的视频需要删除
        if task.video_id and task.status == 'completed':
            video = Video.query.get(task.video_id)
            if video:
                cleanup_video_files(video)
                db.session.delete(video)
        
        db.session.delete(task)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '任务删除成功'})
    
    except Exception as e:
        db.session.rollback()
        log_error(f"删除任务失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'删除任务失败: {str(e)}'
        }), 500

@app.route('/api/task-queue/<int:task_id>/move-to-front', methods=['POST'])
@login_required
def move_task_to_front(task_id):
    """将任务移动到队列最前面"""
    try:
        task = TaskQueue.query.filter_by(id=task_id, user_id=current_user.id).first()
        if not task:
            return jsonify({'success': False, 'message': '任务不存在'}), 404
        
        # 只能移动等待中的任务
        if task.status != 'waiting':
            return jsonify({'success': False, 'message': '只能移动等待中的任务'}), 400
        
        # 获取当前最早的任务时间
        earliest_task = TaskQueue.query.filter_by(
            user_id=current_user.id,
            status='waiting'
        ).order_by(TaskQueue.created_at).first()
        
        if earliest_task and earliest_task.id != task_id:
            # 将当前任务的创建时间设置为比最早任务更早1秒
            from datetime import timedelta
            task.created_at = earliest_task.created_at - timedelta(seconds=1)
            db.session.commit()
            
            log_info(f"用户 {current_user.username} 将任务 {task_id} 移动到队列最前面")
            
            return jsonify({'success': True, 'message': '任务已移动到队列最前面'})
        else:
            return jsonify({'success': False, 'message': '任务已经在队列最前面'})
        
    except Exception as e:
        db.session.rollback()
        log_error(f"移动任务失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'移动任务失败: {str(e)}'
        }), 500

# API：获取视频信息
@app.route('/api/video-info/<int:video_id>')
@login_required
def video_info(video_id):
    """获取视频详细信息"""
    video = Video.query.get_or_404(video_id)
    
    # 检查视频是否属于当前用户
    if video.user_id != current_user.id:
        return jsonify({
            'success': False,
            'message': '无权访问该视频'
        }), 403
    
    # 构建视频URL和封面URL
    video_url = url_for('video_file', filename=video.video_path.replace('workstore/', '')) if video.video_path else None
    cover_url = url_for('video_file', filename=video.cover_path.replace('workstore/', '')) if video.cover_path else None
    
    return jsonify({
        'success': True,
        'title': video.title,
        'style': video.style,
        'prompt': video.prompt,
        'status': video.status,
        'created_at': video.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'video_url': video_url,
        'cover_url': cover_url
    })

# API：删除视频
@app.route('/api/delete-video/<int:video_id>', methods=['POST'])
@login_required
def delete_video(video_id):
    """删除视频"""
    video = Video.query.get_or_404(video_id)
    
    # 检查视频是否属于当前用户
    if video.user_id != current_user.id:
        return jsonify({
            'success': False,
            'message': '无权删除该视频'
        }), 403
    
    # 获取项目ID (从视频标题)
    project_id = video.title
    user_id = video.user_id
    project_dir = None
    
    # 找到项目目录
    if project_id and user_id:
        project_dir = os.path.join("./workstore", str(user_id), project_id)
        log_info(f"准备删除项目目录: {project_dir}", "video")
    
    # 删除视频文件
    if video.video_path and os.path.exists(video.video_path):
        try:
            os.remove(video.video_path)
            log_info(f"已删除视频文件: {video.video_path}", "video")
        except Exception as e:
            log_error(f"删除视频文件失败: {str(e)}", "video")
    
    # 删除封面文件
    if video.cover_path and os.path.exists(video.cover_path):
        try:
            os.remove(video.cover_path)
            log_info(f"已删除封面文件: {video.cover_path}", "video")
        except Exception as e:
            log_error(f"删除封面文件失败: {str(e)}", "video")
    
    # 删除整个项目目录
    if project_dir and os.path.exists(project_dir):
        try:
            import shutil
            shutil.rmtree(project_dir)
            log_info(f"已删除项目目录: {project_dir}", "video")
        except Exception as e:
            log_error(f"删除项目目录失败: {str(e)}", "video")
    
    # 删除数据库记录
    db.session.delete(video)
    db.session.commit()
    log_info(f"已删除视频数据库记录, ID: {video_id}", "video")
    
    return jsonify({
        'success': True,
        'message': '视频已删除'
    })

def cleanup_video_files(video):
    """
    清理视频相关的所有文件和目录
    返回清理结果的详细信息
    """
    cleanup_result = {
        'video_file': False,
        'cover_file': False,
        'project_dir': False,
        'errors': []
    }
    
    try:
        # 获取项目ID和用户ID
        project_id = video.title
        user_id = video.user_id
        
        # 删除视频文件
        if video.video_path and os.path.exists(video.video_path):
            try:
                os.remove(video.video_path)
                cleanup_result['video_file'] = True
                log_info(f"已删除视频文件: {video.video_path}", "video")
            except Exception as e:
                error_msg = f"删除视频文件失败: {str(e)}"
                cleanup_result['errors'].append(error_msg)
                log_error(error_msg, "video")
        
        # 删除封面文件
        if video.cover_path and os.path.exists(video.cover_path):
            try:
                os.remove(video.cover_path)
                cleanup_result['cover_file'] = True
                log_info(f"已删除封面文件: {video.cover_path}", "video")
            except Exception as e:
                error_msg = f"删除封面文件失败: {str(e)}"
                cleanup_result['errors'].append(error_msg)
                log_error(error_msg, "video")
        
        # 删除整个项目目录 - 使用统一路径管理器
        if project_id and user_id:
            try:
                cleanup_result_from_manager = path_manager.cleanup_project_files(user_id, project_id)
                
                if cleanup_result_from_manager['project_dir_removed']:
                    cleanup_result['project_dir'] = True
                    log_info(f"已使用路径管理器删除项目目录: {project_id}", "video")
                
                # 记录错误
                if cleanup_result_from_manager['errors']:
                    cleanup_result['errors'].extend(cleanup_result_from_manager['errors'])
                    for error in cleanup_result_from_manager['errors']:
                        log_error(error, "video")
            except Exception as e:
                error_msg = f"删除项目目录失败: {str(e)}"
                cleanup_result['errors'].append(error_msg)
                log_error(error_msg, "video")
    
    except Exception as e:
        error_msg = f"清理文件时发生未知错误: {str(e)}"
        cleanup_result['errors'].append(error_msg)
        log_error(error_msg, "video")
    
    return cleanup_result

# API：停止视频生成并删除文件
@app.route('/api/stop-generation/<int:video_id>', methods=['POST'])
@login_required
def stop_generation(video_id):
    """停止视频生成并删除相关文件"""
    try:
        # 检查视频权限
        video = Video.query.filter_by(id=video_id, user_id=current_user.id).first()
        if not video:
            return jsonify({'success': False, 'message': '视频不存在或无权限访问'})
        
        # 只允许停止正在处理中的视频
        if video.status not in ['pending', 'processing']:
            return jsonify({'success': False, 'message': '该视频不在生成过程中，无法停止'})
        
        log_info(f"用户 {current_user.username} 请求停止视频生成，视频ID: {video_id}", "video")
        
        # 查找对应的任务并标记为取消
        task_cancelled = False
        cancelled_task_id = None
        for task_id, task_data in generation_status.items():
            if task_data.get('video_id') == video_id:
                generation_status[task_id]['status'] = 'cancelled'
                generation_status[task_id]['message'] = '用户主动停止生成'
                task_cancelled = True
                cancelled_task_id = task_id
                log_info(f"已标记任务为取消状态，任务ID: {task_id}", "video")
                break
        
        # 清理已创建的文件和目录
        cleanup_result = cleanup_video_files(video)
        
        # 返还用户额度
        credits_to_return = video.credits_used or 1
        current_user.credits += credits_to_return
        
        # 删除数据库记录
        db.session.delete(video)
        db.session.commit()
        
        log_info(f"用户 {current_user.username} 停止生成成功，返还 {credits_to_return} 额度，当前余额: {current_user.credits}", "video")
        
        return jsonify({
            'success': True, 
            'message': f'已停止生成并清理文件，返还 {credits_to_return} 个额度',
            'task_cancelled': task_cancelled,
            'files_cleaned': cleanup_result,
            'credits_returned': credits_to_return,
            'current_credits': current_user.credits
        })
        
    except Exception as e:
        log_error(f"停止生成失败，用户: {current_user.username}, 视频ID: {video_id}, 错误: {str(e)}", "video", exc_info=True)
        return jsonify({'success': False, 'message': f'停止失败: {str(e)}'})

# API：获取充值记录
@app.route('/api/payment-history')
@login_required
def payment_history():
    """获取用户充值记录"""
    payments = Payment.query.filter_by(user_id=current_user.id).order_by(Payment.created_at.desc()).all()
    
    payment_list = [{
        'id': payment.id,
        'amount': payment.amount,
        'credits': payment.credits,
        'status': payment.status,
        'created_at': payment.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for payment in payments]
    
    return jsonify({
        'success': True,
        'payments': payment_list
    })

# API：获取使用记录
@app.route('/api/usage-history')
@login_required
def usage_history():
    """获取用户使用记录"""
    videos = Video.query.filter_by(user_id=current_user.id).order_by(Video.created_at.desc()).all()
    
    usage_list = []
    for video in videos:
        # 使用数据库中记录的实际扣除额度
        credits_used = getattr(video, 'credits_used', 1)
        
        # 如果数据库中没有记录，则根据模式计算
        if not credits_used:
            credits_used = 1
            if video.mode == 'script' and video.prompt:
                # 每超过2000字多扣1条额度
                char_count = len(video.prompt)
                credits_used = max(1, (char_count - 1) // 2000 + 1)
        
        usage_list.append({
            'id': video.id,
            'video_title': video.title,
            'template': getattr(video, 'template', '通用'),  # 如果没有template字段，默认为通用
            'style': video.style,
            'credits_used': credits_used,
            'status': video.status,
            'created_at': video.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return jsonify({
        'success': True,
        'records': usage_list
    })

# 路由：视频文件
@app.route('/video/<path:filename>')
@login_required
def video_file(filename):
    """提供视频文件"""
    return send_from_directory('workstore', filename)

# 管理员仪表盘
@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    """管理员仪表盘"""
    # 获取统计数据
    user_count = User.query.count()
    video_count = Video.query.count()
    total_income = db.session.query(db.func.sum(Payment.amount)).scalar() or 0
    
    # 今日新增用户
    today = datetime.utcnow().date()
    new_users_today = User.query.filter(
        db.func.date(User.created_at) == today
    ).count()
    
    # 最近7天用户增长
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=6)
    
    # 生成日期范围
    date_range = [start_date + timedelta(days=i) for i in range(7)]
    date_labels = [d.strftime('%m-%d') for d in date_range]
    
    # 查询每天的用户数
    user_growth = []
    for single_date in date_range:
        next_date = single_date + timedelta(days=1)
        count = User.query.filter(
            User.created_at >= single_date,
            User.created_at < next_date
        ).count()
        user_growth.append(count)
    
    # 用户角色分布
    admin_count = User.query.filter_by(is_admin=True).count()
    user_distribution = {
        'admin': admin_count,
        'regular': user_count - admin_count
    }
    
    # 最近登录的用户
    recent_users = User.query.filter(
        User.last_login_at.isnot(None)
    ).order_by(
        User.last_login_at.desc()
    ).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         user_count=user_count,
                         video_count=video_count,
                         total_income=total_income,
                         new_users_today=new_users_today,
                         growth_dates=date_labels,
                         growth_counts=user_growth,
                         user_distribution=user_distribution,
                         recent_users=recent_users)

# 用户管理
@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    """用户管理"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    query = User.query
    
    # 搜索功能
    search = request.args.get('q', '').strip()
    if search:
        query = query.filter(
            or_(
                User.username.like(f'%{search}%'),
                User.email.like(f'%{search}%')
            )
        )
    
    # 角色筛选
    role = request.args.get('role', '')
    if role == 'admin':
        query = query.filter_by(is_admin=True)
    elif role == 'user':
        query = query.filter_by(is_admin=False)
    
    # 排序
    query = query.order_by(User.created_at.desc())
    
    # 分页
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    users = pagination.items
    
    return render_template('admin/users.html',
                         users=users,
                         pagination=pagination,
                         total_users=query.count())

# 编辑用户
@app.route('/admin/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_user(user_id):
    """编辑用户信息"""
    from sqlalchemy.orm import joinedload
    from sqlalchemy import desc
    
    # 获取用户信息
    user = User.query.get_or_404(user_id)
    
    # 获取最近的登录日志
    recent_logs = UserLoginLog.query.filter_by(user_id=user_id).order_by(desc(UserLoginLog.created_at)).limit(5).all()
    
    if request.method == 'POST':
        # 更新用户信息
        user.username = request.form.get('username', user.username)
        user.email = request.form.get('email', user.email)
        user.credits = int(request.form.get('credits', user.credits))
        user.is_admin = 'is_admin' in request.form
        user.is_active = 'is_active' in request.form
        
        # 更新VIP到期时间
        vip_expires_str = request.form.get('vip_expires_at', '').strip()
        if vip_expires_str:
            try:
                user.vip_expires_at = datetime.strptime(vip_expires_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                flash('VIP到期时间格式不正确', 'danger')
                return redirect(url_for('admin_edit_user', user_id=user.id))
        else:
            user.vip_expires_at = None
        
        # 更新密码（如果提供了新密码）
        password = request.form.get('password', '').strip()
        if password:
            user.set_password(password)
        
        db.session.commit()
        flash('用户信息已更新', 'success')
        return redirect(url_for('admin_edit_user', user_id=user.id))
    
    return render_template('admin/edit_user.html', user=user, recent_logs=recent_logs)

# 添加用户
@app.route('/admin/user/add', methods=['POST'])
@login_required
@admin_required
def admin_add_user():
    """添加新用户"""
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    password_confirm = request.form.get('password_confirm', '').strip()
    credits = int(request.form.get('credits', 0))
    is_admin = 'is_admin' in request.form
    
    # 验证输入
    if not all([username, email, password, password_confirm]):
        flash('请填写所有必填字段', 'danger')
        return redirect(url_for('admin_users'))
    
    if password != password_confirm:
        flash('两次输入的密码不一致', 'danger')
        return redirect(url_for('admin_users'))
    
    if len(password) < 6:
        flash('密码长度不能少于6个字符', 'danger')
        return redirect(url_for('admin_users'))
    
    # 检查用户名和邮箱是否已存在
    if User.query.filter_by(username=username).first():
        flash('用户名已存在', 'danger')
        return redirect(url_for('admin_users'))
    
    if User.query.filter_by(email=email).first():
        flash('邮箱已被注册', 'danger')
        return redirect(url_for('admin_users'))
    
    # 创建新用户
    user = User(
        username=username,
        email=email,
        credits=credits,
        is_admin=is_admin
    )
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    flash('用户添加成功', 'success')
    return redirect(url_for('admin_edit_user', user_id=user.id))

# 删除用户
@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    """删除用户"""
    if current_user.id == user_id:
        flash('不能删除当前登录的管理员账户', 'danger')
        return redirect(url_for('admin_users'))
    
    user = User.query.get_or_404(user_id)
    
    # 删除相关数据（根据实际需求调整）
    UserLoginLog.query.filter_by(user_id=user_id).delete()
    
    # 删除用户
    db.session.delete(user)
    db.session.commit()
    
    flash('用户已删除', 'success')
    return redirect(url_for('admin_users'))

# 切换用户状态
@app.route('/admin/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def admin_toggle_user_status(user_id):
    """切换用户状态（启用/禁用）"""
    try:
        user = User.query.get_or_404(user_id)
        
        # 不能禁用管理员
        if user.is_admin:
            return jsonify({'success': False, 'message': '不能禁用管理员账户'})
        
        # 不能禁用当前登录用户
        if current_user.id == user_id:
            return jsonify({'success': False, 'message': '不能禁用当前登录的账户'})
        
        # 切换状态
        user.is_active = not user.is_active
        db.session.commit()
        
        action = '启用' if user.is_active else '禁用'
        return jsonify({'success': True, 'message': f'用户已{action}'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# 删除用户（API版本）
@app.route('/admin/users/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def admin_delete_user_api(user_id):
    """删除用户（API版本）"""
    try:
        if current_user.id == user_id:
            return jsonify({'success': False, 'message': '不能删除当前登录的管理员账户'})
        
        user = User.query.get_or_404(user_id)
        
        # 不能删除管理员
        if user.is_admin:
            return jsonify({'success': False, 'message': '不能删除管理员账户'})
        
        # 删除相关数据（根据实际需求调整）
        UserLoginLog.query.filter_by(user_id=user_id).delete()
        
        # 删除用户
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '用户已删除'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# 重置用户密码
@app.route('/admin/user/<int:user_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def admin_reset_password(user_id):
    """重置用户密码"""
    user = User.query.get_or_404(user_id)
    new_password = '123456'  # 默认重置密码
    user.set_password(new_password)
    db.session.commit()
    
    flash(f'已重置用户 {user.username} 的密码为: 123456', 'success')
    return redirect(url_for('admin_edit_user', user_id=user.id))

# 查看用户登录日志
@app.route('/admin/user/<int:user_id>/logs')
@login_required
@admin_required
def admin_user_logs(user_id):
    """查看用户登录日志"""
    from sqlalchemy.orm import joinedload
    user = User.query.options(joinedload(User.login_logs)).get_or_404(user_id)
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # 查询登录日志
    query = UserLoginLog.query.filter_by(user_id=user_id)
    
    # 分页
    pagination = query.order_by(
        UserLoginLog.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    logs = pagination.items
    
    return render_template('admin/user_logs.html',
                         user=user,
                         logs=logs,
                         pagination=pagination,
                         get_ip_info=get_ip_info)

def get_ip_info(ip=None):
    """
    获取IP地址信息
    :param ip: IP地址，如果为None则获取请求IP
    :return: IP信息字典
    """
    if not ip:
        if request:
            # 获取客户端IP
            if request.headers.get('X-Forwarded-For'):
                ip = request.headers.get('X-Forwarded-For').split(',')[0]
            else:
                ip = request.remote_addr or '127.0.0.1'
        else:
            ip = '127.0.0.1'
    
    try:
        # 使用ip-api.com免费API获取IP信息
        response = requests.get(f'http://ip-api.com/json/{ip}?fields=status,message,country,regionName,city,isp,org,as,query', timeout=3)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                return {
                    'ip': data.get('query', ip),
                    'country': data.get('country', ''),
                    'region': data.get('regionName', ''),
                    'city': data.get('city', ''),
                    'isp': data.get('isp', ''),
                    'org': data.get('org', ''),
                    'as': data.get('as', '')
                }
    except Exception as e:
        print(f"获取IP信息失败: {str(e)}")
    
    # 如果获取失败，返回基本IP信息
    return {
        'ip': ip,
        'country': '未知',
        'region': '未知',
        'city': '未知',
        'isp': '未知',
        'org': '未知',
        'as': '未知'
    }

# 视频文件访问路由
@app.route('/video/<path:filepath>')
@login_required
def serve_video(filepath):
    """提供视频文件访问"""
    try:
        # 记录请求路径
        app.logger.info(f"请求视频文件: {filepath}")
        
        # 解码URL编码的路径
        filepath = unquote(filepath)
        
        # 安全检查：确保路径在 workstore 目录下
        if not filepath.startswith('workstore/'):
            app.logger.error(f"非法路径访问: {filepath}")
            return 'Access denied', 403
        
        # 构建完整路径
        full_path = os.path.join(os.getcwd(), filepath)
        full_path = os.path.normpath(full_path)  # 标准化路径，处理 '..' 和 '.'
        
        # 再次检查路径是否在 workstore 目录下
        workstore_dir = os.path.join(os.getcwd(), 'workstore')
        if not os.path.abspath(full_path).startswith(os.path.abspath(workstore_dir)):
            app.logger.error(f"尝试访问 workstore 之外的路径: {full_path}")
            return 'Access denied', 403
        
        # 检查文件是否存在
        if not os.path.exists(full_path):
            # 如果是目录，尝试查找 output.mp4
            if os.path.isdir(full_path):
                full_path = os.path.join(full_path, 'output.mp4')
                if not os.path.exists(full_path):
                    app.logger.error(f"文件不存在: {full_path}")
                    return 'File not found', 404
            else:
                app.logger.error(f"文件不存在: {full_path}")
                return 'File not found', 404
        
        # 发送文件
        response = send_file(full_path, conditional=True)
        
        # 设置缓存控制头，防止浏览器缓存视频文件
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        
        return response
        
    except Exception as e:
        app.logger.error(f"提供视频文件时出错: {str(e)}", exc_info=True)
        return str(e), 500


@app.route('/download-video/<int:video_id>')
@login_required
def download_video(video_id):
    """下载视频及其封面"""
    try:
        # 获取视频信息
        video = Video.query.filter_by(id=video_id, user_id=current_user.id).first()
        if not video:
            app.logger.error(f"用户 {current_user.id} 尝试下载不存在的视频 {video_id}")
            return jsonify({'error': '视频不存在或无权访问'}), 404

        app.logger.info(f"用户 {current_user.id} 请求下载视频 {video_id}, 路径: {video.video_path}")

        # 获取视频目录路径
        video_path = video.video_path or ''
        if not video_path:
            app.logger.error(f"视频 {video_id} 的路径为空")
            return jsonify({'error': '视频路径为空'}), 404

        # 从完整路径中提取基础目录
        if video_path.startswith('workstore/'):
            # 去掉 workstore/ 前缀
            relative_path = video_path[10:]  # 去掉 'workstore/' 的10个字符
            # 分割路径获取用户目录和视频目录
            path_parts = relative_path.split('/')
            if len(path_parts) >= 2:
                user_dir = path_parts[0]  # 可能是 '1' 或 'user1'
                video_dir = path_parts[1]  # 视频目录名
                
                # 构建基础目录路径
                base_dir = os.path.join('workstore', user_dir, video_dir)
            else:
                app.logger.error(f"视频路径格式不正确: {video_path}")
                return jsonify({'error': '视频路径格式错误'}), 404
        else:
            app.logger.error(f"视频路径不以workstore/开头: {video_path}")
            return jsonify({'error': '视频路径格式错误'}), 404
        
        app.logger.info(f"解析的基础目录: {base_dir}")
        
        # 检查目录是否存在
        if not os.path.exists(base_dir):
            app.logger.error(f"视频目录不存在: {base_dir}")
            return jsonify({'error': '视频文件不存在'}), 404

        # 创建内存中的ZIP文件
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 添加output.mp4
            output_file = os.path.join(base_dir, 'output.mp4')
            if os.path.exists(output_file):
                zf.write(output_file, 'output.mp4')
                app.logger.info(f"已添加视频文件到ZIP: {output_file}")
            else:
                app.logger.warning(f"视频文件不存在: {output_file}")
            
            # 添加covers目录
            covers_dir = os.path.join(base_dir, 'covers')
            if os.path.exists(covers_dir):
                for root, dirs, files in os.walk(covers_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.join('covers', os.path.relpath(file_path, covers_dir))
                        zf.write(file_path, arcname)
                        app.logger.info(f"已添加封面文件到ZIP: {file_path}")
            else:
                app.logger.warning(f"封面目录不存在: {covers_dir}")

        # 准备下载
        memory_file.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        download_filename = f'video_{video.id}_{timestamp}.zip'
        
        app.logger.info(f"开始下载，文件名: {download_filename}")
        
        return send_file(
            memory_file,
            as_attachment=True,
            download_name=download_filename,
            mimetype='application/zip'
        )

    except Exception as e:
        app.logger.error(f"下载视频时出错: {str(e)}", exc_info=True)
        return jsonify({'error': f'下载失败: {str(e)}'}), 500

# 处理 workstore 目录下的静态文件
@app.route('/workstore/<path:filename>')
@login_required
def serve_workstore_file(filename):
    """提供 workstore 目录下的文件访问"""
    try:
        # 记录请求路径
        app.logger.info(f"请求 workstore 文件: {filename}")
        
        # 构建完整路径
        base_dir = os.path.join(os.getcwd(), 'workstore')
        full_path = os.path.join(base_dir, filename)
        
        # 标准化路径，处理 '..' 和 '.'
        full_path = os.path.normpath(full_path)
        
        # 检查路径是否在 workstore 目录下
        if not full_path.startswith(os.path.abspath(base_dir) + os.sep):
            app.logger.error(f"尝试访问 workstore 之外的路径: {full_path}")
            return 'Access denied', 403
        
        # 检查文件是否存在
        if not os.path.exists(full_path):
            # 如果是目录，尝试查找 output.mp4
            if os.path.isdir(full_path):
                output_path = os.path.join(full_path, 'output.mp4')
                if os.path.exists(output_path):
                    full_path = output_path
                else:
                    # 尝试查找封面图片
                    cover_path = os.path.join(full_path, 'covers', 'cover_4:3.png')
                    if os.path.exists(cover_path):
                        full_path = cover_path
                    else:
                        app.logger.error(f"文件不存在: {full_path} (尝试查找 output.mp4 和 cover_4:3.png 都失败)")
                        return 'File not found', 404
            else:
                # 检查是否是封面图片请求
                if 'covers/' in filename and filename.endswith('.png'):
                    # 尝试返回默认封面
                    default_cover = os.path.join(app.static_folder, 'img', 'default-cover.png')
                    if os.path.exists(default_cover):
                        return send_file(default_cover, conditional=True)
                
                app.logger.error(f"文件不存在: {full_path}")
                return 'File not found', 404
        
        # 发送文件
        return send_file(full_path, conditional=True)
        
    except Exception as e:
        app.logger.error(f"提供文件时出错: {str(e)}", exc_info=True)
        return str(e), 500

# 封面图片访问路由
@app.route('/covers/<path:filename>')
@login_required
def serve_cover(filename):
    """提供封面图片访问"""
    # 确保文件路径安全
    if '..' in filename or filename.startswith('/'):
        abort(404)
    
    # 设置封面目录路径
    covers_dir = os.path.join(app.root_path, 'static', 'covers')
    
    # 确保目录存在
    if not os.path.exists(covers_dir):
        os.makedirs(covers_dir, exist_ok=True)
    
    return send_from_directory(covers_dir, filename, as_attachment=False)

# 添加模板过滤器
@app.template_filter('humanize')
def humanize_time(dt):
    now = datetime.utcnow()
    diff = now - dt
    
    if diff < timedelta(minutes=1):
        return '刚刚'
    elif diff < timedelta(hours=1):
        minutes = int(diff.seconds / 60)
        return f'{minutes}分钟前'
    elif diff < timedelta(days=1):
        hours = int(diff.seconds / 3600)
        return f'{hours}小时前'
    elif diff < timedelta(weeks=1):
        days = diff.days
        return f'{days}天前'
    else:
        return dt.strftime('%Y-%m-%d')

@app.template_filter('nl2br')
def nl2br(text):
    """将文本中的换行符转换为HTML的<br>标签"""
    if not text:
        return ''
    return text.replace('\n', '<br>\n')

# 上下文处理器：添加模板全局变量
@app.context_processor
def inject_now():
    return {
        'now': datetime.utcnow(),
        'get_ip_info': get_ip_info
    }

# 初始化数据库
def create_tables():
    """创建数据库表"""
    db.create_all()
    # 创建默认管理员账户（如果不存在）
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@example.com',
            is_admin=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("已创建默认管理员账户: admin / admin123")

@app.route('/admin/videos')
@login_required
@admin_required
def admin_videos():
    """视频管理页面"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    query = request.args.get('q', '').strip()
    
    # 构建查询
    video_query = Video.query
    
    # 搜索
    if query:
        video_query = video_query.filter(
            db.or_(
                Video.title.ilike(f'%{query}%'),
                Video.prompt.ilike(f'%{query}%')
            )
        )
    
    # 排序
    video_query = video_query.order_by(Video.created_at.desc())
    
    # 分页
    pagination = video_query.paginate(page=page, per_page=per_page, error_out=False)
    videos = pagination.items
    
    return render_template('admin/videos.html',
                         videos=videos,
                         pagination=pagination,
                         total_videos=video_query.count())

@app.route('/admin/video/<int:video_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_video(video_id):
    """删除视频和相关项目文件"""
    import shutil
    from pathlib import Path
    
    video = Video.query.get_or_404(video_id)
    
    try:
        # 删除整个项目目录
        if video.video_path and os.path.exists(video.video_path):
            video_path = Path(video.video_path)
            project_dir = video_path.parent
            
            if project_dir.exists():
                shutil.rmtree(project_dir)
                log_info(f'删除项目目录: {project_dir}')
        
        # 删除数据库记录
        db.session.delete(video)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '视频和相关文件已删除'})
    except Exception as e:
        db.session.rollback()
        log_error(f'删除视频失败: {str(e)}')
        return jsonify({'success': False, 'message': f'删除视频失败: {str(e)}'}), 500

# 管理员下载视频
@app.route('/admin/videos/<int:video_id>/download', methods=['POST'])
@login_required
@admin_required
def admin_download_video(video_id):
    """管理员下载视频项目文件（包含所有相关文件的压缩包）"""
    import tempfile
    import shutil
    from pathlib import Path
    
    video = Video.query.get_or_404(video_id)
    
    if not video.video_path or not os.path.exists(video.video_path):
        return jsonify({'success': False, 'message': '视频文件不存在'}), 404
    
    try:
        # 确定项目目录路径
        video_path = Path(video.video_path)
        project_dir = video_path.parent
        
        if not project_dir.exists():
            return jsonify({'success': False, 'message': '项目目录不存在'}), 404
        
        # 创建临时zip文件
        temp_dir = tempfile.mkdtemp()
        zip_path = Path(temp_dir) / f'video_project_{video_id}.zip'
        
        # 创建zip文件
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # 遍历项目目录下的所有文件
            for file_path in project_dir.rglob('*'):
                if file_path.is_file():
                    # 计算相对路径
                    rel_path = file_path.relative_to(project_dir)
                    zip_file.write(file_path, rel_path)
        
        # 清理函数：删除临时文件
        def cleanup():
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
        
        # 返回zip文件
        return send_file(
            zip_path, 
            as_attachment=True, 
            download_name=f'video_project_{video.title}_{video_id}.zip'
        )
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'下载失败: {str(e)}'}), 500

@app.route('/test-progress')
def test_progress():
    """测试进度页面预览"""
    # 创建一个模拟的视频对象用于测试
    class MockVideo:
        def __init__(self):
            self.id = 999
            self.title = "测试视频"
    
    mock_video = MockVideo()
    return render_template('test_progress.html', video=mock_video)

# 管理员手动刷新免费额度
@app.route('/admin/refresh-monthly-credits', methods=['POST'])
@login_required
@admin_required
def admin_refresh_monthly_credits():
    """管理员手动刷新月度免费额度"""
    try:
        refreshed_count = 0
        total_count = 0
        
        # 获取所有活跃用户
        users = User.query.filter_by(is_active=True).all()
        
        for user in users:
            total_count += 1
            if user.refresh_monthly_free_credits():
                refreshed_count += 1
        
        db.session.commit()
        
        flash(f'免费额度刷新完成！总共 {total_count} 个用户，刷新了 {refreshed_count} 个用户', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'刷新失败：{str(e)}', 'danger')
    
    return redirect(url_for('admin_users'))

# 联系我们页面
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """联系我们页面"""
    if request.method == 'POST':
        try:
            # 获取表单数据
            email = request.form.get('email', '').strip()
            wechat = request.form.get('wechat', '').strip()
            qq = request.form.get('qq', '').strip()
            phone = request.form.get('phone', '').strip()
            content = request.form.get('content', '').strip()
            
            # 验证必填字段
            if not email or not content:
                return jsonify({'success': False, 'message': '邮箱和留言内容不能为空'})
            
            # 创建留言记录
            message = Message(
                email=email,
                wechat=wechat if wechat else None,
                qq=qq if qq else None,
                phone=phone if phone else None,
                content=content
            )
            
            db.session.add(message)
            db.session.commit()
            
            # 记录日志
            log_info(f"新留言：{email} - {content[:50]}...")
            
            return jsonify({'success': True, 'message': '留言提交成功！我们会尽快回复您。'})
            
        except Exception as e:
            db.session.rollback()
            log_error(f"留言提交失败：{str(e)}")
            return jsonify({'success': False, 'message': '提交失败，请稍后重试'})
    
    return render_template('contact.html')

# 管理员留言管理
@app.route('/admin/messages')
@login_required
@admin_required
def admin_messages():
    """管理员留言管理"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    query = Message.query
    
    # 搜索功能
    search = request.args.get('q', '').strip()
    if search:
        query = query.filter(
            or_(
                Message.email.like(f'%{search}%'),
                Message.content.like(f'%{search}%')
            )
        )
    
    # 状态筛选
    status = request.args.get('status', '')
    if status == 'read':
        query = query.filter_by(is_read=True)
    elif status == 'unread':
        query = query.filter_by(is_read=False)
    
    # 排序
    query = query.order_by(Message.created_at.desc())
    
    # 分页
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    messages = pagination.items
    
    # 统计数据
    total_messages = Message.query.count()
    unread_messages = Message.query.filter_by(is_read=False).count()
    
    return render_template('admin/messages.html',
                         messages=messages,
                         pagination=pagination,
                         total_messages=total_messages,
                         unread_messages=unread_messages)

# 标记留言为已读
@app.route('/admin/message/<int:message_id>/mark-read', methods=['POST'])
@login_required
@admin_required
def admin_mark_message_read(message_id):
    """标记留言为已读"""
    try:
        message = Message.query.get_or_404(message_id)
        message.is_read = True
        message.replied_at = datetime.utcnow()
        db.session.commit()
        
        flash('留言已标记为已读', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'操作失败：{str(e)}', 'danger')
    
    return redirect(url_for('admin_messages'))

# 删除留言
@app.route('/admin/message/<int:message_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_message(message_id):
    """删除留言"""
    try:
        message = Message.query.get_or_404(message_id)
        db.session.delete(message)
        db.session.commit()
        
        flash('留言已删除', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败：{str(e)}', 'danger')
    
    return redirect(url_for('admin_messages'))

if __name__ == '__main__':
    # 确保数据库表存在
    with app.app_context():
        db.create_all()
        # 创建默认管理员账户（如果不存在）
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("已创建默认管理员账户: admin / admin123")
        
        # 恢复中断的任务
        print("正在检查并恢复中断的任务...")
        log_info("正在检查并恢复中断的任务...")
        recover_interrupted_tasks()
        print("任务恢复检查完成")
        log_info("任务恢复检查完成")
    
    # 启动Flask应用 (端口从环境变量读取，默认5001)
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port)