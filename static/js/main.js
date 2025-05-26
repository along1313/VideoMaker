/**
 * 百速一键AI视频生成 - 主JavaScript文件
 * 提供全局通用功能和交互效果
 */

// 全局Vue实例配置
document.addEventListener('DOMContentLoaded', function() {
    // 配置axios默认值
    axios.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
    
    // 添加请求拦截器
    axios.interceptors.request.use(function (config) {
        // 在发送请求之前做些什么
        return config;
    }, function (error) {
        // 对请求错误做些什么
        return Promise.reject(error);
    });
    
    // 添加响应拦截器
    axios.interceptors.response.use(function (response) {
        // 对响应数据做点什么
        return response;
    }, function (error) {
        // 对响应错误做点什么
        if (error.response && error.response.status === 401) {
            // 未授权，跳转到登录页
            window.location.href = '/login';
        } else if (error.response && error.response.data && error.response.data.message) {
            // 显示错误消息
            Vue.prototype.$message.error(error.response.data.message);
        } else {
            // 显示通用错误
            Vue.prototype.$message.error('请求失败，请稍后重试');
        }
        return Promise.reject(error);
    });
    
    // 全局过滤器
    Vue.filter('formatDate', function(value) {
        if (!value) return '';
        const date = new Date(value);
        return date.toLocaleString();
    });
    
    // 全局方法
    Vue.prototype.$formatFileSize = function(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return (bytes / Math.pow(k, i)).toFixed(2) + ' ' + sizes[i];
    };
});

// 通用工具函数
const utils = {
    /**
     * 复制文本到剪贴板
     * @param {string} text - 要复制的文本
     * @returns {Promise} - 复制操作的Promise
     */
    copyToClipboard: function(text) {
        return navigator.clipboard.writeText(text)
            .then(() => {
                Vue.prototype.$message.success('复制成功');
                return true;
            })
            .catch(err => {
                Vue.prototype.$message.error('复制失败: ' + err);
                return false;
            });
    },
    
    /**
     * 格式化时间长度（秒）为时:分:秒格式
     * @param {number} seconds - 秒数
     * @returns {string} - 格式化后的时间字符串
     */
    formatDuration: function(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        let result = '';
        if (hours > 0) {
            result += hours + ':';
        }
        
        result += (minutes < 10 && hours > 0 ? '0' : '') + minutes + ':';
        result += (secs < 10 ? '0' : '') + secs;
        
        return result;
    },
    
    /**
     * 防抖函数
     * @param {Function} func - 要执行的函数
     * @param {number} wait - 等待时间（毫秒）
     * @returns {Function} - 防抖处理后的函数
     */
    debounce: function(func, wait) {
        let timeout;
        return function() {
            const context = this;
            const args = arguments;
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                func.apply(context, args);
            }, wait);
        };
    },
    
    /**
     * 节流函数
     * @param {Function} func - 要执行的函数
     * @param {number} limit - 限制时间（毫秒）
     * @returns {Function} - 节流处理后的函数
     */
    throttle: function(func, limit) {
        let inThrottle;
        return function() {
            const context = this;
            const args = arguments;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
};