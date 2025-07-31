#!/usr/bin/env python3
"""
诊断扇形显示问题
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QTextEdit
from PySide6.QtCore import Qt, QTimer
from src.core_business.graphics.complete_panorama_widget import CompletePanoramaWidget
from src.pages.main_detection_p1.services.dxf_loader_service import DXFLoaderService
from src.core_business.graphics.sector_types import SectorQuadrant


class DiagnosticWindow(QMainWindow):
    """诊断窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("扇形显示诊断")
        self.setGeometry(100, 100, 1000, 800)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        
        # 标题
        title = QLabel("扇形显示诊断工具")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # 创建全景图组件
        self.panorama = CompletePanoramaWidget()
        self.panorama.setFixedSize(600, 600)
        layout.addWidget(self.panorama)
        
        # 诊断信息显示
        self.diag_text = QTextEdit()
        self.diag_text.setReadOnly(True)
        self.diag_text.setMaximumHeight(200)
        layout.addWidget(self.diag_text)
        
        # 自动开始诊断
        QTimer.singleShot(500, self.run_diagnostics)
        
    def log(self, message):
        """添加诊断日志"""
        self.diag_text.append(message)
        print(message)
        
    def run_diagnostics(self):
        """运行诊断"""
        self.log("="*60)
        self.log("开始扇形显示诊断")
        self.log("="*60)
        
        # 1. 加载DXF数据
        self.log("\n1. 加载DXF数据...")
        try:
            dxf_path = str(Path(__file__).parent / "assets" / "dxf" / "DXF Graph" / "东重管板.dxf")
            loader = DXFLoaderService()
            hole_collection = loader.load_dxf_file(dxf_path)
            
            if hole_collection:
                self.log(f"✅ DXF加载成功: {len(hole_collection.holes)} 个孔位")
                
                # 加载到全景图
                self.panorama.load_hole_collection(hole_collection)
                self.log("✅ 数据已加载到全景图")
                
                # 延迟执行进一步诊断
                QTimer.singleShot(1000, lambda: self.diagnose_panorama_state(hole_collection))
            else:
                self.log("❌ DXF加载失败")
                
        except Exception as e:
            self.log(f"❌ 错误: {str(e)}")
            import traceback
            traceback.print_exc()
            
    def diagnose_panorama_state(self, hole_collection):
        """诊断全景图状态"""
        self.log("\n2. 检查全景图状态...")
        
        # 检查场景
        scene = self.panorama._get_scene()
        if scene:
            items = scene.items()
            self.log(f"✅ 场景存在，包含 {len(items)} 个图形项")
            
            # 统计不同类型的项
            from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsPathItem
            from src.core_business.graphics.sector_highlight_item import SectorHighlightItem
            
            item_types = {}
            for item in items:
                item_type = type(item).__name__
                item_types[item_type] = item_types.get(item_type, 0) + 1
                
            self.log("\n图形项类型统计:")
            for item_type, count in sorted(item_types.items()):
                self.log(f"  - {item_type}: {count}")
        else:
            self.log("❌ 场景不存在")
            
        # 检查扇形高亮项
        self.log("\n3. 检查扇形高亮项...")
        if hasattr(self.panorama, 'sector_highlights'):
            self.log(f"扇形高亮字典大小: {len(self.panorama.sector_highlights)}")
            for sector, highlight in self.panorama.sector_highlights.items():
                self.log(f"  - {sector.value}: {highlight}")
                
                # 检查高亮项的属性
                if hasattr(highlight, 'sector'):
                    self.log(f"    sector属性: {highlight.sector}")
                if hasattr(highlight, 'isVisible'):
                    self.log(f"    可见性: {highlight.isVisible()}")
                if hasattr(highlight, 'boundingRect'):
                    rect = highlight.boundingRect()
                    self.log(f"    边界矩形: ({rect.x():.1f}, {rect.y():.1f}, {rect.width():.1f}, {rect.height():.1f})")
        else:
            self.log("❌ 没有sector_highlights属性")
            
        # 检查扇形分隔线
        self.log("\n4. 检查扇形分隔线...")
        line_count = 0
        for item in scene.items():
            if isinstance(item, QGraphicsLineItem):
                line_count += 1
                line = item.line()
                self.log(f"  - 线条: ({line.x1():.1f}, {line.y1():.1f}) -> ({line.x2():.1f}, {line.y2():.1f})")
                
        if line_count > 0:
            self.log(f"✅ 找到 {line_count} 条分隔线")
        else:
            self.log("❌ 没有找到分隔线")
            
        # 手动创建扇形高亮测试
        self.log("\n5. 手动测试扇形高亮...")
        QTimer.singleShot(2000, self.test_manual_highlights)
        
    def test_manual_highlights(self):
        """手动测试扇形高亮"""
        self.log("\n测试扇形高亮功能...")
        
        # 依次高亮每个扇形
        sectors = [SectorQuadrant.SECTOR_1, SectorQuadrant.SECTOR_2, 
                   SectorQuadrant.SECTOR_3, SectorQuadrant.SECTOR_4]
        
        def highlight_next(index=0):
            if index < len(sectors):
                sector = sectors[index]
                self.log(f"高亮 {sector.value}...")
                try:
                    self.panorama.highlight_sector(sector)
                    # 2秒后高亮下一个
                    QTimer.singleShot(2000, lambda: highlight_next(index + 1))
                except Exception as e:
                    self.log(f"❌ 高亮失败: {e}")
            else:
                self.log("\n✅ 扇形高亮测试完成")
                self.check_sector_rendering()
                
        highlight_next()
        
    def check_sector_rendering(self):
        """检查扇形渲染问题"""
        self.log("\n6. 分析扇形渲染问题...")
        
        # 检查SectorHighlightItem的实现
        try:
            from src.core_business.graphics.sector_highlight_item import SectorHighlightItem
            
            # 创建一个测试实例
            if self.panorama.center_point and self.panorama.panorama_radius > 0:
                test_highlight = SectorHighlightItem(
                    sector=SectorQuadrant.SECTOR_1,
                    center=self.panorama.center_point,
                    radius=self.panorama.panorama_radius
                )
                
                # 检查paint方法
                if hasattr(test_highlight, 'paint'):
                    self.log("✅ SectorHighlightItem有paint方法")
                else:
                    self.log("❌ SectorHighlightItem没有paint方法")
                    
                # 检查扇形路径
                if hasattr(test_highlight, 'path'):
                    path = test_highlight.path()
                    if path and not path.isEmpty():
                        self.log("✅ 扇形路径已创建")
                    else:
                        self.log("❌ 扇形路径为空")
                else:
                    self.log("⚠️ SectorHighlightItem没有path方法")
                    
        except Exception as e:
            self.log(f"❌ 检查SectorHighlightItem失败: {e}")
            
        self.log("\n诊断完成！")
        self.log("\n可能的问题:")
        self.log("1. SectorHighlightItem可能渲染了完整的圆而不是扇形")
        self.log("2. 扇形分隔线可能太淡或被遮挡")
        self.log("3. 所有扇形可能使用了相同的颜色")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    window = DiagnosticWindow()
    window.show()
    
    # 30秒后退出
    QTimer.singleShot(30000, app.quit)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()