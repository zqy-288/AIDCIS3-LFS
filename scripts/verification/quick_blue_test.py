#!/usr/bin/env python3
"""
快速测试蓝色状态更新
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor
from src.core_business.models.hole_data import HoleStatus

def test_blue_status_update():
    """测试蓝色状态更新"""
    print("=== 开始测试蓝色状态更新 ===")
    
    # 导入主程序
    try:
        from src.pages.main_detection_p1.native_main_detection_view_p1 import NativeMainDetectionViewP1
        from PySide6.QtWidgets import QApplication
        
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
        
        # 创建主视图
        view = NativeMainDetectionViewP1()
        view.show()
        
        print("1. 主视图已创建")
        
        # 等待初始化完成
        def start_test():
            print("2. 开始测试...")
            
            # 检查是否有simulation_controller
            if hasattr(view, 'simulation_controller') and view.simulation_controller:
                controller = view.simulation_controller
                print("3. 找到simulation_controller")
                
                # 检查graphics_view
                if controller.graphics_view:
                    print("4. 找到graphics_view")
                    
                    # 手动测试一个孔位的颜色更新
                    test_hole_id = "BC100R001"  # 使用一个实际存在的孔位ID
                    
                    # 设置蓝色
                    print(f"5. 设置 {test_hole_id} 为蓝色...")
                    controller._update_hole_status(
                        test_hole_id, 
                        HoleStatus.PENDING,
                        color_override=QColor(33, 150, 243)
                    )
                    
                    # 2秒后清除蓝色
                    def clear_blue():
                        print(f"6. 清除 {test_hole_id} 的蓝色，设置为绿色...")
                        controller._update_hole_status(
                            test_hole_id,
                            HoleStatus.QUALIFIED,
                            color_override=None
                        )
                        print("7. 测试完成！请检查孔位是否变为绿色")
                    
                    QTimer.singleShot(2000, clear_blue)
                else:
                    print("错误：graphics_view 未找到")
            else:
                print("错误：simulation_controller 未找到")
        
        # 等待2秒后开始测试，确保初始化完成
        QTimer.singleShot(2000, start_test)
        
        # 运行应用
        app.exec()
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_blue_status_update()