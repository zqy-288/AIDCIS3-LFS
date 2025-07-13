#!/usr/bin/env python3
"""
调试模拟进度颜色问题
"""

import sys
import logging
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def debug_simulation_colors():
    """调试模拟进度颜色问题"""
    print("🔍 调试模拟进度颜色问题")
    print("=" * 50)
    
    # 1. 检查当前运行的是哪个main_window.py
    try:
        import main_window.main_window as main_window
        main_window_file = main_window.__file__
        print(f"✅ 当前使用的main_window.py: {main_window_file}")
        
        # 检查文件修改时间
        import os
        mtime = os.path.getmtime(main_window_file)
        import datetime
        mod_time = datetime.datetime.fromtimestamp(mtime)
        print(f"📅 文件修改时间: {mod_time}")
        
    except Exception as e:
        print(f"❌ 检查main_window失败: {e}")
        return False
    
    # 2. 检查模拟进度方法是否包含最新修复
    try:
        from main_window.main_window import MainWindow
        import inspect
        
        # 检查_update_simulation_progress方法
        method = getattr(MainWindow, '_update_simulation_progress', None)
        if method:
            source = inspect.getsource(method)
            
            # 检查关键修复点
            fixes_found = []
            
            if "QTimer.singleShot" in source:
                fixes_found.append("✅ 延迟更新机制")
            else:
                fixes_found.append("❌ 缺少延迟更新机制")
            
            if "hole_item = self.graphics_view.hole_items" in source:
                fixes_found.append("✅ 统一图形项引用")
            else:
                fixes_found.append("❌ 缺少统一图形项引用")
            
            if "update_final_status" in source:
                fixes_found.append("✅ 最终状态更新函数")
            else:
                fixes_found.append("❌ 缺少最终状态更新函数")
            
            if "🎨 最终颜色变化" in source:
                fixes_found.append("✅ 详细颜色日志")
            else:
                fixes_found.append("❌ 缺少详细颜色日志")
            
            print("\n🔧 模拟进度方法检查:")
            for fix in fixes_found:
                print(f"  {fix}")
            
            # 如果缺少关键修复，说明可能运行的是旧版本
            missing_fixes = [f for f in fixes_found if f.startswith("❌")]
            if missing_fixes:
                print(f"\n⚠️ 发现 {len(missing_fixes)} 个缺失的修复")
                print("可能原因:")
                print("1. 程序缓存了旧版本的代码")
                print("2. 运行的不是最新修改的文件")
                print("3. Python模块缓存问题")
                return False
            else:
                print("\n✅ 所有关键修复都已存在")
        
    except Exception as e:
        print(f"❌ 检查模拟进度方法失败: {e}")
        return False
    
    # 3. 检查图形项的颜色映射
    try:
        from aidcis2.graphics.hole_item import HoleGraphicsItem
        from aidcis2.models.hole_data import HoleStatus
        
        print("\n🎨 检查颜色映射:")
        colors = HoleGraphicsItem.STATUS_COLORS
        
        key_statuses = [
            HoleStatus.PENDING,
            HoleStatus.PROCESSING, 
            HoleStatus.QUALIFIED,
            HoleStatus.DEFECTIVE
        ]
        
        for status in key_statuses:
            if status in colors:
                color = colors[status]
                print(f"  ✅ {status.value}: {color.name()}")
            else:
                print(f"  ❌ {status.value}: 缺少颜色映射")
        
    except Exception as e:
        print(f"❌ 检查颜色映射失败: {e}")
        return False
    
    # 4. 提供解决方案
    print("\n🔧 解决方案:")
    print("1. 重启Python解释器清除缓存")
    print("2. 删除__pycache__目录")
    print("3. 确认运行的是正确的main.py文件")
    print("4. 检查是否有多个版本的代码")
    
    return True

def clear_python_cache():
    """清除Python缓存"""
    print("\n🧹 清除Python缓存...")
    
    import shutil
    import os
    
    # 删除__pycache__目录
    cache_dirs = []
    for root, dirs, files in os.walk('.'):
        for dir_name in dirs:
            if dir_name == '__pycache__':
                cache_dirs.append(os.path.join(root, dir_name))
    
    for cache_dir in cache_dirs:
        try:
            shutil.rmtree(cache_dir)
            print(f"✅ 删除缓存目录: {cache_dir}")
        except Exception as e:
            print(f"❌ 删除缓存目录失败 {cache_dir}: {e}")
    
    print(f"🧹 清除了 {len(cache_dirs)} 个缓存目录")

if __name__ == "__main__":
    success = debug_simulation_colors()
    
    if not success:
        print("\n🔧 尝试清除缓存...")
        clear_python_cache()
        print("\n💡 建议:")
        print("1. 重启终端")
        print("2. 重新运行 python main.py")
        print("3. 如果问题仍然存在，可能需要检查代码版本")
    else:
        print("\n✅ 代码检查通过，问题可能在运行时")
        print("💡 建议:")
        print("1. 确保点击了'测试颜色更新'按钮验证基础功能")
        print("2. 检查日志输出中是否有颜色变化信息")
        print("3. 尝试重新加载DXF文件")
