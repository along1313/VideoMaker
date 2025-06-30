/**
 * Vue 实用工具库
 * 提供现代化的Vue组件开发工具
 */

// Vue混入 - 通用功能
window.VueMixins = {
    // 通用数据和方法混入
    common: {
        computed: {
            // 全局用户信息
            $user() {
                return this.$global && this.$global.user || {};
            },
            // 全局URL配置
            $urls() {
                return this.$global && this.$global.urls || {};
            },
            // 用户认证状态
            isAuthenticated() {
                return this.$user.isAuthenticated || false;
            },
            // 用户VIP状态
            isVipUser() {
                return this.$user.isVip || false;
            },
            // 用户管理员状态
            isAdmin() {
                return this.$user.isAdmin || false;
            }
        },
        methods: {
            // 导航到指定页面
            navigateTo(page) {
                if (this.$urls[page]) {
                    window.location.href = this.$urls[page];
                } else {
                    console.warn('Unknown page:', page);
                }
            },
            // 显示消息提示
            showMessage(message, type = 'info') {
                if (this.$message) {
                    this.$message[type](message);
                } else {
                    console.log(`[${type.toUpperCase()}] ${message}`);
                }
            },
            // 确认对话框
            async confirmAction(message, title = '确认') {
                if (this.$confirm) {
                    try {
                        await this.$confirm(message, title, {
                            confirmButtonText: '确定',
                            cancelButtonText: '取消',
                            type: 'warning'
                        });
                        return true;
                    } catch {
                        return false;
                    }
                } else {
                    return confirm(message);
                }
            },
            // 处理API错误
            handleApiError(error, defaultMessage = '操作失败') {
                const message = error.response?.data?.message || error.message || defaultMessage;
                this.showMessage(message, 'error');
                console.error('API Error:', error);
            },
            // 格式化日期
            formatDate(dateString) {
                if (!dateString) return '';
                const date = new Date(dateString);
                return isNaN(date.getTime()) ? dateString : date.toLocaleString();
            }
        }
    },

    // 视频相关混入
    video: {
        methods: {
            // 获取封面URL
            getCoverUrl(coverPath) {
                if (!coverPath) return '/static/img/default-cover.png';
                if (coverPath.startsWith('http') || coverPath.startsWith('/')) {
                    return coverPath;
                }
                return `/${coverPath}`;
            },
            // 获取视频URL
            getVideoUrl(videoPath) {
                if (!videoPath) return '';
                
                if (videoPath.startsWith('http://') || videoPath.startsWith('https://')) {
                    return videoPath;
                }
                
                let path = videoPath;
                while (path.includes('workstore/')) {
                    path = path.replace('workstore/', '');
                }
                
                const finalPath = `workstore/${path}`.replace(/\/+/g, '/');
                const fullPath = finalPath.endsWith('.mp4') ? finalPath : `${finalPath}/output.mp4`;
                
                return `/${fullPath}`;
            },
            // 播放视频
            async playVideo(video) {
                if (!video || video.status !== 'completed') {
                    this.showMessage('视频尚未准备好播放', 'warning');
                    return;
                }
                
                try {
                    const videoUrl = this.getVideoUrl(video.video_path);
                    if (!videoUrl) {
                        throw new Error('视频路径不存在');
                    }
                    
                    // 设置当前视频并显示播放器
                    this.currentVideo = { ...video, video_path: videoUrl };
                    this.videoDialogVisible = true;
                    
                    console.log('Playing video from:', videoUrl);
                } catch (error) {
                    this.handleApiError(error, '播放视频失败');
                }
            },
            // 下载视频
            async downloadVideo(video) {
                if (!video || video.status !== 'completed') {
                    this.showMessage('视频尚未准备好下载', 'warning');
                    return;
                }

                this.downloadingVideoId = video.id;
                const loading = this.$loading({
                    lock: true,
                    text: '正在准备下载，请稍候...',
                    spinner: 'el-icon-loading',
                    background: 'rgba(0, 0, 0, 0.7)'
                });

                try {
                    const response = await fetch(`/download-video/${video.id}`, {
                        method: 'GET',
                        headers: { 'Accept': 'application/zip' }
                    });

                    if (!response.ok) {
                        const errorData = await response.json().catch(() => ({}));
                        throw new Error(errorData.error || '下载失败');
                    }

                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const link = document.createElement('a');
                    link.href = url;
                    link.download = `video_${video.id}_${new Date().getTime()}.zip`;
                    document.body.appendChild(link);
                    link.click();
                    
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(link);
                    
                    this.showMessage('下载准备完成', 'success');
                } catch (error) {
                    this.handleApiError(error, '下载失败');
                } finally {
                    this.downloadingVideoId = null;
                    loading.close();
                }
            },
            // 删除视频
            async deleteVideo(video) {
                if (!video || !video.id) {
                    this.showMessage('无效的视频数据', 'error');
                    return;
                }
                
                const confirmed = await this.confirmAction('确定要删除这个视频吗？');
                if (!confirmed) return;
                
                try {
                    const response = await axios.post(`/api/delete-video/${video.id}`);
                    if (response.data.success) {
                        this.showMessage('视频已删除', 'success');
                        // 从列表中移除
                        if (this.videos) {
                            this.videos = this.videos.filter(v => v.id !== video.id);
                        }
                    } else {
                        throw new Error(response.data.message);
                    }
                } catch (error) {
                    this.handleApiError(error, '删除失败');
                }
            }
        }
    }
};

