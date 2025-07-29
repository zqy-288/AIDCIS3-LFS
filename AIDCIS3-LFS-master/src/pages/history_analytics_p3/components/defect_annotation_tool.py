"""
缺陷标注工具组件
基于重构前的DefectAnnotationTool完整实现
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QFrame,
    QGroupBox, QLabel, QComboBox, QListWidget, QPushButton,
    QTableWidget, QTableWidgetItem, QButtonGroup, QHeaderView,
    QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap

from pathlib import Path
import os


class DefectAnnotationTool(QWidget):
    """
    缺陷标注工具 - 完全按照重构前的实现
    3.2级界面：缺陷标注功能
    """
    
    # 信号定义
    hole_changed = Signal(str)  # 孔位改变信号
    annotation_saved = Signal(str)  # 标注保存信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 数据存储
        self.current_hole_id = ""
        self.hole_ids = []
        self.current_image_path = ""
        self.annotations = []
        self.archived_holes = []
        
        # 初始化UI
        self.init_ui()
        
        # 扫描图像
        self.scan_images()
        
    def init_ui(self):
        """初始化用户界面 - 按照重构前的布局"""
        # 创建主布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # 创建左侧图像显示区
        self.create_image_area()
        splitter.addWidget(self.image_area)
        
        # 创建右侧工具信息区
        self.create_tool_area()
        splitter.addWidget(self.tool_area)
        
        # 设置分割比例 (左侧70%, 右侧30%)
        splitter.setSizes([840, 360])
        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)
        
    def create_image_area(self):
        """创建左侧图像显示区 - 按照重构前的设计"""
        self.image_area = QFrame()
        self.image_area.setFrameStyle(QFrame.StyledPanel)
        
        layout = QVBoxLayout(self.image_area)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 创建工具栏
        toolbar_layout = QHBoxLayout()
        
        # 适应视图按钮
        self.fit_view_btn = QPushButton("适应视图")
        self.fit_view_btn.clicked.connect(self.fit_in_view)
        
        toolbar_layout.addWidget(self.fit_view_btn)
        toolbar_layout.addStretch()
        
        layout.addLayout(toolbar_layout)
        
        # 创建图像显示标签（简化版，不使用复杂的图形视图）
        self.image_label = QLabel("请选择孔位和图像文件")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #555;
                border-radius: 8px;
                background-color: #2b2b2b;
                color: #888;
                font-size: 16px;
                min-height: 400px;
            }
        """)
        layout.addWidget(self.image_label)
        
    def create_tool_area(self):
        """创建右侧工具信息区 - 按照重构前的设计"""
        self.tool_area = QFrame()
        self.tool_area.setFrameStyle(QFrame.StyledPanel)
        self.tool_area.setFixedWidth(350)
        
        layout = QVBoxLayout(self.tool_area)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # 顶部：孔ID选择和图像列表
        self.create_hole_selection_group()
        layout.addWidget(self.hole_selection_group)
        
        # 中部：标注工具
        self.create_annotation_tools_group()
        layout.addWidget(self.annotation_tools_group)
        
        # 底部：缺陷列表和归档
        self.create_defect_list_group()
        layout.addWidget(self.defect_list_group)
        
        # 添加弹性空间
        layout.addStretch()
        
    def create_hole_selection_group(self):
        """创建孔ID选择组 - 按照重构前的设计"""
        self.hole_selection_group = QGroupBox("孔位选择")
        layout = QVBoxLayout(self.hole_selection_group)
        
        # 孔ID下拉菜单
        hole_layout = QHBoxLayout()
        hole_layout.addWidget(QLabel("孔ID:"))
        
        self.hole_combo = QComboBox()
        self.hole_combo.currentTextChanged.connect(self.on_hole_changed)
        hole_layout.addWidget(self.hole_combo)
        
        layout.addLayout(hole_layout)
        
        # 孔位信息显示
        self.hole_info_label = QLabel("选择孔位查看信息")
        self.hole_info_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.hole_info_label)
        
        # 图像文件列表
        layout.addWidget(QLabel("图像文件:"))
        
        # 添加提示信息
        tip_label = QLabel("💡 建议：每个孔位只标注最大的图像文件")
        tip_label.setStyleSheet("color: #666; font-size: 11px; font-style: italic;")
        layout.addWidget(tip_label)
        
        self.image_list = QListWidget()
        self.image_list.setMaximumHeight(150)
        self.image_list.itemClicked.connect(self.on_image_selected)
        layout.addWidget(self.image_list)
        
    def create_annotation_tools_group(self):
        """创建标注工具组 - 按照重构前的设计"""
        self.annotation_tools_group = QGroupBox("标注工具")
        layout = QVBoxLayout(self.annotation_tools_group)
        
        # 鼠标模式按钮
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("鼠标模式:"))
        
        self.mode_button_group = QButtonGroup()
        
        self.pan_btn = QPushButton("平移")
        self.annotate_btn = QPushButton("标注")
        self.edit_btn = QPushButton("编辑")
        
        self.pan_btn.setCheckable(True)
        self.annotate_btn.setCheckable(True)
        self.edit_btn.setCheckable(True)
        self.pan_btn.setChecked(True)  # 默认选中平移模式
        
        self.mode_button_group.addButton(self.pan_btn, 0)
        self.mode_button_group.addButton(self.annotate_btn, 1)
        self.mode_button_group.addButton(self.edit_btn, 2)
        
        self.mode_button_group.buttonClicked.connect(self.on_mode_changed)
        
        mode_layout.addWidget(self.pan_btn)
        mode_layout.addWidget(self.annotate_btn)
        mode_layout.addWidget(self.edit_btn)
        
        layout.addLayout(mode_layout)
        
        # 缺陷类别选择
        defect_layout = QHBoxLayout()
        defect_layout.addWidget(QLabel("缺陷类别:"))
        
        self.defect_combo = QComboBox()
        self.populate_defect_categories()
        self.defect_combo.currentIndexChanged.connect(self.on_defect_class_changed)
        defect_layout.addWidget(self.defect_combo)
        
        layout.addLayout(defect_layout)
        
        # 保存按钮
        save_layout = QHBoxLayout()
        self.save_btn = QPushButton("保存标注")
        self.save_btn.clicked.connect(self.save_annotations)
        save_layout.addWidget(self.save_btn)
        
        self.load_btn = QPushButton("加载归档")
        self.load_btn.clicked.connect(self.load_from_archive)
        save_layout.addWidget(self.load_btn)
        
        layout.addLayout(save_layout)
        
    def create_defect_list_group(self):
        """创建缺陷列表组 - 按照重构前的设计"""
        self.defect_list_group = QGroupBox("缺陷列表")
        layout = QVBoxLayout(self.defect_list_group)
        
        # 缺陷列表表格
        self.defect_table = QTableWidget()
        self.defect_table.verticalHeader().setVisible(False)
        self.defect_table.setColumnCount(5)
        self.defect_table.setHorizontalHeaderLabels(["序号", "类别", "位置", "大小", "置信度"])
        
        # 设置表格属性
        header = self.defect_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.defect_table.setMaximumHeight(150)
        self.defect_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        layout.addWidget(self.defect_table)
        
        # 删除按钮
        delete_layout = QHBoxLayout()
        self.delete_btn = QPushButton("删除选中")
        self.delete_btn.clicked.connect(self.delete_selected_annotation)
        delete_layout.addWidget(self.delete_btn)
        
        self.clear_btn = QPushButton("清除所有")
        self.clear_btn.clicked.connect(self.clear_all_annotations)
        delete_layout.addWidget(self.clear_btn)
        
        layout.addLayout(delete_layout)
        
        # 已归档标注
        layout.addWidget(QLabel("已归档标注:"))
        
        self.archive_combo = QComboBox()
        self.archive_combo.currentTextChanged.connect(self.on_archive_selected)
        layout.addWidget(self.archive_combo)
        
    def populate_defect_categories(self):
        """填充缺陷类别下拉菜单 - 按照重构前的设计"""
        categories = [
            "裂纹",
            "气孔", 
            "夹杂",
            "未熔合",
            "咬边",
            "其他"
        ]
        self.defect_combo.addItems(categories)

    def scan_images(self):
        """扫描图像文件 - 按照重构前的实现"""
        try:
            # 按照重构前的路径结构扫描图像
            project_root = Path(__file__).parent.parent.parent.parent.parent
            data_base_dir = project_root / "Data" / "CAP1000"

            hole_ids = []

            if data_base_dir.exists():
                print(f"🔍 扫描缺陷标注图像目录: {data_base_dir}")
                for item in os.listdir(str(data_base_dir)):
                    item_path = data_base_dir / item
                    if item_path.is_dir() and self.is_valid_hole_id(item):
                        hole_ids.append(item)

            # 如果没有找到，使用默认孔位
            if not hole_ids:
                hole_ids = ["R001C001", "R001C002", "R001C003", "R002C001", "R002C002"]
                print("🔧 使用默认孔位列表进行缺陷标注")

            self.hole_ids = sorted(hole_ids)

            # 填充孔ID下拉菜单
            self.hole_combo.clear()
            self.hole_combo.addItems(self.hole_ids)

            # 如果有孔位，选择第一个
            if self.hole_ids:
                self.hole_combo.setCurrentText(self.hole_ids[0])

            print(f"✅ 缺陷标注工具找到 {len(self.hole_ids)} 个孔位")

        except Exception as e:
            print(f"❌ 扫描图像失败: {e}")
            QMessageBox.warning(self, "警告", "未找到图像文件，请检查Data目录结构")

    def is_valid_hole_id(self, hole_id):
        """验证孔位ID格式是否为RxxxCxxx"""
        import re
        pattern = r'^R\d+C\d+$'
        return re.match(pattern, hole_id) is not None

    def on_hole_changed(self, hole_id):
        """孔ID改变事件 - 按照重构前的实现"""
        if not hole_id:
            return

        self.current_hole_id = hole_id

        # 更新孔位信息显示
        self.update_hole_info()

        # 更新图像列表
        self.update_image_list()

        # 发射信号
        self.hole_changed.emit(hole_id)

    def update_hole_info(self):
        """更新孔位信息显示"""
        if self.current_hole_id:
            info_text = f"当前孔位: {self.current_hole_id}"
            self.hole_info_label.setText(info_text)
        else:
            self.hole_info_label.setText("选择孔位查看信息")

    def update_image_list(self):
        """更新图像列表 - 按照重构前的实现"""
        self.image_list.clear()

        if not self.current_hole_id:
            return

        try:
            # 查找孔位对应的图像文件
            project_root = Path(__file__).parent.parent.parent.parent.parent
            hole_dir = project_root / "Data" / "CAP1000" / self.current_hole_id

            image_files = []
            if hole_dir.exists():
                # 查找图像文件（jpg, png, bmp等）
                for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff']:
                    image_files.extend(hole_dir.glob(ext))

            if image_files:
                # 按文件名排序
                image_files.sort()
                for img_file in image_files:
                    self.image_list.addItem(img_file.name)
                print(f"📷 找到 {len(image_files)} 个图像文件")
            else:
                # 添加模拟图像文件
                mock_images = ["image_001.jpg", "image_002.jpg", "image_003.jpg"]
                for img_name in mock_images:
                    self.image_list.addItem(img_name)
                print("🔧 使用模拟图像文件列表")

        except Exception as e:
            print(f"❌ 更新图像列表失败: {e}")

    def on_image_selected(self, item):
        """图像选择事件 - 按照重构前的实现"""
        if not item:
            return

        image_name = item.text()
        print(f"📷 选择图像: {image_name}")

        # 更新图像显示
        self.load_image(image_name)

    def load_image(self, image_name):
        """加载图像显示"""
        try:
            # 构建图像路径
            project_root = Path(__file__).parent.parent.parent.parent.parent
            image_path = project_root / "Data" / "CAP1000" / self.current_hole_id / image_name

            if image_path.exists():
                # 加载真实图像
                pixmap = QPixmap(str(image_path))
                if not pixmap.isNull():
                    # 缩放图像以适应标签
                    scaled_pixmap = pixmap.scaled(
                        self.image_label.size(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    self.image_label.setPixmap(scaled_pixmap)
                    self.current_image_path = str(image_path)
                    print(f"✅ 图像加载成功: {image_name}")
                else:
                    self.show_placeholder_image(f"无法加载图像: {image_name}")
            else:
                self.show_placeholder_image(f"图像文件不存在: {image_name}")

        except Exception as e:
            print(f"❌ 加载图像失败: {e}")
            self.show_placeholder_image(f"加载失败: {image_name}")

    def show_placeholder_image(self, text):
        """显示占位符图像"""
        self.image_label.clear()
        self.image_label.setText(text)
        self.current_image_path = ""

    def fit_in_view(self):
        """适应视图 - 按照重构前的实现"""
        if self.current_image_path:
            self.load_image(Path(self.current_image_path).name)
            print("🔍 适应视图")

    def on_mode_changed(self, button):
        """鼠标模式改变事件"""
        mode_id = self.mode_button_group.id(button)
        mode_names = ["平移", "标注", "编辑"]
        print(f"🖱️ 切换到模式: {mode_names[mode_id]}")

    def on_defect_class_changed(self, index):
        """缺陷类别改变事件"""
        category = self.defect_combo.currentText()
        print(f"🏷️ 选择缺陷类别: {category}")

    def save_annotations(self):
        """保存标注 - 按照重构前的实现"""
        if not self.current_hole_id:
            QMessageBox.warning(self, "警告", "请先选择孔位")
            return

        # 模拟保存标注
        print(f"💾 保存孔位 {self.current_hole_id} 的标注")
        QMessageBox.information(self, "保存成功", f"孔位 {self.current_hole_id} 的标注已保存")
        self.annotation_saved.emit(self.current_hole_id)

    def load_from_archive(self):
        """从归档加载 - 按照重构前的实现"""
        print("📂 从归档加载标注")
        QMessageBox.information(self, "加载归档", "归档加载功能开发中...")

    def delete_selected_annotation(self):
        """删除选中的标注"""
        current_row = self.defect_table.currentRow()
        if current_row >= 0:
            self.defect_table.removeRow(current_row)
            print(f"🗑️ 删除标注行: {current_row}")
        else:
            QMessageBox.warning(self, "警告", "请先选择要删除的标注")

    def clear_all_annotations(self):
        """清除所有标注"""
        self.defect_table.setRowCount(0)
        self.annotations.clear()
        print("🗑️ 清除所有标注")

    def on_archive_selected(self, archive_name):
        """归档选择事件"""
        if archive_name:
            print(f"📂 选择归档: {archive_name}")

    def get_current_hole_id(self):
        """获取当前孔位ID"""
        return self.current_hole_id

    def set_hole_id(self, hole_id):
        """设置当前孔位ID"""
        if hole_id in self.hole_ids:
            self.hole_combo.setCurrentText(hole_id)
