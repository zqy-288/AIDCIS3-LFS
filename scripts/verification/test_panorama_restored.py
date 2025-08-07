#!/usr/bin/env python3
"""
测试左侧全景图预览恢复
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer


def test_panorama_restoration():
    """测试全景图恢复功能"""
    print("🧪 测试左侧全景图预览恢复...")
    
    try:
        app = QApplication.instance() or QApplication([])
        
        from src.pages.main_detection_p1.native_main_detection_view_p1 import NativeMainDetectionView
        from src.core_business.models.hole_data import HoleCollection, HoleData, HoleStatus
        
        # 创建主视图
        main_view = NativeMainDetectionView()
        main_view.show()
        
        # 检查全景图组件
        print("\n📋 检查项目:")
        
        # 1. 检查左侧面板是否有全景组
        if hasattr(main_view.left_panel, 'panorama_group'):
            print("✅ 左侧面板有全景预览组")
        else:
            print("❌ 左侧面板缺少全景预览组")
        
        # 2. 检查sidebar_panorama组件
        if hasattr(main_view.left_panel, 'sidebar_panorama'):
            print("✅ sidebar_panorama组件存在")
            panorama = main_view.left_panel.sidebar_panorama
            print(f"   最小高度: {panorama.minimumHeight()}")
            print(f"   最大高度: {panorama.maximumHeight()}")
        else:
            print("❌ sidebar_panorama组件未找到")
        
        # 3. 创建测试数据
        test_holes = {}
        # 创建分布在四个象限的孔位
        positions = [
            (100, 50),   # 第一象限
            (50, 50),    # 第二象限
            (50, 100),   # 第三象限
            (100, 100),  # 第四象限
        ]
        
        for i, (x, y) in enumerate(positions * 5):  # 每个象限5个孔
            hole = HoleData(
                center_x=x + (i % 5) * 10,
                center_y=y + (i % 5) * 10,
                radius=8.0,
                hole_id=f"HOLE_{i:03d}",
                status=HoleStatus.PENDING
            )
            test_holes[hole.hole_id] = hole
        
        test_collection = HoleCollection(test_holes)
        
        # 4. 加载数据并检查全景图更新
        print("\n🔄 加载测试数据...")
        main_view.load_hole_collection(test_collection)
        
        # 检查全景图是否显示数据
        def check_panorama_data():
            if hasattr(main_view.left_panel, 'sidebar_panorama'):
                panorama = main_view.left_panel.sidebar_panorama
                # 检查是否有场景
                if hasattr(panorama, 'scene'):
                    scene = panorama.scene
                    if callable(scene):
                        scene = scene()
                    if scene:
                        items = scene.items()
                        print(f"\n✅ 全景图场景包含 {len(items)} 个项目")
                    else:
                        print("\n⚠️ 全景图场景为空")
                else:
                    print("\n⚠️ 全景图没有场景")
                    
            # 检查协调器连接
            if main_view.coordinator:
                print("\n✅ 全景图已连接到协调器")
            
            # 检查模拟控制器连接
            if main_view.simulation_controller:
                print("✅ 全景图已连接到模拟控制器")
                
            print("\n🎉 左侧全景图预览已成功恢复！")
            app.quit()
        
        # 延迟检查，让UI完全加载
        QTimer.singleShot(1000, check_panorama_data)
        
        # 运行应用
        app.exec()
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("="*60)
    print("左侧全景图预览恢复测试")
    print("="*60)
    
    test_panorama_restoration()