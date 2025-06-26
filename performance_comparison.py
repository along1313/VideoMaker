#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能对比测试：本地资源 vs CDN资源
"""

import requests
import time
import statistics

def test_load_time(url, name, iterations=3):
    """测试资源加载时间"""
    times = []
    
    for i in range(iterations):
        try:
            start_time = time.time()
            response = requests.get(url, timeout=10)
            end_time = time.time()
            
            if response.status_code == 200:
                load_time = (end_time - start_time) * 1000  # 转换为毫秒
                times.append(load_time)
                print(f"  {i+1}. {load_time:.1f}ms")
            else:
                print(f"  {i+1}. 失败 (状态码: {response.status_code})")
                
        except Exception as e:
            print(f"  {i+1}. 失败 (错误: {str(e)})")
    
    if times:
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        print(f"  📊 平均: {avg_time:.1f}ms, 最小: {min_time:.1f}ms, 最大: {max_time:.1f}ms")
        return avg_time
    else:
        print(f"  📊 所有测试都失败了")
        return None

def performance_comparison():
    """性能对比测试"""
    print("🚀 开始性能对比测试：本地资源 vs CDN资源")
    print("=" * 60)
    
    # 测试资源列表 (本地 vs CDN)
    test_resources = [
        {
            "name": "Vue.js",
            "local": "http://localhost:5002/static/vendor/vue/vue.min.js",
            "cdn": "https://cdn.jsdelivr.net/npm/vue@2.6.14/dist/vue.min.js"
        },
        {
            "name": "Element UI CSS",
            "local": "http://localhost:5002/static/vendor/element-ui/index.css",
            "cdn": "https://cdn.jsdelivr.net/npm/element-ui@2.15.10/lib/theme-chalk/index.css"
        },
        {
            "name": "Element UI JS",
            "local": "http://localhost:5002/static/vendor/element-ui/index.js",
            "cdn": "https://cdn.jsdelivr.net/npm/element-ui@2.15.10/lib/index.js"
        },
        {
            "name": "Axios",
            "local": "http://localhost:5002/static/vendor/axios/axios.min.js",
            "cdn": "https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"
        },
        {
            "name": "Font Awesome",
            "local": "http://localhost:5002/static/vendor/font-awesome/css/all.min.css",
            "cdn": "https://cdn.bootcdn.net/ajax/libs/font-awesome/5.15.4/css/all.min.css"
        }
    ]
    
    results = []
    
    for resource in test_resources:
        print(f"\n📦 测试 {resource['name']}:")
        print("-" * 40)
        
        print("🏠 本地资源:")
        local_time = test_load_time(resource['local'], "本地")
        
        print("🌐 CDN资源:")
        cdn_time = test_load_time(resource['cdn'], "CDN")
        
        if local_time and cdn_time:
            improvement = ((cdn_time - local_time) / cdn_time) * 100
            results.append({
                "name": resource['name'],
                "local": local_time,
                "cdn": cdn_time,
                "improvement": improvement
            })
            print(f"📈 性能提升: {improvement:.1f}%")
        elif local_time:
            print("📈 本地资源可用，CDN资源失败")
        elif cdn_time:
            print("📉 本地资源失败，CDN资源可用")
        else:
            print("❌ 两种资源都失败")
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 性能对比总结:")
    print("=" * 60)
    
    if results:
        total_local = sum(r['local'] for r in results)
        total_cdn = sum(r['cdn'] for r in results)
        total_improvement = ((total_cdn - total_local) / total_cdn) * 100
        
        print(f"🏠 本地资源总加载时间: {total_local:.1f}ms")
        print(f"🌐 CDN资源总加载时间: {total_cdn:.1f}ms")
        print(f"📈 总体性能提升: {total_improvement:.1f}%")
        
        print(f"\n📋 详细对比:")
        for result in results:
            print(f"  {result['name']}: 本地 {result['local']:.1f}ms vs CDN {result['cdn']:.1f}ms (提升 {result['improvement']:.1f}%)")
        
        if total_improvement > 0:
            print(f"\n🎉 本地资源加载速度更快！")
        else:
            print(f"\n⚠️  CDN资源加载速度更快")
    else:
        print("❌ 没有可用的测试结果")

if __name__ == "__main__":
    performance_comparison() 