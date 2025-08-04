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

from .history_viewer import HistoryViewer
from .defect_annotation_tool import DefectAnnotationTool


class UnifiedHistoryViewer(QWidget):
    """统一历史数据查看器"""
    
    # 信号定义
    view_mode_changed = Signal(str)  # 视图模式改变信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化组件
        self.history_viewer = None
        self.annotation_tool = None
        self.current_mode = "管孔直径"
        
        # 初始化UI
        self.init_ui()
        
        # 初始化子组件
        self.init_components()
        
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
        control_group = QGroupBox("数据查看控制")
        # control_group.setMaximumHeight(80)  # 已删除：移除固定高度限制，让布局自适应
        control_layout = QHBoxLayout(control_group)
        control_layout.setSpacing(15)  # 增加控件间的水平间距
        
        # 孔位选择标签 - 新增
        hole_select_label = QLabel("孔位选择：")
        hole_select_label.setObjectName("HistoryViewerLabel")
        hole_select_label.setMinimumWidth(80)
        control_layout.addWidget(hole_select_label)
        
        # 孔位选择下拉框 - 新增
        self.hole_combo = QComboBox()
        self.hole_combo.setObjectName("HistoryViewerCombo")
        self.hole_combo.setMinimumWidth(150)
        self.hole_combo.setPlaceholderText("请选择孔位")
        # 初始化时添加已有数据的孔位
        self._init_hole_list()
        self.hole_combo.currentTextChanged.connect(self.on_hole_changed)
        control_layout.addWidget(self.hole_combo)
        
        # 分隔符 - 使用空间代替竖杠
        control_layout.addSpacing(20)
        
        # 选择标签 - 使用CSS样式，移除代码中的字体设置
        select_label = QLabel("查看内容：")
        select_label.setObjectName("HistoryViewerLabel")  # 使用CSS样式
        select_label.setMinimumWidth(80)  # 调整宽度
        control_layout.addWidget(select_label)

        # 数据类型下拉框 - 使用CSS样式
        self.data_type_combo = QComboBox()
        self.data_type_combo.setObjectName("HistoryViewerCombo")  # 使用CSS样式
        self.data_type_combo.setMinimumWidth(150)  # 调整宽度
        self.data_type_combo.addItems(["管孔直径", "缺陷标注"])
        self.data_type_combo.setCurrentText("管孔直径")
        self.data_type_combo.currentTextChanged.connect(self.on_data_type_changed)
        control_layout.addWidget(self.data_type_combo)

        # 添加弹性空间
        control_layout.addStretch()

        # 状态标签 - 使用CSS样式
        self.status_label = QLabel("当前模式：管孔直径历史数据")
        self.status_label.setObjectName("SuccessLabel")  # 使用CSS样式，字体已改为18px
        self.status_label.setMinimumWidth(300)  # 增加状态标签的文本框长度
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
            self.stacked_widget.addWidget(self.history_viewer)
            print("✅ 历史数据查看器初始化完成")
            
            # 创建缺陷标注工具（3.2界面）
            print("🔧 初始化缺陷标注工具...")
            self.annotation_tool = DefectAnnotationTool()
            self.stacked_widget.addWidget(self.annotation_tool)
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
            # 更新孔位下拉框的选中项（避免触发重复加载）
            self.hole_combo.blockSignals(True)
            index = self.hole_combo.findText(hole_id)
            if index >= 0:
                self.hole_combo.setCurrentIndex(index)
            else:
                # 如果孔位不在列表中，添加并选中
                self.hole_combo.addItem(hole_id)
                self.hole_combo.setCurrentText(hole_id)
            self.hole_combo.blockSignals(False)
            
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
    
    def _init_hole_list(self):
        """初始化孔位列表 - 从数据源获取已检测的孔位"""
        try:
            available_holes = self._get_available_holes()
            
            # 清空并重新填充下拉框
            self.hole_combo.clear()
            if available_holes:
                self.hole_combo.addItems(available_holes)
            else:
                self.hole_combo.addItem("无可用数据")
                
        except Exception as e:
            print(f"❌ 初始化孔位列表失败: {e}")
            self.hole_combo.addItem("数据加载失败")
    
    def _get_available_holes(self):
        """获取有历史数据的孔位列表 - 仅使用真实数据"""
        try:
            # 从最新批次获取孔位列表
            holes_from_batch = self._get_holes_from_latest_batch()
            if holes_from_batch:
                print(f"✅ 从最新批次获取到 {len(holes_from_batch)} 个孔位")
                return holes_from_batch
            
            print("❌ 未找到有效的批次数据")
            return []
            
        except Exception as e:
            print(f"❌ 获取孔位列表时出错: {e}")
            return []
    
    def _get_holes_from_latest_batch(self):
        """从最新批次获取孔位列表"""
        try:
            import json
            from pathlib import Path
            from datetime import datetime
            
            # 查找批次目录
            current_dir = Path(__file__).parent
            batches_dir = None
            for _ in range(10):
                potential_dir = current_dir / "Data" / "Products" / "CAP1000" / "InspectionBatches"
                if potential_dir.exists():
                    batches_dir = potential_dir
                    break
                current_dir = current_dir.parent
            
            if not batches_dir or not batches_dir.exists():
                return []
            
            # 获取所有批次目录，按创建时间排序
            batch_dirs = [d for d in batches_dir.iterdir() if d.is_dir()]
            if not batch_dirs:
                return []
            
            # 根据批次info中的创建时间排序，获取最新批次
            latest_batch = None
            latest_time = None
            
            for batch_dir in batch_dirs:
                batch_info_file = batch_dir / "batch_info.json"
                if batch_info_file.exists():
                    try:
                        with open(batch_info_file, 'r', encoding='utf-8') as f:
                            batch_info = json.load(f)
                        
                        created_at_str = batch_info.get('created_at')
                        if created_at_str:
                            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                            if latest_time is None or created_at > latest_time:
                                latest_time = created_at
                                latest_batch = batch_dir
                    except:
                        continue
            
            if not latest_batch:
                return []
            
            # 从最新批次获取孔位列表
            hole_results_dir = latest_batch / "HoleResults"
            hole_ids = []
            
            if hole_results_dir.exists():
                # 从结果文件中提取孔位ID
                result_files = list(hole_results_dir.glob("*.json"))
                for result_file in result_files:
                    try:
                        with open(result_file, 'r', encoding='utf-8') as f:
                            result_data = json.load(f)
                        hole_id = result_data.get('hole_id')
                        if hole_id:
                            hole_ids.append(hole_id)
                    except:
                        continue
            
            # 如果HoleResults为空或没有有效数据，返回空列表
            if not hole_ids:
                print(f"⚠️ 最新批次 {latest_batch.name} 的HoleResults为空")
            
            return sorted(hole_ids)
            
        except Exception as e:
            print(f"❌ 从最新批次获取孔位失败: {e}")
            return []
    
    

    
    def on_hole_changed(self, hole_id: str):
        """孔位选择改变处理"""
        if hole_id and hole_id not in ["无可用数据", "数据加载失败", "请选择孔位"]:
            print(f"🔄 切换孔位: {hole_id}")
            self.load_data_for_hole(hole_id)
    
    def refresh_hole_list(self):
        """刷新孔位列表 - 可供外部调用"""
        self._init_hole_list()
