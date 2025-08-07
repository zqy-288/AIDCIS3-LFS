#!/usr/bin/env python3
"""
调试全景显示问题
检查左侧全景预览为什么显示空白
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
import logging

# 设置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_panorama_widget():
    """测试全景组件的加载"""
    app = QApplication(sys.argv)
    
    try:
        # 导入组件
        from src.pages.main_detection_p1.components.graphics.complete_panorama_widget import CompletePanoramaWidget
        from src.core_business.models.hole_data import HoleCollection
        
        print("✅ 导入成功")
        
        # 创建组件
        widget = CompletePanoramaWidget()
        widget.setFixedSize(360, 420)
        print("✅ 组件创建成功")
        
        # 创建测试数据
        from src.pages.main_detection_p1.services.dxf_loader_service import DXFLoaderService
        loader = DXFLoaderService()
        
        # 检查CAP1000.dxf文件
        dxf_file = project_root / "Data/Products/CAP1000/dxf/CAP1000.dxf"
        if dxf_file.exists():
            print(f"✅ 找到DXF文件: {dxf_file}")
            hole_collection = loader.load_dxf_file(str(dxf_file))
            
            if hole_collection and len(hole_collection) > 0:
                print(f"✅ 加载了 {len(hole_collection)} 个孔位")
                
                # 测试加载数据到全景组件
                widget.load_hole_collection(hole_collection)
                print("✅ 数据已加载到全景组件")
                
                # 显示组件测试
                widget.show()
                print("✅ 组件已显示")
                
                # 运行几秒钟然后退出
                QTimer.singleShot(3000, app.quit)
                app.exec()
                
            else:
                print("❌ 没有加载到孔位数据")
        else:
            print(f"❌ 找不到DXF文件: {dxf_file}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_panorama_widget()