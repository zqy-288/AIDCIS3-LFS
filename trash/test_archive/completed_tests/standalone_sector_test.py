#!/usr/bin/env python3
"""
独立的扇形测试 - 避开主窗口问题
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import Qt, QTimer

# 直接使用页面版本的组件
from src.pages.main_detection_p1.components.graphics.complete_panorama_widget import CompletePanoramaWidget
from src.pages.main_detection_p1.services.dxf_loader_service import DXFLoaderService


class StandaloneSectorTest(QMainWindow):
    """独立扇形测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("独立扇形测试 - 修复验证")
        self.setGeometry(100, 100, 800, 900)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        
        # 标题
        title = QLabel("🎯 扇形修复验证测试")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 20px; 
            font-weight: bold; 
            padding: 10px; 
            color: #2c3e50;
            background-color: #ecf0f1;
            border-radius: 5px;
            margin: 10px;
        """)
        layout.addWidget(title)
        
        # 说明
        info = QLabel("""
        现在应该能看到：
        ✅ 深灰色十字分隔线（实线，粗3px）
        ✅ 灰色扇形边界线（虚线，细2px）
        ✅ 四个清晰的扇形区域
        ✅ 点击不同区域检测到对应扇形
        """)
        info.setAlignment(Qt.AlignLeft)
        info.setStyleSheet("""
            font-size: 14px; 
            padding: 15px; 
            background-color: #d5f4e6;
            border-radius: 5px;
            border-left: 4px solid #27ae60;
            margin: 10px;
        """)
        layout.addWidget(info)
        
        # 全景图组件 - 直接使用修复后的版本
        self.panorama = CompletePanoramaWidget()
        self.panorama.setFixedSize(700, 600)
        self.panorama.setStyleSheet("""
            border: 2px solid #3498db;
            border-radius: 5px;
            background-color: white;
        """)
        layout.addWidget(self.panorama)
        
        # 状态显示
        self.status = QLabel("正在初始化...")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet("""
            font-size: 16px; 
            padding: 10px; 
            background-color: #f39c12;
            color: white;
            border-radius: 5px;
            margin: 10px;
        """)
        layout.addWidget(self.status)
        
        # 连接点击信号
        self.panorama.sector_clicked.connect(self.on_sector_clicked)
        
        # 自动开始测试
        QTimer.singleShot(1000, self.start_test)
        
    def start_test(self):
        """开始测试"""
        self.status.setText("📂 正在加载DXF数据...")
        self.status.setStyleSheet("""
            font-size: 16px; 
            padding: 10px; 
            background-color: #f39c12;
            color: white;
            border-radius: 5px;
            margin: 10px;
        """)
        
        try:
            # 加载DXF
            dxf_path = str(Path(__file__).parent / "assets" / "dxf" / "DXF Graph" / "东重管板.dxf")
            loader = DXFLoaderService()
            hole_collection = loader.load_dxf_file(dxf_path)
            
            if hole_collection:
                self.panorama.load_hole_collection(hole_collection)
                self.status.setText(f"✅ 成功加载 {len(hole_collection.holes):,} 个孔位，请观察扇形分隔线")
                self.status.setStyleSheet("""
                    font-size: 16px; 
                    padding: 10px; 
                    background-color: #27ae60;
                    color: white;
                    border-radius: 5px;
                    margin: 10px;
                """)
                
                # 分析场景
                QTimer.singleShot(2000, self.analyze_scene)
            else:
                self.status.setText("❌ DXF文件加载失败")
                self.status.setStyleSheet("""
                    font-size: 16px; 
                    padding: 10px; 
                    background-color: #e74c3c;
                    color: white;
                    border-radius: 5px;
                    margin: 10px;
                """)
                
        except Exception as e:
            self.status.setText(f"❌ 错误: {str(e)}")
            self.status.setStyleSheet("""
                font-size: 16px; 
                padding: 10px; 
                background-color: #e74c3c;
                color: white;
                border-radius: 5px;
                margin: 10px;
            """)
            
    def analyze_scene(self):
        """分析场景内容"""
        try:
            scene = self.panorama._get_scene()
            if not scene:
                print("无法获取场景")
                return
                
            items = scene.items()
            print(f"\n🔍 场景分析结果:")
            print(f"总图形项: {len(items)}")
            
            # 统计类型
            from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsLineItem
            from src.pages.main_detection_p1.components.graphics.sector_highlight_item import SectorHighlightItem
            
            holes = 0
            lines = 0
            sectors = 0
            visible_sectors = 0
            
            for item in items:
                if isinstance(item, QGraphicsEllipseItem):
                    holes += 1
                elif isinstance(item, QGraphicsLineItem):
                    lines += 1
                elif isinstance(item, SectorHighlightItem):
                    sectors += 1
                    if item.isVisible():
                        visible_sectors += 1
                        print(f"  📍 可见扇形: {item.sector.value}")
                        
            print(f"孔位: {holes:,}")
            print(f"分隔线: {lines}")
            print(f"扇形区域: {visible_sectors}/{sectors}")
            
            # 更新状态
            if lines >= 2 and visible_sectors >= 4:
                self.status.setText(f"🎉 修复成功！分隔线:{lines}条，可见扇形:{visible_sectors}个")
                self.status.setStyleSheet("""
                    font-size: 16px; 
                    padding: 10px; 
                    background-color: #27ae60;
                    color: white;
                    border-radius: 5px;
                    margin: 10px;
                """)
            else:
                self.status.setText(f"⚠️ 部分修复：分隔线:{lines}条，可见扇形:{visible_sectors}个")
                self.status.setStyleSheet("""
                    font-size: 16px; 
                    padding: 10px; 
                    background-color: #f39c12;
                    color: white;
                    border-radius: 5px;
                    margin: 10px;
                """)
                
        except Exception as e:
            print(f"分析失败: {e}")
            
    def on_sector_clicked(self, sector):
        """处理扇形点击"""
        self.status.setText(f"🎯 点击了 {sector.value} - 扇形检测正常！")
        self.status.setStyleSheet("""
            font-size: 16px; 
            padding: 10px; 
            background-color: #3498db;
            color: white;
            border-radius: 5px;
            margin: 10px;
        """)


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    print("="*60)
    print("🎯 独立扇形修复验证测试")
    print("="*60)
    print("这个测试直接使用修复后的组件，避开主窗口问题")
    print("="*60)
    
    window = StandaloneSectorTest()
    window.show()
    
    # 60秒后自动退出
    QTimer.singleShot(60000, app.quit)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()