#!/usr/bin/env python3
"""
修复全景图缩放问题 - 让孔位变得可见
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def fix_panorama_scaling():
    """修复全景图缩放问题"""
    print("🔧 修复全景图缩放问题...")
    
    try:
        from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QSlider, QHBoxLayout
        from PySide6.QtCore import Qt, QTimer
        from PySide6.QtGui import QColor, QPen, QBrush
        
        # 创建应用
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
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
        window.setWindowTitle(f"🔧 修复全景图缩放 - {len(hole_collection.holes)} 个孔位")
        window.resize(1400, 1000)
        
        central_widget = QWidget()
        window.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 状态信息
        status_label = QLabel("等待加载全景图...")
        status_label.setStyleSheet("font-size: 14px; padding: 10px; background-color: #f0f0f0;")
        layout.addWidget(status_label)
        
        # 创建全景图组件
        print("📊 创建全景图组件...")
        from src.core_business.graphics.complete_panorama_widget import CompletePanoramaWidget
        
        panorama_widget = CompletePanoramaWidget()
        panorama_widget.setMinimumSize(1200, 700)
        panorama_widget.setStyleSheet("border: 2px solid red;")  # 红色边框便于识别
        layout.addWidget(panorama_widget)
        
        # 控制面板
        control_layout = QHBoxLayout()
        
        # 缩放滑块
        zoom_label = QLabel("缩放:")
        control_layout.addWidget(zoom_label)
        
        zoom_slider = QSlider(Qt.Horizontal)
        zoom_slider.setMinimum(1)
        zoom_slider.setMaximum(50)
        zoom_slider.setValue(5)  # 默认5倍缩放
        control_layout.addWidget(zoom_slider)
        
        zoom_value_label = QLabel("5x")
        control_layout.addWidget(zoom_value_label)
        
        def update_zoom():
            """更新缩放"""
            zoom_factor = zoom_slider.value()
            zoom_value_label.setText(f"{zoom_factor}x")
            
            if hasattr(panorama_widget, 'panorama_view') and panorama_widget.panorama_view.scene:
                # 重置变换
                panorama_widget.panorama_view.resetTransform()
                
                # 应用新的缩放
                panorama_widget.panorama_view.scale(zoom_factor, zoom_factor)
                
                # 居中显示
                bounds = panorama_widget.panorama_view.scene.itemsBoundingRect()
                center = bounds.center()
                panorama_widget.panorama_view.centerOn(center)
                
                status_label.setText(f"✅ 缩放已调整为 {zoom_factor}x，场景中心: ({center.x():.1f}, {center.y():.1f})")
        
        zoom_slider.valueChanged.connect(update_zoom)
        
        # 按钮
        def load_and_fix():
            """加载并修复显示"""
            status_label.setText("🔄 正在加载全景图...")
            
            # 加载数据
            panorama_widget.load_complete_view(hole_collection)
            
            # 检查场景
            if hasattr(panorama_widget, 'panorama_view') and panorama_widget.panorama_view.scene:
                scene = panorama_widget.panorama_view.scene
                items = scene.items()
                bounds = scene.itemsBoundingRect()
                
                status_label.setText(f"""
✅ 全景图加载完成！
• 场景项数: {len(items)}
• 场景边界: ({bounds.x():.1f}, {bounds.y():.1f}) {bounds.width():.1f}×{bounds.height():.1f}
• 调整缩放滑块来查看孔位
                """)
                
                # 应用初始缩放
                update_zoom()
                
                print(f"📊 场景信息: {len(items)} 项, 边界: {bounds.width():.1f}×{bounds.height():.1f}")
            else:
                status_label.setText("❌ 无法访问场景")
        
        load_button = QPushButton("🔄 加载全景图")
        load_button.clicked.connect(load_and_fix)
        control_layout.addWidget(load_button)
        
        def make_holes_bigger():
            """让孔位变得更大更明显"""
            status_label.setText("🔧 正在放大孔位...")
            
            if hasattr(panorama_widget, 'panorama_view') and panorama_widget.panorama_view.scene:
                scene = panorama_widget.panorama_view.scene
                items = scene.items()
                
                enlarged_count = 0
                for item in items:
                    # 检查是否是孔位项
                    if hasattr(item, 'setRect'):
                        # 放大孔位 - 设置为固定大小的矩形
                        big_size = 40  # 40像素的孔位，肯定能看到
                        item.setRect(-big_size/2, -big_size/2, big_size, big_size)
                        enlarged_count += 1
                    
                    # 设置明显的颜色
                    if hasattr(item, 'setPen'):
                        item.setPen(QPen(QColor(255, 0, 0), 3))  # 粗红边框
                    if hasattr(item, 'setBrush'):
                        item.setBrush(QBrush(QColor(255, 255, 0, 200)))  # 不透明黄色
                
                status_label.setText(f"✅ 已放大 {enlarged_count} 个孔位为40像素，红边黄心")
                print(f"🔧 已放大 {enlarged_count} 个孔位")
            else:
                status_label.setText("❌ 无法访问场景")
        
        big_button = QPushButton("🔍 放大孔位(40px)")
        big_button.clicked.connect(make_holes_bigger)
        control_layout.addWidget(big_button)
        
        def fit_to_window():
            """适应窗口"""
            if hasattr(panorama_widget, 'panorama_view') and panorama_widget.panorama_view.scene:
                bounds = panorama_widget.panorama_view.scene.itemsBoundingRect()
                panorama_widget.panorama_view.fitInView(bounds, Qt.KeepAspectRatio)
                
                # 更新滑块值
                transform = panorama_widget.panorama_view.transform()
                scale_factor = int(transform.m11())
                zoom_slider.setValue(max(1, min(50, scale_factor)))
                zoom_value_label.setText(f"{scale_factor:.2f}x")
                
                status_label.setText(f"✅ 已适应窗口，缩放: {scale_factor:.2f}x")
        
        fit_button = QPushButton("📐 适应窗口")
        fit_button.clicked.connect(fit_to_window)
        control_layout.addWidget(fit_button)
        
        layout.addLayout(control_layout)
        
        # 显示窗口
        window.show()
        print("🖥️ 修复窗口已显示")
        print("💡 使用步骤:")
        print("   1. 点击'加载全景图'加载数据")
        print("   2. 使用缩放滑块调整显示大小")
        print("   3. 点击'放大孔位'让孔位变得明显")
        print("   4. 点击'适应窗口'自动调整视图")
        
        # 60秒后自动关闭
        def close_window():
            print("⏰ 60秒测试时间到，自动关闭")
            window.close()
            app.quit()
        
        timer = QTimer()
        timer.timeout.connect(close_window)
        timer.setSingleShot(True)
        timer.start(60000)
        
        return app.exec()
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 全景图缩放修复工具")
    print("=" * 60)
    
    result = fix_panorama_scaling()
    
    print("\n" + "=" * 60)
    if result == 0:
        print("✅ 修复工具完成")
    else:
        print("❌ 修复工具失败")
    print("=" * 60)