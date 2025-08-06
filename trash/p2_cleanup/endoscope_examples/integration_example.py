"""
内窥镜管理器集成示例
展示在实际检测流程中如何集成内窥镜图像采集
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
logging.basicConfig(level=logging.INFO)

class DetectionWorkflow:
    """模拟检测工作流程"""
    
    def __init__(self):
        self.endoscope_manager = EndoscopeManager()
        self.current_holes = ["AC097R001", "AC097R002", "AC098R001", "AC098R002"]
        self.current_hole_index = 0
        
    def start_detection_batch(self):
        """开始检测批次"""
        print("🚀 开始检测批次...")
        
        # 第一步：尝试自动获取批次上下文
        print("1. 获取批次上下文...")
        if self.endoscope_manager.refresh_batch_context():
            print("   ✅ 自动获取批次上下文成功")
        else:
            print("   ⚠️ 自动获取失败，使用默认设置")
            # 模拟手动设置（实际应用中可能从用户界面或配置获取）
            self.endoscope_manager.set_batch_context(
                "CAP1000", 
                "CAP1000_检测037_20250805_160000_MOCK"
            )
        
        # 第二步：配置内窥镜采集
        print("2. 配置内窥镜采集...")
        self.endoscope_manager.set_save_images(True)
        self.endoscope_manager.connect_device()
        
        # 第三步：开始逐个孔位检测
        print("3. 开始孔位检测...")
        self.start_hole_detection()
    
    def start_hole_detection(self):
        """开始当前孔位检测"""
        if self.current_hole_index >= len(self.current_holes):
            self.finish_detection()
            return
        
        current_hole = self.current_holes[self.current_hole_index]
        print(f"   🔍 检测孔位: {current_hole}")
        
        # 设置当前孔位（这会自动更新保存目录）
        self.endoscope_manager.set_current_hole(current_hole)
        
        # 显示当前保存路径
        status = self.endoscope_manager.get_status()
        save_dir = status.get('save_directory')
        print(f"      📁 图像保存路径: {save_dir}")
        
        # 开始采集（模拟采集5秒）
        self.endoscope_manager.start_acquisition()
        
        # 5秒后停止当前孔位检测，移动到下一个
        QTimer.singleShot(5000, self.finish_current_hole)
    
    def finish_current_hole(self):
        """完成当前孔位检测"""
        current_hole = self.current_holes[self.current_hole_index]
        print(f"   ✅ 孔位 {current_hole} 检测完成")
        
        # 停止采集
        self.endoscope_manager.stop_acquisition()
        
        # 移动到下一个孔位
        self.current_hole_index += 1
        
        # 短暂延迟后开始下一个孔位
        QTimer.singleShot(1000, self.start_hole_detection)
    
    def finish_detection(self):
        """完成整个检测批次"""
        print("🎉 整个检测批次完成!")
        
        # 断开设备连接
        self.endoscope_manager.disconnect_device()
        
        # 显示最终统计
        status = self.endoscope_manager.get_status()
        print(f"最终状态:")
        print(f"  - 产品: {status.get('product_id')}")
        print(f"  - 批次: {status.get('batch_id')}")
        print(f"  - 检测孔位数: {len(self.current_holes)}")
        
        QApplication.quit()

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 创建检测工作流程
    workflow = DetectionWorkflow()
    
    # 开始检测
    workflow.start_detection_batch()
    
    # 运行应用
    sys.exit(app.exec())

if __name__ == "__main__":
    main()