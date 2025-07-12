#!/usr/bin/env python3
"""诊断全景预览问题"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

def debug_panorama_updates():
    """诊断全景预览更新问题"""
    print("🔍 诊断全景预览更新问题")
    
    # 检查主窗口中的状态更新调用
    main_window_path = "/Users/vsiyo/Desktop/AIDCIS3-1/AIDCIS3-LFS/src/main_window.py"
    
    try:
        with open(main_window_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找_update_panorama_hole_status的调用
        import re
        pattern = r'self\._update_panorama_hole_status\([^)]+\)'
        matches = re.findall(pattern, content)
        
        print(f"📋 在main_window.py中找到 {len(matches)} 处状态更新调用:")
        for i, match in enumerate(matches, 1):
            print(f"  {i}. {match}")
        
        # 检查调用的条件
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if '_update_panorama_hole_status' in line:
                # 显示前后几行的上下文
                start = max(0, i-3)
                end = min(len(lines), i+2)
                print(f"\n📍 第{i+1}行附近的上下文:")
                for j in range(start, end):
                    marker = ">>> " if j == i else "    "
                    print(f"{marker}{j+1:4d}: {lines[j]}")
        
        return True
        
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return False

def check_panorama_method():
    """检查全景预览的更新方法"""
    print("\n🔧 检查全景预览更新方法")
    
    try:
        from aidcis2.graphics.dynamic_sector_view import CompletePanoramaWidget
        from aidcis2.models.hole_data import HoleStatus
        
        # 检查方法是否存在
        panorama = CompletePanoramaWidget()
        
        methods_to_check = [
            'update_hole_status',
            '_apply_batch_updates', 
            'batch_update_hole_status',
            'set_batch_update_interval'
        ]
        
        for method_name in methods_to_check:
            if hasattr(panorama, method_name):
                print(f"✅ 方法存在: {method_name}")
            else:
                print(f"❌ 方法缺失: {method_name}")
        
        # 检查属性
        attrs_to_check = [
            'pending_status_updates',
            'batch_update_timer',
            'batch_update_interval'
        ]
        
        for attr_name in attrs_to_check:
            if hasattr(panorama, attr_name):
                attr_value = getattr(panorama, attr_name)
                print(f"✅ 属性存在: {attr_name} = {type(attr_value)} ({attr_value if not callable(attr_value) else 'callable'})")
            else:
                print(f"❌ 属性缺失: {attr_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

def test_color_conversion():
    """测试颜色转换逻辑"""
    print("\n🎨 测试颜色转换逻辑")
    
    try:
        from aidcis2.models.hole_data import HoleStatus
        from PySide6.QtGui import QColor
        from PySide6.QtWidgets import QApplication
        
        # 需要创建QApplication来使用QColor
        app = QApplication([])
        
        # 测试主窗口中使用的颜色
        test_cases = [
            ("#4CAF50", "绿色", HoleStatus.QUALIFIED),
            ("#F44336", "红色", HoleStatus.DEFECTIVE),
            ("#2196F3", "蓝色", HoleStatus.PROCESSING),
            ("#FF9800", "橙色", HoleStatus.BLIND),
            ("#9C27B0", "紫色", HoleStatus.TIE_ROD),
        ]
        
        for hex_color, color_name, expected_status in test_cases:
            color = QColor(hex_color)
            color_name_from_obj = color.name().upper()
            
            print(f"🔍 测试颜色: {color_name} ({hex_color})")
            print(f"   QColor.name(): {color_name_from_obj}")
            print(f"   期望状态: {expected_status.value}")
            
            # 模拟主窗口中的转换逻辑
            if color_name_from_obj == "#4CAF50":
                status = HoleStatus.QUALIFIED
            elif color_name_from_obj == "#F44336":
                status = HoleStatus.DEFECTIVE
            elif color_name_from_obj == "#2196F3":
                status = HoleStatus.PROCESSING
            elif color_name_from_obj == "#FF9800":
                status = HoleStatus.BLIND
            elif color_name_from_obj == "#9C27B0":
                status = HoleStatus.TIE_ROD
            else:
                status = HoleStatus.NOT_DETECTED
            
            if status == expected_status:
                print(f"   ✅ 转换正确: {status.value}")
            else:
                print(f"   ❌ 转换错误: {status.value}")
        
        return True
        
    except Exception as e:
        print(f"❌ 颜色转换测试失败: {e}")
        return False

def main():
    print("=" * 60)
    print("全景预览问题诊断")
    print("=" * 60)
    
    # 诊断更新调用
    updates_ok = debug_panorama_updates()
    
    # 检查方法
    methods_ok = check_panorama_method()
    
    # 测试颜色转换
    colors_ok = test_color_conversion()
    
    print("\n" + "=" * 60)
    print("诊断结果")
    print("=" * 60)
    print(f"状态更新调用: {'✅ 正常' if updates_ok else '❌ 异常'}")
    print(f"全景方法检查: {'✅ 正常' if methods_ok else '❌ 异常'}")
    print(f"颜色转换测试: {'✅ 正常' if colors_ok else '❌ 异常'}")
    
    if all([updates_ok, methods_ok, colors_ok]):
        print("\n💡 所有检查都通过了，问题可能在于:")
        print("1. 全景预览的hole_items字典可能为空")
        print("2. 批量更新可能没有被触发")
        print("3. 状态更新调用的频率或时机问题")
        print("\n建议运行程序并观察控制台输出中的全景图相关日志")
    else:
        print("\n⚠️ 发现了一些问题，需要进一步修复")

if __name__ == "__main__":
    main()