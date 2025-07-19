"""
实时预览控制器
负责管理实时数据预览界面和相关业务逻辑
"""

import logging
from typing import Optional, Dict, Any, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGroupBox, QProgressBar, QTextEdit, QSplitter, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame
)
from PySide6.QtCore import QObject, Signal, QTimer, Qt
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor

from src.modules.realtime_chart import RealtimeChart
from src.modules.worker_thread import WorkerThread


class RealtimeController(QObject):
    """实时预览控制器类"""
    
    # 信号定义
    data_updated = Signal(dict)  # 数据更新信号
    status_changed = Signal(str)  # 状态改变信号
    preview_ready = Signal(bool)  # 预览准备就绪信号
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.parent = parent
        self.logger = logging.getLogger(__name__)
        
        # 核心组件
        self._widget: Optional[QWidget] = None
        self._chart: Optional[RealtimeChart] = None
        self._worker: Optional[WorkerThread] = None
        
        # 数据管理
        self._current_data: Dict[str, Any] = {}
        self._data_buffer: List[Dict[str, Any]] = []
        self._max_buffer_size = 1000
        
        # 状态管理
        self._is_active = False
        self._is_paused = False
        self._update_interval = 100  # 毫秒
        
        # 定时器
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._update_display)
        
        # UI组件引用
        self._ui_components = {}
        
        self.logger.info("实时预览控制器初始化完成")
    
    def create_widget(self) -> QWidget:
        """创建实时预览界面"""
        if self._widget is not None:
            return self._widget
        
        self._widget = QWidget()
        self._setup_ui()
        self._connect_signals()
        
        self.logger.info("实时预览界面创建完成")
        return self._widget
    
    def _setup_ui(self):
        """设置用户界面"""
        if not self._widget:
            return
        
        # 主布局
        main_layout = QVBoxLayout(self._widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 创建控制面板
        control_panel = self._create_control_panel()
        main_layout.addWidget(control_panel)
        
        # 创建内容区域
        content_area = self._create_content_area()
        main_layout.addWidget(content_area)
        
        # 创建状态栏
        status_bar = self._create_status_bar()
        main_layout.addWidget(status_bar)
        
        self.logger.info("实时预览UI设置完成")
    
    def _create_control_panel(self) -> QWidget:
        """创建控制面板"""
        panel = QGroupBox("实时预览控制")
        panel.setMaximumHeight(80)
        
        layout = QHBoxLayout(panel)
        
        # 启动/停止按钮
        self._ui_components['start_btn'] = QPushButton("启动预览")
        self._ui_components['start_btn'].clicked.connect(self.start_preview)
        layout.addWidget(self._ui_components['start_btn'])
        
        # 暂停/继续按钮
        self._ui_components['pause_btn'] = QPushButton("暂停")
        self._ui_components['pause_btn'].clicked.connect(self.toggle_pause)
        self._ui_components['pause_btn'].setEnabled(False)
        layout.addWidget(self._ui_components['pause_btn'])
        
        # 停止按钮
        self._ui_components['stop_btn'] = QPushButton("停止")
        self._ui_components['stop_btn'].clicked.connect(self.stop_preview)
        self._ui_components['stop_btn'].setEnabled(False)
        layout.addWidget(self._ui_components['stop_btn'])
        
        # 清空数据按钮
        self._ui_components['clear_btn'] = QPushButton("清空数据")
        self._ui_components['clear_btn'].clicked.connect(self.clear_data)
        layout.addWidget(self._ui_components['clear_btn'])
        
        layout.addStretch()
        
        # 状态标签
        self._ui_components['status_label'] = QLabel("状态: 未启动")
        layout.addWidget(self._ui_components['status_label'])
        
        return panel
    
    def _create_content_area(self) -> QWidget:
        """创建内容区域"""
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：图表区域
        chart_widget = self._create_chart_widget()
        splitter.addWidget(chart_widget)
        
        # 右侧：数据区域
        data_widget = self._create_data_widget()
        splitter.addWidget(data_widget)
        
        # 设置分割比例
        splitter.setSizes([600, 400])
        
        return splitter
    
    def _create_chart_widget(self) -> QWidget:
        """创建图表组件"""
        widget = QGroupBox("实时数据图表")
        layout = QVBoxLayout(widget)
        
        # 创建实时图表
        self._chart = RealtimeChart()
        layout.addWidget(self._chart)
        
        return widget
    
    def _create_data_widget(self) -> QWidget:
        """创建数据显示组件"""
        widget = QGroupBox("数据详情")
        layout = QVBoxLayout(widget)
        
        # 数据表格
        self._ui_components['data_table'] = QTableWidget()
        self._ui_components['data_table'].setColumnCount(3)
        self._ui_components['data_table'].setHorizontalHeaderLabels(["参数", "当前值", "单位"])
        
        # 设置表格属性
        table = self._ui_components['data_table']
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setAlternatingRowColors(True)
        
        layout.addWidget(table)
        
        # 数据统计
        stats_widget = QGroupBox("数据统计")
        stats_layout = QVBoxLayout(stats_widget)
        
        self._ui_components['stats_text'] = QTextEdit()
        self._ui_components['stats_text'].setMaximumHeight(150)
        self._ui_components['stats_text'].setReadOnly(True)
        stats_layout.addWidget(self._ui_components['stats_text'])
        
        layout.addWidget(stats_widget)
        
        return widget
    
    def _create_status_bar(self) -> QWidget:
        """创建状态栏"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.StyledPanel)
        widget.setMaximumHeight(40)
        
        layout = QHBoxLayout(widget)
        
        # 进度条
        self._ui_components['progress_bar'] = QProgressBar()
        self._ui_components['progress_bar'].setVisible(False)
        layout.addWidget(self._ui_components['progress_bar'])
        
        # 数据计数
        self._ui_components['data_count_label'] = QLabel("数据点数: 0")
        layout.addWidget(self._ui_components['data_count_label'])
        
        layout.addStretch()
        
        # 更新频率
        self._ui_components['update_rate_label'] = QLabel("更新频率: 0 Hz")
        layout.addWidget(self._ui_components['update_rate_label'])
        
        return widget
    
    def _connect_signals(self):
        """连接信号"""
        # 连接内部信号
        self.data_updated.connect(self._on_data_updated)
        self.status_changed.connect(self._on_status_changed)
        
        # 连接图表信号
        if self._chart:
            self._chart.data_point_selected.connect(self._on_data_point_selected)
    
    def start_preview(self):
        """启动实时预览"""
        if self._is_active:
            return
        
        try:
            self._is_active = True
            self._is_paused = False
            
            # 启动工作线程
            self._start_worker()
            
            # 启动更新定时器
            self._update_timer.start(self._update_interval)
            
            # 更新UI状态
            self._ui_components['start_btn'].setEnabled(False)
            self._ui_components['pause_btn'].setEnabled(True)
            self._ui_components['stop_btn'].setEnabled(True)
            self._ui_components['progress_bar'].setVisible(True)
            
            self.status_changed.emit("运行中")
            self.preview_ready.emit(True)
            
            self.logger.info("实时预览已启动")
            
        except Exception as e:
            self.logger.error(f"启动实时预览失败: {e}")
            self.status_changed.emit("启动失败")
    
    def stop_preview(self):
        """停止实时预览"""
        if not self._is_active:
            return
        
        try:
            self._is_active = False
            self._is_paused = False
            
            # 停止定时器
            self._update_timer.stop()
            
            # 停止工作线程
            self._stop_worker()
            
            # 更新UI状态
            self._ui_components['start_btn'].setEnabled(True)
            self._ui_components['pause_btn'].setEnabled(False)
            self._ui_components['stop_btn'].setEnabled(False)
            self._ui_components['progress_bar'].setVisible(False)
            
            self.status_changed.emit("已停止")
            self.preview_ready.emit(False)
            
            self.logger.info("实时预览已停止")
            
        except Exception as e:
            self.logger.error(f"停止实时预览失败: {e}")
    
    def toggle_pause(self):
        """切换暂停状态"""
        if not self._is_active:
            return
        
        self._is_paused = not self._is_paused
        
        if self._is_paused:
            self._update_timer.stop()
            self._ui_components['pause_btn'].setText("继续")
            self.status_changed.emit("已暂停")
        else:
            self._update_timer.start(self._update_interval)
            self._ui_components['pause_btn'].setText("暂停")
            self.status_changed.emit("运行中")
        
        self.logger.info(f"实时预览暂停状态: {self._is_paused}")
    
    def clear_data(self):
        """清空数据"""
        self._data_buffer.clear()
        self._current_data.clear()
        
        # 清空图表
        if self._chart:
            self._chart.clear_data()
        
        # 清空表格
        if 'data_table' in self._ui_components:
            self._ui_components['data_table'].setRowCount(0)
        
        # 清空统计
        if 'stats_text' in self._ui_components:
            self._ui_components['stats_text'].clear()
        
        # 更新计数
        if 'data_count_label' in self._ui_components:
            self._ui_components['data_count_label'].setText("数据点数: 0")
        
        self.logger.info("数据已清空")
    
    def _start_worker(self):
        """启动工作线程"""
        if self._worker is not None:
            self._stop_worker()
        
        self._worker = WorkerThread()
        self._worker.data_ready.connect(self._on_worker_data)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()
    
    def _stop_worker(self):
        """停止工作线程"""
        if self._worker is not None:
            self._worker.stop()
            self._worker.wait(3000)  # 等待3秒
            self._worker = None
    
    def _update_display(self):
        """更新显示"""
        if not self._is_active or self._is_paused:
            return
        
        try:
            # 更新图表
            if self._chart and self._data_buffer:
                self._chart.update_data(self._data_buffer[-1])
            
            # 更新数据表格
            self._update_data_table()
            
            # 更新统计信息
            self._update_statistics()
            
            # 更新状态栏
            self._update_status_bar()
            
        except Exception as e:
            self.logger.error(f"更新显示失败: {e}")
    
    def _update_data_table(self):
        """更新数据表格"""
        if not self._current_data or 'data_table' not in self._ui_components:
            return
        
        table = self._ui_components['data_table']
        table.setRowCount(len(self._current_data))
        
        for row, (key, value) in enumerate(self._current_data.items()):
            table.setItem(row, 0, QTableWidgetItem(str(key)))
            table.setItem(row, 1, QTableWidgetItem(str(value)))
            table.setItem(row, 2, QTableWidgetItem(""))  # 单位待定
    
    def _update_statistics(self):
        """更新统计信息"""
        if not self._data_buffer or 'stats_text' not in self._ui_components:
            return
        
        stats_text = self._ui_components['stats_text']
        
        # 计算基本统计
        total_points = len(self._data_buffer)
        
        stats_info = f"""
数据统计信息:
━━━━━━━━━━━━━━━━
总数据点数: {total_points}
缓冲区大小: {self._max_buffer_size}
更新间隔: {self._update_interval}ms
当前状态: {'运行中' if self._is_active else '停止'}
        """
        
        stats_text.setText(stats_info.strip())
    
    def _update_status_bar(self):
        """更新状态栏"""
        if 'data_count_label' in self._ui_components:
            count = len(self._data_buffer)
            self._ui_components['data_count_label'].setText(f"数据点数: {count}")
        
        if 'update_rate_label' in self._ui_components:
            rate = 1000 / self._update_interval if self._update_interval > 0 else 0
            self._ui_components['update_rate_label'].setText(f"更新频率: {rate:.1f} Hz")
    
    def _on_data_updated(self, data: dict):
        """处理数据更新"""
        self._current_data = data
        
        # 添加到缓冲区
        self._data_buffer.append(data.copy())
        
        # 限制缓冲区大小
        if len(self._data_buffer) > self._max_buffer_size:
            self._data_buffer.pop(0)
    
    def _on_status_changed(self, status: str):
        """处理状态改变"""
        if 'status_label' in self._ui_components:
            self._ui_components['status_label'].setText(f"状态: {status}")
    
    def _on_data_point_selected(self, point_data: dict):
        """处理数据点选择"""
        self.logger.info(f"数据点被选择: {point_data}")
    
    def _on_worker_data(self, data: dict):
        """处理工作线程数据"""
        self.data_updated.emit(data)
    
    def _on_worker_finished(self):
        """处理工作线程完成"""
        self.logger.info("工作线程已完成")
        if self._is_active:
            self.stop_preview()
    
    def get_current_data(self) -> Dict[str, Any]:
        """获取当前数据"""
        return self._current_data.copy()
    
    def get_data_buffer(self) -> List[Dict[str, Any]]:
        """获取数据缓冲区"""
        return self._data_buffer.copy()
    
    def set_update_interval(self, interval: int):
        """设置更新间隔"""
        self._update_interval = max(50, interval)  # 最小50ms
        if self._is_active and not self._is_paused:
            self._update_timer.setInterval(self._update_interval)
    
    def is_active(self) -> bool:
        """检查是否激活"""
        return self._is_active
    
    def cleanup(self):
        """清理资源"""
        self.stop_preview()
        self._stop_worker()
        
        if self._chart:
            self._chart.deleteLater()
        
        if self._widget:
            self._widget.deleteLater()
        
        self.logger.info("实时预览控制器清理完成")