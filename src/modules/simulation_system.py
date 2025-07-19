"""
模拟系统模块
实现检测进度模拟、随机故障模拟、批次完成模拟等功能
提供可配置的模拟参数，支持系统调试和演示
"""

import logging
import random
import time
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass, field

from PySide6.QtCore import QObject, QTimer, Signal, QThread
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout
from PySide6.QtWidgets import QLabel, QPushButton, QSlider, QSpinBox, QCheckBox
from PySide6.QtWidgets import QGroupBox, QProgressBar, QComboBox
from PySide6.QtCore import Qt


class SimulationState(Enum):
    """模拟状态枚举"""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"


class HoleDetectionResult(Enum):
    """孔位检测结果枚举"""
    QUALIFIED = "qualified"
    UNQUALIFIED = "unqualified"
    ERROR = "error"
    PENDING = "pending"


@dataclass
class SimulationConfig:
    """模拟配置参数"""
    # 速度设置 (检测间隔，毫秒)
    detection_interval_ms: int = 1000
    
    # 故障率设置 (0.0-1.0)
    error_rate: float = 0.05
    unqualified_rate: float = 0.1
    
    # 批次设置
    batch_size: int = 10
    enable_batch_mode: bool = True
    
    # 随机性设置
    enable_random_delays: bool = True
    min_delay_ms: int = 500
    max_delay_ms: int = 2000
    
    # 高级设置
    enable_progressive_slowdown: bool = False  # 模拟设备疲劳
    enable_quality_degradation: bool = False   # 模拟质量下降
    
    # 统计设置
    enable_detailed_logging: bool = True


@dataclass
class SimulationStatistics:
    """模拟统计信息"""
    total_holes: int = 0
    completed_holes: int = 0
    qualified_holes: int = 0
    unqualified_holes: int = 0
    error_holes: int = 0
    
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    batches_completed: int = 0
    current_batch: int = 0
    
    # 性能统计
    average_detection_time: float = 0.0
    min_detection_time: float = float('inf')
    max_detection_time: float = 0.0
    
    detection_times: List[float] = field(default_factory=list)


