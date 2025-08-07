#!/usr/bin/env python3
"""
简化的扇形显示组件单元测试
专注于核心功能验证，避免复杂的GUI交互
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent / 'src'
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor

def test_sector_highlight_component():
    """测试扇形高亮组件的核心功能"""
    print("🔍 测试扇形高亮组件...")
    
    try:
        from pages.main_detection_p1.components.graphics.sector_highlight_item import SectorHighlightItem
        from core_business.graphics.sector_types import SectorQuadrant
        
        # 创建扇形高亮项
        center = QPointF(300, 300)
        radius = 200
        sector = list(SectorQuadrant)[0]  # 获取第一个扇形
        
        highlight_item = SectorHighlightItem(sector, center, radius)
        
        # 验证基本属性
        assert highlight_item.sector == sector, "扇形属性设置错误"
        assert highlight_item.center == center, "中心点设置错误"  
        assert highlight_item.radius == radius, "半径设置错误"
        assert highlight_item.isVisible() == True, "默认可见性设置错误"
        
        # 验证样式设置
        pen = highlight_item.pen()
        assert pen.width() == 2, "线宽设置错误"
        assert pen.color().alpha() > 0, "透明度设置错误"
        
        print("✅ 扇形高亮组件测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 扇形高亮组件测试失败: {e}")
        return False

def test_panorama_widget_component():
    """测试全景图组件的导入和基本创建"""
    print("🔍 测试全景图组件...")
    
    try:
        from pages.main_detection_p1.components.graphics.complete_panorama_widget import CompletePanoramaWidget
        
        # 创建全景图组件（不显示）
        panorama_widget = CompletePanoramaWidget()
        
        # 验证基本属性
        assert panorama_widget is not None, "全景图组件创建失败"
        assert hasattr(panorama_widget, '_create_sector_dividers'), "缺少分隔线创建方法"
        
        print("✅ 全景图组件测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 全景图组件测试失败: {e}")
        return False

def test_component_integration():
    """测试组件集成"""
    print("🔍 测试组件集成...")
    
    try:
        # 测试关键导入路径
        from pages.main_detection_p1.native_main_detection_view_p1 import NativeMainDetectionView
        
        # 验证导入成功
        assert NativeMainDetectionView is not None, "主检测视图导入失败"
        
        print("✅ 组件集成测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 组件集成测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 启动扇形显示组件单元测试")
    print("=" * 50)
    
    # 创建最小化的QApplication
    app = QApplication([])
    
    # 运行测试
    tests = [
        ("扇形高亮组件", test_sector_highlight_component),
        ("全景图组件", test_panorama_widget_component),
        ("组件集成", test_component_integration),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 运行测试: {test_name}")
        success = test_func()
        results.append((test_name, success))
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 单元测试总结:")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
    
    if passed == total:
        print(f"\n🎉 所有 {total} 项测试通过!")
        print("✅ 扇形显示组件已正确修复")
        print("💡 建议: 运行主程序验证视觉效果")
    else:
        failed = total - passed
        print(f"\n⚠️ {failed}/{total} 项测试失败")
        print("建议检查相关组件")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)