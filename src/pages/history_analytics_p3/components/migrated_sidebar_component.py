"""
迁移的侧边栏组件 - 高内聚
直接从重构前代码迁移，专门负责左侧数据筛选和操作功能
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QLabel, QPushButton, QComboBox, QGroupBox, 
                               QTextEdit, QToolButton, QMenu)
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QAction
import numpy as np


class ScrollableTextLabel(QLabel):
    """可滚动的文本标签 - 从重构前代码直接迁移"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.full_text = ""
        self.placeholder_text = ""
        self.scroll_timer = QTimer()
        self.scroll_timer.timeout.connect(self.scroll_text)
        self.scroll_offset = 0
        self.scroll_direction = 1
        self.pause_counter = 0
        self.max_scroll_offset = 0
        self.text_width = 0
        self.visible_width = 0
        self.scroll_step = 1
        self.setStyleSheet("""
            QLabel {
                border: 1px solid #505869;
                padding: 5px;
                background-color: #2a2d35;
                color: #D3D8E0;
                text-align: left;
            }
        """)
        
    def setPlaceholderText(self, text):
        """设置占位符文本"""
        self.placeholder_text = text
        if not self.full_text:
            super().setText(text)
            
    def setText(self, text):
        """设置文本并启动滚动"""
        self.full_text = text
        if not text:
            super().setText(self.placeholder_text)
            self.scroll_timer.stop()
            return
            
        super().setText(text)
        self.check_text_overflow()
        
    def check_text_overflow(self):
        """检查文本是否溢出并决定是否启动滚动"""
        if not self.full_text:
            return
            
        font_metrics = self.fontMetrics()
        self.text_width = font_metrics.horizontalAdvance(self.full_text)
        self.visible_width = self.width() - 12  # 减去padding
        
        if self.text_width > self.visible_width:
            self.max_scroll_offset = self.text_width - self.visible_width
            self.start_scrolling()
        else:
            self.scroll_timer.stop()
            
    def start_scrolling(self):
        """开始滚动"""
        if not self.scroll_timer.isActive():
            self.scroll_offset = 0
            self.scroll_direction = 1
            self.pause_counter = 0
            self.scroll_timer.start(50)
            
    def scroll_text(self):
        """滚动文本"""
        if not self.full_text:
            return
            
        # 在两端暂停
        if self.scroll_offset <= 0 or self.scroll_offset >= self.max_scroll_offset:
            if self.pause_counter < 30:  # 暂停1.5秒
                self.pause_counter += 1
                return
            else:
                self.scroll_direction *= -1
                self.pause_counter = 0
                
        self.scroll_offset += self.scroll_direction * self.scroll_step
        self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll_offset))
        
        # 更新显示的文本
        font_metrics = self.fontMetrics()
        char_width = font_metrics.averageCharWidth()
        start_char = max(0, int(self.scroll_offset / char_width))
        visible_chars = int(self.visible_width / char_width)
        
        if start_char < len(self.full_text):
            visible_text = self.full_text[start_char:start_char + visible_chars + 1]
            super().setText(visible_text)
            
    def resizeEvent(self, event):
        """窗口大小改变时重新检查滚动"""
        super().resizeEvent(event)
        if self.full_text:
            self.check_text_overflow()
            
    def clear(self):
        """清除文本"""
        self.full_text = ""
        self.scroll_timer.stop()
        super().setText(self.placeholder_text)


