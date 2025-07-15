#!/usr/bin/env python3
"""修复全景图交互问题"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'src'))

from PySide6.QtWidgets import QApplication
from main_window import MainWindow
from aidcis2.dxf_parser import DXFParser
import time

def diagnose_panorama_interaction():
    app = QApplication(sys.argv)
    
    # 创建主窗口
    main_window = MainWindow()
    
    # 加载DXF文件
    dxf_path = "/Users/vsiyo/Desktop/AIDCIS/AIDCIS3-LFS/assets/dxf/DXF Graph/东重管板.dxf"
    parser = DXFParser()
    hole_collection = parser.parse_file(dxf_path)
    
    if hole_collection:
        print(f"📊 加载了 {len(hole_collection.holes)} 个孔位")
        
        # 设置到主窗口
        main_window.hole_collection = hole_collection
        main_window.update_hole_display()
        
        # 显示主窗口
        main_window.show()
        
        # 等待界面更新
        app.processEvents()
        time.sleep(1)
        
        # 诊断全景图状态
        print("\n=== 全景图诊断 ===")
        
        if hasattr(main_window, 'sidebar_panorama'):
            panorama = main_window.sidebar_panorama
            print(f"✅ 找到 sidebar_panorama")
            
            # 检查基本属性
            print(f"- hole_collection: {panorama.hole_collection is not None}")
            print(f"- center_point: {panorama.center_point}")
            print(f"- panorama_radius: {getattr(panorama, 'panorama_radius', 'N/A')}")
            
            # 检查信息标签
            if hasattr(panorama, 'info_label'):
                print(f"- info_label 文本: '{panorama.info_label.text()}'")
                print(f"- info_label 可见: {panorama.info_label.isVisible()}")
            
            # 检查事件过滤器
            if hasattr(panorama, 'panorama_view'):
                print(f"- panorama_view 存在: ✅")
                filters = panorama.panorama_view.viewport().findChildren(object)
                print(f"- 事件过滤器数量: {len(filters)}")
            
            # 尝试清除高亮
            print("\n尝试清除高亮...")
            try:
                panorama.clear_highlight()
                print("✅ 清除高亮成功")
            except Exception as e:
                print(f"❌ 清除高亮失败: {e}")
            
            # 手动设置 hole_collection（如果需要）
            if panorama.hole_collection is None:
                print("\n⚠️ hole_collection 为 None，尝试手动设置...")
                panorama.hole_collection = hole_collection
                print("✅ 已手动设置 hole_collection")
        
        else:
            print("❌ 未找到 sidebar_panorama")
        
        print("\n=== 诊断完成 ===")
        print("请尝试点击全景图的不同扇形区域")
        print("观察控制台输出是否有点击事件响应")
        
        return app.exec()
    else:
        print("❌ 无法加载DXF文件")
        return 1

if __name__ == "__main__":
    sys.exit(diagnose_panorama_interaction())