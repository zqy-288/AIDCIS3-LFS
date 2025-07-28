#!/usr/bin/env python3
"""
简单的孔位显示测试
用最基本的方法验证孔位是否能显示
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def simple_hole_test():
    """简单孔位显示测试"""
    print("🔍 开始简单孔位显示测试...")
    
    try:
        from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                                      QWidget, QGraphicsView, QGraphicsScene, 
                                      QGraphicsEllipseItem, QLabel, QPushButton)
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
        
        # 分析孔位分布
        holes = list(hole_collection.holes.values())
        min_x = min(hole.center_x for hole in holes)
        max_x = max(hole.center_x for hole in holes)
        min_y = min(hole.center_y for hole in holes)
        max_y = max(hole.center_y for hole in holes)
        
        print(f"📊 孔位分布:")
        print(f"   X范围: {min_x:.1f} 到 {max_x:.1f} (跨度: {max_x-min_x:.1f})")
        print(f"   Y范围: {min_y:.1f} 到 {max_y:.1f} (跨度: {max_y-min_y:.1f})")
        
        # 创建主窗口
        window = QMainWindow()
        window.setWindowTitle(f"🔍 简单孔位测试 - {len(hole_collection.holes)} 个孔位")
        window.resize(1200, 900)
        
        central_widget = QWidget()
        window.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 信息标签
        info_label = QLabel(f"""
📊 孔位数据分析:
• 总孔位数: {len(hole_collection.holes)}
• X坐标范围: {min_x:.1f} ~ {max_x:.1f} (跨度: {max_x-min_x:.1f})
• Y坐标范围: {min_y:.1f} ~ {max_y:.1f} (跨度: {max_y-min_y:.1f})
• 第一个孔位: ({holes[0].center_x:.1f}, {holes[0].center_y:.1f})
        """)
        info_label.setStyleSheet("font-size: 12px; padding: 10px; background-color: #f0f0f0;")
        layout.addWidget(info_label)
        
        # 创建图形视图
        view = QGraphicsView()
        scene = QGraphicsScene()
        view.setScene(scene)
        view.setMinimumSize(800, 600)
        layout.addWidget(view)
        
        # 测试按钮
        def load_sample_holes():
            """加载少量样本孔位"""
            print("🔍 加载前100个孔位作为样本...")
            scene.clear()
            
            sample_holes = list(hole_collection.holes.items())[:100]
            
            for hole_id, hole in sample_holes:
                x, y = hole.center_x, hole.center_y
                radius = 10  # 固定半径10像素
                
                # 创建圆形
                ellipse = QGraphicsEllipseItem(x - radius, y - radius, radius * 2, radius * 2)
                ellipse.setPen(QPen(QColor(255, 0, 0), 2))  # 红色边框
                ellipse.setBrush(QBrush(QColor(255, 255, 0, 100)))  # 半透明黄色
                
                scene.addItem(ellipse)
            
            # 适应视图
            bounds = scene.itemsBoundingRect()
            view.fitInView(bounds, Qt.KeepAspectRatio)
            
            print(f"✅ 已加载 {len(sample_holes)} 个样本孔位")
            print(f"📐 场景边界: ({bounds.x():.1f}, {bounds.y():.1f}) {bounds.width():.1f}×{bounds.height():.1f}")
            
            # 更新信息
            info_label.setText(f"""
✅ 样本加载完成:
• 显示孔位数: {len(sample_holes)}
• 场景边界: ({bounds.x():.1f}, {bounds.y():.1f}) {bounds.width():.1f}×{bounds.height():.1f}
• 如果能看到红边黄心的圆形，说明基本显示正常
            """)
        
        def load_all_holes():
            """加载所有孔位"""
            print("🔍 加载所有25270个孔位...")
            scene.clear()
            
            count = 0
            for hole_id, hole in hole_collection.holes.items():
                x, y = hole.center_x, hole.center_y
                radius = 3  # 小半径3像素
                
                # 创建圆形
                ellipse = QGraphicsEllipseItem(x - radius, y - radius, radius * 2, radius * 2)
                ellipse.setPen(QPen(QColor(0, 255, 0), 1))  # 绿色边框
                ellipse.setBrush(QBrush(QColor(0, 255, 255, 80)))  # 半透明青色
                
                scene.addItem(ellipse)
                count += 1
                
                # 显示进度
                if count % 5000 == 0:
                    print(f"已加载 {count} 个孔位...")
            
            # 适应视图
            bounds = scene.itemsBoundingRect()
            view.fitInView(bounds, Qt.KeepAspectRatio)
            
            print(f"✅ 已加载所有 {count} 个孔位")
            
            # 更新信息
            info_label.setText(f"""
