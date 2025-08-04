"""
缺陷标注工具 - 3.2界面
用于缺陷标注和管理
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QGroupBox, QSplitter,
    QTextEdit, QComboBox, QSpinBox, QColorDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor


class DefectAnnotationTool(QWidget):
    """缺陷标注工具"""
    
    # 信号定义
    defect_added = Signal(str, dict)  # 缺陷添加信号
    defect_removed = Signal(str)  # 缺陷删除信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 缺陷数据
        self.defects = {}
        self.current_hole_id = None
        
        # 初始化UI
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("缺陷标注工具")
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 创建标题区域
        self.create_header(main_layout)
        
        # 创建内容区域
        self.create_content_area(main_layout)
        
    def create_header(self, parent_layout):
        """创建标题区域"""
        header_group = QGroupBox("缺陷标注管理")
        header_layout = QHBoxLayout(header_group)
        
        # 当前孔位标签
        self.hole_label = QLabel("当前孔位: 未选择")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.hole_label.setFont(font)
        
        # 缺陷数量标签
        self.defect_count_label = QLabel("缺陷数量: 0")
        self.defect_count_label.setStyleSheet("color: #D32F2F;")
        
        header_layout.addWidget(self.hole_label)
        header_layout.addStretch()
        header_layout.addWidget(self.defect_count_label)
        
        parent_layout.addWidget(header_group)
        
    def create_content_area(self, parent_layout):
        """创建内容区域"""
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：缺陷列表
        self.create_defect_list(splitter)
        
        # 右侧：缺陷编辑面板
        self.create_edit_panel(splitter)
        
        # 设置分割比例
        splitter.setSizes([400, 400])
        
        parent_layout.addWidget(splitter)
        
    def create_defect_list(self, parent):
        """创建缺陷列表"""
        list_group = QGroupBox("缺陷列表")
        list_layout = QVBoxLayout(list_group)
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        
        self.add_defect_btn = QPushButton("添加缺陷")
        self.remove_defect_btn = QPushButton("删除缺陷")
        self.clear_all_btn = QPushButton("清空全部")
        
        self.add_defect_btn.clicked.connect(self.add_defect)
        self.remove_defect_btn.clicked.connect(self.remove_defect)
        self.clear_all_btn.clicked.connect(self.clear_all_defects)
        
        toolbar_layout.addWidget(self.add_defect_btn)
        toolbar_layout.addWidget(self.remove_defect_btn)
        toolbar_layout.addWidget(self.clear_all_btn)
        toolbar_layout.addStretch()
        
        # 缺陷列表
        self.defect_list = QListWidget()
        self.defect_list.itemSelectionChanged.connect(self.on_defect_selected)
        
        list_layout.addLayout(toolbar_layout)
        list_layout.addWidget(self.defect_list)
        
        parent.addWidget(list_group)
        
    def create_edit_panel(self, parent):
        """创建缺陷编辑面板"""
        edit_group = QGroupBox("缺陷详情")
        edit_layout = QVBoxLayout(edit_group)
        
        # 缺陷类型
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("缺陷类型:"))
        
        self.defect_type_combo = QComboBox()
        self.defect_type_combo.addItems([
            "孔径偏大", "孔径偏小", "孔位偏移", 
            "表面粗糙", "毛刺", "其他"
        ])
        type_layout.addWidget(self.defect_type_combo)
        
        # 严重程度
        severity_layout = QHBoxLayout()
        severity_layout.addWidget(QLabel("严重程度:"))
        
        self.severity_combo = QComboBox()
        self.severity_combo.addItems(["轻微", "中等", "严重"])
        severity_layout.addWidget(self.severity_combo)
        
        # 标注颜色
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("标注颜色:"))
        
        self.color_btn = QPushButton()
        self.color_btn.setMaximumSize(50, 30)
        self.color_btn.setStyleSheet("background-color: red;")
        self.color_btn.clicked.connect(self.choose_color)
        self.current_color = QColor(255, 0, 0)
        
        color_layout.addWidget(self.color_btn)
        color_layout.addStretch()
        
        # 缺陷描述
        desc_label = QLabel("缺陷描述:")
        self.description_text = QTextEdit()
        self.description_text.setMaximumHeight(100)
        self.description_text.setPlaceholderText("请输入缺陷的详细描述...")
        
        # 保存按钮
        self.save_btn = QPushButton("保存缺陷")
        self.save_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; }")
        self.save_btn.clicked.connect(self.save_current_defect)
        
        # 添加到布局
        edit_layout.addLayout(type_layout)
        edit_layout.addLayout(severity_layout)
        edit_layout.addLayout(color_layout)
        edit_layout.addWidget(desc_label)
        edit_layout.addWidget(self.description_text)
        edit_layout.addWidget(self.save_btn)
        edit_layout.addStretch()
        
        parent.addWidget(edit_group)
        
    def load_data_for_hole(self, hole_id: str):
        """为指定孔位加载数据"""
        print(f"📊 缺陷标注工具: 加载孔位 {hole_id} 的数据")
        
        self.current_hole_id = hole_id
        self.hole_label.setText(f"当前孔位: {hole_id}")
        
        # 加载该孔位的缺陷数据
        self._load_defects_for_hole(hole_id)
        
    def add_defect(self):
        """添加新缺陷"""
        if not self.current_hole_id:
            return
            
        defect_id = f"defect_{len(self.defects) + 1:03d}"
        defect_data = {
            'id': defect_id,
            'hole_id': self.current_hole_id,
            'type': self.defect_type_combo.currentText(),
            'severity': self.severity_combo.currentText(),
            'color': self.current_color,
            'description': "新缺陷"
        }
        
        self.defects[defect_id] = defect_data
        self._refresh_defect_list()
        
        print(f"➕ 添加缺陷: {defect_id}")
        
    def remove_defect(self):
        """删除选中的缺陷"""
        current_item = self.defect_list.currentItem()
        if current_item:
            defect_id = current_item.data(Qt.UserRole)
            if defect_id in self.defects:
                del self.defects[defect_id]
                self._refresh_defect_list()
                self.defect_removed.emit(defect_id)
                print(f"➖ 删除缺陷: {defect_id}")
                
    def clear_all_defects(self):
        """清空所有缺陷"""
        self.defects.clear()
        self._refresh_defect_list()
        print("🧹 清空所有缺陷")
        
    def choose_color(self):
        """选择标注颜色"""
        color = QColorDialog.getColor(self.current_color, self)
        if color.isValid():
            self.current_color = color
            self.color_btn.setStyleSheet(f"background-color: {color.name()};")
            
    def save_current_defect(self):
        """保存当前缺陷"""
        current_item = self.defect_list.currentItem()
        if current_item:
            defect_id = current_item.data(Qt.UserRole)
            if defect_id in self.defects:
                # 更新缺陷数据
                self.defects[defect_id].update({
                    'type': self.defect_type_combo.currentText(),
                    'severity': self.severity_combo.currentText(),
                    'color': self.current_color,
                    'description': self.description_text.toPlainText()
                })
                
                self._refresh_defect_list()
                self.defect_added.emit(defect_id, self.defects[defect_id])
                print(f"💾 保存缺陷: {defect_id}")
                
    def on_defect_selected(self):
        """缺陷选中处理"""
        current_item = self.defect_list.currentItem()
        if current_item:
            defect_id = current_item.data(Qt.UserRole)
            if defect_id in self.defects:
                defect = self.defects[defect_id]
                
                # 更新编辑面板
                self.defect_type_combo.setCurrentText(defect['type'])
                self.severity_combo.setCurrentText(defect['severity'])
                self.current_color = defect['color']
                self.color_btn.setStyleSheet(f"background-color: {defect['color'].name()};")
                self.description_text.setPlainText(defect['description'])
                
    def _load_defects_for_hole(self, hole_id: str):
        """加载指定孔位的缺陷数据"""
        # 清空现有缺陷
        hole_defects = {k: v for k, v in self.defects.items() 
                       if v.get('hole_id') == hole_id}
        
        # 模拟一些缺陷数据
        if not hole_defects and hole_id in ["C001R001", "C002R001"]:
            mock_defects = {
                'defect_001': {
                    'id': 'defect_001',
                    'hole_id': hole_id,
                    'type': '孔径偏大',
                    'severity': '轻微',
                    'color': QColor(255, 165, 0),
                    'description': '孔径超出容差范围 0.02mm'
                },
                'defect_002': {
                    'id': 'defect_002', 
                    'hole_id': hole_id,
                    'type': '表面粗糙',
                    'severity': '中等',
                    'color': QColor(255, 0, 0),
                    'description': '表面粗糙度超标'
                }
            }
            self.defects.update(mock_defects)
            
        self._refresh_defect_list()
        
    def _refresh_defect_list(self):
        """刷新缺陷列表"""
        self.defect_list.clear()
        
        # 过滤当前孔位的缺陷
        hole_defects = {k: v for k, v in self.defects.items() 
                       if v.get('hole_id') == self.current_hole_id}
        
        for defect_id, defect in hole_defects.items():
            item_text = f"{defect['type']} - {defect['severity']} - {defect['description'][:20]}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, defect_id)
            
            # 设置颜色
            color = defect['color']
            item.setBackground(color)
            
            self.defect_list.addItem(item)
            
        # 更新缺陷数量
        self.defect_count_label.setText(f"缺陷数量: {len(hole_defects)}")
        
    def cleanup(self):
        """清理资源"""
        print("🧹 缺陷标注工具: 清理资源")
        self.defects.clear()
        self.current_hole_id = None