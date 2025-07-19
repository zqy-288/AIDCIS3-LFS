"""
历史查看控制器
负责管理历史数据查看界面和相关业务逻辑
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QDateTimeEdit, QComboBox, QLineEdit, QTextEdit, QSplitter,
    QTreeWidget, QTreeWidgetItem, QFrame, QCheckBox, QSpinBox
)
from PySide6.QtCore import QObject, Signal, QTimer, Qt, QDateTime
from PySide6.QtGui import QFont, QIcon, QPixmap

from src.modules.unified_history_viewer import UnifiedHistoryViewer


class HistoryController(QObject):
    """历史查看控制器类"""
    
    # 信号定义
    data_loaded = Signal(list)  # 数据加载完成信号
    filter_changed = Signal(dict)  # 过滤条件改变信号
    export_requested = Signal(str, dict)  # 导出请求信号
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.parent = parent
        self.logger = logging.getLogger(__name__)
        
        # 核心组件
        self._widget: Optional[QWidget] = None
        self._history_viewer: Optional[UnifiedHistoryViewer] = None
        
        # 数据管理
        self._current_data: List[Dict[str, Any]] = []
        self._filtered_data: List[Dict[str, Any]] = []
        self._filter_conditions: Dict[str, Any] = {}
        
        # 状态管理
        self._is_loading = False
        self._current_page = 1
        self._page_size = 100
        self._total_records = 0
        
        # UI组件引用
        self._ui_components = {}
        
        # 搜索和过滤
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._apply_search)
        
        self.logger.info("历史查看控制器初始化完成")
    
    def create_widget(self) -> QWidget:
        """创建历史查看界面"""
        if self._widget is not None:
            return self._widget
        
        self._widget = QWidget()
        self._setup_ui()
        self._connect_signals()
        
        self.logger.info("历史查看界面创建完成")
        return self._widget
    
    def _setup_ui(self):
        """设置用户界面"""
        if not self._widget:
            return
        
        # 主布局
        main_layout = QVBoxLayout(self._widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 创建过滤面板
        filter_panel = self._create_filter_panel()
        main_layout.addWidget(filter_panel)
        
        # 创建内容区域
        content_area = self._create_content_area()
        main_layout.addWidget(content_area)
        
        # 创建分页控制
        pagination_panel = self._create_pagination_panel()
        main_layout.addWidget(pagination_panel)
        
        self.logger.info("历史查看UI设置完成")
    
    def _create_filter_panel(self) -> QWidget:
        """创建过滤面板"""
        panel = QGroupBox("数据过滤")
        panel.setMaximumHeight(120)
        
        main_layout = QVBoxLayout(panel)
        
        # 第一行：时间范围
        time_layout = QHBoxLayout()
        
        time_layout.addWidget(QLabel("时间范围:"))
        
        # 开始时间
        self._ui_components['start_time'] = QDateTimeEdit()
        self._ui_components['start_time'].setDateTime(QDateTime.currentDateTime().addDays(-7))
        self._ui_components['start_time'].setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        time_layout.addWidget(self._ui_components['start_time'])
        
        time_layout.addWidget(QLabel("到"))
        
        # 结束时间
        self._ui_components['end_time'] = QDateTimeEdit()
        self._ui_components['end_time'].setDateTime(QDateTime.currentDateTime())
        self._ui_components['end_time'].setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        time_layout.addWidget(self._ui_components['end_time'])
        
        time_layout.addStretch()
        main_layout.addLayout(time_layout)
        
        # 第二行：其他过滤条件
        filter_layout = QHBoxLayout()
        
        # 状态过滤
        filter_layout.addWidget(QLabel("状态:"))
        self._ui_components['status_filter'] = QComboBox()
        self._ui_components['status_filter'].addItems(["全部", "成功", "失败", "处理中", "已取消"])
        filter_layout.addWidget(self._ui_components['status_filter'])
        
        # 类型过滤
        filter_layout.addWidget(QLabel("类型:"))
        self._ui_components['type_filter'] = QComboBox()
        self._ui_components['type_filter'].addItems(["全部", "检测", "校准", "维护", "报告"])
        filter_layout.addWidget(self._ui_components['type_filter'])
        
        # 关键字搜索
        filter_layout.addWidget(QLabel("关键字:"))
        self._ui_components['keyword_search'] = QLineEdit()
        self._ui_components['keyword_search'].setPlaceholderText("输入关键字...")
        filter_layout.addWidget(self._ui_components['keyword_search'])
        
        # 控制按钮
        self._ui_components['search_btn'] = QPushButton("搜索")
        self._ui_components['search_btn'].clicked.connect(self.search_data)
        filter_layout.addWidget(self._ui_components['search_btn'])
        
        self._ui_components['reset_btn'] = QPushButton("重置")
        self._ui_components['reset_btn'].clicked.connect(self.reset_filters)
        filter_layout.addWidget(self._ui_components['reset_btn'])
        
        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)
        
        return panel
    
    def _create_content_area(self) -> QWidget:
        """创建内容区域"""
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：历史数据列表
        left_widget = self._create_data_list_widget()
        splitter.addWidget(left_widget)
        
        # 右侧：详细信息
        right_widget = self._create_detail_widget()
        splitter.addWidget(right_widget)
        
        # 设置分割比例
        splitter.setSizes([700, 300])
        
        return splitter
    
    def _create_data_list_widget(self) -> QWidget:
        """创建数据列表组件"""
        widget = QGroupBox("历史数据列表")
        layout = QVBoxLayout(widget)
        
        # 创建历史查看器
        self._history_viewer = UnifiedHistoryViewer()
        layout.addWidget(self._history_viewer)
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        
        # 导出按钮
        self._ui_components['export_btn'] = QPushButton("导出数据")
        self._ui_components['export_btn'].clicked.connect(self.export_data)
        toolbar_layout.addWidget(self._ui_components['export_btn'])
        
        # 删除按钮
        self._ui_components['delete_btn'] = QPushButton("删除选中")
        self._ui_components['delete_btn'].clicked.connect(self.delete_selected)
        toolbar_layout.addWidget(self._ui_components['delete_btn'])
        
        # 刷新按钮
        self._ui_components['refresh_btn'] = QPushButton("刷新")
        self._ui_components['refresh_btn'].clicked.connect(self.refresh_data)
        toolbar_layout.addWidget(self._ui_components['refresh_btn'])
        
        toolbar_layout.addStretch()
        
        # 显示选项
        self._ui_components['show_details'] = QCheckBox("显示详细信息")
        self._ui_components['show_details'].setChecked(True)
        toolbar_layout.addWidget(self._ui_components['show_details'])
        
        layout.addLayout(toolbar_layout)
        
        return widget
    
    def _create_detail_widget(self) -> QWidget:
        """创建详细信息组件"""
        widget = QGroupBox("详细信息")
        layout = QVBoxLayout(widget)
        
        # 基本信息
        info_group = QGroupBox("基本信息")
        info_layout = QVBoxLayout(info_group)
        
        self._ui_components['detail_text'] = QTextEdit()
        self._ui_components['detail_text'].setReadOnly(True)
        info_layout.addWidget(self._ui_components['detail_text'])
        
        layout.addWidget(info_group)
        
        # 数据预览
        preview_group = QGroupBox("数据预览")
        preview_layout = QVBoxLayout(preview_group)
        
        self._ui_components['preview_table'] = QTableWidget()
        self._ui_components['preview_table'].setMaximumHeight(200)
        preview_layout.addWidget(self._ui_components['preview_table'])
        
        layout.addWidget(preview_group)
        
        # 操作按钮
        action_layout = QHBoxLayout()
        
        self._ui_components['view_btn'] = QPushButton("查看详情")
        self._ui_components['view_btn'].clicked.connect(self.view_details)
        action_layout.addWidget(self._ui_components['view_btn'])
        
        self._ui_components['edit_btn'] = QPushButton("编辑")
        self._ui_components['edit_btn'].clicked.connect(self.edit_record)
        action_layout.addWidget(self._ui_components['edit_btn'])
        
        action_layout.addStretch()
        
        layout.addLayout(action_layout)
        
        return widget
    
    def _create_pagination_panel(self) -> QWidget:
        """创建分页控制面板"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        panel.setMaximumHeight(50)
        
        layout = QHBoxLayout(panel)
        
        # 分页信息
        self._ui_components['page_info'] = QLabel("第 1 页，共 0 条记录")
        layout.addWidget(self._ui_components['page_info'])
        
        layout.addStretch()
        
        # 每页显示数量
        layout.addWidget(QLabel("每页显示:"))
        self._ui_components['page_size'] = QComboBox()
        self._ui_components['page_size'].addItems(["50", "100", "200", "500"])
        self._ui_components['page_size'].setCurrentText("100")
        self._ui_components['page_size'].currentTextChanged.connect(self._on_page_size_changed)
        layout.addWidget(self._ui_components['page_size'])
        
        # 分页按钮
        self._ui_components['first_btn'] = QPushButton("首页")
        self._ui_components['first_btn'].clicked.connect(self.first_page)
        layout.addWidget(self._ui_components['first_btn'])
        
        self._ui_components['prev_btn'] = QPushButton("上一页")
        self._ui_components['prev_btn'].clicked.connect(self.previous_page)
        layout.addWidget(self._ui_components['prev_btn'])
        
        self._ui_components['next_btn'] = QPushButton("下一页")
        self._ui_components['next_btn'].clicked.connect(self.next_page)
        layout.addWidget(self._ui_components['next_btn'])
        
        self._ui_components['last_btn'] = QPushButton("末页")
        self._ui_components['last_btn'].clicked.connect(self.last_page)
        layout.addWidget(self._ui_components['last_btn'])
        
        return panel
    
    def _connect_signals(self):
        """连接信号"""
        # 连接内部信号
        self.data_loaded.connect(self._on_data_loaded)
        self.filter_changed.connect(self._on_filter_changed)
        
        # 连接历史查看器信号
        if self._history_viewer:
            self._history_viewer.selection_changed.connect(self._on_selection_changed)
            self._history_viewer.item_double_clicked.connect(self._on_item_double_clicked)
        
        # 连接搜索框信号
        if 'keyword_search' in self._ui_components:
            self._ui_components['keyword_search'].textChanged.connect(self._on_search_text_changed)
        
        # 连接过滤器信号
        for filter_name in ['status_filter', 'type_filter']:
            if filter_name in self._ui_components:
                self._ui_components[filter_name].currentTextChanged.connect(self._on_filter_changed)
        
        # 连接时间过滤器信号
        for time_name in ['start_time', 'end_time']:
            if time_name in self._ui_components:
                self._ui_components[time_name].dateTimeChanged.connect(self._on_time_filter_changed)
    
    def search_data(self):
        """搜索数据"""
        try:
            self._is_loading = True
            self._update_filter_conditions()
            
            # 这里应该调用数据访问层来获取数据
            # 暂时使用模拟数据
            self._simulate_data_load()
            
            self.logger.info("数据搜索完成")
            
        except Exception as e:
            self.logger.error(f"搜索数据失败: {e}")
        finally:
            self._is_loading = False
    
    def reset_filters(self):
        """重置过滤条件"""
        try:
            # 重置时间范围
            self._ui_components['start_time'].setDateTime(QDateTime.currentDateTime().addDays(-7))
            self._ui_components['end_time'].setDateTime(QDateTime.currentDateTime())
            
            # 重置下拉框
            self._ui_components['status_filter'].setCurrentIndex(0)
            self._ui_components['type_filter'].setCurrentIndex(0)
            
            # 重置搜索框
            self._ui_components['keyword_search'].clear()
            
            # 清空过滤条件
            self._filter_conditions.clear()
            
            # 重新加载数据
            self.search_data()
            
            self.logger.info("过滤条件已重置")
            
        except Exception as e:
            self.logger.error(f"重置过滤条件失败: {e}")
    
    def export_data(self):
        """导出数据"""
        try:
            export_format = "CSV"  # 可以通过对话框选择格式
            self.export_requested.emit(export_format, self._filter_conditions)
            
            self.logger.info(f"请求导出数据: {export_format}")
            
        except Exception as e:
            self.logger.error(f"导出数据失败: {e}")
    
    def delete_selected(self):
        """删除选中的记录"""
        try:
            if self._history_viewer:
                selected_items = self._history_viewer.get_selected_items()
                if selected_items:
                    # 这里应该调用数据访问层来删除数据
                    self.logger.info(f"请求删除 {len(selected_items)} 条记录")
                    
                    # 刷新数据
                    self.refresh_data()
            
        except Exception as e:
            self.logger.error(f"删除记录失败: {e}")
    
    def refresh_data(self):
        """刷新数据"""
        self.search_data()
    
    def view_details(self):
        """查看详细信息"""
        try:
            if self._history_viewer:
                selected_item = self._history_viewer.get_current_item()
                if selected_item:
                    # 这里应该打开详细信息对话框
                    self.logger.info(f"查看详细信息: {selected_item}")
            
        except Exception as e:
            self.logger.error(f"查看详细信息失败: {e}")
    
    def edit_record(self):
        """编辑记录"""
        try:
            if self._history_viewer:
                selected_item = self._history_viewer.get_current_item()
                if selected_item:
                    # 这里应该打开编辑对话框
                    self.logger.info(f"编辑记录: {selected_item}")
            
        except Exception as e:
            self.logger.error(f"编辑记录失败: {e}")
    
    def first_page(self):
        """跳转到首页"""
        if self._current_page > 1:
            self._current_page = 1
            self.search_data()
    
    def previous_page(self):
        """上一页"""
        if self._current_page > 1:
            self._current_page -= 1
            self.search_data()
    
    def next_page(self):
        """下一页"""
        max_page = max(1, (self._total_records + self._page_size - 1) // self._page_size)
        if self._current_page < max_page:
            self._current_page += 1
            self.search_data()
    
    def last_page(self):
        """跳转到末页"""
        max_page = max(1, (self._total_records + self._page_size - 1) // self._page_size)
        if self._current_page < max_page:
            self._current_page = max_page
            self.search_data()
    
    def _update_filter_conditions(self):
        """更新过滤条件"""
        self._filter_conditions = {
            'start_time': self._ui_components['start_time'].dateTime().toPython(),
            'end_time': self._ui_components['end_time'].dateTime().toPython(),
            'status': self._ui_components['status_filter'].currentText(),
            'type': self._ui_components['type_filter'].currentText(),
            'keyword': self._ui_components['keyword_search'].text(),
            'page': self._current_page,
            'page_size': self._page_size
        }
    
    def _simulate_data_load(self):
        """模拟数据加载"""
        # 这里应该替换为真实的数据加载逻辑
        import random
        
        sample_data = []
        for i in range(self._page_size):
            sample_data.append({
                'id': i + 1,
                'timestamp': datetime.now() - timedelta(days=random.randint(0, 30)),
                'type': random.choice(['检测', '校准', '维护', '报告']),
                'status': random.choice(['成功', '失败', '处理中']),
                'description': f"记录 {i + 1} 的描述信息",
                'details': {'param1': random.randint(1, 100), 'param2': random.random()}
            })
        
        self._total_records = 500  # 模拟总记录数
        self.data_loaded.emit(sample_data)
    
    def _apply_search(self):
        """应用搜索"""
        self.search_data()
    
    def _on_data_loaded(self, data: List[Dict[str, Any]]):
        """处理数据加载完成"""
        self._current_data = data
        self._filtered_data = data.copy()
        
        # 更新历史查看器
        if self._history_viewer:
            self._history_viewer.update_data(data)
        
        # 更新分页信息
        self._update_pagination_info()
        
        self.logger.info(f"数据加载完成: {len(data)} 条记录")
    
    def _on_filter_changed(self, conditions: Dict[str, Any]):
        """处理过滤条件改变"""
        self._filter_conditions = conditions
        self.search_data()
    
    def _on_selection_changed(self, selected_items: List[Any]):
        """处理选择改变"""
        if selected_items:
            self._update_detail_view(selected_items[0])
    
    def _on_item_double_clicked(self, item: Any):
        """处理双击事件"""
        self.view_details()
    
    def _on_search_text_changed(self, text: str):
        """处理搜索文本改变"""
        self._search_timer.stop()
        self._search_timer.start(500)  # 500ms 延迟搜索
    
    def _on_time_filter_changed(self):
        """处理时间过滤器改变"""
        self._on_filter_changed(self._filter_conditions)
    
    def _on_page_size_changed(self, size_text: str):
        """处理每页大小改变"""
        self._page_size = int(size_text)
        self._current_page = 1
        self.search_data()
    
    def _update_detail_view(self, item: Any):
        """更新详细信息视图"""
        if 'detail_text' in self._ui_components:
            detail_info = f"""
记录详细信息:
━━━━━━━━━━━━━━━━
ID: {item.get('id', 'N/A')}
时间: {item.get('timestamp', 'N/A')}
类型: {item.get('type', 'N/A')}
状态: {item.get('status', 'N/A')}
描述: {item.get('description', 'N/A')}
            """
            self._ui_components['detail_text'].setText(detail_info.strip())
        
        # 更新预览表格
        if 'preview_table' in self._ui_components and 'details' in item:
            self._update_preview_table(item['details'])
    
    def _update_preview_table(self, details: Dict[str, Any]):
        """更新预览表格"""
        table = self._ui_components['preview_table']
        table.setRowCount(len(details))
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["参数", "值"])
        
        for row, (key, value) in enumerate(details.items()):
            table.setItem(row, 0, QTableWidgetItem(str(key)))
            table.setItem(row, 1, QTableWidgetItem(str(value)))
        
        table.resizeColumnsToContents()
    
    def _update_pagination_info(self):
        """更新分页信息"""
        if 'page_info' in self._ui_components:
            total_pages = max(1, (self._total_records + self._page_size - 1) // self._page_size)
            info_text = f"第 {self._current_page} 页，共 {self._total_records} 条记录 (共 {total_pages} 页)"
            self._ui_components['page_info'].setText(info_text)
        
        # 更新按钮状态
        self._ui_components['first_btn'].setEnabled(self._current_page > 1)
        self._ui_components['prev_btn'].setEnabled(self._current_page > 1)
        
        max_page = max(1, (self._total_records + self._page_size - 1) // self._page_size)
        self._ui_components['next_btn'].setEnabled(self._current_page < max_page)
        self._ui_components['last_btn'].setEnabled(self._current_page < max_page)
    
    def get_current_data(self) -> List[Dict[str, Any]]:
        """获取当前数据"""
        return self._current_data.copy()
    
    def get_filtered_data(self) -> List[Dict[str, Any]]:
        """获取过滤后的数据"""
        return self._filtered_data.copy()
    
    def get_filter_conditions(self) -> Dict[str, Any]:
        """获取过滤条件"""
        return self._filter_conditions.copy()
    
    def cleanup(self):
        """清理资源"""
        self._search_timer.stop()
        
        if self._history_viewer:
            self._history_viewer.deleteLater()
        
        if self._widget:
            self._widget.deleteLater()
        
        self.logger.info("历史查看控制器清理完成")