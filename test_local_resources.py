#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试本地资源加载
"""

import requests
import time

def test_local_resources():
    """测试本地资源加载"""
    base_url = "http://localhost:5002"
    
    # 测试的资源列表
    resources = [
        "/static/vendor/vue/vue.min.js",
        "/static/vendor/element-ui/index.css",
        "/static/vendor/element-ui/index.js",
        "/static/vendor/axios/axios.min.js",
        "/static/vendor/font-awesome/css/all.min.css",
        "/static/vendor/element-ui/fonts/element-icons.woff",
        "/static/vendor/element-ui/fonts/element-icons.ttf",
        "/static/vendor/font-awesome/webfonts/fa-solid-900.woff2",
        "/static/vendor/font-awesome/webfonts/fa-regular-400.woff2",
        "/static/vendor/font-awesome/webfonts/fa-brands-400.woff2",
    ]
    
    print("开始测试本地资源加载...")
    print("=" * 50)
    
    success_count = 0
    total_count = len(resources)
    
    for resource in resources:
        try:
            start_time = time.time()
            response = requests.get(f"{base_url}{resource}", timeout=5)
            end_time = time.time()
            
            if response.status_code == 200:
                print(f"✅ {resource} - 加载成功 ({(end_time - start_time)*1000:.1f}ms)")
                success_count += 1
            else:
                print(f"❌ {resource} - 加载失败 (状态码: {response.status_code})")
                
        except Exception as e:
            print(f"❌ {resource} - 加载失败 (错误: {str(e)})")
    
    print("=" * 50)
    print(f"测试完成: {success_count}/{total_count} 个资源加载成功")
    
    if success_count == total_count:
        print("🎉 所有本地资源加载正常！")
    else:
        print("⚠️  部分资源加载失败，请检查文件路径")

if __name__ == "__main__":
    test_local_resources() 