import os
import json
import uuid
import traceback
import io
import zipfile
from datetime import datetime, timedelta
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

# 导入日志模块
from logger import log_info, log_error, log_warning, log_video_task

# 导入核心服务
from service.ai_service import LLMService, ImageModelService, TTSModelService
from service.work_flow_service import run_work_flow, run_work_flow_with_script
from static.style_config import STYLE_CONFIG

# 初始化Flask应用
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_for_baisu_ai_video')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///baisu_video.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# 初始化登录管理器
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 全局变量存储生成状态
generation_status = {}

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
    last_login_ip = db.Column(db.String(50))  # 最后登录IP
    last_login_at = db.Column(db.DateTime)  # 最后登录时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    login_logs = db.relationship('UserLoginLog', backref='user', lazy=True)  # 登录日志
    videos = db.relationship('Video', backref='user', lazy=True)  # 视频
    payments = db.relationship('Payment', backref='user', lazy=True)  # 充值记录
    
    def is_administrator(self):
        return self.is_admin
    
    def set_password(self, password):
        """设置密码哈希"""
        self.password_hash = generate_password_hash(password)
        
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
    # 移除重复的 user 关系，因为已经在 User 模型中定义了 backref

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
        
        # 根据模式选择不同的生成方式
        if mode == 'script':
            # 使用文案模式
            log_info(f"[任务 {task_id}] 使用文案模式生成视频")
            run_work_flow_with_script(
                script=prompt,
                result_dir=result_dir,
                user_id=str(user_id),
                style=style,
                llm=llm,
                image_model=image_model,
                tts_model=tts_model,
                user_name="百速AI视频"
            )
        else:
            # 使用提示词模式
            log_info(f"[任务 {task_id}] 使用提示词模式生成视频")
            run_work_flow(
                text=prompt,
                result_dir=result_dir,
                user_id=str(user_id),
                style=style,
                llm=llm,
                image_model=image_model,
                tts_model=tts_model,
                user_name="百速AI视频"
            )
        
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

# 路由：登录
@app.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        
        return render_template('login.html', error='用户名或密码错误')
    
    return render_template('login.html')

