#!/usr/bin/env python3
"""
可视化模拟检测测试脚本
专注于观察图像渲染和关键状态更新
"""

import sys
import time
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import QTimer

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置简化的日志 - 只显示关键信息
logging.basicConfig(
    level=logging.WARNING,  # 只显示WARNING及以上级别
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 为测试相关的日志设置INFO级别
test_logger = logging.getLogger(__name__)
test_logger.setLevel(logging.INFO)

# 只允许关键组件的INFO日志
key_loggers = [
    'src.pages.main_detection_p1.components.simulation_controller',
    'src.core_business.graphics.snake_path_renderer',
    '__main__'
]

for logger_name in key_loggers:
    logging.getLogger(logger_name).setLevel(logging.INFO)

class VisualTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("可视化模拟检测测试 - 观察图像渲染")
        self.setGeometry(100, 100, 1400, 900)  # 更大的窗口便于观察
        
        # 导入主检测页面
        from src.pages.main_detection_p1.main_detection_page import MainDetectionPage
        
        # 创建主检测页面
        self.main_page = MainDetectionPage()
        self.setCentralWidget(self.main_page)
        
        # 测试状态
        self.simulation_started = False
        self.pairs_processed = 0
        self.last_status_time = 0
        
        # 连接关键信号
        if hasattr(self.main_page, 'simulation_controller') and self.main_page.simulation_controller:
            self.main_page.simulation_controller.simulation_progress.connect(self.on_simulation_progress)
            self.main_page.simulation_controller.simulation_completed.connect(self.on_simulation_completed)
            # 只记录重要的状态变化
            self.main_page.simulation_controller.simulation_started.connect(self.on_simulation_started)
            self.main_page.simulation_controller.simulation_stopped.connect(self.on_simulation_stopped)
        
        # 启动自动测试
        QTimer.singleShot(3000, self.start_auto_test)
    
    def start_auto_test(self):
        """启动自动测试"""
        test_logger.info("🚀 开始可视化模拟测试")
        
        # 第一步：加载CAP1000
        try:
            if self.main_page.controller:
                success = self.main_page.controller.select_product("CAP1000")
                if success:
                    test_logger.info("✅ CAP1000加载成功")
                    QTimer.singleShot(2000, self.start_simulation)
                else:
                    test_logger.error("❌ CAP1000加载失败")
        except Exception as e:
            test_logger.error(f"❌ 加载产品失败: {e}")
    
    def start_simulation(self):
        """启动模拟"""
        try:
            if self.main_page.controller and self.main_page.controller.hole_collection:
                hole_count = len(self.main_page.controller.hole_collection.holes)
                test_logger.info(f"🐍 开始模拟 - 总孔位: {hole_count}")
                
                # 启动模拟
                self.main_page._on_start_simulation()
                
                # 检查是否启动成功
                QTimer.singleShot(2000, self.check_simulation_status)
            else:
                test_logger.error("❌ 没有孔位数据，无法启动模拟")
        except Exception as e:
            test_logger.error(f"❌ 启动模拟失败: {e}")
    
    def check_simulation_status(self):
        """检查模拟状态"""
        if (self.main_page.simulation_controller and 
            self.main_page.simulation_controller.is_simulation_running()):
            test_logger.info("✅ 模拟已启动 - 等待观察图像渲染...")
            test_logger.info("📝 观察要点:")
            test_logger.info("   - 左侧全景图中的扇形高亮")
            test_logger.info("   - 中间视图的孔位颜色变化")
            test_logger.info("   - 每10秒的配对检测进度")
            test_logger.info("   - 孔位从灰色→蓝色→绿色/红色的变化")
            
            # 设置60秒后自动停止
            QTimer.singleShot(60000, self.stop_and_summarize)
        else:
            test_logger.warning("⚠️ 模拟未能启动")
            QTimer.singleShot(3000, self.close)
    
    def stop_and_summarize(self):
        """停止模拟并总结"""
        test_logger.info("⏹️ 测试时间到，停止模拟")
        
        if (self.main_page.simulation_controller and 
            self.main_page.simulation_controller.is_simulation_running()):
            self.main_page._on_stop_simulation()
        
        # 总结结果
        test_logger.info("📊 测试总结:")
        test_logger.info(f"   - 模拟是否启动: {'是' if self.simulation_started else '否'}")
        test_logger.info(f"   - 处理的配对数: {self.pairs_processed}")
        
        if self.main_page.simulation_controller:
            current, total = self.main_page.simulation_controller.get_progress()
            test_logger.info(f"   - 当前进度: {current}/{total}")
        
        # 3秒后关闭
        QTimer.singleShot(3000, self.close)
    
    # 信号处理 - 只记录关键事件
    def on_simulation_started(self):
        self.simulation_started = True
        test_logger.info("🟢 模拟正式开始 - 开始观察图像变化")
    
    def on_simulation_stopped(self):
        test_logger.info("🔴 模拟已停止")
    
    def on_simulation_progress(self, current, total):
        """只在每个配对完成时记录进度"""
        if current > self.pairs_processed:
            self.pairs_processed = current
            current_time = time.time()
            
            # 计算时间间隔
            if self.last_status_time > 0:
                interval = current_time - self.last_status_time
                test_logger.info(f"📈 配对 {current}/{total} 完成 (间隔: {interval:.1f}秒)")
            else:
                test_logger.info(f"📈 配对 {current}/{total} 完成")
            
            self.last_status_time = current_time
    
    def on_simulation_completed(self):
        test_logger.info("🏁 模拟完成")
        QTimer.singleShot(2000, self.close)

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 创建测试窗口
    window = VisualTestWindow()
    window.show()
    
    # 设置2分钟超时
    def force_exit():
        test_logger.info("⏰ 强制退出")
        app.quit()
    
    QTimer.singleShot(120000, force_exit)  # 2分钟后强制退出
    
    test_logger.info("🎬 启动可视化测试 - 请观察图像渲染效果")
    test_logger.info("💡 提示: 关注中间视图的孔位颜色变化和左侧全景图的扇形高亮")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()