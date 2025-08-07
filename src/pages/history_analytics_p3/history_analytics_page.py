"""
P3历史数据分析页面 - 完全基于重构前代码恢复
按照高内聚，低耦合原则重构，保持原有功能和布局
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QStackedWidget, QGroupBox, QTableWidget, QTableWidgetItem,
    QSplitter, QTextEdit, QHeaderView, QListWidget, QListWidgetItem,
    QPushButton, QColorDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
import logging

# 导入模块化组件
from .history_main_view import HistoryMainView


class SimpleHistoryViewer(QWidget):
    """简化的历史数据查看器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_sample_data()
        
    def init_ui(self):
        """初始化UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 标题
        header_label = QLabel("管孔直径历史数据")
        header_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        main_layout.addWidget(header_label)
        
        # 状态信息
        status_layout = QHBoxLayout()
        self.hole_label = QLabel("当前孔位: 未选择")
        self.status_label = QLabel("状态: 就绪")
        self.status_label.setStyleSheet("color: #4CAF50;")
        
        status_layout.addWidget(self.hole_label)
        status_layout.addStretch()
        status_layout.addWidget(self.status_label)
        main_layout.addLayout(status_layout)
        
        # 内容区域
        content_splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：数据表格
        self.create_data_table(content_splitter)
        
        # 右侧：统计信息
        self.create_stats_panel(content_splitter)
        
        # 设置分割比例
        content_splitter.setSizes([800, 400])
        main_layout.addWidget(content_splitter)
        
    def create_data_table(self, parent):
        """创建数据表格"""
        table_group = QGroupBox("历史测量数据")
        table_layout = QVBoxLayout(table_group)
        
        # 创建表格
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(5)
        self.data_table.setHorizontalHeaderLabels([
            "测量时间", "管孔直径(mm)", "深度(mm)", "质量等级", "备注"
        ])
        
        # 设置表格属性
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        # 设置列宽
        header = self.data_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        
        self.data_table.setColumnWidth(1, 120)
        self.data_table.setColumnWidth(2, 100)
        self.data_table.setColumnWidth(3, 100)
        
        table_layout.addWidget(self.data_table)
        parent.addWidget(table_group)
        
    def create_stats_panel(self, parent):
        """创建统计面板"""
        stats_group = QGroupBox("详细信息")
        stats_layout = QVBoxLayout(stats_group)
        
        # 统计信息标签
        self.total_count_label = QLabel("总测量次数: 0")
        self.avg_diameter_label = QLabel("平均直径: 0.00 mm")
        self.min_diameter_label = QLabel("最小直径: 0.00 mm")
        self.max_diameter_label = QLabel("最大直径: 0.00 mm")
        
        stats_layout.addWidget(self.total_count_label)
        stats_layout.addWidget(self.avg_diameter_label)
        stats_layout.addWidget(self.min_diameter_label)
        stats_layout.addWidget(self.max_diameter_label)
        
        # 备注区域
        notes_label = QLabel("备注信息:")
        self.notes_text = QTextEdit()
        self.notes_text.setMaximumHeight(100)
        self.notes_text.setPlaceholderText("选择测量记录查看备注...")
        
        stats_layout.addWidget(notes_label)
        stats_layout.addWidget(self.notes_text)
        stats_layout.addStretch()
        
        parent.addWidget(stats_group)
        
    def load_sample_data(self):
        """加载示例数据"""
        sample_data = [
            ["2024-01-15 09:30:00", "12.50", "25.0", "优秀", "正常测量"],
            ["2024-01-14 14:20:00", "12.48", "24.8", "良好", "轻微偏差"],
            ["2024-01-13 11:45:00", "12.52", "25.2", "优秀", "标准范围内"],
            ["2024-01-12 16:10:00", "12.49", "24.9", "良好", "正常测量"],
            ["2024-01-11 10:25:00", "12.51", "25.1", "优秀", "质量良好"],
        ]
        
        self.data_table.setRowCount(len(sample_data))
        for row, data in enumerate(sample_data):
            for col, value in enumerate(data):
                item = QTableWidgetItem(str(value))
                self.data_table.setItem(row, col, item)
        
        # 更新统计信息
        diameters = [float(data[1]) for data in sample_data]
        self.total_count_label.setText(f"总测量次数: {len(sample_data)}")
        self.avg_diameter_label.setText(f"平均直径: {sum(diameters)/len(diameters):.2f} mm")
        self.min_diameter_label.setText(f"最小直径: {min(diameters):.2f} mm")
        self.max_diameter_label.setText(f"最大直径: {max(diameters):.2f} mm")
        
    def load_data_for_hole(self, hole_id: str):
        """为指定孔位加载数据"""
        self.hole_label.setText(f"当前孔位: {hole_id}")
        self.status_label.setText("状态: 数据已加载")
        print(f"📊 历史数据查看器: 加载孔位 {hole_id} 的数据")


class SimpleDefectViewer(QWidget):
    """简化的缺陷标注查看器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_sample_defects()
        
    def init_ui(self):
        """初始化UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 标题
        header_label = QLabel("缺陷标注管理")
        header_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        main_layout.addWidget(header_label)
        
        # 状态信息
        status_layout = QHBoxLayout()
        self.hole_label = QLabel("当前孔位: 未选择")
        self.defect_count_label = QLabel("缺陷数量: 0")
        self.defect_count_label.setStyleSheet("color: #FF5722;")
        
        status_layout.addWidget(self.hole_label)
        status_layout.addStretch()
        status_layout.addWidget(self.defect_count_label)
        main_layout.addLayout(status_layout)
        
        # 内容区域
        content_splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：缺陷列表
        self.create_defect_list(content_splitter)
        
        # 右侧：缺陷详情
        self.create_defect_details(content_splitter)
        
        # 设置分割比例
        content_splitter.setSizes([600, 600])
        main_layout.addWidget(content_splitter)
        
    def create_defect_list(self, parent):
        """创建缺陷列表"""
        list_group = QGroupBox("缺陷列表")
        list_layout = QVBoxLayout(list_group)
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        add_btn = QPushButton("添加缺陷")
        remove_btn = QPushButton("删除缺陷")
        clear_btn = QPushButton("清空全部")
        
        toolbar_layout.addWidget(add_btn)
        toolbar_layout.addWidget(remove_btn)
        toolbar_layout.addWidget(clear_btn)
        toolbar_layout.addStretch()
        
        # 缺陷列表
        self.defect_list = QListWidget()
        
        list_layout.addLayout(toolbar_layout)
        list_layout.addWidget(self.defect_list)
        parent.addWidget(list_group)
        
    def create_defect_details(self, parent):
        """创建缺陷详情"""
        details_group = QGroupBox("缺陷详情")
        details_layout = QVBoxLayout(details_group)
        
        # 缺陷类型
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("缺陷类型:"))
        type_combo = QComboBox()
        type_combo.addItems(["孔径偏大", "孔径偏小", "孔位偏移", "表面粗糙", "毛刺", "其他"])
        type_layout.addWidget(type_combo)
        
        # 严重程度
        severity_layout = QHBoxLayout()
        severity_layout.addWidget(QLabel("严重程度:"))
        severity_combo = QComboBox()
        severity_combo.addItems(["轻微", "中等", "严重"])
        severity_layout.addWidget(severity_combo)
        
        # 标注颜色
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("标注颜色:"))
        color_btn = QPushButton()
        color_btn.setMaximumSize(50, 30)
        color_btn.setStyleSheet("background-color: red;")
        color_layout.addWidget(color_btn)
        color_layout.addStretch()
        
        # 描述
        desc_label = QLabel("缺陷描述:")
        desc_text = QTextEdit()
        desc_text.setMaximumHeight(100)
        desc_text.setPlaceholderText("请输入缺陷的详细描述...")
        
        # 保存按钮
        save_btn = QPushButton("保存缺陷")
        save_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; }")
        
        details_layout.addLayout(type_layout)
        details_layout.addLayout(severity_layout)
        details_layout.addLayout(color_layout)
        details_layout.addWidget(desc_label)
        details_layout.addWidget(desc_text)
        details_layout.addWidget(save_btn)
        details_layout.addStretch()
        
        parent.addWidget(details_group)
        
    def load_sample_defects(self):
        """加载示例缺陷"""
        sample_defects = [
            "孔径偏大 - 轻微 - 孔径超出容差范围 0.02mm",
            "表面粗糙 - 中等 - 表面粗糙度超标",
            "孔位偏移 - 轻微 - 位置偏差 0.1mm"
        ]
        
        for defect in sample_defects:
            item = QListWidgetItem(defect)
            self.defect_list.addItem(item)
            
        self.defect_count_label.setText(f"缺陷数量: {len(sample_defects)}")
        
    def load_data_for_hole(self, hole_id: str):
        """为指定孔位加载数据"""
        self.hole_label.setText(f"当前孔位: {hole_id}")
        print(f"📊 缺陷标注工具: 加载孔位 {hole_id} 的数据")


class HistoryAnalyticsPage(QWidget):
    """历史数据分析页面 - 统一历史数据查看器"""
    
    view_mode_changed = Signal(str)
    
    def __init__(self, shared_components=None, view_model=None, parent=None):
        super().__init__(parent)
        self.current_mode = "管孔直径"
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 顶部控制面板
        self.create_control_panel(main_layout)
        
        # 内容区域
        self.stacked_widget = QStackedWidget()
        
        # 创建两个页面 - 使用高内聚低耦合的迁移组件
        from .migrated_main_view import MigratedMainView
        self.history_viewer = MigratedMainView()  # 使用高内聚低耦合的迁移主界面
        
        # 使用完整的P3.2缺陷标注工具（重构前完整功能 - 含图片浏览）
        from src.pages.defect_annotation_p32.defect_annotation_with_browser import DefectAnnotationWithBrowser
        self.defect_viewer = DefectAnnotationWithBrowser()
        
        self.stacked_widget.addWidget(self.history_viewer)
        self.stacked_widget.addWidget(self.defect_viewer)
        
        # 默认显示历史数据查看器
        self.stacked_widget.setCurrentWidget(self.history_viewer)
        
        # 连接信号
        self.connect_signals()
        
        main_layout.addWidget(self.stacked_widget)
        
    def create_control_panel(self, parent_layout):
        """创建控制面板"""
        control_group = QGroupBox("数据类型选择")
        control_layout = QHBoxLayout(control_group)
        control_layout.setSpacing(15)
        
        # 选择标签
        select_label = QLabel("查看内容：")
        select_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        control_layout.addWidget(select_label)
        
        # 数据类型下拉框
        self.data_type_combo = QComboBox()
        self.data_type_combo.setMinimumWidth(200)
        self.data_type_combo.addItems(["管孔直径", "缺陷标注"])
        self.data_type_combo.setCurrentText("管孔直径")
        self.data_type_combo.currentTextChanged.connect(self.on_data_type_changed)
        control_layout.addWidget(self.data_type_combo)
        
        # 弹性空间
        control_layout.addStretch()
        
        # 状态标签
        self.status_label = QLabel("当前模式：管孔直径历史数据")
        self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold; font-size: 12px;")
        control_layout.addWidget(self.status_label)
        
        parent_layout.addWidget(control_group)
        
    def connect_signals(self):
        """连接信号 - 高内聚低耦合原则"""
        try:
            # 连接历史查看器信号
            if hasattr(self.history_viewer, 'data_exported'):
                self.history_viewer.data_exported.connect(self.on_data_exported)
            if hasattr(self.history_viewer, 'hole_selected'):
                self.history_viewer.hole_selected.connect(self.on_hole_selected)
                
            logging.info("P3界面信号连接完成")
            
        except Exception as e:
            logging.error(f"P3界面信号连接失败: {e}")
            
    def on_data_exported(self, file_path):
        """数据导出处理"""
        print(f"📤 数据已导出: {file_path}")
        
    def on_hole_selected(self, hole_id):
        """孔位选择处理"""
        print(f"🎯 孔位已选择: {hole_id}")
        
    def on_data_type_changed(self, data_type):
        """数据类型改变处理"""
        print(f"🔄 切换数据类型: {self.current_mode} → {data_type}")
        self.current_mode = data_type
        
        if data_type == "管孔直径":
            self.stacked_widget.setCurrentWidget(self.history_viewer)
            self.status_label.setText("当前模式：管孔直径历史数据")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold; font-size: 12px;")
            print("✅ 切换到历史数据查看器")
        elif data_type == "缺陷标注":
            self.stacked_widget.setCurrentWidget(self.defect_viewer)
            self.status_label.setText("当前模式：缺陷标注工具（含图片浏览）")
            self.status_label.setStyleSheet("color: #2196F3; font-weight: bold; font-size: 12px;")
            print("✅ 切换到缺陷标注工具")
            
        self.view_mode_changed.emit(data_type)
        
    def load_data_for_hole(self, hole_id: str):
        """为指定孔位加载数据"""
        print(f"📊 为孔位 {hole_id} 加载数据 (当前模式: {self.current_mode})")
        
        if self.current_mode == "管孔直径":
            self.history_viewer.load_data_for_hole(hole_id)
        elif self.current_mode == "缺陷标注":
            self.defect_viewer.load_data_for_hole(hole_id)
        
    def get_current_mode(self):
        """获取当前模式"""
        return self.current_mode
        
    def set_mode(self, mode: str):
        """设置模式"""
        if mode in ["管孔直径", "缺陷标注"]:
            self.data_type_combo.setCurrentText(mode)
        
    def get_page_info(self):
        """获取页面信息"""
        return {
            'name': 'history_analytics',
            'title': '历史数据',
            'version': '1.0.0',
            'status': 'active',
            'current_mode': self.current_mode
        }