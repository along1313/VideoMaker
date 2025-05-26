import os
import json
import uuid
import traceback
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import threading
import time
from datetime import datetime

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

# 初始化登录管理器
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 全局变量存储生成状态
generation_status = {}

# 用户模型
class User(UserMixin, db.Model):
    """用户模型，存储用户信息"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    credits = db.Column(db.Integer, default=3)  # 新用户赠送3条视频额度
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
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
    
    user = db.relationship('User', backref=db.backref('videos', lazy=True))

# 充值记录模型
class Payment(db.Model):
    """充值记录模型，存储用户充值信息"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    credits = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='completed')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('payments', lazy=True))

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
    """我的视频列表"""
    try:
        # 获取用户的视频，最多显示20个，按创建时间倒序排列
        video_objects = Video.query.filter_by(user_id=current_user.id).order_by(Video.created_at.desc()).limit(20).all()
        
        # 将Video对象转换为可序列化的字典
        videos = []
        for video in video_objects:
            # 处理时间格式，确保可序列化
            created_at = video.created_at.strftime('%Y-%m-%d %H:%M:%S') if video.created_at else None
            
            videos.append({
                'id': video.id,
                'title': video.title,
                'style': video.style,
                'prompt': video.prompt,
                'status': video.status,
                'video_path': video.video_path,
                'cover_path': video.cover_path,
                'created_at': created_at
            })
        
        log_info(f"用户 {current_user.username} 访问我的视频页面，找到 {len(videos)} 个视频")
        return render_template('my_videos.html', videos=videos)
    except Exception as e:
        log_error(f"获取用户视频列表失败: {str(e)}", exc_info=True)
        return render_template('my_videos.html', videos=[], error=f"获取视频列表失败: {str(e)}")

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

# 初始化数据库
# 初始化数据库函数
def create_tables():
    """创建数据库表"""
    db.create_all()

if __name__ == '__main__':
    # 确保数据库表存在
    with app.app_context():
        db.create_all()
    
    # 启动应用
    app.run(debug=True, host='0.0.0.0', port=5001)