#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
邮件服务模块
支持验证码发送、密码重置等邮件功能
"""

import os
import secrets
import string
from datetime import datetime, timedelta
from flask import current_app, url_for, render_template_string
from flask_mail import Mail, Message
from dotenv import load_dotenv

load_dotenv()

class EmailService:
    """邮件服务类"""
    
    def __init__(self, app=None):
        self.mail = None
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化邮件服务"""
        # 配置邮件服务器
        app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.exmail.qq.com')
        app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 465))
        app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'True').lower() == 'true'
        app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'False').lower() == 'true'
        app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'noreply@baisuai.com')
        app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
        app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', '百速AI <noreply@baisuai.com>')
        
        self.mail = Mail(app)
        
        # 验证配置
        if not app.config['MAIL_PASSWORD']:
            current_app.logger.warning("邮件服务未配置密码，邮件发送功能将不可用")
    
    def generate_verification_code(self, length=6):
        """生成数字验证码"""
        return ''.join(secrets.choice(string.digits) for _ in range(length))
    
    def send_verification_email(self, user_email, verification_code, username=None):
        """发送邮箱验证码"""
        try:
            subject = '【百速AI】邮箱验证码'
            html_body = self._render_verification_template(verification_code, username)
            
            msg = Message(
                subject=subject,
                recipients=[user_email],
                html=html_body
            )
            
            self.mail.send(msg)
            current_app.logger.info(f"验证码邮件已发送至: {user_email}")
            return True
            
        except Exception as e:
            current_app.logger.error(f"发送验证码邮件失败: {str(e)}")
            return False
    
    def send_password_reset_email(self, user_email, reset_token, username=None):
        """发送密码重置邮件"""
        try:
            reset_url = url_for('reset_password_page', token=reset_token, _external=True)
            subject = '【百速AI】密码重置链接'
            html_body = self._render_reset_template(reset_url, username)
            
            msg = Message(
                subject=subject,
                recipients=[user_email],
                html=html_body
            )
            
            self.mail.send(msg)
            current_app.logger.info(f"密码重置邮件已发送至: {user_email}")
            return True
            
        except Exception as e:
            current_app.logger.error(f"发送密码重置邮件失败: {str(e)}")
            return False
    
    def send_welcome_email(self, user_email, username):
        """发送欢迎邮件"""
        try:
            subject = '【百速AI】欢迎加入百速AI！'
            html_body = self._render_welcome_template(username)
            
            msg = Message(
                subject=subject,
                recipients=[user_email],
                html=html_body
            )
            
            self.mail.send(msg)
            current_app.logger.info(f"欢迎邮件已发送至: {user_email}")
            return True
            
        except Exception as e:
            current_app.logger.error(f"发送欢迎邮件失败: {str(e)}")
            return False
    
    def _render_verification_template(self, verification_code, username=None):
        """渲染验证码邮件模板"""
        template = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>邮箱验证码</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #f4f4f4;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #6750a4 0%, #8e24aa 100%); padding: 40px 20px; text-align: center;">
            <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 300;">百速AI</h1>
            <p style="color: #ffffff; margin: 10px 0 0 0; opacity: 0.9;">让创意更简单</p>
        </div>
        
        <!-- Content -->
        <div style="padding: 40px 20px;">
            <h2 style="color: #333333; margin: 0 0 20px 0; font-size: 24px; font-weight: 400;">
                {% if username %}Hi {{ username }}，{% endif %}邮箱验证码
            </h2>
            
            <p style="color: #666666; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                您正在注册百速AI账号，请使用以下验证码完成验证：
            </p>
            
            <!-- Verification Code -->
            <div style="text-align: center; margin: 40px 0;">
                <div style="background-color: #f8f9fa; border: 2px dashed #6750a4; border-radius: 8px; padding: 30px; display: inline-block;">
                    <div style="color: #6750a4; font-size: 32px; font-weight: bold; letter-spacing: 6px; font-family: Monaco, 'Courier New', monospace;">
                        {{ verification_code }}
                    </div>
                </div>
            </div>
            
            <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 6px; padding: 15px; margin: 30px 0;">
                <p style="color: #856404; margin: 0; font-size: 14px;">
                    <strong>⚠️ 安全提示：</strong><br>
                    • 验证码有效期为 <strong>10分钟</strong><br>
                    • 请勿向任何人泄露此验证码<br>
                    • 如非本人操作，请忽略此邮件
                </p>
            </div>
            
            <p style="color: #999999; font-size: 14px; line-height: 1.5; margin: 30px 0 0 0;">
                如果您在使用过程中遇到任何问题，请联系我们的客服团队：
                <a href="mailto:admin@baisuai.com" style="color: #6750a4; text-decoration: none;">admin@baisuai.com</a>
            </p>
        </div>
        
        <!-- Footer -->
        <div style="background-color: #f8f9fa; padding: 30px 20px; text-align: center; border-top: 1px solid #e9ecef;">
            <p style="color: #6c757d; margin: 0; font-size: 14px;">
                © 2025 百速AI - 让创意更简单<br>
                <a href="https://baisuai.com" style="color: #6750a4; text-decoration: none;">baisuai.com</a>
            </p>
        </div>
    </div>
