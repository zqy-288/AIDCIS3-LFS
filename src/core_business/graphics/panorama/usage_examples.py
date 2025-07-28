"""
全景图组件使用示例
演示如何使用新的组件架构
"""

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt

from src.core_business.graphics.panorama import (
    PanoramaDIContainer, 
    get_global_container,
    PanoramaEvent
)
from src.core_business.models.hole_data import HoleCollection, HoleData, HoleStatus
from src.core_business.graphics.sector_types import SectorQuadrant


class PanoramaExampleWindow(QMainWindow):
    """全景图使用示例窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("全景图组件示例")
        self.setGeometry(100, 100, 1000, 800)
        
        # 使用依赖注入容器
        self.panorama_container = PanoramaDIContainer()
        
        # 设置UI
        self._setup_ui()
        
        # 设置事件监听
        self._setup_event_listeners()
        
        # 加载示例数据
        self._load_sample_data()
    
    def _setup_ui(self):
        """设置UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 控制按钮布局
        button_layout = QHBoxLayout()
        
        # 创建控制按钮
        self.load_data_btn = QPushButton("加载数据")
        self.update_status_btn = QPushButton("更新状态")
        self.highlight_btn = QPushButton("高亮扇区")
        self.clear_highlight_btn = QPushButton("清除高亮")
        self.snake_path_btn = QPushButton("切换蛇形路径")
        
        # 连接按钮事件
        self.load_data_btn.clicked.connect(self._load_sample_data)
        self.update_status_btn.clicked.connect(self._update_random_status)
        self.highlight_btn.clicked.connect(self._highlight_random_sector)
        self.clear_highlight_btn.clicked.connect(self._clear_highlight)
        self.snake_path_btn.clicked.connect(self._toggle_snake_path)
        
        # 添加按钮到布局
        button_layout.addWidget(self.load_data_btn)
        button_layout.addWidget(self.update_status_btn)
        button_layout.addWidget(self.highlight_btn)
        button_layout.addWidget(self.clear_highlight_btn)
        button_layout.addWidget(self.snake_path_btn)
        button_layout.addStretch()
        
        # 创建全景图组件
        self.panorama_widget = self.panorama_container.create_panorama_widget()
        
        # 添加到主布局
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.panorama_widget, 1)
        
        # 连接全景图信号
        self.panorama_widget.sector_clicked.connect(self._on_sector_clicked)
        self.panorama_widget.status_update_completed.connect(self._on_status_update_completed)
    
    def _setup_event_listeners(self):
        """设置事件监听"""
        event_bus = self.panorama_container.get_event_bus()
        
        # 监听所有事件（用于调试）
        event_bus.subscribe_all(self._on_panorama_event)
        
        # 监听特定事件
        event_bus.subscribe(PanoramaEvent.SECTOR_CLICKED, self._on_sector_event)
        event_bus.subscribe(PanoramaEvent.DATA_LOADED, self._on_data_loaded_event)
    
    def _load_sample_data(self):
        """加载示例数据"""
        # 创建示例孔位数据
        holes = {}
        
        # 创建网格状分布的孔位
        for i in range(10):
            for j in range(10):
                hole_id = f"H{i:02d}{j:02d}"
                hole_data = HoleData(
                    hole_id=hole_id,
                    center_x=i * 50 + 100,  # X坐标
                    center_y=j * 50 + 100,  # Y坐标
                    status=HoleStatus.PENDING
                )
                holes[hole_id] = hole_data
        
        # 创建孔位集合
        hole_collection = HoleCollection()
        hole_collection.holes = holes
        
        # 加载到全景图
        self.panorama_widget.load_hole_collection(hole_collection)
        
        print(f"已加载 {len(holes)} 个孔位")
    
    def _update_random_status(self):
        """随机更新一些孔位的状态"""
        import random
        
        # 获取数据模型
        data_model = self.panorama_container.get_data_model()
        holes = data_model.get_holes()
        
        if not holes:
            print("没有孔位数据")
            return
        
        # 随机选择一些孔位更新状态
        hole_ids = list(holes.keys())
        selected_holes = random.sample(hole_ids, min(10, len(hole_ids)))
        
        statuses = [HoleStatus.IN_PROGRESS, HoleStatus.COMPLETED, HoleStatus.FAILED]
        
        for hole_id in selected_holes:
            status = random.choice(statuses)
            self.panorama_widget.update_hole_status(hole_id, status)
        
        print(f"已更新 {len(selected_holes)} 个孔位的状态")
    
    def _highlight_random_sector(self):
        """随机高亮一个扇区"""
        import random
        
        sectors = list(SectorQuadrant)
        sector = random.choice(sectors)
        
        self.panorama_widget.highlight_sector(sector)
        print(f"高亮扇区: {sector.value}")
    
    def _clear_highlight(self):
        """清除高亮"""
        self.panorama_widget.clear_sector_highlight()
        print("已清除高亮")
    
    def _toggle_snake_path(self):
        """切换蛇形路径显示"""
        # 这里需要维护一个状态
        if not hasattr(self, '_snake_path_enabled'):
            self._snake_path_enabled = False
        
        self._snake_path_enabled = not self._snake_path_enabled
        self.panorama_widget.enable_snake_path(self._snake_path_enabled)
        
        print(f"蛇形路径: {'启用' if self._snake_path_enabled else '禁用'}")
    
    # 事件处理方法
    
    def _on_sector_clicked(self, sector: SectorQuadrant):
        """处理扇区点击"""
        print(f"点击了扇区: {sector.value}")
    
    def _on_status_update_completed(self, count: int):
        """处理状态更新完成"""
        print(f"批量更新完成，更新了 {count} 个孔位")
    
    def _on_panorama_event(self, event_data):
        """处理全景图事件（调试用）"""
        print(f"事件: {event_data.event_type.value}, 数据: {event_data.data}")
    
    def _on_sector_event(self, event_data):
        """处理扇区事件"""
        sector = event_data.data
        print(f"扇区事件: {sector.value if sector else None}")
    
    def _on_data_loaded_event(self, event_data):
        """处理数据加载事件"""
        print("数据加载完成")


def main():
    """主函数"""
    app = QApplication([])
    
    # 创建示例窗口
    window = PanoramaExampleWindow()
    window.show()
    
    # 运行应用
    app.exec()


if __name__ == "__main__":
    main()