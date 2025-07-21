"""
缺陷标注工具主界面
实现两栏布局和完整的用户界面
"""

import os
from typing import List, Optional, Dict
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QGridLayout,
                               QLabel, QPushButton, QComboBox, QListWidget,
                               QListWidgetItem, QGroupBox, QTableWidget,
                               QTableWidgetItem, QButtonGroup, QMessageBox,
                               QSplitter, QFrame, QHeaderView)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QIcon

from .image_scanner import ImageScanner, ImageInfo
from .defect_annotation_model import DefectAnnotation
from .yolo_file_manager import YOLOFileManager
from .defect_category_manager import DefectCategoryManager
from .annotation_graphics_view import AnnotationGraphicsView, MouseMode
from .archive_manager import ArchiveManager


class DefectAnnotationTool(QWidget):
    """缺陷标注工具主界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化数据
        self.image_scanner = ImageScanner("Data")
        self.yolo_manager = YOLOFileManager()
        self.category_manager = DefectCategoryManager()
        # 创建ArchiveManager时传入ImageScanner实例，确保使用相同的扫描结果
        self.archive_manager = ArchiveManager("Data", "Archive", self.image_scanner)
        self.current_hole_id: Optional[str] = None
        self.current_image: Optional[ImageInfo] = None
        self.archived_holes: List[str] = []
        
        # 初始化UI
        self.init_ui()
        
        # 扫描图像
        self.scan_images()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("缺陷标注工具 (Defect Annotation Tool)")
        self.setMinimumSize(1200, 800)
        
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
        """创建左侧图像显示区"""
        self.image_area = QFrame()
        self.image_area.setFrameStyle(QFrame.StyledPanel)
        
        layout = QVBoxLayout(self.image_area)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 创建工具栏
        toolbar_layout = QHBoxLayout()

        # 只保留适应视图按钮，删除放大和缩小按钮
        self.fit_view_btn = QPushButton("适应视图")
        self.fit_view_btn.clicked.connect(self.fit_in_view)

        toolbar_layout.addWidget(self.fit_view_btn)
        toolbar_layout.addStretch()
        
        layout.addLayout(toolbar_layout)
        
        # 创建图形视图
        self.graphics_view = AnnotationGraphicsView()
        self.graphics_view.set_category_manager(self.category_manager)  # 设置类别管理器
        layout.addWidget(self.graphics_view)

        # 连接信号
        self.graphics_view.annotation_created.connect(self.on_annotation_created)
        self.graphics_view.annotation_selected.connect(self.on_annotation_selected)
        self.graphics_view.annotation_deleted.connect(self.on_annotation_deleted)
        
    def create_tool_area(self):
        """创建右侧工具信息区"""
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
        """创建孔ID选择组"""
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
        """创建标注工具组"""
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
        """创建缺陷列表组"""
        self.defect_list_group = QGroupBox("缺陷列表")
        layout = QVBoxLayout(self.defect_list_group)

        # 缺陷列表表格
        self.defect_table = QTableWidget()
        # 隐藏默认的垂直表头，解决左上角空白问题
        self.defect_table.verticalHeader().setVisible(False)
        self.defect_table.setColumnCount(5)  # 增加序号列，从4列改为5列
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
        """填充缺陷类别下拉菜单"""
        ui_items = self.category_manager.create_ui_combo_items()
        for text, value in ui_items:
            self.defect_combo.addItem(text, value)
            
    def scan_images(self):
        """扫描图像文件"""
        if self.image_scanner.scan_directories():
            hole_ids = self.image_scanner.get_hole_ids()
            
            # 填充孔ID下拉菜单
            self.hole_combo.clear()
            self.hole_combo.addItems(hole_ids)
            
            # 如果有孔位，选择第一个
            if hole_ids:
                self.hole_combo.setCurrentText(hole_ids[0])
                
        else:
            QMessageBox.warning(self, "警告", "未找到图像文件，请检查Data目录结构")
            
    def on_hole_changed(self, hole_id: str):
        """孔ID改变事件"""
        if not hole_id:
            return

        self.current_hole_id = hole_id

        # 更新孔位信息显示
        self.update_hole_info()

        # 更新图像列表
        self.update_image_list()

        # 清除当前图像和标注
        self.graphics_view.clear_scene()
        self.current_image = None
        self.update_defect_table()

    def update_hole_info(self):
        """更新孔位信息显示"""
        if not self.current_hole_id:
            self.hole_info_label.setText("选择孔位查看信息")
            return

        images = self.image_scanner.get_images_for_hole(self.current_hole_id)
        if not images:
            self.hole_info_label.setText(f"{self.current_hole_id}: 无图像文件")
            return

        # 计算总大小和找到最大文件
        total_size = 0
        largest_size = 0
        largest_name = ""

        for image_info in images:
            try:
                file_size = os.path.getsize(image_info.file_path)
                total_size += file_size
                if file_size > largest_size:
                    largest_size = file_size
                    largest_name = image_info.file_name
            except OSError:
                pass

        total_mb = total_size / (1024 * 1024)
        largest_mb = largest_size / (1024 * 1024)

        info_text = f"{self.current_hole_id}: {len(images)}个文件, 总计{total_mb:.1f}MB, 最大: {largest_name} ({largest_mb:.1f}MB)"
        self.hole_info_label.setText(info_text)

    def update_image_list(self):
        """更新图像列表"""
        self.image_list.clear()

        if not self.current_hole_id:
            return

        images = self.image_scanner.get_images_for_hole(self.current_hole_id)

        # 找到最大的图像文件
        largest_image = None
        largest_size = 0

        for image_info in images:
            item = QListWidgetItem()

            # 获取文件大小
            try:
                file_size = os.path.getsize(image_info.file_path)
                size_mb = file_size / (1024 * 1024)

                # 标记最大文件
                if file_size > largest_size:
                    largest_size = file_size
                    largest_image = image_info

                # 显示文件名和大小，最大文件用特殊标记
                if file_size == largest_size:
                    item.setText(f"📌 {image_info.file_name} ({size_mb:.1f} MB) [推荐]")
                else:
                    item.setText(f"{image_info.file_name} ({size_mb:.1f} MB)")

            except OSError:
                item.setText(image_info.file_name)

            item.setData(Qt.UserRole, image_info)
            self.image_list.addItem(item)

        # 自动选择最大的图像文件
        if largest_image:
            for i in range(self.image_list.count()):
                item = self.image_list.item(i)
                image_info = item.data(Qt.UserRole)
                if image_info.file_path == largest_image.file_path:
                    self.image_list.setCurrentRow(i)
                    self.on_image_selected(item)
                    break
        elif images:
            # 如果没找到最大文件，选择第一个
            self.image_list.setCurrentRow(0)
            self.on_image_selected(self.image_list.item(0))

    def on_image_selected(self, item: QListWidgetItem):
        """图像选择事件"""
        if not item:
            return

        image_info = item.data(Qt.UserRole)
        if not image_info:
            return

        self.current_image = image_info

        # 加载图像
        if self.graphics_view.load_image(image_info.file_path):
            # 自动加载对应的标注文件
            self.load_annotations()
        else:
            QMessageBox.warning(self, "错误", f"无法加载图像: {image_info.file_name}")

    def on_mode_changed(self, button: QPushButton):
        """鼠标模式改变事件"""
        button_id = self.mode_button_group.id(button)

        if button_id == 0:  # 平移模式
            self.graphics_view.set_mouse_mode(MouseMode.PAN)
        elif button_id == 1:  # 标注模式
            self.graphics_view.set_mouse_mode(MouseMode.ANNOTATE)
        elif button_id == 2:  # 编辑模式
            self.graphics_view.set_mouse_mode(MouseMode.EDIT)

    def on_defect_class_changed(self, index: int):
        """缺陷类别改变事件"""
        defect_class = self.defect_combo.itemData(index)
        if defect_class is not None:
            self.graphics_view.set_defect_class(defect_class)

    def on_annotation_created(self, annotation: DefectAnnotation):
        """标注创建事件"""
        self.update_defect_table()

    def on_annotation_selected(self, annotation: DefectAnnotation):
        """标注选择事件"""
        # 在表格中高亮对应行
        self.highlight_annotation_in_table(annotation)

    def on_annotation_deleted(self, annotation: DefectAnnotation):
        """标注删除事件"""
        self.update_defect_table()

    def update_defect_table(self):
        """更新缺陷列表表格"""
        annotations = self.graphics_view.get_annotations()

        self.defect_table.setRowCount(len(annotations))

        for row, annotation in enumerate(annotations):
            # 序号列（新增）
            seq_item = QTableWidgetItem(str(row + 1))
            seq_item.setTextAlignment(Qt.AlignCenter)
            self.defect_table.setItem(row, 0, seq_item)

            # 类别（原第0列，现在是第1列）
            category_name = self.category_manager.get_category_name(annotation.defect_class)
            self.defect_table.setItem(row, 1, QTableWidgetItem(category_name))

            # 位置（原第1列，现在是第2列）
            position_text = f"({annotation.x_center:.3f}, {annotation.y_center:.3f})"
            self.defect_table.setItem(row, 2, QTableWidgetItem(position_text))

            # 大小（原第2列，现在是第3列）
            size_text = f"{annotation.width:.3f} × {annotation.height:.3f}"
            self.defect_table.setItem(row, 3, QTableWidgetItem(size_text))

            # 置信度（原第3列，现在是第4列）
            confidence_text = f"{annotation.confidence:.2f}"
            self.defect_table.setItem(row, 4, QTableWidgetItem(confidence_text))

    def highlight_annotation_in_table(self, annotation: DefectAnnotation):
        """在表格中高亮指定标注"""
        annotations = self.graphics_view.get_annotations()

        for row, ann in enumerate(annotations):
            if (ann.defect_class == annotation.defect_class and
                abs(ann.x_center - annotation.x_center) < 0.001 and
                abs(ann.y_center - annotation.y_center) < 0.001):
                self.defect_table.selectRow(row)
                break

    def delete_selected_annotation(self):
        """删除选中的标注"""
        current_row = self.defect_table.currentRow()
        if current_row >= 0:
            annotations = self.graphics_view.get_annotations()
            if current_row < len(annotations):
                annotation = annotations[current_row]
                # 从图形视图中删除
                annotation_items = self.graphics_view.annotation_items
                if current_row < len(annotation_items):
                    self.graphics_view.remove_annotation(annotation_items[current_row])

    def clear_all_annotations(self):
        """清除所有标注"""
        reply = QMessageBox.question(
            self, "确认", "确定要清除所有标注吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.graphics_view.clear_annotations()

    def save_annotations(self):
        """保存标注到文件"""
        if not self.current_image:
            QMessageBox.warning(self, "警告", "请先选择图像")
            return

        annotations = self.graphics_view.get_annotations()
        annotation_file = self.yolo_manager.get_annotation_file_path(self.current_image.file_path)

        if self.yolo_manager.save_annotations(annotations, annotation_file):
            QMessageBox.information(self, "成功", f"标注已保存到: {annotation_file}")

            # 询问是否要归档当前孔位
            if len(annotations) > 0:  # 只有当有标注时才询问
                reply = QMessageBox.question(
                    self, "归档确认",
                    f"标注已保存。是否要将孔位 {self.current_hole_id} 归档？\n"
                    f"归档后可以通过'已归档标注'下拉菜单重新加载。",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )

                if reply == QMessageBox.Yes:
                    self.archive_current_hole()

            # 更新归档列表
            self.update_archive_list()
        else:
            QMessageBox.critical(self, "错误", "保存标注失败")

    def load_annotations(self):
        """从文件加载标注"""
        if not self.current_image:
            return

        annotation_file = self.yolo_manager.get_annotation_file_path(self.current_image.file_path)

        if os.path.exists(annotation_file):
            annotations = self.yolo_manager.load_annotations(annotation_file)

            # 清除现有标注
            self.graphics_view.clear_annotations()

            # 添加加载的标注
            for annotation in annotations:
                self.graphics_view.add_annotation(annotation)

            self.update_defect_table()

    def load_from_archive(self):
        """从归档加载标注数据"""
        # 获取选中的归档
        current_text = self.archive_combo.currentText()
        if not current_text or current_text == "选择已归档孔位...":
            QMessageBox.warning(self, "警告", "请先选择要加载的归档孔位")
            return

        # 提取孔位ID
        hole_id = current_text.split(' ')[0]

        try:
            # 从归档恢复数据到原始位置
            success = self.archive_manager.load_archived_hole(hole_id)

            if success:
                # 重新扫描图像
                self.scan_images()

                # 切换到恢复的孔位
                self.hole_combo.setCurrentText(hole_id)

                # 使用QTimer延迟执行图像选择，确保孔位切换完成
                QTimer.singleShot(100, lambda: self.auto_select_annotated_image(hole_id))

                QMessageBox.information(self, "成功", f"已从归档恢复孔位 {hole_id} 的数据")
            else:
                QMessageBox.critical(self, "错误", f"无法从归档恢复孔位 {hole_id}")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载归档时发生错误: {str(e)}")

    def auto_select_annotated_image(self, hole_id: str):
        """自动选择有标注的图像"""
        try:
            # 获取孔位的所有图像
            images = self.image_scanner.get_images_for_hole(hole_id)

            # 查找有标注的图像
            annotated_image = None
            for image_info in images:
                if self.yolo_manager.has_annotations(image_info.file_path):
                    annotated_image = image_info
                    break

            if annotated_image:
                # 在图像列表中选择这个图像
                for i in range(self.image_list.count()):
                    item = self.image_list.item(i)
                    item_data = item.data(Qt.UserRole)
                    if item_data and item_data.file_path == annotated_image.file_path:
                        self.image_list.setCurrentRow(i)
                        self.on_image_selected(item)
                        break

                print(f"自动选择了有标注的图像: {annotated_image.file_name}")
            else:
                print(f"孔位 {hole_id} 没有找到有标注的图像")

        except Exception as e:
            print(f"自动选择图像时发生错误: {e}")

    def archive_current_hole(self):
        """归档当前孔位"""
        if not self.current_hole_id:
            QMessageBox.warning(self, "警告", "没有选择孔位")
            return

        try:
            # 首先检查当前孔位是否有任何标注文件（已保存的）
            images = self.image_scanner.get_images_for_hole(self.current_hole_id)
            has_any_annotations = False
            total_annotations = 0
            annotated_images = 0

            for image_info in images:
                if self.yolo_manager.has_annotations(image_info.file_path):
                    has_any_annotations = True
                    annotated_images += 1

                    # 计算标注数量
                    annotation_file = self.yolo_manager.get_annotation_file_path(image_info.file_path)
                    annotations = self.yolo_manager.load_annotations(annotation_file)
                    total_annotations += len(annotations)

            if not has_any_annotations:
                QMessageBox.warning(self, "警告", "当前孔位没有标注数据")
                return

            # 归档孔位
            notes = f"标注完成归档 - {total_annotations}个标注"
            success = self.archive_manager.archive_hole(self.current_hole_id, notes)

            if success:
                QMessageBox.information(
                    self, "成功",
                    f"孔位 {self.current_hole_id} 已成功归档\n"
                    f"包含 {annotated_images} 张图像，{total_annotations} 个标注"
                )
            else:
                QMessageBox.critical(self, "错误", f"归档孔位 {self.current_hole_id} 失败")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"归档时发生错误: {str(e)}")

    def update_archive_list(self):
        """更新归档列表"""
        # 获取真正的已归档孔位
        archived_holes = self.archive_manager.get_archived_holes()

        # 更新归档下拉菜单
        self.archive_combo.clear()
        self.archive_combo.addItem("选择已归档孔位...")

        # 添加归档信息
        for hole_id in archived_holes:
            record = self.archive_manager.get_archive_record(hole_id)
            if record:
                display_text = f"{hole_id} ({record.total_annotations}个标注)"
                self.archive_combo.addItem(display_text, hole_id)

        self.archived_holes = archived_holes

    def on_archive_selected(self, text: str):
        """归档选择事件"""
        if text and text != "选择已归档孔位...":
            # 获取实际的孔位ID（从显示文本中提取）
            hole_id = text.split(' ')[0]  # 提取孔位ID部分

            # 更新状态，但不自动切换孔位
            # 用户需要点击"加载归档"按钮来实际加载数据
            pass

    # 缩放控制方法（删除了zoom_in和zoom_out，改为鼠标滚轮缩放）
    def fit_in_view(self):
        """适应视图"""
        self.graphics_view.fit_in_view()

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        stats = self.image_scanner.get_statistics()

        # 添加标注统计
        total_annotations = 0
        annotated_images = 0

        for hole_id in self.image_scanner.get_hole_ids():
            images = self.image_scanner.get_images_for_hole(hole_id)
            for image_info in images:
                if self.yolo_manager.has_annotations(image_info.file_path):
                    annotated_images += 1
                    annotations = self.yolo_manager.load_annotations(
                        self.yolo_manager.get_annotation_file_path(image_info.file_path)
                    )
                    total_annotations += len(annotations)

        stats.update({
            'total_annotations': total_annotations,
            'annotated_images': annotated_images,
            'annotation_rate': round(annotated_images / max(stats['total_images'], 1) * 100, 1)
        })

        return stats
