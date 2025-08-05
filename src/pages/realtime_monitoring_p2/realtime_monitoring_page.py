"""
实时监控页面
简化版本，解决原版"魔幻"问题，提供更实用的监控界面
"""

import logging
import numpy as np
from typing import Optional
from collections import deque
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QGroupBox, QLabel, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QTextEdit, QSpinBox, QDoubleSpinBox,
    QLineEdit
)
from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtGui import QFont, QColor

# matplotlib imports
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib

# 设置matplotlib中文字体
def setup_safe_chinese_font():
    """设置安全的中文字体"""
    try:
        matplotlib.rcParams['font.family'] = 'sans-serif'
        matplotlib.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang SC', 'SimHei', 'DejaVu Sans']
        matplotlib.rcParams['axes.unicode_minus'] = False
    except Exception as e:
        matplotlib.rcParams['font.family'] = 'DejaVu Sans'

setup_safe_chinese_font()


class RealtimeMonitoringPage(QWidget):
    """
    简化版实时监控页面
    
    特点：
    1. 清晰的布局，不花哨
    2. 实用的功能，易于理解
    3. 减少不必要的复杂性
    4. 重点突出数据监控
    """
    
    # 页面信号
    monitoring_started = Signal()
    monitoring_stopped = Signal()
    hole_selected = Signal(str)
    
    def __init__(self, shared_components=None, view_model=None, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        self.shared_components = shared_components
        self.view_model = view_model
        
        # 状态变量
        self.is_monitoring = False
        self.current_hole = "未选择"
        self.data_count = 0
        self.anomaly_count = 0
        
        # matplotlib数据存储
        self.time_data = deque(maxlen=1000)
        self.diameter_data = deque(maxlen=1000)
        self.depth_data = deque(maxlen=1000)
        self.anomaly_data = []
        
        # 标准参数 - 从产品选择中读取
        self.standard_diameter = 20.0  # 默认标准直径20mm
        self.tolerance_upper = 0.1  # 默认公差上限+0.1mm
        self.tolerance_lower = 0.1  # 默认公差下限-0.1mm
        
        # 尝试从当前产品获取参数
        self._load_product_parameters()
        
        # 模拟数据时间计数
        self.simulation_time = 0
        
        # 初始化
        self._init_ui()
        self._init_timer()
        
        self.logger.info("✅ 简化版实时监控页面初始化完成")
        
    def _load_product_parameters(self):
        """从当前选择的产品中加载标准参数"""
        try:
            # 尝试从shared_components获取business_service
            if self.shared_components and hasattr(self.shared_components, 'business_service'):
                business_service = self.shared_components.business_service
                if hasattr(business_service, 'current_product') and business_service.current_product:
                    product = business_service.current_product
                    self._update_parameters_from_product(product)
                    return
            
            # 尝试从共享数据管理器获取
            if self.shared_components and hasattr(self.shared_components, 'shared_data_manager'):
                shared_data = self.shared_components.shared_data_manager
                if hasattr(shared_data, 'get_current_product'):
                    product = shared_data.get_current_product()
                    if product:
                        self._update_parameters_from_product(product)
                        return
            
            # 尝试通过服务获取
            try:
                from src.shared.services import get_business_service
                business_service = get_business_service()
                if business_service and hasattr(business_service, 'current_product') and business_service.current_product:
                    product = business_service.current_product
                    self._update_parameters_from_product(product)
                    return
            except ImportError:
                pass
                
            self.logger.info("📋 使用默认产品参数 (未找到当前产品信息)")
            
        except Exception as e:
            self.logger.warning(f"⚠️ 加载产品参数失败，使用默认值: {e}")
    
    def _update_parameters_from_product(self, product):
        """从产品对象更新参数"""
        try:
            # 更新标准直径
            if hasattr(product, 'standard_diameter') and product.standard_diameter:
                self.standard_diameter = float(product.standard_diameter)
                self.logger.info(f"📊 从产品加载标准直径: {self.standard_diameter} mm")
            
            # 更新公差上限
            if hasattr(product, 'tolerance_upper') and product.tolerance_upper is not None:
                self.tolerance_upper = float(product.tolerance_upper)
                self.logger.info(f"📊 从产品加载公差上限: +{self.tolerance_upper} mm")
            
            # 更新公差下限
            if hasattr(product, 'tolerance_lower') and product.tolerance_lower is not None:
                self.tolerance_lower = float(product.tolerance_lower)
                self.logger.info(f"📊 从产品加载公差下限: -{self.tolerance_lower} mm")
            
            # 记录产品名称
            product_name = getattr(product, 'model_name', '未知产品')
            self.logger.info(f"✅ 成功加载产品 '{product_name}' 的参数")
            
            # 如果有UI组件需要更新，在这里调用
            if hasattr(self, '_update_parameter_display'):
                self._update_parameter_display()
                
        except Exception as e:
            self.logger.error(f"❌ 更新产品参数失败: {e}")
    
    def refresh_product_parameters(self):
        """刷新产品参数 - 可被外部调用"""
        self._load_product_parameters()
        
    def _update_parameter_display(self):
        """更新参数显示界面"""
        if hasattr(self, 'std_diameter_input'):
            self.std_diameter_input.setText(str(self.standard_diameter))
        if hasattr(self, 'tolerance_input'):
            if self.tolerance_upper == self.tolerance_lower:
                self.tolerance_input.setText(f"±{self.tolerance_upper}")
            else:
                self.tolerance_input.setText(f"+{self.tolerance_upper}/-{self.tolerance_lower}")
        # 更新图表的公差带
        if hasattr(self, 'canvas'):
            self._update_tolerance_band()
            self.canvas.draw()
        
    def _init_ui(self):
        """初始化用户界面 - 清晰简洁的布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # 1. 顶部控制面板
        self._create_control_panel(layout)
        
        # 2. 主要显示区域
        self._create_main_display(layout)
        
    def _create_control_panel(self, parent_layout):
        """创建顶部控制面板 - 紧凑布局"""
        control_group = QGroupBox("监控控制")
        control_group.setMaximumHeight(80)  # 限制高度
        control_layout = QHBoxLayout(control_group)
        control_layout.setSpacing(15)
        control_layout.setContentsMargins(10, 8, 10, 8)
        
        # 孔位选择 - 紧凑版
        hole_widget = QWidget()
        hole_layout = QHBoxLayout(hole_widget)
        hole_layout.setContentsMargins(0, 0, 0, 0)
        hole_layout.setSpacing(8)
        
        hole_label = QLabel("当前孔位:")
        hole_label.setFont(QFont("Arial", 9))
        hole_label.setMinimumWidth(60)
        
        self.hole_combo = QComboBox()
        self.hole_combo.addItems([
            "ABC001R001", "ABC001R002", "ABC002R001", 
            "ABC002R002", "ABC003R001", "ABC003R002"
        ])
        self.hole_combo.currentTextChanged.connect(self._on_hole_changed)
        self.hole_combo.setMinimumWidth(100)
        
        hole_layout.addWidget(hole_label)
        hole_layout.addWidget(self.hole_combo)
        
        # 监控状态 - 紧凑版
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(8)
        
        status_label = QLabel("监控状态:")
        status_label.setFont(QFont("Arial", 9))
        status_label.setMinimumWidth(60)
        
        self.status_display = QLabel("未开始")
        self.status_display.setStyleSheet("color: red; font-weight: bold; font-size: 9pt;")
        self.status_display.setMinimumWidth(60)
        
        status_layout.addWidget(status_label)
        status_layout.addWidget(self.status_display)
        
        # 数据统计 - 水平排列，更紧凑
        stats_widget = QWidget()
        stats_layout = QHBoxLayout(stats_widget)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(15)
        
        self.data_count_label = QLabel("数据: 0 条")
        self.data_count_label.setFont(QFont("Arial", 9))
        self.data_count_label.setStyleSheet("color: #2196F3; font-weight: bold;")
        
        self.anomaly_count_label = QLabel("异常: 0 条")
        self.anomaly_count_label.setFont(QFont("Arial", 9))
        self.anomaly_count_label.setStyleSheet("color: #FF5722; font-weight: bold;")
        
        stats_layout.addWidget(self.data_count_label)
        stats_layout.addWidget(self.anomaly_count_label)
        
        # 控制按钮 - 水平排列
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)
        
        self.start_btn = QPushButton("开始监控")
        self.start_btn.setCheckable(True)
        self.start_btn.clicked.connect(self._toggle_monitoring)
        self.start_btn.setFixedSize(80, 35)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                font-size: 10pt;
                border-radius: 4px;
            }
            QPushButton:checked {
                background-color: #f44336;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        self.clear_btn = QPushButton("清除数据")
        self.clear_btn.clicked.connect(self._clear_data)
        self.clear_btn.setFixedSize(70, 35)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-weight: bold;
                font-size: 9pt;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
        """)
        
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.clear_btn)
        
        # 添加到控制面板 - 紧凑排列
        control_layout.addWidget(hole_widget)
        control_layout.addWidget(status_widget)
        control_layout.addWidget(stats_widget)
        control_layout.addStretch()
        control_layout.addWidget(button_widget)
        
        parent_layout.addWidget(control_group)
        
    def _create_main_display(self, parent_layout):
        """创建主显示区域"""
        # 创建垂直分割器，上下分割
        main_splitter = QSplitter(Qt.Vertical)
        
        # 上部：数据监控区域（水平分割）
        upper_widget = QWidget()
        upper_layout = QHBoxLayout(upper_widget)
        upper_layout.setContentsMargins(0, 0, 0, 0)
        
        upper_splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：数据显示
        self._create_data_display(upper_splitter)
        
        # 右侧：异常监控
        self._create_anomaly_display(upper_splitter)
        
        # 设置上部分割比例（65% : 35%）- 为异常监控稍微增加空间
        upper_splitter.setSizes([650, 350])
        upper_layout.addWidget(upper_splitter)
        
        # 下部：内窥镜检测区域
        self._create_endoscope_display(main_splitter)
        
        # 添加上部区域到主分割器
        main_splitter.addWidget(upper_widget)
        
        # 设置主分割器比例（上部45% : 下部55%）- 为内窥镜预留更多空间
        main_splitter.setSizes([450, 550])
        
        parent_layout.addWidget(main_splitter)
        
    def _create_data_display(self, splitter):
        """创建数据显示区域 - 使用matplotlib图表"""
        data_group = QGroupBox("实时数据监控")
        data_layout = QVBoxLayout(data_group)
        data_layout.setContentsMargins(5, 5, 5, 5)
        
        # 创建matplotlib图表
        self._create_chart_widget()
        data_layout.addWidget(self.canvas)
        
        splitter.addWidget(data_group)
        
    def _create_chart_widget(self):
        """创建matplotlib图表组件"""
        # 创建Figure和Canvas - 适中的尺寸
        self.figure = Figure(figsize=(10, 5))  # 调整为更合适的尺寸
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumHeight(400)  # 设置最小高度，确保图表足够大
        self.ax = self.figure.add_subplot(111)
        
        # 初始化图表
        self._setup_chart()
        
    def _setup_chart(self):
        """设置图表样式和布局"""
        self.ax.clear()
        
        # 设置标题和标签 - 减小字体
        self.ax.set_title('实时直径监测', fontsize=12, fontweight='bold')
        self.ax.set_xlabel('时间 (秒)', fontsize=10)
        self.ax.set_ylabel('直径 (mm)', fontsize=10)
        
        # 设置网格
        self.ax.grid(True, alpha=0.3, linestyle='--')
        
        # 初始化数据线
        self.line, = self.ax.plot([], [], 'b-', linewidth=2, label='直径数据')
        self.anomaly_scatter = self.ax.scatter([], [], c='red', s=50, label='异常点', zorder=5)
        
        # 绘制公差带
        self._update_tolerance_band()
        
        # 设置图例 - 减小图例
        self.ax.legend(loc='upper right', fontsize=8)
        
        # 设置初始范围
        self.ax.set_xlim(0, 60)
        self.ax.set_ylim(self.standard_diameter - 1, self.standard_diameter + 1)
        
        # 紧凑布局，减小边距
        self.figure.tight_layout(pad=1.0)
        
    def _update_tolerance_band(self):
        """更新公差带显示"""
        # 移除旧的公差带
        for patch in self.ax.patches:
            patch.remove()
            
        # 添加公差带
        tolerance_band = patches.Rectangle(
            (0, self.standard_diameter - self.tolerance_lower),
            60,
            self.tolerance_upper + self.tolerance_lower,
            alpha=0.2,
            facecolor='green',
            edgecolor='none',
            label='公差范围'
        )
        self.ax.add_patch(tolerance_band)
        
        # 添加标准线
        self.ax.axhline(y=self.standard_diameter, color='green', 
                       linestyle='--', alpha=0.8, label='标准直径')
        
    def _create_anomaly_display(self, splitter):
        """创建异常显示区域 - 简洁专业版"""
        anomaly_group = QGroupBox("异常监控")
        anomaly_group.setMinimumWidth(300)
        anomaly_layout = QVBoxLayout(anomaly_group)
        anomaly_layout.setSpacing(8)
        anomaly_layout.setContentsMargins(8, 8, 8, 8)
        
        # 异常统计 - 简洁展示
        self.total_anomalies_label = QLabel("总异常数: 0")
        self.max_deviation_label = QLabel("最大偏差: 0.000 mm")
        self.avg_deviation_label = QLabel("平均偏差: 0.000 mm")
        
        stats_font = QFont("Arial", 9)
        for label in [self.total_anomalies_label, self.max_deviation_label, self.avg_deviation_label]:
            label.setFont(stats_font)
            label.setStyleSheet("color: #333; padding: 2px 0px;")
            anomaly_layout.addWidget(label)
        
        # 分隔线
        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #ddd; margin: 5px 0px;")
        anomaly_layout.addWidget(line)
        
        # 异常数据显示
        self.anomaly_text = QTextEdit()
        self.anomaly_text.setReadOnly(True)
        self.anomaly_text.setMinimumHeight(140)
        self.anomaly_text.setPlaceholderText("暂无异常数据...")
        self.anomaly_text.setStyleSheet("""
            QTextEdit {
                font-size: 9pt;
                border: 1px solid #ccc;
                background-color: white;
                padding: 4px;
            }
        """)
        anomaly_layout.addWidget(self.anomaly_text)
        
        # 参数设置 - 简洁布局
        params_widget = QWidget()
        params_layout = QVBoxLayout(params_widget)
        params_layout.setSpacing(6)
        params_layout.setContentsMargins(0, 8, 0, 0)
        
        # 参数标题
        params_title = QLabel("参数设置")
        params_title.setFont(QFont("Arial", 10, QFont.Bold))
        params_title.setStyleSheet("color: #333; margin-bottom: 4px;")
        params_layout.addWidget(params_title)
        
        # 标准直径
        std_layout = QHBoxLayout()
        std_label = QLabel("标准直径:")
        std_label.setFont(QFont("Arial", 9))
        std_label.setMinimumWidth(65)
        self.std_diameter_input = QLineEdit(str(self.standard_diameter))
        self.std_diameter_input.setMaximumWidth(50)
        self.std_diameter_input.setFont(QFont("Arial", 9))
        self.std_diameter_input.editingFinished.connect(self._update_standard_diameter)
        mm_label1 = QLabel("mm")
        mm_label1.setFont(QFont("Arial", 9))
        
        std_layout.addWidget(std_label)
        std_layout.addWidget(self.std_diameter_input)
        std_layout.addWidget(mm_label1)
        std_layout.addStretch()
        
        # 公差范围
        tolerance_layout = QHBoxLayout()
        tolerance_label = QLabel("公差范围:")
        tolerance_label.setFont(QFont("Arial", 9))
        tolerance_label.setMinimumWidth(65)
        self.tolerance_input = QLineEdit(f"+{self.tolerance_upper}/-{self.tolerance_lower}")
        self.tolerance_input.setMaximumWidth(50)
        self.tolerance_input.setFont(QFont("Arial", 9))
        self.tolerance_input.editingFinished.connect(self._update_tolerance)
        mm_label2 = QLabel("mm")
        mm_label2.setFont(QFont("Arial", 9))
        
        tolerance_layout.addWidget(tolerance_label)
        tolerance_layout.addWidget(self.tolerance_input)
        tolerance_layout.addWidget(mm_label2)
        tolerance_layout.addStretch()
        
        params_layout.addLayout(std_layout)
        params_layout.addLayout(tolerance_layout)
        
        anomaly_layout.addWidget(params_widget)
        
        # 导出按钮 - 简洁样式
        export_btn = QPushButton("导出异常数据")
        export_btn.clicked.connect(self._export_anomaly_data)
        export_btn.setFixedHeight(26)
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                color: white;
                font-size: 9pt;
                border: none;
                border-radius: 3px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
        """)
        anomaly_layout.addWidget(export_btn)
        
        anomaly_layout.addStretch()
        splitter.addWidget(anomaly_group)
        
    def _create_endoscope_display(self, splitter):
        """创建内窥镜显示区域 - 简单占位符"""
        endoscope_group = QGroupBox("内窥镜检测")
        endoscope_layout = QVBoxLayout(endoscope_group)
        endoscope_layout.setContentsMargins(8, 8, 8, 8)
        
        # 简单占位符
        endoscope_label = QLabel("内窥镜图像显示")
        endoscope_label.setAlignment(Qt.AlignCenter)
        endoscope_label.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border: 2px dashed #ccc;
                color: #666;
                font-size: 14pt;
                padding: 20px;
            }
        """)
        endoscope_label.setMinimumHeight(350)  # 增加最小高度，确保充足显示空间
        
        endoscope_layout.addWidget(endoscope_label)
        splitter.addWidget(endoscope_group)
        
    def _update_standard_diameter(self):
        """更新标准直径"""
        try:
            new_diameter = float(self.std_diameter_input.text())
            self.standard_diameter = new_diameter
            self._update_tolerance_band()
            self.canvas.draw()
            self.logger.info(f"标准直径更新为: {new_diameter}mm")
        except ValueError:
            self.std_diameter_input.setText(str(self.standard_diameter))
            self.logger.warning("标准直径输入格式错误")
            
    def _update_tolerance(self):
        """更新公差范围"""
        try:
            text = self.tolerance_input.text().strip()
            # 解析格式如 "+0.1/-0.05" 或 "±0.1"
            if "±" in text:
                # 对称公差
                tolerance_val = float(text.replace("±", ""))
                self.tolerance_upper = tolerance_val
                self.tolerance_lower = tolerance_val
                self.tolerance_input.setText(f"±{tolerance_val}")
            elif "/" in text:
                # 非对称公差
                parts = text.replace("+", "").split("/")
                if len(parts) == 2:
                    self.tolerance_upper = float(parts[0])
                    self.tolerance_lower = float(parts[1].replace("-", ""))
                    self.tolerance_input.setText(f"+{self.tolerance_upper}/-{self.tolerance_lower}")
            else:
                # 单个值，当作对称公差
                tolerance_val = float(text.replace("+", "").replace("-", ""))
                self.tolerance_upper = tolerance_val
                self.tolerance_lower = tolerance_val
                self.tolerance_input.setText(f"±{tolerance_val}")
                
            self._update_tolerance_band()
            self.canvas.draw()
            self.logger.info(f"公差范围更新为: +{self.tolerance_upper}/-{self.tolerance_lower}mm")
        except ValueError:
            self.tolerance_input.setText(f"+{self.tolerance_upper}/-{self.tolerance_lower}")
            self.logger.warning("公差范围输入格式错误")
        
    def _init_timer(self):
        """初始化定时器"""
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._update_monitoring_data)
        
    def _on_hole_changed(self, hole_id: str):
        """孔位改变处理"""
        self.current_hole = hole_id
        self.hole_selected.emit(hole_id)
        self.logger.info(f"切换到孔位: {hole_id}")
        
    def _toggle_monitoring(self):
        """切换监控状态"""
        self.is_monitoring = self.start_btn.isChecked()
        
        if self.is_monitoring:
            self.start_btn.setText("停止监控")
            self.status_display.setText("监控中...")
            self.status_display.setStyleSheet("color: green; font-weight: bold; font-size: 9pt;")
            
            # 开始定时器（每500ms更新一次）
            self.monitor_timer.start(500)
            
            self.monitoring_started.emit()
            self.logger.info("开始监控")
            
        else:
            self.start_btn.setText("开始监控")
            self.status_display.setText("已停止")
            self.status_display.setStyleSheet("color: red; font-weight: bold; font-size: 9pt;")
            
            # 停止定时器
            self.monitor_timer.stop()
            
            self.monitoring_stopped.emit()
            self.logger.info("停止监控")
            
    def _update_monitoring_data(self):
        """更新监控数据 - 生成模拟数据并更新图表"""
        if not self.is_monitoring:
            return
            
        # 生成模拟数据
        import random
        import math
        
        self.simulation_time += 0.1
        
        # 生成直径数据（基于标准直径）
        base_diameter = self.standard_diameter
        noise = random.gauss(0, 0.02)  # 小噪声
        periodic = 0.05 * math.sin(self.simulation_time * 0.5)  # 周期性变化
        
        # 偶尔产生异常值
        if random.random() < 0.08:  # 8%概率产生异常
            diameter = base_diameter + random.uniform(-0.3, 0.3)
        else:
            diameter = base_diameter + noise + periodic
            
        # 生成深度数据
        depth = self.simulation_time * 2.0
        
        # 添加数据点
        self._add_data_point(self.simulation_time, diameter, depth)
            
    def _add_data_point(self, time_val, diameter, depth=None):
        """添加数据点到缓冲区"""
        self.time_data.append(time_val)
        self.diameter_data.append(diameter)
        self.depth_data.append(depth if depth is not None else 0)
        
        # 更新计数
        self.data_count += 1
        self.data_count_label.setText(f"数据: {self.data_count} 条")
        
        # 检查异常
        deviation = diameter - self.standard_diameter
        # 检查是否超出公差范围
        is_anomaly = (deviation > self.tolerance_upper or deviation < -self.tolerance_lower)
        if is_anomaly:
            anomaly = {
                'time': time_val,
                'diameter': diameter,
                'deviation': deviation
            }
            self.anomaly_data.append(anomaly)
            self._add_anomaly_display(anomaly)
            self.anomaly_count += 1
            self.anomaly_count_label.setText(f"异常: {self.anomaly_count} 条")
            
        # 更新图表
        self._update_chart()
        
    def _add_anomaly_display(self, anomaly):
        """添加异常显示到文本区域"""
        time_str = f"{anomaly['time']:.2f}s"
        diameter_str = f"{anomaly['diameter']:.3f}mm"
        deviation_str = f"{anomaly['deviation']:+.3f}mm"
        
        # 判断严重程度：超出2倍公差为红色，否则为橙色
        max_tolerance = max(self.tolerance_upper, self.tolerance_lower)
        color = "red" if abs(anomaly['deviation']) > max_tolerance * 2 else "orange"
        html = f'<span style="color: {color};">时间: {time_str}, 直径: {diameter_str}, 偏差: {deviation_str}</span><br>'
        
        cursor = self.anomaly_text.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertHtml(html)
        
        # 更新统计信息
        self._update_anomaly_statistics()
        
    def _update_anomaly_statistics(self):
        """更新异常统计信息"""
        self.total_anomalies_label.setText(f"总异常数: {len(self.anomaly_data)}")
        
        if self.anomaly_data:
            max_deviation = max(abs(a['deviation']) for a in self.anomaly_data)
            avg_deviation = sum(abs(a['deviation']) for a in self.anomaly_data) / len(self.anomaly_data)
            
            self.max_deviation_label.setText(f"最大偏差: {max_deviation:.3f} mm")
            self.avg_deviation_label.setText(f"平均偏差: {avg_deviation:.3f} mm")
        else:
            self.max_deviation_label.setText("最大偏差: 0.000 mm")
            self.avg_deviation_label.setText("平均偏差: 0.000 mm")
            
    def _update_chart(self):
        """更新matplotlib图表"""
        if not self.time_data:
            return
            
        # 更新数据线
        self.line.set_data(list(self.time_data), list(self.diameter_data))
        
        # 更新异常点
        if self.anomaly_data:
            anomaly_times = [a['time'] for a in self.anomaly_data]
            anomaly_diameters = [a['diameter'] for a in self.anomaly_data]
            self.anomaly_scatter.set_offsets(np.c_[anomaly_times, anomaly_diameters])
            
        # 自动调整x轴（滚动显示最近60秒）
        if self.time_data:
            max_time = max(self.time_data)
            if max_time > 60:
                self.ax.set_xlim(max_time - 60, max_time)
                # 更新公差带位置
                for patch in self.ax.patches:
                    patch.remove()
                tolerance_band = patches.Rectangle(
                    (max_time - 60, self.standard_diameter - self.tolerance_lower),
                    60,
                    self.tolerance_upper + self.tolerance_lower,
                    alpha=0.2,
                    facecolor='green',
                    edgecolor='none'
                )
                self.ax.add_patch(tolerance_band)
            else:
                self.ax.set_xlim(0, 60)
                
        # 自动调整y轴
        if self.diameter_data:
            min_d = min(self.diameter_data)
            max_d = max(self.diameter_data)
            margin = max(0.2, (max_d - min_d) * 0.1)
            self.ax.set_ylim(min_d - margin, max_d + margin)
            
        # 重绘图表
        self.canvas.draw()
            
        
    def _clear_data(self):
        """清除所有数据"""
        # 清除数据缓冲区
        self.time_data.clear()
        self.diameter_data.clear()
        self.depth_data.clear()
        self.anomaly_data.clear()
        
        # 重置计数
        self.data_count = 0
        self.anomaly_count = 0
        self.simulation_time = 0
        
        # 更新UI显示
        self.data_count_label.setText("数据: 0 条")
        self.anomaly_count_label.setText("异常: 0 条")
        
        # 清除异常文本显示
        self.anomaly_text.clear()
        
        # 重置统计
        self.total_anomalies_label.setText("总异常数: 0")
        self.max_deviation_label.setText("最大偏差: 0.000 mm")
        self.avg_deviation_label.setText("平均偏差: 0.000 mm")
        
        # 重新初始化图表
        self._setup_chart()
        self.canvas.draw()
        
        self.logger.info("数据已清除")
        
    def _export_anomaly_data(self):
        """导出异常数据"""
        if not self.anomaly_data:
            self.logger.warning("没有异常数据可导出")
            return
            
        try:
            from datetime import datetime
            filename = f"anomaly_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            # 创建CSV内容
            csv_content = "时间(秒),直径(mm),偏差(mm),孔位\n"
            for anomaly in self.anomaly_data:
                csv_content += f"{anomaly['time']:.2f},{anomaly['diameter']:.3f},{anomaly['deviation']:+.3f},{self.current_hole}\n"
            
            # 模拟导出（实际应用中应该保存到文件）
            self.logger.info(f"异常数据已导出到: {filename} (共{len(self.anomaly_data)}条)")
            
        except Exception as e:
            self.logger.error(f"导出异常数据失败: {e}")
    
    def load_data_for_hole(self, hole_id: str):
        """为特定孔位加载数据（预留接口）"""
        self.current_hole = hole_id
        self.hole_combo.setCurrentText(hole_id)
        
        # TODO: 这里可以集成真实的数据文件读取逻辑
        # 例如从 Data/Products/{product_id}/holes/{hole_id}/ 读取CSV文件
        # 目前使用模拟数据
        
        self.logger.info(f"已切换到孔位: {hole_id}，准备加载数据")
            
    def get_current_hole(self) -> str:
        """获取当前孔位"""
        return self.current_hole
        
    def is_monitoring_active(self) -> bool:
        """检查是否正在监控"""
        return self.is_monitoring
        
    def get_monitoring_statistics(self) -> dict:
        """获取监控统计信息"""
        return {
            'total_data': self.data_count,
            'total_anomalies': self.anomaly_count,
            'current_hole': self.current_hole,
            'is_monitoring': self.is_monitoring
        }