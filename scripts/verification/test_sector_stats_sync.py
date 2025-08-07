#!/usr/bin/env python3
"""测试扇形统计表格同步功能"""

import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.pages.main_detection_p1.native_main_detection_view_p1 import NativeMainDetectionView

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_sector_stats_sync():
    """测试扇形统计表格同步"""
    app = QApplication(sys.argv)
    
    # 创建主视图
    view = NativeMainDetectionView()
    view.setWindowTitle("扇形统计同步测试")
    view.resize(1400, 900)
    view.show()
    
    # 模拟加载DXF文件和开始模拟的操作
    def load_and_start():
        # 加载DXF文件
        dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-LFS/data/cap1000.dxf"
        if Path(dxf_path).exists():
            logging.info(f"加载DXF文件: {dxf_path}")
            view._load_dxf_file()  # 这会弹出文件选择对话框，手动选择文件
            
            # 延迟启动模拟，等待文件加载完成
            QTimer.singleShot(3000, start_simulation)
        else:
            logging.error(f"DXF文件不存在: {dxf_path}")
            logging.info("请手动点击'加载DXF文件'按钮并选择文件，然后点击'开始模拟'")
    
    def start_simulation():
        """启动模拟"""
        logging.info("启动模拟检测...")
        if view.simulation_controller and view.current_hole_collection:
            view._on_start_simulation()
            
            # 监控扇形统计更新
            QTimer.singleShot(5000, check_stats_update)
        else:
            logging.warning("请先加载DXF文件")
    
    def check_stats_update():
        """检查扇形统计是否更新"""
        if view.left_panel and hasattr(view.left_panel, 'sector_stats_table'):
            table = view.left_panel.sector_stats_table
            logging.info(f"扇形统计表格状态:")
            logging.info(f"- 行数: {table.rowCount()}")
            logging.info(f"- 列数: {table.columnCount()}")
            
            # 读取表格内容
            for row in range(table.rowCount()):
                row_data = []
                for col in range(table.columnCount()):
                    item = table.item(row, col)
                    if item:
                        row_data.append(item.text())
                    else:
                        row_data.append("")
                logging.info(f"  第{row+1}行: {row_data}")
            
            # 检查当前扇形标签
            if hasattr(view.left_panel, 'current_sector_label'):
                logging.info(f"当前扇形标签: {view.left_panel.current_sector_label.text()}")
        
        # 继续监控
        QTimer.singleShot(5000, check_stats_update)
    
    # 延迟加载，等待界面初始化
    QTimer.singleShot(1000, load_and_start)
    
    logging.info("""
    ========== 扇形统计同步测试指南 ==========
    1. 如果自动加载失败，请手动点击'加载DXF文件'按钮
    2. 选择一个DXF文件（如cap1000.dxf）
    3. 点击'开始模拟'按钮
    4. 观察左侧面板的"选中扇形"表格是否随着模拟进行而更新
    5. 控制台会每5秒输出一次表格内容
    
    预期结果：
    - 扇形标签应显示当前正在检测的扇形（如"当前扇形: SECTOR_1"）
    - 表格应显示当前扇形的统计数据
    - 随着模拟进行，统计数据应实时更新
    ==========================================
    """)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    test_sector_stats_sync()