class MigratedSidebarComponent(QWidget):
    """
    迁移的侧边栏组件 - 高内聚设计
    职责：专门负责左侧数据筛选和操作功能
    直接从重构前的 create_sidebar 方法迁移而来
    """
    
    # 信号定义 - 低耦合通信
    workpiece_selected = Signal(str)
    hole_selected = Signal(str)
    query_requested = Signal(str)
    export_requested = Signal()
    review_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_initial_data()
        
    def setup_ui(self):
        """设置用户界面 - 直接从重构前代码迁移"""
        self.setObjectName("Sidebar")
        self.setMinimumWidth(200)
        self.setMaximumWidth(250)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(25)
        
        # 标题
        title_label = QLabel("光谱共焦历史数据查看器")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #D3D8E0;
                padding: 10px;
                background-color: #3a3d45;
                border: 1px solid #505869;
                border-radius: 5px;
            }
        """)
        layout.addWidget(title_label)
        
        # 数据筛选部分
        self.create_data_filter_section(layout)
        
        # 操作命令部分
        self.create_operation_section(layout)
        
        # 当前状态部分
        self.create_status_section(layout)
        
        layout.addStretch()
        
    def create_data_filter_section(self, parent_layout):
        """创建数据筛选部分 - 直接从重构前迁移"""
        filter_group = QGroupBox("数据筛选")
        filter_group.setStyleSheet("""
            QGroupBox {
                font-size: 11px;
                font-weight: bold;
                color: #D3D8E0;
                border: 1px solid #505869;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #313642;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        filter_layout = QGridLayout(filter_group)
        filter_layout.setContentsMargins(10, 15, 10, 15)
        filter_layout.setSpacing(15)
        
        # 工件ID
        workpiece_label = QLabel("工件ID:")
        workpiece_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.wp_display = ScrollableTextLabel()
        self.wp_button = QToolButton()
        self.wp_button.setText("▼")
        self.wp_button.setMinimumWidth(30)
        self.wp_button.setStyleSheet(self.get_button_style())
        self.wp_button.clicked.connect(self.show_workpiece_menu)
        
        wp_combo_layout = QHBoxLayout()
        wp_combo_layout.setSpacing(0)
        wp_combo_layout.setContentsMargins(0, 0, 0, 0)
        wp_combo_layout.addWidget(self.wp_display)
        wp_combo_layout.addWidget(self.wp_button)
        
        # 合格孔ID
        qualified_label = QLabel("合格孔ID:")
        qualified_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.ql_display = ScrollableTextLabel()
        self.ql_display.setPlaceholderText("请选择合格孔ID")
        self.ql_button = QToolButton()
        self.ql_button.setText("▼")
        self.ql_button.setMinimumWidth(30)
        self.ql_button.setStyleSheet(self.get_button_style())
        self.ql_button.clicked.connect(self.show_qualified_hole_menu)
        
        ql_combo_layout = QHBoxLayout()
        ql_combo_layout.setSpacing(0)
        ql_combo_layout.setContentsMargins(0, 0, 0, 0)
        ql_combo_layout.addWidget(self.ql_display)
        ql_combo_layout.addWidget(self.ql_button)
        
        # 不合格孔ID
        unqualified_label = QLabel("不合格孔ID:")
        unqualified_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.uql_display = ScrollableTextLabel()
        self.uql_display.setPlaceholderText("请选择不合格孔ID")
        self.uql_button = QToolButton()
        self.uql_button.setText("▼")
        self.uql_button.setMinimumWidth(30)
        self.uql_button.setStyleSheet(self.get_button_style())
        self.uql_button.clicked.connect(self.show_unqualified_hole_menu)
        
        uql_combo_layout = QHBoxLayout()
        uql_combo_layout.setSpacing(0)
        uql_combo_layout.setContentsMargins(0, 0, 0, 0)
        uql_combo_layout.addWidget(self.uql_display)
        uql_combo_layout.addWidget(self.uql_button)
        
        # 添加到网格布局
        filter_layout.addWidget(workpiece_label, 0, 0)
        filter_layout.addLayout(wp_combo_layout, 0, 1)
        filter_layout.addWidget(qualified_label, 1, 0)
        filter_layout.addLayout(ql_combo_layout, 1, 1)
        filter_layout.addWidget(unqualified_label, 2, 0)
        filter_layout.addLayout(uql_combo_layout, 2, 1)
        
        parent_layout.addWidget(filter_group)
        
        # 创建隐藏的ComboBox用于数据管理
        self.workpiece_combo = QComboBox()
        self.qualified_hole_combo = QComboBox()
        self.unqualified_hole_combo = QComboBox()
        
    def create_operation_section(self, parent_layout):
        """创建操作命令部分"""
        ops_group = QGroupBox("操作命令")
        ops_group.setStyleSheet("""
            QGroupBox {
                font-size: 13px;
                font-weight: bold;
                color: #D3D8E0;
                border: 1px solid #505869;
                border-radius: 5px;
                margin-top: 12px;
                padding-top: 12px;
                background-color: #313642;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        ops_layout = QVBoxLayout(ops_group)
        ops_layout.setSpacing(18)  # 从重构前的18px间距
        ops_layout.setContentsMargins(15, 20, 15, 15)
        
        button_style = """
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 12px 18px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
                min-height: 22px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #888;
            }
        """
        
        # 查询数据按钮
        self.query_button = QPushButton("查询数据")
        self.query_button.setStyleSheet(button_style)
        self.query_button.clicked.connect(self.on_query_clicked)
        ops_layout.addWidget(self.query_button)
        
        # 导出数据按钮
        self.export_button = QPushButton("导出数据")
        self.export_button.setStyleSheet(button_style)
        self.export_button.setEnabled(False)
        self.export_button.clicked.connect(self.on_export_clicked)
        ops_layout.addWidget(self.export_button)
        
        # 人工复查按钮
        self.review_button = QPushButton("人工复查")
        self.review_button.setStyleSheet(button_style)
        self.review_button.setEnabled(False)
        self.review_button.clicked.connect(self.on_review_clicked)
        ops_layout.addWidget(self.review_button)
        
        parent_layout.addWidget(ops_group)
        
    def create_status_section(self, parent_layout):
        """创建状态显示部分"""
        status_group = QGroupBox("当前状态")
        status_group.setStyleSheet("""
            QGroupBox {
                font-size: 11px;
                font-weight: bold;
                color: #D3D8E0;
                border: 1px solid #505869;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #313642;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        status_layout = QVBoxLayout(status_group)
        status_layout.setContentsMargins(15, 20, 15, 15)
        
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setPlainText("请选择孔位加载数据")
        self.status_text.setStyleSheet("""
            QTextEdit {
                background-color: #1a1d23;
                border: 1px solid #505869;
                color: #D3D8E0;
                font-size: 12px;
                font-weight: bold;
                padding: 10px;
                border-radius: 3px;
                line-height: 1.5;
            }
        """)
        self.status_text.setReadOnly(True)
        
        status_layout.addWidget(self.status_text)
        parent_layout.addWidget(status_group)
        
    def get_button_style(self):
        """获取按钮样式"""
        return """
            QToolButton {
                border: 1px solid #505869;
                background-color: #2a2d35;
                color: #D3D8E0;
                padding: 4px;
            }
            QToolButton:hover {
                background-color: #3a3d45;
            }
            QToolButton:pressed {
                background-color: #1a1d25;
            }
        """
        
    def load_initial_data(self):
        """加载初始数据"""
        # 加载工件列表
        self.workpiece_combo.addItem("CAP1000")
        self.wp_display.setText("CAP1000")
        self.load_hole_list("CAP1000")
        
    def load_hole_list(self, workpiece_id):
        """加载孔位列表 - 直接从重构前代码迁移"""
        print(f"🔍 加载工件 {workpiece_id} 的孔位列表...")
        
        # 清空现有选项
        self.qualified_hole_combo.clear()
        self.unqualified_hole_combo.clear()
        self.ql_display.clear()
        self.uql_display.clear()
        
        try:
            # 导入真实数据读取器
            from ..services.real_csv_reader import RealCSVReader
            
            csv_reader = RealCSVReader()
            available_holes = csv_reader.get_available_holes(workpiece_id)
            
            if available_holes:
                print(f"📁 从文件系统发现 {len(available_holes)} 个真实孔位: {', '.join(available_holes)}")
                # 使用重构前的分类逻辑
                qualified_holes, unqualified_holes = self.classify_holes_by_quality(available_holes, csv_reader)
                
                # 添加合格孔位选项到下拉框（严格验证格式）
                if qualified_holes:
                    for hole_id in qualified_holes:
                        if self._validate_hole_id_format(hole_id):
                            print(f"🔍 正在添加合格孔位到下拉框: {hole_id}")
                            self.qualified_hole_combo.addItem(hole_id)
                        else:
                            print(f"❌ 跳过无效格式的孔位ID: {hole_id}")
                    print(f"✅ 加载了 {len(qualified_holes)} 个合格孔位: {', '.join(qualified_holes)}")
                        
                # 添加不合格孔位选项到下拉框（严格验证格式）
                if unqualified_holes:
                    for hole_id in unqualified_holes:
                        if self._validate_hole_id_format(hole_id):
                            print(f"🔍 正在添加不合格孔位到下拉框: {hole_id}")
                            self.unqualified_hole_combo.addItem(hole_id)
                        else:
                            print(f"❌ 跳过无效格式的孔位ID: {hole_id}")
                    print(f"✅ 加载了 {len(unqualified_holes)} 个不合格孔位: {', '.join(unqualified_holes)}")
                
            else:
                print("⚠️ 未找到真实数据文件，孔位列表为空")
                    
        except Exception as e:
            print(f"❌ 加载孔位列表失败: {e}")
            print("⚠️ 无可用孔位数据")
    
    def _validate_hole_id_format(self, hole_id: str) -> bool:
        """验证孔位ID格式是否有效"""
        if not hole_id:
            return False
        # 必须以R开头，包含C，且长度合理
        return (hole_id.startswith('R') and 
                'C' in hole_id and 
                len(hole_id) >= 7 and 
                len(hole_id) <= 10)
                
    def classify_holes_by_quality(self, available_holes, csv_reader):
        """根据测量数据将孔位分类为合格和不合格 - 只处理有实际数据的孔位"""
        qualified_holes = []
        unqualified_holes = []
        
        print(f"🔍 开始分析 {len(available_holes)} 个孔位的数据质量...")
        
        for hole_id in available_holes:
            # 首先检查是否有测量数据
            measurements = csv_reader.load_csv_data_for_hole(hole_id)
            if not measurements:
                print(f"  ⚠️ {hole_id}: 无数据文件，跳过")
                continue  # 跳过没有数据的孔位
                
            # 对有数据的孔位进行质量分析
            if self.is_hole_qualified(hole_id, csv_reader):
                qualified_holes.append(hole_id)
                print(f"  ✅ {hole_id}: 数据分析-合格")
            else:
                unqualified_holes.append(hole_id)
                print(f"  ❌ {hole_id}: 数据分析-不合格")
                    
        print(f"📊 分析结果: 合格 {len(qualified_holes)} 个, 不合格 {len(unqualified_holes)} 个")
        return qualified_holes, unqualified_holes
        
    def is_hole_qualified(self, hole_id, csv_reader):
        """判断管孔是否合格 - 直接从重构前代码迁移"""
        try:
            # 加载孔位的测量数据
            measurements = csv_reader.load_csv_data_for_hole(hole_id)
            if not measurements:
                print(f"⚠️ 孔位 {hole_id} 无测量数据")
                return False
                
            # 计算合格率
            qualified_count = 0
            total_count = len(measurements)
            
            for measurement in measurements:
                # 使用重构前的判断键名
                if measurement.get('is_qualified', False) or measurement.get('qualified', False):
                    qualified_count += 1
                    
            qualified_rate = qualified_count / total_count * 100
            print(f"📊 孔位 {hole_id} 合格率: {qualified_rate:.1f}% ({qualified_count}/{total_count})")
            
            # 合格率大于等于95%认为合格 - 重构前的标准
            return qualified_rate >= 95.0
            
        except Exception as e:
            print(f"❌ 判断孔位 {hole_id} 合格性失败: {e}")
            return False
        
    # === 菜单显示方法 ===
    
    def show_workpiece_menu(self):
        """显示工件选择菜单"""
        menu = QMenu(self)
        for i in range(self.workpiece_combo.count()):
            text = self.workpiece_combo.itemText(i)
            action = menu.addAction(text)
            action.triggered.connect(lambda checked, t=text: self.select_workpiece(t))
        menu.exec(self.wp_button.mapToGlobal(self.wp_button.rect().bottomLeft()))
        
    def show_qualified_hole_menu(self):
        """显示合格孔位选择菜单"""
        menu = QMenu(self)
        for i in range(self.qualified_hole_combo.count()):
            text = self.qualified_hole_combo.itemText(i)
            action = menu.addAction(text)
            action.triggered.connect(lambda checked, t=text: self.select_qualified_hole(t))
        menu.exec(self.ql_button.mapToGlobal(self.ql_button.rect().bottomLeft()))
        
    def show_unqualified_hole_menu(self):
        """显示不合格孔位选择菜单"""
        menu = QMenu(self)
        if self.unqualified_hole_combo.count() == 0:
            action = menu.addAction("暂无不合格孔位")
            action.setEnabled(False)
        else:
            for i in range(self.unqualified_hole_combo.count()):
                text = self.unqualified_hole_combo.itemText(i)
                action = menu.addAction(text)
                action.triggered.connect(lambda checked, t=text: self.select_unqualified_hole(t))
        menu.exec(self.uql_button.mapToGlobal(self.uql_button.rect().bottomLeft()))
        
    # === 选择处理方法 ===
    
    def select_workpiece(self, workpiece_id):
        """选择工件"""
        self.wp_display.setText(workpiece_id)
        self.workpiece_combo.setCurrentText(workpiece_id)
        self.load_hole_list(workpiece_id)
        self.workpiece_selected.emit(workpiece_id)
        
    def select_qualified_hole(self, hole_id):
        """选择合格孔位"""
        print(f"🎯 选择合格孔位: {hole_id}")
        self.ql_display.setText(hole_id)
        self.qualified_hole_combo.setCurrentText(hole_id)
        # 清空不合格孔位选择
        self.uql_display.clear()
        print(f"📝 合格孔位显示标签内容: full_text='{self.ql_display.full_text}', text='{self.ql_display.text()}'")
        self.hole_selected.emit(hole_id)
        
    def select_unqualified_hole(self, hole_id):
        """选择不合格孔位"""
        print(f"🎯 选择不合格孔位: {hole_id}")
        self.uql_display.setText(hole_id)
        self.unqualified_hole_combo.setCurrentText(hole_id)
        # 清空合格孔位选择
        self.ql_display.clear()
        print(f"📝 不合格孔位显示标签内容: full_text='{self.uql_display.full_text}', text='{self.uql_display.text()}'")
        self.hole_selected.emit(hole_id)
        
    # === 事件处理方法 ===
    
    def on_query_clicked(self):
        """查询按钮点击处理"""
        # 从完整文本获取孔位ID，避免滚动截断问题
        qualified_hole = self.ql_display.full_text if self.ql_display.full_text and self.ql_display.full_text != self.ql_display.placeholder_text else ""
        unqualified_hole = self.uql_display.full_text if self.uql_display.full_text and self.uql_display.full_text != self.uql_display.placeholder_text else ""
        
        selected_hole = qualified_hole or unqualified_hole
        
        print(f"🔍 获取到的孔位ID: 合格='{qualified_hole}', 不合格='{unqualified_hole}', 选中='{selected_hole}'")
        
        if not selected_hole:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "警告", "请选择合格孔ID或不合格孔ID")
            return
            
        self.query_requested.emit(selected_hole)
        
    def on_export_clicked(self):
        """导出按钮点击处理"""
        self.export_requested.emit()
        
    def on_review_clicked(self):
        """复查按钮点击处理"""
        self.review_requested.emit()
        
    # === 外部接口方法 ===
    
    def enable_operations(self, enabled):
        """启用/禁用操作按钮"""
        self.export_button.setEnabled(enabled)
        self.review_button.setEnabled(enabled)
        
    def update_status(self, text):
        """更新状态显示"""
        self.status_text.setPlainText(text)
        
    def get_selected_hole(self):
        """获取当前选择的孔位"""
        # 从完整文本获取孔位ID，避免滚动截断问题
        qualified_hole = self.ql_display.full_text if self.ql_display.full_text and self.ql_display.full_text != self.ql_display.placeholder_text else ""
        unqualified_hole = self.uql_display.full_text if self.uql_display.full_text and self.uql_display.full_text != self.uql_display.placeholder_text else ""
        return qualified_hole or unqualified_hole