✅ 全部孔位加载完成:
• 显示孔位数: {count}
• 场景边界: ({bounds.x():.1f}, {bounds.y():.1f}) {bounds.width():.1f}×{bounds.height():.1f}
• 如果能看到密密麻麻的绿色小圆点，说明全景显示正常
            """)
        
        def create_coordinate_test():
            """创建坐标系测试"""
            print("🔍 创建坐标系测试图案...")
            scene.clear()
            
            # 坐标轴
            from PySide6.QtWidgets import QGraphicsLineItem
            
            # X轴
            x_axis = QGraphicsLineItem(-3000, 0, 3000, 0)
            x_axis.setPen(QPen(QColor(255, 0, 0), 3))
            scene.addItem(x_axis)
            
            # Y轴  
            y_axis = QGraphicsLineItem(0, -3000, 0, 3000)
            y_axis.setPen(QPen(QColor(0, 255, 0), 3))
            scene.addItem(y_axis)
            
            # 原点
            origin = QGraphicsEllipseItem(-20, -20, 40, 40)
            origin.setPen(QPen(QColor(0, 0, 255), 3))
            origin.setBrush(QBrush(QColor(0, 0, 255)))
            scene.addItem(origin)
            
            # 刻度标记
            for i in range(-2000, 2001, 500):
                if i != 0:
                    # X轴刻度
                    mark = QGraphicsLineItem(i, -50, i, 50)
                    mark.setPen(QPen(QColor(255, 0, 0), 1))
                    scene.addItem(mark)
                    
                    # Y轴刻度
                    mark = QGraphicsLineItem(-50, i, 50, i)
                    mark.setPen(QPen(QColor(0, 255, 0), 1))
                    scene.addItem(mark)
            
            # 适应视图
            view.fitInView(scene.itemsBoundingRect(), Qt.KeepAspectRatio)
            
            print("✅ 坐标系测试图案创建完成")
            info_label.setText("""
✅ 坐标系测试:
• 红线是X轴，绿线是Y轴，蓝点是原点
• 如果能看到坐标轴，说明基本图形显示正常
            """)
        
        # 按钮
        button_layout = QVBoxLayout()
        
        coord_button = QPushButton("🎯 坐标系测试")
        coord_button.clicked.connect(create_coordinate_test)
        button_layout.addWidget(coord_button)
        
        sample_button = QPushButton("🔍 加载100个样本孔位")
        sample_button.clicked.connect(load_sample_holes)
        button_layout.addWidget(sample_button)
        
        all_button = QPushButton("🌐 加载所有25270个孔位")
        all_button.clicked.connect(load_all_holes)
        button_layout.addWidget(all_button)
        
        layout.addLayout(button_layout)
        
        # 显示窗口
        window.show()
        print("🖥️ 测试窗口已显示")
        print("💡 请按顺序测试:")
        print("   1. 先点击'坐标系测试'确认基本图形显示正常")
        print("   2. 再点击'加载100个样本孔位'测试少量孔位显示")
        print("   3. 最后点击'加载所有孔位'测试完整显示")
        
        # 30秒后自动关闭
        def close_window():
            print("⏰ 30秒测试时间到，自动关闭")
            window.close()
            app.quit()
        
        timer = QTimer()
        timer.timeout.connect(close_window)
        timer.setSingleShot(True)
        timer.start(30000)
        
        return app.exec()
        
    except Exception as e:
        print(f"❌ 简单测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🔍 简单孔位显示测试")
    print("=" * 60)
    
    result = simple_hole_test()
    
    print("\n" + "=" * 60)
    if result == 0:
        print("✅ 简单测试完成")
    else:
        print("❌ 简单测试失败")
    print("=" * 60)