"""
内窥镜管理器使用示例
演示如何正确设置批次上下文和孔位信息
"""

import sys
from pathlib import Path

# 添加项目根路径
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.pages.realtime_monitoring_p2.components.endoscope.endoscope_manager import EndoscopeManager
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
import logging

# 设置日志
logging.basicConfig(level=logging.DEBUG)

def example_usage():
    """示例：内窥镜图像保存到标准路径结构"""
    
    app = QApplication(sys.argv)
    
    # 创建内窥镜管理器
    endoscope_manager = EndoscopeManager()
    
    # 方法1: 自动获取当前批次上下文（推荐）
    print("尝试自动获取当前批次上下文...")
    if endoscope_manager.refresh_batch_context():
        print("✅ 自动获取批次上下文成功")
    else:
        print("⚠️ 自动获取失败，使用手动设置")
        # 方法2: 手动设置批次上下文（备用方案）
        product_id = "CAP1000"
        batch_id = "CAP1000_检测035_20250805_145238_MOCK"
        print(f"手动设置批次上下文: {product_id}/{batch_id}")
        endoscope_manager.set_batch_context(product_id, batch_id)
    
    # 启用图像保存
    endoscope_manager.set_save_images(True)
    
    # 连接虚拟设备
    endoscope_manager.connect_device()
    
    # 设置当前检测孔位
    hole_id = "AC097R001"
    print(f"设置当前孔位: {hole_id}")
    endoscope_manager.set_current_hole(hole_id)
    
    # 开始采集（这会将图像保存到对应孔位的BISDM目录）
    # 路径示例: /Data/Products/CAP1000/InspectionBatches/CAP1000_检测035_20250805_145238_MOCK/HoleResults/AC097R001/BISDM/endoscope_images/
    print("开始图像采集...")
    endoscope_manager.start_acquisition()
    
    # 运行几秒钟进行演示
    def stop_demo():
        print("停止采集...")
        endoscope_manager.stop_acquisition()
        endoscope_manager.disconnect_device()
        
        # 显示状态信息
        status = endoscope_manager.get_status()
        print("最终状态:")
        for key, value in status.items():
            print(f"  {key}: {value}")
        
        app.quit()
    
    # 5秒后停止演示
    QTimer.singleShot(5000, stop_demo)
    
    print("演示运行中...")
    sys.exit(app.exec())

if __name__ == "__main__":
    example_usage()