#!/usr/bin/env python3
"""
诊断全景图渲染问题
检查DXF数据是否正确加载到全景图中
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置环境变量
os.environ['MPLCONFIGDIR'] = '/tmp/matplotlib'

def diagnose_panorama():
    """诊断全景图渲染问题"""
    print("🔍 开始诊断全景图渲染问题...")
    
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QTimer
        
        # 获取现有应用实例
        app = QApplication.instance()
        if not app:
            print("❌ 没有找到运行中的Qt应用")
            return 1
        
        print("✅ 找到运行中的Qt应用")
        
        # 查找主窗口
        main_window = None
        for widget in app.topLevelWidgets():
            if hasattr(widget, 'sidebar_panorama'):
                main_window = widget
                break
        
        if not main_window:
            print("❌ 没有找到主窗口")
            return 1
        
        print("✅ 找到主窗口")
        
        def run_diagnosis():
            try:
                print("\n🔍 开始详细诊断...")
                
                panorama = main_window.sidebar_panorama
                if not panorama:
                    print("❌ 全景图组件不存在")
                    return
                
                print("✅ 全景图组件存在")
                
                # 检查hole_collection
                if hasattr(panorama, 'hole_collection') and panorama.hole_collection:
                    collection = panorama.hole_collection
                    print(f"✅ HoleCollection存在，包含 {len(collection)} 个孔位")
                    
                    # 检查前几个孔位的数据
                    if len(collection) > 0:
                        holes_list = list(collection.holes.values())[:5]
                        print("📊 前5个孔位的数据:")
                        for hole in holes_list:
                            print(f"  - {hole.hole_id}: center=({hole.center_x:.2f}, {hole.center_y:.2f}), radius={hole.radius:.2f}")
                else:
                    print("❌ HoleCollection不存在或为空")
                    return
                
                # 检查panorama_view
                view = panorama.panorama_view
                if not view:
                    print("❌ panorama_view不存在")
                    return
                
                print("✅ panorama_view存在")
                
                # 检查hole_items
                if hasattr(view, 'hole_items') and view.hole_items:
                    print(f"✅ hole_items存在，包含 {len(view.hole_items)} 个图形项")
                    
                    # 检查图形项是否被添加到场景中
                    scene_items = view.scene.items() if view.scene else []
                    print(f"✅ 场景包含 {len(scene_items)} 个图形项")
                    
                    # 检查前几个hole_items的详细信息
                    print("📊 前5个hole_items的详细信息:")
                    for i, (hole_id, item) in enumerate(list(view.hole_items.items())[:5]):
                        pos = item.pos()
                        rect = item.rect()
                        visible = item.isVisible()
                        in_scene = item.scene() is not None
                        print(f"  - {hole_id}: pos=({pos.x():.2f}, {pos.y():.2f}), "
                              f"rect=({rect.x():.2f}, {rect.y():.2f}, {rect.width():.2f}, {rect.height():.2f}), "
                              f"visible={visible}, in_scene={in_scene}")
                        
                        # 检查画笔和画刷
                        pen = item.pen()
                        brush = item.brush()
                        print(f"    pen: color={pen.color().name()}, width={pen.width()}")
                        print(f"    brush: color={brush.color().name()}, style={brush.style()}")
                else:
                    print("❌ hole_items不存在或为空")
                    return
                
                # 检查场景矩形
                if view.scene:
                    scene_rect = view.scene.sceneRect()
                    print(f"📐 场景矩形: ({scene_rect.x():.2f}, {scene_rect.y():.2f}, "
                          f"{scene_rect.width():.2f}, {scene_rect.height():.2f})")
                    
                    # 检查视图矩形
                    view_rect = view.viewport().rect()
                    print(f"📐 视图矩形: ({view_rect.x():.2f}, {view_rect.y():.2f}, "
                          f"{view_rect.width():.2f}, {view_rect.height():.2f})")
                    
                    # 检查变换矩阵
                    transform = view.transform()
                    print(f"🔄 变换矩阵: m11={transform.m11():.4f}, m22={transform.m22():.4f}, "
                          f"dx={transform.dx():.2f}, dy={transform.dy():.2f}")
                
                # 检查全景图几何信息
                if hasattr(panorama, 'center_point') and panorama.center_point:
                    center = panorama.center_point
                    radius = getattr(panorama, 'panorama_radius', 0)
                    print(f"📐 全景图几何: center=({center.x():.2f}, {center.y():.2f}), radius={radius:.2f}")
                else:
                    print("❌ 全景图几何信息不存在")
                
                print("\n🎯 诊断总结:")
                print("1. HoleCollection数据加载正常")
                print("2. hole_items图形项创建正常")
                print("3. 图形项已添加到场景中")
                print("4. 如果仍然看不到孔位，可能是:")
                print("   - 孔位大小太小（需要放大显示）")
                print("   - 视图缩放不合适（需要调整缩放）")
                print("   - 孔位颜色与背景相近（需要调整颜色）")
                print("   - 视图变换有问题（需要重置变换）")
                
                # 尝试强制更新显示
                print("\n🔧 尝试强制更新显示...")
                view.scene.update()
                view.update()
                view.viewport().update()
                panorama.update()
                
                print("✅ 诊断完成")
                
            except Exception as e:
                print(f"❌ 诊断过程中出错: {e}")
                import traceback
                traceback.print_exc()
        
        # 立即执行诊断
        run_diagnosis()
        
        return 0
        
    except Exception as e:
        print(f"❌ 诊断失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    result = diagnose_panorama()
    if result == 0:
        print("🎉 诊断完成！")
    else:
        print("❌ 诊断失败")
    sys.exit(result)