#!/usr/bin/env python3
"""
诊断检测时序问题
分析为什么有些孔位在检测周期结束后仍保持蓝色状态
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d [%(name)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S',
    handlers=[
        logging.FileHandler(f'timing_diagnosis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# 添加项目路径
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from PySide6.QtCore import QObject, Signal, QTimer, QElapsedTimer
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor

# 创建一个增强的模拟控制器用于诊断
class DiagnosticSimulationController(QObject):
    """诊断版模拟控制器 - 增加详细的时序日志"""
    
    hole_status_updated = Signal(str, object)
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger("DiagnosticController")
        
        # 时序追踪
        self.detection_start_times = {}  # hole_id -> start_time
        self.status_change_scheduled = {}  # hole_id -> scheduled_time
        self.status_change_executed = {}  # hole_id -> execution_time
        self.timer_delays = []  # 记录定时器延迟
        
        # 模拟定时器
        self.simulation_timer = QTimer()
        self.simulation_timer.timeout.connect(self._process_next)
        self.simulation_timer.setInterval(10000)
        
        # 状态变化定时器
        self.status_change_timer = QTimer()
        self.status_change_timer.timeout.connect(self._finalize_status)
        self.status_change_timer.setSingleShot(True)
        
        # 计时器
        self.elapsed_timer = QElapsedTimer()
        
        # 测试数据
        self.test_holes = [f"C{i:03d}R001" for i in range(1, 11)]
        self.current_index = 0
        self.current_holes = []
        
    def start_test(self):
        """开始诊断测试"""
        self.logger.info("="*60)
        self.logger.info("开始检测时序诊断测试")
        self.logger.info(f"测试孔位数量: {len(self.test_holes)}")
        self.logger.info(f"检测周期: 10秒")
        self.logger.info(f"状态变化时间: 9.5秒")
        self.logger.info("="*60)
        
        self.elapsed_timer.start()
        self.current_index = 0
        self.simulation_timer.start()
        
        # 立即处理第一个
        self._process_next()
        
    def _process_next(self):
        """处理下一个检测单元"""
        if self.current_index >= len(self.test_holes):
            self._complete_test()
            return
            
        # 获取当前孔位（模拟配对检测）
        holes_to_detect = []
        if self.current_index < len(self.test_holes):
            holes_to_detect.append(self.test_holes[self.current_index])
        if self.current_index + 1 < len(self.test_holes):
            holes_to_detect.append(self.test_holes[self.current_index + 1])
            
        self.current_holes = holes_to_detect
        current_time = self.elapsed_timer.elapsed()
        
        self.logger.info(f"\n[{current_time}ms] 开始检测: {holes_to_detect}")
        
        # 记录检测开始时间
        for hole_id in holes_to_detect:
            self.detection_start_times[hole_id] = current_time
            self._update_hole_status(hole_id, "DETECTING", QColor(33, 150, 243))
            
        # 计划状态变化
        scheduled_time = current_time + 9500
        for hole_id in holes_to_detect:
            self.status_change_scheduled[hole_id] = scheduled_time
            
        self.logger.info(f"[{current_time}ms] 计划在 {scheduled_time}ms 时变更状态")
        
        # 启动状态变化定时器
        self.status_change_timer.stop()  # 确保停止之前的定时器
        self.status_change_timer.start(9500)
        
        # 移动到下一对
        self.current_index += 2
        
    def _finalize_status(self):
        """完成当前检测单元的状态变更"""
        current_time = self.elapsed_timer.elapsed()
        
        if not self.current_holes:
            self.logger.warning(f"[{current_time}ms] ⚠️  _finalize_status 被调用但没有当前检测孔位!")
            return
            
        self.logger.info(f"\n[{current_time}ms] 执行状态变更: {self.current_holes}")
        
        for hole_id in self.current_holes:
            # 记录实际执行时间
            self.status_change_executed[hole_id] = current_time
            
            # 计算延迟
            if hole_id in self.status_change_scheduled:
                scheduled = self.status_change_scheduled[hole_id]
                delay = current_time - scheduled
                self.timer_delays.append(delay)
                
                if abs(delay) > 100:  # 超过100ms的延迟
                    self.logger.warning(f"[{current_time}ms] ⚠️  定时器延迟: {delay}ms (计划: {scheduled}ms)")
                    
            # 模拟最终状态（95%合格）
            import random
            if random.random() < 0.95:
                self._update_hole_status(hole_id, "QUALIFIED", QColor(76, 175, 80))
            else:
                self._update_hole_status(hole_id, "DEFECTIVE", QColor(244, 67, 54))
                
        # 清除当前检测孔位
        self.current_holes = []
        
    def _update_hole_status(self, hole_id: str, status: str, color: QColor):
        """更新孔位状态"""
        self.logger.debug(f"更新孔位 {hole_id}: {status} (颜色: {color.name()})")
        self.hole_status_updated.emit(hole_id, (status, color))
        
    def _complete_test(self):
        """完成测试并生成报告"""
        self.simulation_timer.stop()
        self.status_change_timer.stop()
        
        self.logger.info("\n" + "="*60)
        self.logger.info("检测时序诊断完成")
        self.logger.info("="*60)
        
        # 分析结果
        self._analyze_results()
        
    def _analyze_results(self):
        """分析诊断结果"""
        self.logger.info("\n诊断结果分析:")
        
        # 检查未执行的状态变更
        unexecuted = []
        for hole_id in self.status_change_scheduled:
            if hole_id not in self.status_change_executed:
                unexecuted.append(hole_id)
                
        if unexecuted:
            self.logger.error(f"\n❌ 发现 {len(unexecuted)} 个孔位未执行状态变更:")
            for hole_id in unexecuted:
                self.logger.error(f"  - {hole_id}")
                
        # 定时器延迟统计
        if self.timer_delays:
            avg_delay = sum(self.timer_delays) / len(self.timer_delays)
            max_delay = max(self.timer_delays)
            min_delay = min(self.timer_delays)
            
            self.logger.info(f"\n定时器延迟统计:")
            self.logger.info(f"  平均延迟: {avg_delay:.2f}ms")
            self.logger.info(f"  最大延迟: {max_delay}ms")
            self.logger.info(f"  最小延迟: {min_delay}ms")
            
        # 检测周期分析
        detection_durations = []
        for hole_id in self.detection_start_times:
            if hole_id in self.status_change_executed:
                duration = self.status_change_executed[hole_id] - self.detection_start_times[hole_id]
                detection_durations.append(duration)
                
        if detection_durations:
            avg_duration = sum(detection_durations) / len(detection_durations)
            self.logger.info(f"\n检测周期统计:")
            self.logger.info(f"  平均检测时长: {avg_duration:.2f}ms")
            self.logger.info(f"  期望检测时长: 9500ms")
            self.logger.info(f"  偏差: {avg_duration - 9500:.2f}ms")


def main():
    """运行诊断测试"""
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
        
    # 创建诊断控制器
    controller = DiagnosticSimulationController()
    
    # 监听状态更新
    def on_status_updated(hole_id, status_data):
        status, color = status_data
        logging.getLogger("StatusMonitor").info(f"孔位 {hole_id} 状态更新: {status} ({color.name()})")
        
    controller.hole_status_updated.connect(on_status_updated)
    
    # 开始测试
    controller.start_test()
    
    # 设置测试超时
    QTimer.singleShot(120000, app.quit)  # 2分钟超时
    
    # 运行应用
    app.exec()
    
    print("\n诊断完成! 请查看生成的日志文件。")


if __name__ == "__main__":
    main()