</body>
</html>
        """
        
        return render_template_string(template, 
                                    verification_code=verification_code, 
                                    username=username)
    
    def _render_reset_template(self, reset_url, username=None):
        """渲染密码重置邮件模板"""
        template = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>密码重置</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #f4f4f4;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #6750a4 0%, #8e24aa 100%); padding: 40px 20px; text-align: center;">
            <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 300;">百速AI</h1>
            <p style="color: #ffffff; margin: 10px 0 0 0; opacity: 0.9;">让创意更简单</p>
        </div>
        
        <!-- Content -->
        <div style="padding: 40px 20px;">
            <h2 style="color: #333333; margin: 0 0 20px 0; font-size: 24px; font-weight: 400;">
                {% if username %}Hi {{ username }}，{% endif %}重置您的密码
            </h2>
            
            <p style="color: #666666; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                我们收到了您的密码重置请求。请点击下方按钮重置您的密码：
            </p>
            
            <!-- Reset Button -->
            <div style="text-align: center; margin: 40px 0;">
                <a href="{{ reset_url }}" 
                   style="background-color: #6750a4; color: #ffffff; padding: 15px 40px; text-decoration: none; border-radius: 6px; font-size: 16px; font-weight: 500; display: inline-block;">
                    重置密码
                </a>
            </div>
            
            <p style="color: #999999; font-size: 14px; line-height: 1.5; margin: 30px 0;">
                如果按钮无法点击，请复制以下链接到浏览器地址栏：<br>
                <a href="{{ reset_url }}" style="color: #6750a4; word-break: break-all;">{{ reset_url }}</a>
            </p>
            
            <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 6px; padding: 15px; margin: 30px 0;">
                <p style="color: #721c24; margin: 0; font-size: 14px;">
                    <strong>🔒 安全提示：</strong><br>
                    • 重置链接有效期为 <strong>1小时</strong><br>
                    • 如非本人操作，请忽略此邮件<br>
                    • 为了账户安全，请设置强密码
                </p>
            </div>
        </div>
        
        <!-- Footer -->
        <div style="background-color: #f8f9fa; padding: 30px 20px; text-align: center; border-top: 1px solid #e9ecef;">
            <p style="color: #6c757d; margin: 0; font-size: 14px;">
                © 2025 百速AI - 让创意更简单<br>
                <a href="https://baisuai.com" style="color: #6750a4; text-decoration: none;">baisuai.com</a>
            </p>
        </div>
    </div>
</body>
</html>
        """
        
        return render_template_string(template, reset_url=reset_url, username=username)
    
    def _render_welcome_template(self, username):
        """渲染欢迎邮件模板"""
        template = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>欢迎加入百速AI</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #f4f4f4;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #6750a4 0%, #8e24aa 100%); padding: 40px 20px; text-align: center;">
            <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 300;">🎉 欢迎加入百速AI！</h1>
            <p style="color: #ffffff; margin: 10px 0 0 0; opacity: 0.9;">让创意更简单</p>
        </div>
        
        <!-- Content -->
        <div style="padding: 40px 20px;">
            <h2 style="color: #333333; margin: 0 0 20px 0; font-size: 24px; font-weight: 400;">
                Hi {{ username }}，欢迎您！
            </h2>
            
            <p style="color: #666666; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                感谢您注册百速AI账号！现在您可以开始体验我们的AI视频生成服务了。
            </p>
            
            <!-- Features -->
            <div style="margin: 30px 0;">
                <h3 style="color: #333333; font-size: 18px; margin: 0 0 15px 0;">🚀 您可以开始：</h3>
                <ul style="color: #666666; line-height: 1.8; padding-left: 20px;">
                    <li>输入创意文案，一键生成专业视频</li>
                    <li>选择多种视频风格和模板</li>
                    <li>享受免费的月度额度</li>
                    <li>下载高清视频用于商业用途</li>
                </ul>
            </div>
            
            <!-- CTA Button -->
            <div style="text-align: center; margin: 40px 0;">
                <a href="https://baisuai.com" 
                   style="background-color: #6750a4; color: #ffffff; padding: 15px 40px; text-decoration: none; border-radius: 6px; font-size: 16px; font-weight: 500; display: inline-block;">
                    开始创作视频
                </a>
            </div>
            
            <p style="color: #999999; font-size: 14px; line-height: 1.5; margin: 30px 0 0 0;">
                如果您有任何问题或建议，随时联系我们：
                <a href="mailto:admin@baisuai.com" style="color: #6750a4; text-decoration: none;">admin@baisuai.com</a>
            </p>
        </div>
        
        <!-- Footer -->
        <div style="background-color: #f8f9fa; padding: 30px 20px; text-align: center; border-top: 1px solid #e9ecef;">
            <p style="color: #6c757d; margin: 0; font-size: 14px;">
                © 2025 百速AI - 让创意更简单<br>
                <a href="https://baisuai.com" style="color: #6750a4; text-decoration: none;">baisuai.com</a>
            </p>
        </div>
    </div>
</body>
</html>
        """
        
        return render_template_string(template, username=username)

# 全局邮件服务实例
email_service = EmailService() 