# 路由：注册
@app.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # 检查用户名和邮箱是否已存在
        if User.query.filter_by(username=username).first():
            return render_template('register.html', error='用户名已存在')
        
        if User.query.filter_by(email=email).first():
            return render_template('register.html', error='邮箱已存在')
        
        # 创建新用户
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        # 自动登录
        login_user(user)
        return redirect(url_for('index'))
    
    return render_template('register.html')

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
    try:
        video_objects = Video.query.filter_by(user_id=current_user.id).order_by(Video.created_at.desc()).limit(20).all()
        videos = []
        for video in video_objects:
            created_at = video.created_at.strftime('%Y-%m-%d %H:%M:%S') if video.created_at else None
            
            # 处理视频路径
            video_path = video.video_path or ''
            # 移除可能存在的重复前缀
            if video_path.startswith('workstore/1/workstore/'):
                video_path = video_path.replace('workstore/1/workstore/', 'workstore/1/')
            
            # 确保视频路径格式正确
            if video_path and not video_path.startswith('workstore/'):
                video_path = f'workstore/1/{video_path}'
            
            # 处理封面路径
            cover_path = video.cover_path or ''
            if not cover_path:
                # 如果没有封面路径，尝试使用默认封面
                cover_path = f'/workstore/1/{video.title}/covers/cover_4:3.png' if video.title else ''
            elif not cover_path.startswith(('http://', 'https://', '/static/', '/workstore/')):
                cover_path = f'/workstore/1/{video.title}/{cover_path}' if video.title else f'/static/{cover_path}'
            
            videos.append({
                'id': video.id,
                'title': video.title or '未命名视频',
                'style': video.style or '默认风格',
                'prompt': video.prompt or '',
                'status': video.status or 'unknown',
                'created_at': created_at,
                'video_path': video_path,
                'cover_path': cover_path
            })
        
        return render_template('my_videos.html', 
                             videos_json=json.dumps(videos, ensure_ascii=False),
                             error=None)
    except Exception as e:
        app.logger.error(f"Error in my_videos: {str(e)}", exc_info=True)
        return render_template('my_videos.html', 
                             videos_json=json.dumps([], ensure_ascii=False),
                             error=f'加载视频列表失败: {str(e)}')

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
        # 记录API调用
        log_info(f"用户 {current_user.username} (ID: {current_user.id}) 请求生成视频", "video")
        
        # 检查用户额度
        if current_user.credits <= 0:
            log_warning(f"用户 {current_user.username} 视频额度不足 (当前额度: {current_user.credits})")
            return jsonify({
                'success': False,
                'message': '视频生成额度不足，请充值'
            }), 400
        
        # 获取请求参数
        data = request.get_json()
        prompt = data.get('prompt', '')
        style = data.get('style', '3D景深')
        mode = data.get('mode', 'prompt')  # 默认为提示词模式
        
        if not prompt:
            error_msg = '请输入提示词' if mode == 'prompt' else '请输入文案内容'
            log_warning(f"用户 {current_user.username} 提交了空{'提示词' if mode == 'prompt' else '文案'}")
            return jsonify({
                'success': False,
                'message': error_msg
            }), 400
        
        log_info(f"创建视频记录 - 用户: {current_user.username}, 风格: {style}, 模式: {mode}", "video")
        
        # 创建视频记录
        video = Video(
            user_id=current_user.id,
            title=f"视频_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            style=style,
            prompt=prompt,
            status='pending',
            mode=mode  # 保存生成模式
        )
        db.session.add(video)
        db.session.commit()
        
        log_info(f"视频记录创建成功 - 视频ID: {video.id}", "video")
    except Exception as e:
        log_error(f"创建视频记录失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'创建视频记录失败: {str(e)}'
        }), 500
    
    try:
        # 扣除用户额度
        current_user.credits -= 1
        db.session.commit()
        log_info(f"用户 {current_user.username} 额度已扣除 (剩余: {current_user.credits})", "video")
        
        # 启动视频生成后台任务
        thread = threading.Thread(target=generate_video_task, args=(prompt, style, current_user.id, video.id, mode))
        thread.daemon = True
        thread.start()
        
        log_info(f"视频生成任务已启动 - 视频ID: {video.id}", "video")
        
        return jsonify({
            'success': True,
            'message': '视频生成任务已提交',
            'video_id': video.id
        })
    except Exception as e:
        log_error(f"启动视频生成任务失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'启动视频生成任务失败: {str(e)}'
        }), 500

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
                    'logs': task_data.get('logs', [])
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
    user = User.query.options(joinedload(User.login_logs)).get_or_404(user_id)
    
    if request.method == 'POST':
        # 更新用户信息
        user.username = request.form.get('username', user.username)
        user.email = request.form.get('email', user.email)
        user.credits = int(request.form.get('credits', user.credits))
        user.is_admin = 'is_admin' in request.form
        user.is_active = 'is_active' in request.form
        
        # 更新密码（如果提供了新密码）
        password = request.form.get('password', '').strip()
        if password:
            user.set_password(password)
        
        db.session.commit()
        flash('用户信息已更新', 'success')
        return redirect(url_for('admin_edit_user', user_id=user.id))
    
    return render_template('admin/edit_user.html', user=user)

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
            return jsonify({'error': '视频不存在或无权访问'}), 404

        # 获取视频目录
        video_path = video.video_path or ''
        if 'workstore/1/' in video_path:
            video_path = video_path.split('workstore/1/')[-1]
        
        # 获取基础目录
        base_dir = os.path.join('workstore', '1', video_path.split('/')[0])
        
        # 检查目录是否存在
        if not os.path.exists(base_dir):
            return jsonify({'error': '视频文件不存在'}), 404

        # 创建内存中的ZIP文件
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 添加output.mp4
            output_file = os.path.join(base_dir, 'output.mp4')
            if os.path.exists(output_file):
                zf.write(output_file, 'output.mp4')
            
            # 添加covers目录
            covers_dir = os.path.join(base_dir, 'covers')
            if os.path.exists(covers_dir):
                for root, dirs, files in os.walk(covers_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.join('covers', os.path.relpath(file_path, covers_dir))
                        zf.write(file_path, arcname)

        # 准备下载
        memory_file.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return send_file(
            memory_file,
            as_attachment=True,
            download_name=f'video_{video.id}_{timestamp}.zip',
            mimetype='application/zip'
        )

    except Exception as e:
        app.logger.error(f"下载视频时出错: {str(e)}", exc_info=True)
        return jsonify({'error': '下载失败'}), 500

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
    
    # 启动Flask应用
    app.run(debug=True, host='0.0.0.0', port=5000)