"""
统一历史数据查看器
合并3.1【历史数据界面】和3.2【缺陷标注】界面
通过下拉框选择查看内容：【管孔直径】或【缺陷标注】
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QStackedWidget, QGroupBox, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import weakref
import gc

from .history_viewer import HistoryViewer
from .defect_annotation_tool import DefectAnnotationTool


class UnifiedHistoryViewer(QWidget):
    """统一历史数据查看器"""
    
    # 信号定义
    view_mode_changed = Signal(str)  # 视图模式改变信号
    selection_changed = Signal(dict)  # 选择改变信号，携带选中项的数据
    item_double_clicked = Signal(dict)  # 项目双击信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化组件
        self.history_viewer = None
        self.annotation_tool = None
        self.current_mode = "管孔直径"
        
        # 内存管理相关
        self._cleanup_called = False
        self._widget_refs = weakref.WeakSet()
        self._signal_connections = []
        
        # 初始化UI
        self.init_ui()
        
        # 初始化子组件
        self.init_components()
        
    def _connect_signal(self, signal, slot):
        """安全地连接信号和槽，并跟踪连接"""
        connection = signal.connect(slot)
        self._signal_connections.append((signal, slot, connection))
        return connection
        
    def _disconnect_all_signals(self):
        """断开所有信号连接"""
        for signal, slot, connection in self._signal_connections:
            try:
                signal.disconnect(slot)
            except:
                pass
        self._signal_connections.clear()
        
    def cleanup(self):
        """清理资源"""
        if self._cleanup_called:
            return
        self._cleanup_called = True
        
        try:
            # 断开所有信号连接
            self._disconnect_all_signals()
            
            # 清理子组件
            if self.history_viewer:
                if hasattr(self.history_viewer, 'cleanup'):
                    self.history_viewer.cleanup()
                self.history_viewer = None
                
            if self.annotation_tool:
                if hasattr(self.annotation_tool, 'cleanup'):
                    self.annotation_tool.cleanup()
                self.annotation_tool = None
                
            # 清理弱引用
            self._widget_refs.clear()
            
            # 强制垃圾回收
            gc.collect()
            
        except Exception as e:
            print(f"清理UnifiedHistoryViewer资源时出错: {e}")
            
    def __del__(self):
        """析构函数"""
        self.cleanup()
        
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.cleanup()
        super().closeEvent(event)
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("历史数据查看器")
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 创建顶部控制面板
        self.create_control_panel(main_layout)
        
        # 创建内容区域
        self.create_content_area(main_layout)
        
    def create_control_panel(self, parent_layout):
        """创建顶部控制面板"""
        # 控制面板组框
        control_group = QGroupBox("数据类型选择")
        control_group.setMaximumHeight(80)
        control_layout = QHBoxLayout(control_group)
        
        # 设置字体
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        
        label_font = QFont()
        label_font.setPointSize(11)
        
        # 选择标签
        select_label = QLabel("查看内容：")
        select_label.setFont(label_font)
        control_layout.addWidget(select_label)
        
        # 数据类型下拉框
        self.data_type_combo = QComboBox()
        self.data_type_combo.setFont(label_font)
        self.data_type_combo.setMinimumWidth(150)
        self.data_type_combo.addItems(["管孔直径", "缺陷标注"])
        self.data_type_combo.setCurrentText("管孔直径")
        self._connect_signal(self.data_type_combo.currentTextChanged, self.on_data_type_changed)
        control_layout.addWidget(self.data_type_combo)
        
        # 添加弹性空间
        control_layout.addStretch()
        
        # 状态标签
        self.status_label = QLabel("当前模式：管孔直径历史数据")
        self.status_label.setFont(label_font)
        self.status_label.setObjectName("SuccessLabel")
        control_layout.addWidget(self.status_label)
        
        parent_layout.addWidget(control_group)
        
    def create_content_area(self, parent_layout):
        """创建内容区域"""
        # 创建堆叠窗口部件用于切换不同的视图
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        parent_layout.addWidget(self.stacked_widget)
        
    def init_components(self):
        """初始化子组件"""
        try:
            # 创建历史数据查看器（3.1界面）
            print("🔧 初始化历史数据查看器...")
            self.history_viewer = HistoryViewer()
            self._widget_refs.add(self.history_viewer)
            self.stacked_widget.addWidget(self.history_viewer)
            
            # 连接历史数据查看器的选择事件
            if hasattr(self.history_viewer, 'data_table'):
                self._connect_signal(
                    self.history_viewer.data_table.cellClicked, 
                    self._on_history_table_selection_changed
                )
                self._connect_signal(
                    self.history_viewer.data_table.cellDoubleClicked, 
                    self._on_history_table_item_activated
                )
            
            print("✅ 历史数据查看器初始化完成")
            
            # 创建缺陷标注工具（3.2界面）
            print("🔧 初始化缺陷标注工具...")
            self.annotation_tool = DefectAnnotationTool()
            self._widget_refs.add(self.annotation_tool)
            self.stacked_widget.addWidget(self.annotation_tool)
            
            # 连接缺陷标注工具的选择事件
            if hasattr(self.annotation_tool, 'image_list'):
                self._connect_signal(
                    self.annotation_tool.image_list.itemClicked,
                    self._on_annotation_image_selection_changed
                )
            
            print("✅ 缺陷标注工具初始化完成")
            
            # 设置默认显示历史数据查看器
            self.stacked_widget.setCurrentWidget(self.history_viewer)
            
            print("✅ 统一历史数据查看器初始化完成")
            
        except Exception as e:
            print(f"❌ 初始化子组件失败: {e}")
            # 创建错误显示组件
            error_widget = QWidget()
            error_layout = QVBoxLayout(error_widget)
            error_label = QLabel(f"初始化失败: {str(e)}")
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet("color: red; font-size: 14px;")
            error_layout.addWidget(error_label)
            self.stacked_widget.addWidget(error_widget)
            
    def on_data_type_changed(self, data_type):
        """数据类型改变处理"""
        print(f"🔄 切换数据类型: {self.current_mode} → {data_type}")
        
        self.current_mode = data_type
        
        try:
            if data_type == "管孔直径":
                if self.history_viewer:
                    self.stacked_widget.setCurrentWidget(self.history_viewer)
                    self.status_label.setText("当前模式：管孔直径历史数据")
                    self.status_label.setStyleSheet("color: #2E7D32; font-weight: bold;")
                    print("✅ 切换到历史数据查看器")
                else:
                    print("❌ 历史数据查看器未初始化")
                    
            elif data_type == "缺陷标注":
                if self.annotation_tool:
                    self.stacked_widget.setCurrentWidget(self.annotation_tool)
                    self.status_label.setText("当前模式：缺陷标注工具")
                    self.status_label.setStyleSheet("color: #1976D2; font-weight: bold;")
                    print("✅ 切换到缺陷标注工具")
                else:
                    print("❌ 缺陷标注工具未初始化")
            
            # 发射信号
            self.view_mode_changed.emit(data_type)
            
        except Exception as e:
            print(f"❌ 切换数据类型失败: {e}")
            self.status_label.setText(f"切换失败: {str(e)}")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
    
    def load_data_for_hole(self, hole_id: str):
        """为指定孔位加载数据"""
        print(f"📊 为孔位 {hole_id} 加载数据 (当前模式: {self.current_mode})")
        
        try:
            if self.current_mode == "管孔直径" and self.history_viewer:
                if hasattr(self.history_viewer, 'load_data_for_hole'):
                    self.history_viewer.load_data_for_hole(hole_id)
                    print(f"✅ 历史数据查看器已加载孔位 {hole_id} 的数据")
                else:
                    print("⚠️ 历史数据查看器不支持 load_data_for_hole 方法")
                    
            elif self.current_mode == "缺陷标注" and self.annotation_tool:
                # 缺陷标注工具可能需要不同的加载方式
                if hasattr(self.annotation_tool, 'load_data_for_hole'):
                    self.annotation_tool.load_data_for_hole(hole_id)
                    print(f"✅ 缺陷标注工具已加载孔位 {hole_id} 的数据")
                else:
                    print(f"💡 缺陷标注工具使用默认方式处理孔位 {hole_id}")
                    
        except Exception as e:
            print(f"❌ 加载孔位 {hole_id} 数据失败: {e}")
    
    def get_current_mode(self):
        """获取当前模式"""
        return self.current_mode
    
    def set_mode(self, mode: str):
        """设置模式"""
        if mode in ["管孔直径", "缺陷标注"]:
            self.data_type_combo.setCurrentText(mode)
        else:
            print(f"⚠️ 无效的模式: {mode}")
    
    def get_history_viewer(self):
        """获取历史数据查看器实例"""
        return self.history_viewer
    
    def get_annotation_tool(self):
        """获取缺陷标注工具实例"""
        return self.annotation_tool
    
    # ==================== 选择事件处理方法 ====================
    
    def _on_history_table_selection_changed(self, row, column):
        """处理历史数据表格选择改变事件"""
        try:
            if self.history_viewer and hasattr(self.history_viewer, 'data_table'):
                # 获取选中行的数据
                table = self.history_viewer.data_table
                if row < table.rowCount():
                    # 构造选择数据字典
                    selection_data = {
                        'type': 'history_measurement',
                        'mode': '管孔直径',
                        'row': row,
                        'column': column,
                        'data': {}
                    }
                    
                    # 提取表格行数据
                    for col in range(table.columnCount()):
                        if table.horizontalHeaderItem(col):
                            header = table.horizontalHeaderItem(col).text()
                            item = table.item(row, col)
                            value = item.text() if item else ""
                            selection_data['data'][header] = value
                    
                    # 添加孔位ID信息（如果可用）
                    if hasattr(self.history_viewer, 'current_hole_data') and self.history_viewer.current_hole_data:
                        selection_data['hole_id'] = self.history_viewer.current_hole_data.get('hole_id', '')
                        selection_data['workpiece_id'] = self.history_viewer.current_hole_data.get('workpiece_id', '')
                    
                    print(f"📊 历史数据表格选择: 行{row}, 列{column}")
                    print(f"🔍 选择数据: {selection_data.get('hole_id', 'Unknown')} - {list(selection_data['data'].keys())}")
                    
                    # 发射选择改变信号
                    self.selection_changed.emit(selection_data)
                    
        except Exception as e:
            print(f"❌ 处理历史数据表格选择失败: {e}")
    
    def _on_history_table_item_activated(self, row, column):
        """处理历史数据表格项目激活事件（双击）"""
        try:
            if self.history_viewer and hasattr(self.history_viewer, 'data_table'):
                # 获取激活行的数据
                table = self.history_viewer.data_table
                if row < table.rowCount():
                    # 构造激活数据字典
                    activation_data = {
                        'type': 'history_measurement_activated',
                        'mode': '管孔直径',
                        'row': row,
                        'column': column,
                        'action': 'double_click',
                        'data': {}
                    }
                    
                    # 提取表格行数据
                    for col in range(table.columnCount()):
                        if table.horizontalHeaderItem(col):
                            header = table.horizontalHeaderItem(col).text()
                            item = table.item(row, col)
                            value = item.text() if item else ""
                            activation_data['data'][header] = value
                    
                    # 添加孔位ID信息（如果可用）
                    if hasattr(self.history_viewer, 'current_hole_data') and self.history_viewer.current_hole_data:
                        activation_data['hole_id'] = self.history_viewer.current_hole_data.get('hole_id', '')
                        activation_data['workpiece_id'] = self.history_viewer.current_hole_data.get('workpiece_id', '')
                    
                    print(f"🎯 历史数据表格激活: 行{row}, 列{column} (双击)")
                    print(f"🔍 激活数据: {activation_data.get('hole_id', 'Unknown')} - 触发详细分析")
                    
                    # 发射选择改变信号（激活也算一种特殊的选择）
                    self.selection_changed.emit(activation_data)
                    # 同时发射双击信号
                    self.item_double_clicked.emit(activation_data)
                    
        except Exception as e:
            print(f"❌ 处理历史数据表格激活失败: {e}")
    
    def _on_annotation_image_selection_changed(self, item):
        """处理缺陷标注工具图像选择改变事件"""
        try:
            if item and self.annotation_tool:
                # 构造选择数据字典
                selection_data = {
                    'type': 'defect_image',
                    'mode': '缺陷标注',
                    'item_text': item.text(),
                    'data': {
                        'image_name': item.text(),
                        'item_data': item.data(Qt.UserRole) if item.data(Qt.UserRole) else {}
                    }
                }
                
                # 尝试获取当前孔位信息
                if hasattr(self.annotation_tool, 'current_hole_id'):
                    selection_data['hole_id'] = getattr(self.annotation_tool, 'current_hole_id', '')
                
                print(f"🖼️ 缺陷标注图像选择: {item.text()}")
                print(f"🔍 选择数据: {selection_data.get('hole_id', 'Unknown')} - {selection_data['data']['image_name']}")
                
                # 发射选择改变信号
                self.selection_changed.emit(selection_data)
                
        except Exception as e:
            print(f"❌ 处理缺陷标注图像选择失败: {e}")
    
    def get_current_selection(self):
        """获取当前选择状态"""
        current_selection = {
            'mode': self.current_mode,
            'active_widget': None,
            'selection_info': None
        }
        
        try:
            if self.current_mode == "管孔直径" and self.history_viewer:
                current_selection['active_widget'] = 'history_viewer'
                if hasattr(self.history_viewer, 'data_table'):
                    table = self.history_viewer.data_table
                    current_row = table.currentRow()
                    current_column = table.currentColumn()
                    if current_row >= 0 and current_column >= 0:
                        current_selection['selection_info'] = {
                            'row': current_row,
                            'column': current_column,
                            'type': 'table_cell'
                        }
                        
            elif self.current_mode == "缺陷标注" and self.annotation_tool:
                current_selection['active_widget'] = 'annotation_tool'
                if hasattr(self.annotation_tool, 'image_list'):
                    current_item = self.annotation_tool.image_list.currentItem()
                    if current_item:
                        current_selection['selection_info'] = {
                            'item_text': current_item.text(),
                            'type': 'image_item'
                        }
                        
        except Exception as e:
            print(f"❌ 获取当前选择状态失败: {e}")
            
        return current_selection
