#!/usr/bin/env python3
"""
简单的扇形测试
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import Qt, QTimer
from src.core_business.graphics.complete_panorama_widget import CompletePanoramaWidget
from src.pages.main_detection_p1.services.dxf_loader_service import DXFLoaderService


class SimpleSectorTest(QMainWindow):
    """简单扇形测试"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("简单扇形测试")
        self.setGeometry(100, 100, 800, 700)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        
        # 标题
        title = QLabel("简单扇形测试 - 检查分隔线是否可见")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # 使用原来的CompletePanoramaWidget测试
        self.panorama = CompletePanoramaWidget()
        self.panorama.setFixedSize(600, 600)
        layout.addWidget(self.panorama)
        
        # 状态标签
        self.status_label = QLabel("加载中...")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # 自动加载
        QTimer.singleShot(1000, self.load_and_test)
        
    def load_and_test(self):
        """加载和测试"""
        try:
            # 加载DXF数据
            dxf_path = str(Path(__file__).parent / "assets" / "dxf" / "DXF Graph" / "东重管板.dxf")
            loader = DXFLoaderService()
            hole_collection = loader.load_dxf_file(dxf_path)
            
            if hole_collection:
                self.panorama.load_hole_collection(hole_collection)
                self.status_label.setText(f"✅ 数据加载完成: {len(hole_collection.holes)} 个孔位")
                
                # 检查场景项
                QTimer.singleShot(2000, self.analyze_scene)
            else:
                self.status_label.setText("❌ DXF加载失败")
                
        except Exception as e:
            self.status_label.setText(f"❌ 错误: {str(e)}")
            
    def analyze_scene(self):
        """分析场景内容"""
        try:
            scene = self.panorama._get_scene()
            if not scene:
                print("❌ 无法获取场景")
                return
                
            items = scene.items()
            print(f"\n场景分析:")
            print(f"总图形项数: {len(items)}")
            
            # 统计各种类型
            from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsLineItem
            try:
                from src.pages.main_detection_p1.components.graphics.sector_highlight_item import SectorHighlightItem
                has_new_highlight = True
            except:
                try:
                    from src.core_business.graphics.sector_highlight_item import SectorHighlightItem
                    has_new_highlight = False
                except:
                    SectorHighlightItem = None
                    has_new_highlight = False
            
            ellipse_count = 0
            line_count = 0 
            highlight_count = 0
            visible_highlight_count = 0
            
            for item in items:
                if isinstance(item, QGraphicsEllipseItem):
                    ellipse_count += 1
                elif isinstance(item, QGraphicsLineItem):
                    line_count += 1
                    line = item.line()
                    print(f"  线条: ({line.x1():.0f},{line.y1():.0f}) -> ({line.x2():.0f},{line.y2():.0f})")
                elif SectorHighlightItem and isinstance(item, SectorHighlightItem):
                    highlight_count += 1
                    if item.isVisible():
                        visible_highlight_count += 1
                        print(f"  可见扇形: {item.sector.value}")
                    else:
                        print(f"  隐藏扇形: {item.sector.value}")
                        
            print(f"\n统计结果:")
            print(f"  孔位(椭圆): {ellipse_count}")
            print(f"  分隔线: {line_count}")
            print(f"  扇形高亮: {visible_highlight_count}/{highlight_count} 可见")
            print(f"  使用新版扇形高亮: {'是' if has_new_highlight else '否'}")
            
            if line_count >= 2:
                print("✅ 扇形分隔线存在")
            else:
                print("❌ 扇形分隔线缺失")
                
            if visible_highlight_count > 0:
                print("✅ 扇形边界可见")
            else:
                print("❌ 扇形边界不可见")
                
        except Exception as e:
            print(f"分析失败: {e}")
            import traceback
            traceback.print_exc()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    print("="*50)
    print("简单扇形测试")
    print("="*50)
    
    window = SimpleSectorTest()
    window.show()
    
    # 30秒后退出
    QTimer.singleShot(30000, app.quit)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()