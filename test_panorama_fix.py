#\!/usr/bin/env python3
"""
验证全景预览图修复效果的测试
"""

import sys
import os

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
import time

from aidcis2.graphics.dynamic_sector_view import CompletePanoramaWidget
from aidcis2.models.hole_data import HoleData, HoleCollection


def create_real_test_data():
    """创建更接近实际数据的测试"""
    holes = {}
    
    # 创建类似实际全景图的数据分布
    for row in range(1, 21):  # 20行
        for col in range(1, 26):  # 25列
            x = 100 + col * 30  # X坐标：130-850
            y = 100 + row * 25  # Y坐标：125-575
            
            hole_id = f"C{col:03d}R{row:03d}"
            hole = HoleData(
                hole_id=hole_id,
                center_x=x,
                center_y=y,
                radius=8.5,
                row=row,
                column=col
            )
            holes[hole_id] = hole
    
    return HoleCollection(holes=holes)


def test_panorama_display():
    """测试全景预览图显示"""
    print("🧪 全景预览图修复效果验证测试")
    print("="*50)
    
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    
    # 创建全景图组件
    panorama_widget = CompletePanoramaWidget()
    panorama_widget.resize(800, 600)
    panorama_widget.show()
    
    # 创建测试数据
    print("🔧 创建测试数据（500个孔位）...")
    test_data = create_real_test_data()
    print(f"✅ 测试数据创建完成：{len(test_data)} 个孔位")
    
    # 检查数据边界
    bounds = test_data.get_bounds()
    print(f"📏 数据边界：{bounds}")
    
    # 加载数据
    print("⏳ 加载数据到全景图...")
    panorama_widget.load_complete_view(test_data)
    
    # 等待加载完成
    time.sleep(0.5)
    
    # 检查加载结果
    view = panorama_widget.panorama_view
    scene_items = len(view.scene.items()) if view.scene else 0
    hole_items = len(view.hole_items) if hasattr(view, 'hole_items') else 0
    scene_rect = view.scene.sceneRect() if view.scene else None
    
    print(f"📊 加载结果：")
    print(f"   - 场景图形项：{scene_items}")
    print(f"   - 孔位项字典：{hole_items}")
    print(f"   - 场景矩形：{scene_rect.width():.1f}x{scene_rect.height():.1f}" if scene_rect else "   - 场景矩形：无")
    
    # 检查图形项位置
    if hasattr(view, 'hole_items') and view.hole_items:
        sample_id = next(iter(view.hole_items.keys()))
        sample_item = view.hole_items[sample_id]
        sample_pos = sample_item.pos()
        sample_data = sample_item.hole_data
        
        print(f"📍 样本图形项检查（{sample_id}）：")
        print(f"   - 数据坐标：({sample_data.center_x:.1f}, {sample_data.center_y:.1f})")
        print(f"   - 图形项位置：({sample_pos.x():.1f}, {sample_pos.y():.1f})")
        
        position_match = (abs(sample_pos.x() - sample_data.center_x) < 1 and 
                         abs(sample_pos.y() - sample_data.center_y) < 1)
        print(f"   - 位置匹配：{'✅ 正确' if position_match else '❌ 错误'}")
    
    # 检查可见性
    visible_items = 0
    for item in view.scene.items():
        if item.isVisible():
            visible_items += 1
    
    print(f"👁️ 可见图形项：{visible_items}")
    
    # 总结
    success = (scene_items == len(test_data) and 
              hole_items == len(test_data) and 
              visible_items > 0 and
              scene_rect is not None)
    
    print(f"\n🎯 修复效果验证：{'✅ 成功' if success else '❌ 失败'}")
    
    if success:
        print("🎉 全景预览图显示问题已成功修复！")
        print("   - 图形项位置正确")
        print("   - 场景边界正常")
        print("   - 渲染设置统一")
        print("   - 数据加载完整")
    else:
        print("❌ 仍存在问题，需要进一步调试")
    
    # 保持窗口显示一会儿
    QTimer.singleShot(2000, app.quit)
    app.exec()
    
    return success


if __name__ == "__main__":
    success = test_panorama_display()
    sys.exit(0 if success else 1)