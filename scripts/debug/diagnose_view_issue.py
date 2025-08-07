#!/usr/bin/env python3
"""诊断中间视图无法显示内容的问题"""

import sys
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from src.pages.main_detection_p1.native_main_detection_view_p1 import NativeMainDetectionView
from src.core_business.models.hole_data import HoleCollection, HoleData, HoleStatus

def main():
    app = QApplication(sys.argv)
    
    # 创建视图
    view = NativeMainDetectionView()
    
    # 检查各组件是否正确初始化
    print("=== 组件初始化检查 ===")
    print(f"左侧面板: {view.left_panel is not None}")
    print(f"中间面板: {view.center_panel is not None}")
    print(f"右侧面板: {view.right_panel is not None}")
    
    if view.center_panel:
        print(f"中间面板.graphics_view: {hasattr(view.center_panel, 'graphics_view')}")
        if hasattr(view.center_panel, 'graphics_view'):
            gv = view.center_panel.graphics_view
            print(f"  - graphics_view 实例: {gv is not None}")
            print(f"  - graphics_view 类型: {type(gv)}")
            print(f"  - 有 load_holes 方法: {hasattr(gv, 'load_holes')}")
            print(f"  - 有 scene: {hasattr(gv, 'scene')}")
            if hasattr(gv, 'scene'):
                scene = gv.scene if not callable(gv.scene) else gv.scene()
                print(f"  - scene 实例: {scene is not None}")
                if scene:
                    print(f"  - scene 类型: {type(scene)}")
                    print(f"  - scene items 数量: {len(scene.items())}")
    
    # 创建测试数据
    print("\n=== 创建测试数据 ===")
    holes = {}
    for i in range(10):
        hole_id = f"TEST{i:03d}"
        hole = HoleData(
            hole_id=hole_id,
            center_x=100 + i * 50,
            center_y=100 + (i % 2) * 50,
            diameter=20,
            depth=10,
            type='normal',
            status=HoleStatus.PENDING
        )
        holes[hole_id] = hole
    
    collection = HoleCollection()
    collection.holes = holes
    print(f"创建了 {len(holes)} 个测试孔位")
    
    # 加载数据
    print("\n=== 加载数据测试 ===")
    try:
        view.load_hole_collection(collection)
        print("✅ load_hole_collection 调用成功")
    except Exception as e:
        print(f"❌ load_hole_collection 失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 再次检查场景
    if view.center_panel and hasattr(view.center_panel, 'graphics_view'):
        gv = view.center_panel.graphics_view
        if hasattr(gv, 'scene'):
            scene = gv.scene if not callable(gv.scene) else gv.scene()
            if scene:
                print(f"\n加载后 scene items 数量: {len(scene.items())}")
                
                # 列出前5个项
                items = scene.items()[:5]
                for i, item in enumerate(items):
                    print(f"  Item {i}: {type(item)}, pos=({item.x()}, {item.y()})")
    
    # 显示窗口
    view.show()
    
    print("\n=== 诊断完成 ===")
    print("窗口已显示，请检查中间区域是否有内容")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()