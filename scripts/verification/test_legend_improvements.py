#!/usr/bin/env python3
"""
测试图例改进效果对比
展示改进前后的颜色图例显示效果
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def create_improved_legend_demo():
    """创建改进后的图例演示"""
    try:
        from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, 
                                     QHBoxLayout, QLabel, QPushButton, QFrame)
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QFont
        from src.pages.main_detection_p1.components.color_legend_widget import CompactColorLegendWidget
        
        app = QApplication(sys.argv)
        
        # 创建主窗口
        window = QWidget()
        window.setWindowTitle("颜色图例改进效果对比")
        window.resize(800, 400)
        
        # 设置深色背景，模拟实际界面
        window.setStyleSheet("""
            QWidget {
                background-color: #2B2B2B;
                color: #E0E0E0;
            }
        """)
        
        main_layout = QVBoxLayout(window)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title = QLabel("颜色图例改进效果对比")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("margin-bottom: 20px;")
        main_layout.addWidget(title)
        
        # 模拟视图模式按钮区域
        demo_frame = QFrame()
        demo_frame.setStyleSheet("""
            QFrame {
                background-color: #3A3A3A;
                border: 1px solid #555555;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        demo_layout = QVBoxLayout(demo_frame)
        
        # 视图模式标签
        mode_label = QLabel("视图模式:")
        mode_label.setFont(QFont("Arial", 11, QFont.Bold))
        demo_layout.addWidget(mode_label)
        
        # 按钮行
        button_row = QHBoxLayout()
        
        # 模拟视图模式按钮
        macro_btn = QPushButton("📊 宏观区域视图")
        macro_btn.setMinimumHeight(35)
        macro_btn.setMinimumWidth(140)
        macro_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A90E2;
                border: none;
                border-radius: 4px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5BA0F2;
            }
        """)
        
        micro_btn = QPushButton("🔍 微观孔位视图")  
        micro_btn.setMinimumHeight(35)
        micro_btn.setMinimumWidth(140)
        micro_btn.setStyleSheet("""
            QPushButton {
                background-color: #666666;
                border: none;
                border-radius: 4px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #777777;
            }
        """)
        
        # 改进后的图例
        legend_widget = CompactColorLegendWidget()
        legend_widget.setStyleSheet("""
            CompactColorLegendWidget {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 4px;
                margin: 2px;
            }
        """)
        
        button_row.addWidget(macro_btn)
        button_row.addWidget(micro_btn)
        button_row.addSpacing(8)
        button_row.addWidget(legend_widget)
        button_row.addStretch()
        
        demo_layout.addLayout(button_row)
        main_layout.addWidget(demo_frame)
        
        # 改进说明
        improvements_label = QLabel("""
🎯 改进内容：
• 颜色方块尺寸从 12x12 增大到 16x16 像素
• 添加白色边框增强对比度，在深色背景下更清晰
• 文字大小从 7pt 增加到 9pt 并加粗
• 文字颜色使用浅色 (#E0E0E0) 适配深色主题
• 增加图例标题 "图例:" 提供上下文
• 优化间距和边距，视觉层次更清晰
• 添加半透明背景和边框，与界面风格统一

📊 显示内容：
🔳 待检 - 灰色 (#C8C8C8)
🔵 检测中 - 蓝色 (#6496FF)  
🟢 合格 - 绿色 (#32C832)

💡 使用项目中已定义的6种孔位状态颜色，显示最重要的前3种
        """)
        
        improvements_label.setStyleSheet("""
            QLabel {
                background-color: #1E1E1E;
                border: 1px solid #444444;
                border-radius: 6px;
                padding: 15px;
                line-height: 1.4;
            }
        """)
        improvements_label.setWordWrap(True)
        main_layout.addWidget(improvements_label)
        
        window.show()
        
        print("✅ 改进后的图例演示窗口已启动")
        print("📋 请观察以下改进效果：")
        print("   1. 颜色方块是否足够大和清晰")
        print("   2. 文字是否在深色背景下清晰可读")
        print("   3. 整体布局是否协调美观")
        print("   4. 与按钮的间距是否合适")
        
        return app.exec()
        
    except Exception as e:
        print(f"❌ 创建演示失败: {e}")
        return 1

def main():
    """主函数"""
    print("=" * 60)
    print("颜色图例改进效果演示")
    print("=" * 60)
    
    print("\n🎨 主要改进：")
    print("• 更大的颜色方块 (16x16px)")
    print("• 白色边框增强对比度") 
    print("• 更大更粗的文字 (9pt Bold)")
    print("• 适配深色主题的文字颜色")
    print("• 优化的间距和布局")
    print("• 半透明背景提升视觉层次")
    
    print("\n🚀 启动演示...")
    
    try:
        result = create_improved_legend_demo()
        if result == 0:
            print("✅ 演示完成")
        else:
            print("⚠️ 演示结束")
        return result
        
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断演示")
        return 0
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())