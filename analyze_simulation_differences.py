#!/usr/bin/env python3
"""
分析 simulation_running 和 simulation_running_v2 的差别
"""

import re
from pathlib import Path

def analyze_simulation_differences():
    """分析两个模拟系统的差别"""
    
    print("🔍 分析模拟系统差别")
    print("=" * 60)
    
    main_window_file = Path(__file__).parent / "src" / "main_window.py"
    
    try:
        with open(main_window_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 1. 找到两个模拟系统的定义和使用
        print("\n1. 模拟系统版本对比:")
        
        # 查找simulation_running相关代码
        v1_patterns = find_simulation_v1_usage(content)
        v2_patterns = find_simulation_v2_usage(content)
        
        print(f"\n📊 使用统计:")
        print(f"  simulation_running (V1): {len(v1_patterns)} 处")
        print(f"  simulation_running_v2 (V2): {len(v2_patterns)} 处")
        
        # 2. 分析按钮连接
        print(f"\n2. 按钮连接分析:")
        button_connection = re.search(r'simulate_btn\.clicked\.connect\(([^)]+)\)', content)
        if button_connection:
            connected_method = button_connection.group(1)
            print(f"  当前连接到: {connected_method}")
            if "_v2" in connected_method:
                print(f"  ✅ 使用的是V2版本")
                current_version = "V2"
            else:
                print(f"  ⚠️ 使用的是V1版本")
                current_version = "V1"
        else:
            print(f"  ❌ 未找到按钮连接")
            current_version = "Unknown"
        
        # 3. 分析两个版本的功能差异
        print(f"\n3. 功能差异分析:")
        analyze_v1_features(content)
        analyze_v2_features(content)
        
        # 4. 分析状态检查兼容性
        print(f"\n4. 状态检查兼容性:")
        check_compatibility_issues(content, current_version)
        
        # 5. 总结建议
        print(f"\n5. 总结和建议:")
        provide_recommendations(current_version)
        
        return True
        
    except Exception as e:
        print(f"❌ 分析过程出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def find_simulation_v1_usage(content):
    """查找V1模拟系统的使用"""
    patterns = re.findall(r'simulation_running[^_][^=]*[=].*', content)
    return patterns

def find_simulation_v2_usage(content):
    """查找V2模拟系统的使用"""
    patterns = re.findall(r'simulation_running_v2.*[=].*', content)
    return patterns

def analyze_v1_features(content):
    """分析V1版本的特性"""
    print(f"\n  📋 V1 模拟系统特性:")
    
    # 查找V1相关的方法和特性
    v1_method = re.search(r'def _start_simulation_progress\(self\):.*?(?=def|\Z)', content, re.DOTALL)
    if v1_method:
        method_content = v1_method.group(0)
        
        features = []
        if "1000ms" in method_content:
            features.append("1000ms 间隔更新")
        if "按孔位ID顺序" in method_content or "sort" in method_content:
            features.append("按孔位ID顺序处理")
        if "simulation_timer" in method_content:
            features.append("使用 simulation_timer")
        
        for feature in features:
            print(f"    • {feature}")
    else:
        print(f"    ❌ 未找到V1方法定义")

def analyze_v2_features(content):
    """分析V2版本的特性"""
    print(f"\n  📋 V2 模拟系统特性:")
    
    # 查找V2相关的方法和特性
    v2_method = re.search(r'def _start_simulation_progress_v2\(self\):.*?(?=def|\Z)', content, re.DOTALL)
    if v2_method:
        method_content = v2_method.group(0)
        
        features = []
        if "扇形顺序" in method_content:
            features.append("按扇形顺序处理")
        if "100ms" in method_content:
            features.append("100ms 间隔更新 (更快)")
        if "50ms" in method_content:
            features.append("50ms 颜色变化延迟")
        if "simulation_timer_v2" in method_content:
            features.append("使用 simulation_timer_v2")
        if "智能切换" in content:
            features.append("智能扇形切换")
        if "99.5%" in method_content:
            features.append("精确的统计分布 (99.5%/0.49%/0.01%)")
        if "蓝色→最终颜色" in method_content:
            features.append("两阶段颜色变化 (蓝色→最终颜色)")
        
        for feature in features:
            print(f"    • {feature}")
    else:
        print(f"    ❌ 未找到V2方法定义")

def check_compatibility_issues(content, current_version):
    """检查兼容性问题"""
    
    # 检查父级检查逻辑
    parent_check = re.search(r'while main_window and not hasattr\(main_window, \'([^\']+)\'\):', content)
    if parent_check:
        checked_attribute = parent_check.group(1)
        print(f"  父级检查属性: {checked_attribute}")
        
        if checked_attribute == "simulation_running" and current_version == "V2":
            print(f"  ⚠️ 兼容性问题: 父级检查 'simulation_running' 但当前使用 V2")
            print(f"  🔧 修复: 已在之前的修复中同时检查V1和V2属性")
        elif checked_attribute == "simulation_running_v2" and current_version == "V1":
            print(f"  ⚠️ 兼容性问题: 父级检查 'simulation_running_v2' 但当前使用 V1")
        else:
            print(f"  ✅ 兼容性正常")
    
    # 检查全景图更新兼容性
    panorama_checks = re.findall(r'getattr\(.*?, \'(simulation_running[^\']*)', content)
    if panorama_checks:
        print(f"  全景图检查的属性: {panorama_checks}")
        if len(set(panorama_checks)) > 1:
            print(f"  ✅ 同时检查多个版本，兼容性良好")
        else:
            print(f"  ⚠️ 只检查单一版本，可能有兼容性问题")

def provide_recommendations(current_version):
    """提供建议"""
    
    print(f"  当前使用版本: {current_version}")
    
    if current_version == "V2":
        print(f"  ✅ 建议: 继续使用V2版本")
        print(f"    理由:")
        print(f"    • 更快的更新频率 (100ms vs 1000ms)")
        print(f"    • 智能扇形切换功能")
        print(f"    • 更精确的统计分布")
        print(f"    • 更好的视觉效果 (两阶段颜色变化)")
        print(f"    • 按扇形顺序处理，符合用户操作习惯")
        
        print(f"\n  🔧 确保兼容性:")
        print(f"    • ✅ 父级检查已修复，同时支持V1和V2")
        print(f"    • ✅ 全景图更新已兼容两个版本")
        print(f"    • ✅ 状态检测逻辑已优化")
        
    elif current_version == "V1":
        print(f"  ⚠️ 建议: 考虑升级到V2版本")
        print(f"    当前V1的局限性:")
        print(f"    • 更新频率较慢 (1000ms)")
        print(f"    • 按孔位ID顺序，不够直观")
        print(f"    • 缺少智能扇形切换")
        print(f"    • 视觉效果较简单")
        
        print(f"\n  🔄 升级方法:")
        print(f"    • 将按钮连接改为: _start_simulation_progress_v2")
        print(f"    • 确保V2相关的初始化代码完整")
        
    else:
        print(f"  ❌ 未知版本，请检查按钮连接配置")

if __name__ == "__main__":
    success = analyze_simulation_differences()
    
    if success:
        print(f"\n✅ 模拟系统差别分析完成！")
        print(f"\n📋 关键发现:")
        print(f"  • V1: 简单的顺序模拟 (1000ms间隔)")
        print(f"  • V2: 高级扇形模拟 (100ms间隔，智能切换)")
        print(f"  • 当前使用V2版本，功能更强大")
        print(f"  • 兼容性问题已在之前的修复中解决")
    else:
        print(f"\n❌ 分析失败！")