// Vue组件工厂
window.VueComponents = {
    // 创建视频卡片组件
    createVideoCard: function() {
        return {
            props: ['video'],
            template: `
                <div class="video-card">
                    <div class="video-thumbnail">
                        <img :src="getCoverUrl(video.cover_path)" :alt="video.title || '未命名视频'">
                        <div class="video-status" v-if="video.status !== 'completed'">
                            <el-tag type="warning" v-if="video.status === 'pending'">等待处理</el-tag>
                            <el-tag type="info" v-if="video.status === 'processing'">处理中</el-tag>
                            <el-tag type="danger" v-if="video.status === 'failed'">处理失败</el-tag>
                        </div>
                        <div class="video-play" v-if="video.status === 'completed'" @click="$emit('play', video)">
                            <i class="el-icon-video-play"></i>
                        </div>
                    </div>
                    <div class="video-info">
                        <h3>\${ video.title || '未命名视频' }</h3>
                        <p class="video-date">\${ formatDate(video.created_at || '') }</p>
                        <p class="video-style">风格: \${ video.style || '默认' }</p>
                        <div class="video-actions">
                            <el-button type="primary" size="mini" @click="$emit('play', video)" :disabled="!video || video.status !== 'completed'">
                                <i class="el-icon-video-play"> 播放</i>
                            </el-button>
                            <el-button 
                                type="success" 
                                size="mini" 
                                @click="$emit('download', video)" 
                                :disabled="!video || video.status !== 'completed'"
                                :loading="downloadingVideoId === video.id">
                                <i class="el-icon-download"> 下载</i>
                            </el-button>
                            <el-button type="danger" size="mini" @click="$emit('delete', video)" :disabled="!video">
                                <i class="el-icon-delete"> 删除</i>
                            </el-button>
                        </div>
                    </div>
                </div>
            `,
            mixins: [window.VueMixins.common, window.VueMixins.video]
        };
    }
};

// 导出工具函数
window.VueUtils = {
    // 创建标准的Vue实例
    createApp: function(options = {}) {
        // 自动添加通用混入
        if (!options.mixins) {
            options.mixins = [];
        }
        options.mixins.unshift(window.VueMixins.common);
        
        return window.AppConfig.createVue(options);
    },
    
    // 创建视频管理应用
    createVideoApp: function(options = {}) {
        if (!options.mixins) {
            options.mixins = [];
        }
        options.mixins.unshift(window.VueMixins.video);
        
        return this.createApp(options);
    }
}; 