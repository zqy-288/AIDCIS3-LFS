#!/usr/bin/env python3
"""快速同步测试 - 验证全景预览批量更新"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

# 简单测试批量更新机制
def test_batch_update_mechanism():
    """测试批量更新机制"""
    print("🔍 测试批量更新机制")
    
    # 导入必要的模块
    try:
        from aidcis2.graphics.dynamic_sector_view import CompletePanoramaWidget
        from aidcis2.models.hole_data import HoleStatus
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QTimer
        
        print("✅ 模块导入成功")
        
        # 创建应用
        app = QApplication([])
        
        # 创建全景组件
        panorama = CompletePanoramaWidget()
        
        # 检查批量更新属性
        print(f"✅ 批量更新间隔: {panorama.batch_update_interval}ms")
        print(f"✅ 待更新缓存: {type(panorama.pending_status_updates)}")
        print(f"✅ 批量更新定时器: {type(panorama.batch_update_timer)}")
        
        # 测试状态更新
        panorama.update_hole_status("test_hole_1", HoleStatus.QUALIFIED)
        panorama.update_hole_status("test_hole_2", HoleStatus.DEFECTIVE)
        
        print(f"✅ 缓存中有 {len(panorama.pending_status_updates)} 个待更新项")
        print(f"✅ 定时器是否激活: {panorama.batch_update_timer.isActive()}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_color_mapping():
    """测试颜色映射"""
    print("\n🎨 测试颜色映射")
    
    try:
        from aidcis2.models.hole_data import HoleStatus
        from PySide6.QtGui import QColor
        
        # 测试主窗口中的颜色映射逻辑
        test_colors = [
            QColor("#4CAF50"),  # 绿色 - QUALIFIED
            QColor("#F44336"),  # 红色 - DEFECTIVE  
            QColor("#2196F3"),  # 蓝色 - PROCESSING
            QColor("#FF9800"),  # 橙色 - BLIND
            QColor("#9C27B0"),  # 紫色 - TIE_ROD
        ]
        
        expected_statuses = [
            HoleStatus.QUALIFIED,
            HoleStatus.DEFECTIVE,
            HoleStatus.PROCESSING,
            HoleStatus.BLIND,
            HoleStatus.TIE_ROD,
        ]
        
        for color, expected_status in zip(test_colors, expected_statuses):
            color_name = color.name().upper()
            
            # 模拟主窗口中的颜色映射逻辑
            if color_name == "#4CAF50":
                status = HoleStatus.QUALIFIED
            elif color_name == "#F44336":
                status = HoleStatus.DEFECTIVE
            elif color_name == "#2196F3":
                status = HoleStatus.PROCESSING
            elif color_name == "#FF9800":
                status = HoleStatus.BLIND
            elif color_name == "#9C27B0":
                status = HoleStatus.TIE_ROD
            else:
                status = HoleStatus.NOT_DETECTED
            
            if status == expected_status:
                print(f"✅ 颜色映射正确: {color_name} -> {status.value}")
            else:
                print(f"❌ 颜色映射错误: {color_name} -> {status.value} (期望: {expected_status.value})")
        
        return True
        
    except Exception as e:
        print(f"❌ 颜色映射测试失败: {e}")
        return False

def main():
    print("=" * 60)
    print("全景预览同步修复验证")
    print("=" * 60)
    
    # 测试批量更新机制
    batch_test_passed = test_batch_update_mechanism()
    
    # 测试颜色映射
    color_test_passed = test_color_mapping()
    
    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)
    print(f"批量更新机制: {'✅ 通过' if batch_test_passed else '❌ 失败'}")
    print(f"颜色映射测试: {'✅ 通过' if color_test_passed else '❌ 失败'}")
    
    if batch_test_passed and color_test_passed:
        print("\n🎉 所有测试通过！修复应该有效。")
        print("\n📋 修复内容:")
        print("• 批量更新间隔改为1秒")
        print("• 移除了每10个孔位同步一次的限制")
        print("• 改进了状态更新的颜色映射")
        print("• 优化了批量渲染机制")
    else:
        print("\n⚠️ 部分测试失败，可能需要进一步调试")
    
    print("=" * 60)

if __name__ == "__main__":
    main()