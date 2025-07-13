"""检测控制管理器"""
import logging
from datetime import datetime
from typing import Optional, List
from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QMessageBox

from aidcis2.models.hole_data import HoleStatus, HoleCollection


class DetectionManager(QObject):
    """
    检测流程管理器
    负责管理检测的开始、暂停、停止和进度控制
    """
    
    # 信号定义
    detection_started = Signal()
    detection_paused = Signal()
    detection_resumed = Signal()
    detection_stopped = Signal()
    detection_step_completed = Signal(str, str)  # hole_id, status
    detection_progress_updated = Signal(int, int)  # completed, total
    log_message = Signal(str)
    status_message = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 检测状态
        self.detection_running = False
        self.detection_paused = False
        self.detection_holes: List = []
        self.hole_collection: Optional[HoleCollection] = None
        
        # 检测时间
        self.detection_start_time: Optional[datetime] = None
        self.detection_elapsed_seconds = 0
        
        # 检测定时器
        self.detection_timer = QTimer()
        self.detection_timer.timeout.connect(self._process_detection_step)
        
        # UI引用（将由主窗口设置）
        self.graphics_view = None
        self.start_detection_btn = None
        self.pause_detection_btn = None
        self.stop_detection_btn = None
        
    def set_ui_components(self, graphics_view, start_btn, pause_btn, stop_btn):
        """设置UI组件引用"""
        self.graphics_view = graphics_view
        self.start_detection_btn = start_btn
        self.pause_detection_btn = pause_btn
        self.stop_detection_btn = stop_btn
        
    def set_hole_collection(self, hole_collection: HoleCollection):
        """设置孔位集合"""
        self.hole_collection = hole_collection
        
    def start_detection(self):
        """开始检测"""
        if not self.hole_collection:
            QMessageBox.warning(None, "警告", "请先加载DXF文件")
            return False
            
        if self.detection_running:
            return False
            
        # 创建有序的孔位列表
        self.detection_holes = self._create_ordered_hole_list()
        self.detection_running = True
        self.detection_paused = False
        
        # 初始化检测时间
        self.detection_start_time = datetime.now()
        self.detection_elapsed_seconds = 0
        
        # 更新按钮状态
        if self.start_detection_btn:
            self.start_detection_btn.setEnabled(False)
        if self.pause_detection_btn:
            self.pause_detection_btn.setEnabled(True)
        if self.stop_detection_btn:
            self.stop_detection_btn.setEnabled(True)
            
        # 启动检测定时器
        self.detection_timer.start(1000)  # 每秒处理一个孔位
        
        self.log_message.emit("开始检测")
        self.status_message.emit("检测进行中...")
        self.detection_started.emit()
        
        return True
        
    def pause_detection(self):
        """暂停/恢复检测"""
        if not self.detection_running:
            return
            
        if self.detection_paused:
            # 恢复检测
            self.detection_timer.start(1000)
            self.detection_paused = False
            if self.pause_detection_btn:
                self.pause_detection_btn.setText("暂停检测")
            self.log_message.emit("恢复检测")
            self.status_message.emit("检测进行中...")
            self.detection_resumed.emit()
        else:
            # 暂停检测
            self.detection_timer.stop()
            self.detection_paused = True
            if self.pause_detection_btn:
                self.pause_detection_btn.setText("恢复检测")
            self.log_message.emit("暂停检测")
            self.status_message.emit("检测已暂停")
            self.detection_paused.emit()
            
    def stop_detection(self):
        """停止检测"""
        if not self.detection_running:
            return
            
        self.detection_timer.stop()
        self.detection_running = False
        self.detection_paused = False
        
        # 重置检测时间
        self.detection_start_time = None
        
        # 更新按钮状态
        if self.start_detection_btn:
            self.start_detection_btn.setEnabled(True)
        if self.pause_detection_btn:
            self.pause_detection_btn.setEnabled(False)
            self.pause_detection_btn.setText("暂停检测")
        if self.stop_detection_btn:
            self.stop_detection_btn.setEnabled(False)
            
        self.log_message.emit("停止检测")
        self.status_message.emit("检测已停止")
        self.detection_stopped.emit()
        
    def _process_detection_step(self):
        """处理检测步骤"""
        if not self.detection_holes or not self.detection_running:
            self.stop_detection()
            return
            
        # 获取下一个待检测的孔位
        current_hole = self.detection_holes.pop(0)
        
        # 更新检测中状态
        current_hole.status = HoleStatus.PROCESSING
        if self.graphics_view:
            self.graphics_view.update_hole_status(current_hole.hole_id, current_hole.status)
            
        # 模拟检测结果
        import random
        rand_value = random.random()
        
        if rand_value < 0.995:  # 99.5%概率合格
            current_hole.status = HoleStatus.QUALIFIED
        elif rand_value < 0.9999:  # 0.49%概率异常
            current_hole.status = HoleStatus.DEFECTIVE
        else:  # 0.01%概率其他状态
            other_statuses = [HoleStatus.BLIND, HoleStatus.TIE_ROD]
            current_hole.status = random.choice(other_statuses)
            
        # 更新最终状态
        if self.graphics_view:
            self.graphics_view.update_hole_status(current_hole.hole_id, current_hole.status)
            
        self.detection_step_completed.emit(current_hole.hole_id, current_hole.status.value)
        self.log_message.emit(f"检测完成: {current_hole.hole_id} - {current_hole.status.value}")
        
        # 更新进度
        total = len(self.detection_holes) + 1  # +1 因为刚处理了一个
        completed = total - len(self.detection_holes)
        self.detection_progress_updated.emit(completed, total)
        
        # 检查是否完成
        if not self.detection_holes:
            self.stop_detection()
            self.log_message.emit("所有孔位检测完成")
            QMessageBox.information(None, "完成", "所有孔位检测完成！")
            
    def _create_ordered_hole_list(self):
        """创建有序的孔位列表"""
        if not self.hole_collection:
            return []
            
        holes = list(self.hole_collection.holes.values())
        # 按孔位ID排序
        holes.sort(key=lambda h: h.hole_id)
        return holes
        
    def get_detection_elapsed_time(self) -> int:
        """获取检测经过的秒数"""
        if self.detection_start_time:
            return int((datetime.now() - self.detection_start_time).total_seconds())
        return self.detection_elapsed_seconds
        
    def get_completed_holes_count(self) -> int:
        """获取已完成的孔位数量"""
        if not self.hole_collection:
            return 0
            
        completed_statuses = [
            HoleStatus.QUALIFIED,
            HoleStatus.DEFECTIVE,
            HoleStatus.BLIND,
            HoleStatus.TIE_ROD
        ]
        
        count = sum(1 for hole in self.hole_collection.holes.values() 
                   if hole.status in completed_statuses)
        return count