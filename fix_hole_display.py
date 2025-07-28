#!/usr/bin/env python3
"""
修复孔位显示问题
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def create_fixed_gui():
    """创建修复后的GUI"""
    print("🔧 创建修复后的GUI...")
    
    try:
        from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QTextEdit
        from PySide6.QtCore import Qt, QTimer, QRectF
        from PySide6.QtGui import QColor, QPen, QBrush
        
        # 创建应用
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        print("✅ QApplication创建成功")
        
        # 加载DXF数据
        print("📖 加载DXF数据...")
        from src.core_business.dxf_parser import DXFParser
        
        dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-LFS/assets/dxf/DXF Graph/东重管板.dxf"
        parser = DXFParser()
        hole_collection = parser.parse_file(dxf_path)
        
        print(f"✅ DXF载入成功: {len(hole_collection.holes)} 个孔位")
        
        # 创建主窗口
        window = QMainWindow()
        window.setWindowTitle(f"🔧 修复孔位显示 - {len(hole_collection.holes)} 个孔位")
        window.resize(1400, 1000)
        
        central_widget = QWidget()
        window.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 状态显示
        status_text = QTextEdit()
        status_text.setMaximumHeight(200)
        status_text.setPlainText(f"🔍 调试开始...\n已加载 {len(hole_collection.holes)} 个孔位\n")
        layout.addWidget(status_text)
        
        def log_status(message):
            status_text.append(message)
            print(message)
        
        # 创建全景图组件
        log_status("📊 创建全景图组件...")
        from src.core_business.graphics.complete_panorama_widget import CompletePanoramaWidget
        
        panorama_widget = CompletePanoramaWidget()
        panorama_widget.setMinimumSize(1000, 700)
        panorama_widget.setStyleSheet("border: 2px solid blue;")
        layout.addWidget(panorama_widget)
        
        # 修复按钮
        button_layout = QVBoxLayout()
        
        def manual_load_holes():
            """手动加载孔位到场景"""
            log_status("🔧 开始手动加载孔位...")
            
            try:
                scene = panorama_widget.panorama_view.scene
                if not scene:
                    log_status("❌ 无法获取场景")
                    return
                
                # 清空场景
                scene.clear()
                log_status("🧹 场景已清空")
                
                # 手动创建孔位图形项
                from PySide6.QtWidgets import QGraphicsEllipseItem
                
                hole_items = {}
                radius = 5.0  # 固定半径5像素，确保可见
                
                count = 0
                for hole_id, hole in hole_collection.holes.items():
                    # 创建圆形项
                    x, y = hole.center_x, hole.center_y
                    
                    # 创建圆形
                    ellipse = QGraphicsEllipseItem(x - radius, y - radius, radius * 2, radius * 2)
                    
                    # 设置样式 - 明亮的颜色
                    pen = QPen(QColor(255, 0, 0), 2)  # 红色边框
                    brush = QBrush(QColor(255, 255, 0, 150))  # 半透明黄色填充
                    
                    ellipse.setPen(pen)
                    ellipse.setBrush(brush)
                    ellipse.setVisible(True)
                    
                    # 添加到场景
                    scene.addItem(ellipse)
                    hole_items[hole_id] = ellipse
                    
                    count += 1
                    if count <= 5:  # 显示前5个的位置
                        log_status(f"  孔位 {hole_id}: ({x:.1f}, {y:.1f})")
                    
                    # 每1000个孔位显示一次进度
                    if count % 1000 == 0:
                        log_status(f"已加载 {count} 个孔位...")
                
                log_status(f"✅ 手动加载完成: {count} 个孔位")
                
                # 适应视图
                bounds = scene.itemsBoundingRect()
                log_status(f"📐 场景边界: ({bounds.x():.1f}, {bounds.y():.1f}) {bounds.width():.1f}×{bounds.height():.1f}")
                
                panorama_widget.panorama_view.fitInView(bounds, Qt.KeepAspectRatio)
                log_status("🎯 视图已适应场景")
                
                # 保存引用
                panorama_widget.panorama_view.hole_items = hole_items
                
            except Exception as e:
                log_status(f"❌ 手动加载失败: {e}")
                import traceback
                traceback.print_exc()
        
        manual_button = QPushButton("🔧 手动加载孔位 (红边黄心)")
        manual_button.clicked.connect(manual_load_holes)
        button_layout.addWidget(manual_button)
        
        def create_test_pattern():
            """创建测试图案"""
            log_status("🎨 创建测试图案...")
            
            try:
                scene = panorama_widget.panorama_view.scene
                scene.clear()
                
                from PySide6.QtWidgets import QGraphicsEllipseItem, QGraphicsRectItem
                
                # 创建一个大圆圈作为边界
                border = QGraphicsEllipseItem(-2000, -2000, 4000, 4000)
                border.setPen(QPen(QColor(0, 255, 0), 5))
                border.setBrush(QBrush())
                scene.addItem(border)
                
                # 创建中心点
                center = QGraphicsEllipseItem(-10, -10, 20, 20)
                center.setPen(QPen(QColor(255, 0, 0), 3))
                center.setBrush(QBrush(QColor(255, 0, 0)))
                scene.addItem(center)
                
                # 创建四个角落的标记
                corners = [(-1500, -1500), (1500, -1500), (1500, 1500), (-1500, 1500)]
                for i, (x, y) in enumerate(corners):
                    corner = QGraphicsRectItem(x-20, y-20, 40, 40)
                    corner.setPen(QPen(QColor(0, 0, 255), 3))
                    corner.setBrush(QBrush(QColor(0, 0, 255)))
                    scene.addItem(corner)
                
                # 创建网格
                for i in range(-10, 11, 2):
                    for j in range(-10, 11, 2):
                        x, y = i * 200, j * 200
                        dot = QGraphicsEllipseItem(x-5, y-5, 10, 10)
                        dot.setPen(QPen(QColor(128, 128, 128), 1))
                        dot.setBrush(QBrush(QColor(128, 128, 128)))
                        scene.addItem(dot)
                
                log_status("✅ 测试图案创建完成")
                log_status("🎯 绿色圆圈是边界，红点是中心，蓝方块是角落，灰点是网格")
                
                # 适应视图
                panorama_widget.panorama_view.fitInView(scene.itemsBoundingRect(), Qt.KeepAspectRatio)
                
            except Exception as e:
                log_status(f"❌ 测试图案创建失败: {e}")
        
        test_button = QPushButton("🎨 创建测试图案")
        test_button.clicked.connect(create_test_pattern)
        button_layout.addWidget(test_button)
        
        def use_original_load():
            """使用原始的加载方法"""
            log_status("📊 使用原始加载方法...")
            try:
                panorama_widget.load_complete_view(hole_collection)
                
                # 检查结果
                scene = panorama_widget.panorama_view.scene
                items = scene.items()
                bounds = scene.itemsBoundingRect()
                
                log_status(f"📊 原始加载结果:")
                log_status(f"  - 场景项数: {len(items)}")
                log_status(f"  - 场景边界: ({bounds.x():.1f}, {bounds.y():.1f}) {bounds.width():.1f}×{bounds.height():.1f}")
                
                # 检查前几个项的属性
                for i, item in enumerate(items[:5]):
                    pos = item.pos()
                    visible = item.isVisible()
                    log_status(f"  - 项{i}: {type(item).__name__} 位置({pos.x():.1f},{pos.y():.1f}) 可见:{visible}")
                
                # 检查hole_items
                if hasattr(panorama_widget.panorama_view, 'hole_items'):
                    hole_count = len(panorama_widget.panorama_view.hole_items)
                    log_status(f"  - hole_items数量: {hole_count}")
                
            except Exception as e:
                log_status(f"❌ 原始加载失败: {e}")
                import traceback
                traceback.print_exc()
        
        original_button = QPushButton("📊 使用原始加载方法")
        original_button.clicked.connect(use_original_load)
        button_layout.addWidget(original_button)
        
        layout.addLayout(button_layout)
        
        # 显示窗口
        window.show()
        log_status("🖥️ 修复窗口已显示")
        log_status("💡 操作说明:")
        log_status("  1. 点击'创建测试图案'查看基本图形是否显示")
        log_status("  2. 点击'手动加载孔位'直接创建孔位图形")
        log_status("  3. 点击'使用原始加载方法'测试原始功能")
        
        # 60秒后关闭
        def close_window():
            log_status("⏰ 60秒测试时间到，自动关闭")
            window.close()
            app.quit()
        
        timer = QTimer()
        timer.timeout.connect(close_window)
        timer.setSingleShot(True)
        timer.start(60000)
        
        return app.exec()
        
    except Exception as e:
        print(f"❌ 修复GUI创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 孔位显示修复工具")
    print("=" * 60)
    
    result = create_fixed_gui()
    
    print("\n" + "=" * 60)
    if result == 0:
        print("✅ 修复工具正常结束")
    else:
        print("❌ 修复工具遇到问题")
    print("=" * 60)