class SimulationWorkerThread(QThread):
    """模拟工作线程"""
    
    # 信号定义
    hole_detection_completed = Signal(str, str)  # hole_id, result
    progress_updated = Signal(float)  # progress percentage
    batch_completed = Signal(int)  # batch_number
    statistics_updated = Signal(dict)  # statistics dict
    error_occurred = Signal(str)  # error message
    
    def __init__(self, config: SimulationConfig, hole_ids: List[str]):
        super().__init__()
        self.config = config
        self.hole_ids = hole_ids
        self.current_index = 0
        self.is_running = False
        self.is_paused = False
        self.logger = logging.getLogger(__name__)
        
        # 统计信息
        self.stats = SimulationStatistics()
        self.stats.total_holes = len(hole_ids)
        
    def run(self):
        """运行模拟检测"""
        try:
            self.is_running = True
            self.stats.start_time = time.time()
            
            while self.current_index < len(self.hole_ids) and self.is_running:
                # 检查暂停状态
                while self.is_paused and self.is_running:
                    self.msleep(100)
                
                if not self.is_running:
                    break
                
                # 执行单个孔位检测模拟
                self._simulate_hole_detection()
                
                # 检查批次完成
                if self.config.enable_batch_mode:
                    self._check_batch_completion()
                
                self.current_index += 1
                
                # 更新进度
                progress = (self.current_index / len(self.hole_ids)) * 100
                self.progress_updated.emit(progress)
                
                # 发送统计更新
                self._update_statistics()
            
            # 模拟完成
            if self.is_running:
                self.stats.end_time = time.time()
                self._update_statistics()
                self.logger.info("✅ 模拟检测完成")
            
        except Exception as e:
            self.logger.error(f"❌ 模拟线程运行失败: {e}")
            self.error_occurred.emit(str(e))
        finally:
            self.is_running = False
    
    def _simulate_hole_detection(self):
        """模拟单个孔位检测"""
        try:
            hole_id = self.hole_ids[self.current_index]
            detection_start = time.time()
            
            # 计算检测延迟
            delay_ms = self._calculate_detection_delay()
            self.msleep(delay_ms)
            
            # 生成检测结果
            result = self._generate_detection_result()
            
            # 记录检测时间
            detection_time = time.time() - detection_start
            self.stats.detection_times.append(detection_time)
            
            # 更新统计
            self.stats.completed_holes += 1
            if result == HoleDetectionResult.QUALIFIED:
                self.stats.qualified_holes += 1
            elif result == HoleDetectionResult.UNQUALIFIED:
                self.stats.unqualified_holes += 1
            elif result == HoleDetectionResult.ERROR:
                self.stats.error_holes += 1
            
            # 发出信号
            self.hole_detection_completed.emit(hole_id, result.value)
            
            if self.config.enable_detailed_logging:
                self.logger.debug(f"🔍 模拟检测: {hole_id} -> {result.value} ({detection_time:.2f}s)")
                
        except Exception as e:
            self.logger.error(f"❌ 模拟孔位检测失败: {e}")
            self.error_occurred.emit(f"模拟孔位检测失败: {e}")
    
    def _calculate_detection_delay(self) -> int:
        """计算检测延迟"""
        base_delay = self.config.detection_interval_ms
        
        if self.config.enable_random_delays:
            # 添加随机延迟
            random_delay = random.randint(
                self.config.min_delay_ms, 
                self.config.max_delay_ms
            )
            base_delay = random_delay
        
        if self.config.enable_progressive_slowdown:
            # 模拟设备疲劳 - 随着时间增加检测变慢
            fatigue_factor = 1.0 + (self.current_index / len(self.hole_ids)) * 0.5
            base_delay = int(base_delay * fatigue_factor)
        
        return base_delay
    
    def _generate_detection_result(self) -> HoleDetectionResult:
        """生成检测结果"""
        rand_value = random.random()
        
        # 应用质量下降
        error_rate = self.config.error_rate
        unqualified_rate = self.config.unqualified_rate
        
        if self.config.enable_quality_degradation:
            # 随着时间推移，故障率和不合格率增加
            degradation_factor = (self.current_index / len(self.hole_ids)) * 0.3
            error_rate += degradation_factor * 0.02
            unqualified_rate += degradation_factor * 0.05
        
        if rand_value < error_rate:
            return HoleDetectionResult.ERROR
        elif rand_value < error_rate + unqualified_rate:
            return HoleDetectionResult.UNQUALIFIED
        else:
            return HoleDetectionResult.QUALIFIED
    
    def _check_batch_completion(self):
        """检查批次完成"""
        if (self.current_index + 1) % self.config.batch_size == 0:
            batch_number = (self.current_index + 1) // self.config.batch_size
            self.stats.batches_completed = batch_number
            self.batch_completed.emit(batch_number)
            
            if self.config.enable_detailed_logging:
                self.logger.info(f"📦 批次 {batch_number} 完成")
    
    def _update_statistics(self):
        """更新统计信息"""
        # 计算平均检测时间
        if self.stats.detection_times:
            self.stats.average_detection_time = sum(self.stats.detection_times) / len(self.stats.detection_times)
            self.stats.min_detection_time = min(self.stats.detection_times)
            self.stats.max_detection_time = max(self.stats.detection_times)
        
        # 计算当前批次
        if self.config.enable_batch_mode:
            self.stats.current_batch = (self.current_index // self.config.batch_size) + 1
        
        # 发送统计信号
        stats_dict = {
            'total_holes': self.stats.total_holes,
            'completed_holes': self.stats.completed_holes,
            'qualified_holes': self.stats.qualified_holes,
            'unqualified_holes': self.stats.unqualified_holes,
            'error_holes': self.stats.error_holes,
            'batches_completed': self.stats.batches_completed,
            'current_batch': self.stats.current_batch,
            'average_detection_time': self.stats.average_detection_time,
            'progress_percentage': (self.stats.completed_holes / self.stats.total_holes) * 100 if self.stats.total_holes > 0 else 0
        }
        self.statistics_updated.emit(stats_dict)
    
    def pause_simulation(self):
        """暂停模拟"""
        self.is_paused = True
        self.logger.info("⏸️ 模拟已暂停")
    
    def resume_simulation(self):
        """恢复模拟"""
        self.is_paused = False
        self.logger.info("▶️ 模拟已恢复")
    
    def stop_simulation(self):
        """停止模拟"""
        self.is_running = False
        self.is_paused = False
        self.logger.info("⏹️ 模拟已停止")


class SimulationSystem(QObject):
    """模拟系统主类"""
    
    # 信号定义
    simulation_started = Signal()
    simulation_stopped = Signal()
    simulation_paused = Signal()
    simulation_resumed = Signal()
    progress_updated = Signal(float)
    hole_detected = Signal(str, str)  # hole_id, result
    batch_completed = Signal(int)
    statistics_updated = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 配置和状态
        self.config = SimulationConfig()
        self.state = SimulationState.STOPPED
        self.worker_thread: Optional[SimulationWorkerThread] = None
        
        # 数据
        self.hole_ids: List[str] = []
        self.current_statistics: Dict[str, Any] = {}
        
        self.logger.info("🎮 模拟系统初始化完成")
    
    def start_simulation(self, hole_ids: List[str]) -> bool:
        """开始模拟检测"""
        try:
            if self.state == SimulationState.RUNNING:
                self.logger.warning("⚠️ 模拟已在运行中")
                return False
            
            if not hole_ids:
                self.logger.error("❌ 孔位列表为空，无法开始模拟")
                return False
            
            self.hole_ids = hole_ids.copy()
            
            # 创建工作线程
            self.worker_thread = SimulationWorkerThread(self.config, self.hole_ids)
            
            # 连接信号
            self.worker_thread.hole_detection_completed.connect(self.hole_detected.emit)
            self.worker_thread.progress_updated.connect(self.progress_updated.emit)
            self.worker_thread.batch_completed.connect(self.batch_completed.emit)
            self.worker_thread.statistics_updated.connect(self._on_statistics_updated)
            self.worker_thread.error_occurred.connect(self.error_occurred.emit)
            self.worker_thread.finished.connect(self._on_simulation_finished)
            
            # 启动线程
            self.worker_thread.start()
            self.state = SimulationState.RUNNING
            
            self.simulation_started.emit()
            self.logger.info(f"🚀 开始模拟检测，共 {len(hole_ids)} 个孔位")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 启动模拟失败: {e}")
            self.error_occurred.emit(f"启动模拟失败: {e}")
            return False
    
    def pause_simulation(self) -> bool:
        """暂停模拟"""
        try:
            if self.state != SimulationState.RUNNING:
                return False
            
            if self.worker_thread:
                self.worker_thread.pause_simulation()
                self.state = SimulationState.PAUSED
                self.simulation_paused.emit()
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ 暂停模拟失败: {e}")
            return False
    
    def resume_simulation(self) -> bool:
        """恢复模拟"""
        try:
            if self.state != SimulationState.PAUSED:
                return False
            
            if self.worker_thread:
                self.worker_thread.resume_simulation()
                self.state = SimulationState.RUNNING
                self.simulation_resumed.emit()
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ 恢复模拟失败: {e}")
            return False
    
    def stop_simulation(self) -> bool:
        """停止模拟"""
        try:
            if self.state == SimulationState.STOPPED:
                return True
            
            if self.worker_thread:
                self.worker_thread.stop_simulation()
                self.worker_thread.wait(3000)  # 等待3秒
                self.worker_thread = None
            
            self.state = SimulationState.STOPPED
            self.simulation_stopped.emit()
            self.logger.info("⏹️ 模拟已停止")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 停止模拟失败: {e}")
            return False
    
    def get_simulation_state(self) -> SimulationState:
        """获取模拟状态"""
        return self.state
    
    def get_current_statistics(self) -> Dict[str, Any]:
        """获取当前统计信息"""
        return self.current_statistics.copy()
    
    def update_config(self, **kwargs) -> bool:
        """更新配置参数"""
        try:
            for key, value in kwargs.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
                    self.logger.debug(f"🔧 更新配置: {key} = {value}")
                else:
                    self.logger.warning(f"⚠️ 未知配置参数: {key}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 更新配置失败: {e}")
            return False
    
    def get_config(self) -> SimulationConfig:
        """获取当前配置"""
        return self.config
    
    def _on_statistics_updated(self, stats_dict: Dict[str, Any]):
        """处理统计更新"""
        self.current_statistics = stats_dict
        self.statistics_updated.emit(stats_dict)
    
    def _on_simulation_finished(self):
        """处理模拟完成"""
        self.state = SimulationState.COMPLETED
        self.simulation_stopped.emit()
        self.logger.info("🎉 模拟检测完成")


class SimulationControlWidget(QWidget):
    """模拟控制界面组件"""
    
    # 信号定义
    start_requested = Signal(dict)  # config dict
    pause_requested = Signal()
    resume_requested = Signal()
    stop_requested = Signal()
    config_changed = Signal(dict)  # config dict
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.config = SimulationConfig()
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # 控制按钮组
        self.create_control_group(layout)
        
        # 配置参数组
        self.create_config_group(layout)
        
        # 状态显示组
        self.create_status_group(layout)
        
        layout.addStretch()
    
    def create_control_group(self, layout):
        """创建控制按钮组"""
        control_group = QGroupBox("模拟控制")
        control_layout = QGridLayout(control_group)
        
        self.start_btn = QPushButton("🚀 开始模拟")
        self.pause_btn = QPushButton("⏸️ 暂停")
        self.resume_btn = QPushButton("▶️ 恢复")
        self.stop_btn = QPushButton("⏹️ 停止")
        
        # 设置按钮状态
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        
        # 设置按钮大小
        for btn in [self.start_btn, self.pause_btn, self.resume_btn, self.stop_btn]:
            btn.setFixedHeight(35)
        
        control_layout.addWidget(self.start_btn, 0, 0)
        control_layout.addWidget(self.pause_btn, 0, 1)
        control_layout.addWidget(self.resume_btn, 1, 0)
        control_layout.addWidget(self.stop_btn, 1, 1)
        
        layout.addWidget(control_group)
    
    def create_config_group(self, layout):
        """创建配置参数组"""
        config_group = QGroupBox("模拟参数")
        config_layout = QGridLayout(config_group)
        
        # 检测间隔
        config_layout.addWidget(QLabel("检测间隔 (ms):"), 0, 0)
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(100, 10000)
        self.interval_spin.setValue(self.config.detection_interval_ms)
        config_layout.addWidget(self.interval_spin, 0, 1)
        
        # 故障率
        config_layout.addWidget(QLabel("故障率 (%):"), 1, 0)
        self.error_rate_spin = QSpinBox()
        self.error_rate_spin.setRange(0, 100)
        self.error_rate_spin.setValue(int(self.config.error_rate * 100))
        config_layout.addWidget(self.error_rate_spin, 1, 1)
        
        # 不合格率
        config_layout.addWidget(QLabel("不合格率 (%):"), 2, 0)
        self.unqualified_rate_spin = QSpinBox()
        self.unqualified_rate_spin.setRange(0, 100)
        self.unqualified_rate_spin.setValue(int(self.config.unqualified_rate * 100))
        config_layout.addWidget(self.unqualified_rate_spin, 2, 1)
        
        # 批次大小
        config_layout.addWidget(QLabel("批次大小:"), 3, 0)
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(1, 100)
        self.batch_size_spin.setValue(self.config.batch_size)
        config_layout.addWidget(self.batch_size_spin, 3, 1)
        
        # 高级选项
        self.enable_random_delays_cb = QCheckBox("启用随机延迟")
        self.enable_random_delays_cb.setChecked(self.config.enable_random_delays)
        config_layout.addWidget(self.enable_random_delays_cb, 4, 0, 1, 2)
        
        self.enable_progressive_slowdown_cb = QCheckBox("启用设备疲劳模拟")
        self.enable_progressive_slowdown_cb.setChecked(self.config.enable_progressive_slowdown)
        config_layout.addWidget(self.enable_progressive_slowdown_cb, 5, 0, 1, 2)
        
        layout.addWidget(config_group)
    
    def create_status_group(self, layout):
        """创建状态显示组"""
        status_group = QGroupBox("模拟状态")
        status_layout = QGridLayout(status_group)
        
        # 状态标签
        status_layout.addWidget(QLabel("当前状态:"), 0, 0)
        self.status_label = QLabel("已停止")
        status_layout.addWidget(self.status_label, 0, 1)
        
        # 进度条
        status_layout.addWidget(QLabel("进度:"), 1, 0)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        status_layout.addWidget(self.progress_bar, 1, 1)
        
        # 统计信息
        status_layout.addWidget(QLabel("已完成:"), 2, 0)
        self.completed_label = QLabel("0/0")
        status_layout.addWidget(self.completed_label, 2, 1)
        
        status_layout.addWidget(QLabel("合格率:"), 3, 0)
        self.qualified_rate_label = QLabel("0%")
        status_layout.addWidget(self.qualified_rate_label, 3, 1)
        
        layout.addWidget(status_group)
    
    def setup_connections(self):
        """设置信号连接"""
        self.start_btn.clicked.connect(self._on_start_clicked)
        self.pause_btn.clicked.connect(self.pause_requested.emit)
        self.resume_btn.clicked.connect(self.resume_requested.emit)
        self.stop_btn.clicked.connect(self._on_stop_clicked)
        
        # 配置变化信号
        self.interval_spin.valueChanged.connect(self._on_config_changed)
        self.error_rate_spin.valueChanged.connect(self._on_config_changed)
        self.unqualified_rate_spin.valueChanged.connect(self._on_config_changed)
        self.batch_size_spin.valueChanged.connect(self._on_config_changed)
        self.enable_random_delays_cb.toggled.connect(self._on_config_changed)
        self.enable_progressive_slowdown_cb.toggled.connect(self._on_config_changed)
    
    def _on_start_clicked(self):
        """处理开始按钮点击"""
        config_dict = self._get_current_config()
        self.start_requested.emit(config_dict)
    
    def _on_stop_clicked(self):
        """处理停止按钮点击"""
        self.stop_requested.emit()
    
    def _on_config_changed(self):
        """处理配置变化"""
        config_dict = self._get_current_config()
        self.config_changed.emit(config_dict)
    
    def _get_current_config(self) -> dict:
        """获取当前配置"""
        return {
            'detection_interval_ms': self.interval_spin.value(),
            'error_rate': self.error_rate_spin.value() / 100.0,
            'unqualified_rate': self.unqualified_rate_spin.value() / 100.0,
            'batch_size': self.batch_size_spin.value(),
            'enable_random_delays': self.enable_random_delays_cb.isChecked(),
            'enable_progressive_slowdown': self.enable_progressive_slowdown_cb.isChecked(),
        }
    
    def update_simulation_state(self, state: SimulationState):
        """更新模拟状态显示"""
        state_texts = {
            SimulationState.STOPPED: "已停止",
            SimulationState.RUNNING: "运行中",
            SimulationState.PAUSED: "已暂停",
            SimulationState.COMPLETED: "已完成"
        }
        
        self.status_label.setText(state_texts.get(state, "未知"))
        
        # 更新按钮状态
        if state == SimulationState.STOPPED or state == SimulationState.COMPLETED:
            self.start_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.resume_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
        elif state == SimulationState.RUNNING:
            self.start_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            self.resume_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
        elif state == SimulationState.PAUSED:
            self.start_btn.setEnabled(False)
            self.pause_btn.setEnabled(False)
            self.resume_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
    
    def update_progress(self, progress: float):
        """更新进度显示"""
        self.progress_bar.setValue(int(progress))
    
    def update_statistics(self, stats: Dict[str, Any]):
        """更新统计显示"""
        completed = stats.get('completed_holes', 0)
        total = stats.get('total_holes', 0)
        qualified = stats.get('qualified_holes', 0)
        
        self.completed_label.setText(f"{completed}/{total}")
        
        if completed > 0:
            qualified_rate = (qualified / completed) * 100
            self.qualified_rate_label.setText(f"{qualified_rate:.1f}%")
        else:
            self.qualified_rate_label.setText("0%")


# 导出的公共接口
__all__ = [
    'SimulationSystem',
    'SimulationControlWidget', 
    'SimulationConfig',
    'SimulationState',
    'HoleDetectionResult'
]