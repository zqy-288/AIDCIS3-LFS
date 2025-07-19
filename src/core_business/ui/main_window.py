"""
AIDCIS2 主窗口
"""

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import QObject, Signal


class AIDCIS2MainWindow(QMainWindow):
    """AIDCIS2 主窗口类"""
    
    # 信号
    hole_selected = Signal(str)  # 孔位选择信号
    view_changed = Signal(str)   # 视图变化信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AIDCIS2 管孔检测系统")
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        layout.addWidget(QLabel("AIDCIS2 主界面"))
        
        # 初始化组件
        self._init_components()
        
    def _init_components(self):
        """初始化组件"""
        # 视图控制相关
        self.view_mode = "normal"
        self.zoom_level = 1.0
        
        # 数据相关
        self.hole_collection = None
        self.current_hole = None
        
    def set_hole_collection(self, hole_collection):
        """设置孔位集合"""
        self.hole_collection = hole_collection
        
    def get_hole_collection(self):
        """获取孔位集合"""
        return self.hole_collection
        
    def zoom_in(self):
        """放大视图"""
        self.zoom_level *= 1.2
        self.view_changed.emit("zoom_in")
        
    def zoom_out(self):
        """缩小视图"""
        self.zoom_level /= 1.2
        self.view_changed.emit("zoom_out")
        
    def fit_view(self):
        """适应视图"""
        self.zoom_level = 1.0
        self.view_changed.emit("fit_view")
        
    def select_hole(self, hole_id):
        """选择孔位"""
        if self.hole_collection and hole_id in self.hole_collection.holes:
            self.current_hole = self.hole_collection.holes[hole_id]
            self.hole_selected.emit(hole_id)
            
    def get_current_hole(self):
        """获取当前选择的孔位"""
        return self.current_hole