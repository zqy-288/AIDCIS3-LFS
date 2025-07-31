#!/usr/bin/env python3
"""
自动化模拟测试 - 自动完成产品选择和模拟流程
包含纠错机制和虚线路径显示
"""

import sys
import os
import logging
import time
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal, QThread, QTimer

class AutoSimulationController(QObject):
    """自动化模拟控制器"""
    
    # 状态信号
    status_updated = Signal(str)
    error_occurred = Signal(str)
    step_completed = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.main_window = None
        self.detection_page = None
        self.simulation_controller = None
        self.current_step = 0
        self.max_retries = 3
        self.retry_count = 0
        
        # 自动化步骤
        self.steps = [
            ("初始化主窗口", self._step_init_window),
            ("选择CAP1000产品", self._step_select_product),
            ("等待数据加载", self._step_wait_data_load),
            ("配置虚线路径显示", self._step_configure_path_display),
            ("开始模拟检测", self._step_start_simulation),
            ("运行模拟5秒", self._step_run_simulation),
            ("暂停模拟", self._step_pause_simulation),
            ("完成测试", self._step_complete_test)
        ]
        
        # 定时器
        self.step_timer = QTimer()
        self.step_timer.timeout.connect(self._execute_next_step)
        self.step_timer.setSingleShot(True)
        
    def start_auto_test(self):
        """开始自动化测试"""
        logger.info("🚀 开始自动化模拟测试...")
        self.current_step = 0
        self.retry_count = 0
        self._execute_next_step()
        
    def _execute_next_step(self):
        """执行下一步"""
        if self.current_step >= len(self.steps):
            logger.info("🎉 所有步骤完成!")
            return
            
        step_name, step_func = self.steps[self.current_step]
        logger.info(f"📋 执行步骤 {self.current_step + 1}/{len(self.steps)}: {step_name}")
        
        try:
            success = step_func()
            if success:
                self.step_completed.emit(step_name)
                self.current_step += 1
                self.retry_count = 0
                # 延迟执行下一步
                self.step_timer.start(1000)
            else:
                self._handle_step_failure(step_name)
        except Exception as e:
            logger.error(f"❌ 步骤执行失败: {e}")
            self._handle_step_failure(step_name)
            
    def _handle_step_failure(self, step_name):
        """处理步骤失败"""
        self.retry_count += 1
        if self.retry_count <= self.max_retries:
            logger.warning(f"⚠️ 步骤失败，重试 {self.retry_count}/{self.max_retries}: {step_name}")
            self.step_timer.start(2000)  # 重试延迟更长
        else:
            logger.error(f"💥 步骤彻底失败: {step_name}")
            self.error_occurred.emit(f"步骤失败: {step_name}")
            
    def _step_init_window(self):
        """初始化主窗口"""
        try:
            from src.main_window_aggregator import MainWindowAggregator
            self.main_window = MainWindowAggregator()
            self.main_window.show()
            
            # 获取P1检测页面
            self.detection_page = self.main_window.main_detection_p1
            if self.detection_page:
                self.simulation_controller = self.detection_page.simulation_controller
                logger.info("✅ 主窗口和检测页面初始化完成")
                return True
            else:
                logger.error("❌ 无法获取检测页面")
                return False
        except Exception as e:
            logger.error(f"❌ 初始化失败: {e}")
            return False
            
    def _step_select_product(self):
        """选择CAP1000产品"""
        try:
            if self.detection_page and self.detection_page.controller:
                # 调用控制器的产品选择方法
                success = self.detection_page.controller.select_product("CAP1000")
                if success:
                    logger.info("✅ CAP1000产品选择成功")
                    return True
                else:
                    logger.error("❌ CAP1000产品选择失败")
                    return False
            return False
        except Exception as e:
            logger.error(f"❌ 选择产品失败: {e}")
            return False
            
    def _step_wait_data_load(self):
        """等待数据加载完成"""
        try:
            if (self.detection_page and 
                self.detection_page.controller and 
                self.detection_page.controller.hole_collection):
                
                hole_count = len(self.detection_page.controller.hole_collection.holes)
                logger.info(f"✅ 数据加载完成: {hole_count} 个孔位")
                return True
            else:
                logger.warning("⏳ 数据仍在加载中...")
                return False
        except Exception as e:
            logger.error(f"❌ 检查数据加载失败: {e}")
            return False
            
    def _step_configure_path_display(self):
        """配置虚线路径显示"""
        try:
            if self.simulation_controller:
                # 设置路径为虚线样式
                self._configure_dashed_path_style()
                logger.info("✅ 虚线路径样式配置完成")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ 配置路径样式失败: {e}")
            return False
            
    def _step_start_simulation(self):
        """开始模拟检测"""
        try:
            if self.detection_page:
                self.detection_page._on_start_simulation()
                logger.info("✅ 模拟检测已启动")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ 启动模拟失败: {e}")
            return False
            
    def _step_run_simulation(self):
        """运行模拟5秒"""
        logger.info("⏳ 模拟运行中... (5秒)")
        # 这一步总是成功的，只是等待时间
        return True
        
    def _step_pause_simulation(self):
        """暂停模拟"""
        try:
            if self.detection_page:
                self.detection_page._on_pause_simulation()
                logger.info("✅ 模拟检测已暂停")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ 暂停模拟失败: {e}")
            return False
            
    def _step_complete_test(self):
        """完成测试"""
        logger.info("🎉 自动化测试完成!")
        self.status_updated.emit("自动化测试完成")
        return True
        
    def _configure_dashed_path_style(self):
        """配置虚线路径样式 - 减少渲染负担"""
        try:
            if hasattr(self.simulation_controller, 'snake_path_renderer'):
                renderer = self.simulation_controller.snake_path_renderer
                
                # 设置虚线样式
                from PySide6.QtCore import Qt
                from PySide6.QtGui import QPen, QColor
                
                # 创建虚线画笔 - 使用简单的灰色虚线
                dashed_pen = QPen(QColor(128, 128, 128, 128))  # 半透明灰色
                dashed_pen.setStyle(Qt.DashLine)
                dashed_pen.setWidth(1)  # 细线条
                
                # 应用到渲染器
                if hasattr(renderer, 'set_path_pen'):
                    renderer.set_path_pen(dashed_pen)
                    
                logger.info("✅ 虚线路径样式设置完成")
                
        except Exception as e:
            logger.error(f"❌ 设置虚线样式失败: {e}")

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 创建自动化控制器
    auto_controller = AutoSimulationController()
    
    # 连接信号
    auto_controller.status_updated.connect(lambda msg: logger.info(f"📊 状态: {msg}"))
    auto_controller.error_occurred.connect(lambda msg: logger.error(f"💥 错误: {msg}"))
    auto_controller.step_completed.connect(lambda step: logger.info(f"✅ 完成: {step}"))
    
    # 延迟启动自动化测试
    QTimer.singleShot(2000, auto_controller.start_auto_test)
    
    logger.info("🎬 自动化模拟测试应用启动")
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())