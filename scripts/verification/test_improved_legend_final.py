#!/usr/bin/env python3
"""
测试最终改进的颜色图例
显示更大、更清晰的状态图例
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def create_final_legend_demo():
    """创建最终改进的图例演示"""
    try:
        from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, 
                                     QHBoxLayout, QLabel, QPushButton, QFrame)
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QFont
        from src.pages.main_detection_p1.components.color_legend_widget import CompactColorLegendWidget
        
        app = QApplication(sys.argv)
        
        # 创建主窗口
        window = QWidget()
        window.setWindowTitle("最终改进的颜色图例")
        window.resize(900, 300)
        
        # 设置深色背景，完全模拟实际界面
        window.setStyleSheet("""
            QWidget {
                background-color: #2E3440;
                color: #ECEFF4;
            }
        """)
        
        main_layout = QVBoxLayout(window)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 20, 30, 20)
        
        # 标题
        title = QLabel("🎯 最终改进的颜色图例效果")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #88C0D0; margin-bottom: 15px;")
        main_layout.addWidget(title)
        
        # 模拟实际界面
        demo_frame = QFrame()
        demo_frame.setStyleSheet("""
            QFrame {
                background-color: #3B4252;
                border: 1px solid #4C566A;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        demo_layout = QVBoxLayout(demo_frame)
        
        # 视图模式标签
        mode_label = QLabel("视图模式:")
        mode_label.setFont(QFont("Arial", 12, QFont.Bold))
        mode_label.setStyleSheet("color: #ECEFF4; margin-bottom: 8px;")
        demo_layout.addWidget(mode_label)
        
        # 按钮和图例行
        button_row = QHBoxLayout()
        button_row.setSpacing(10)
        
        # 宏观视图按钮（选中状态）
        macro_btn = QPushButton("📊 宏观区域视图")
        macro_btn.setMinimumHeight(40)
        macro_btn.setMinimumWidth(160)
        macro_btn.setStyleSheet("""
            QPushButton {
                background-color: #5E81AC;
                border: 2px solid #81A1C1;
                border-radius: 6px;
                color: #ECEFF4;
                font-weight: bold;
                font-size: 11px;
            }
        """)
        
        # 微观视图按钮（未选中状态）
        micro_btn = QPushButton("🔍 微观孔位视图")  
        micro_btn.setMinimumHeight(40)
        micro_btn.setMinimumWidth(160)
        micro_btn.setStyleSheet("""
            QPushButton {
                background-color: #434C5E;
                border: 1px solid #4C566A;
                border-radius: 6px;
                color: #D8DEE9;
                font-weight: bold;
                font-size: 11px;
            }
        """)
        
        # 最终改进的图例
        legend_widget = CompactColorLegendWidget()
        legend_widget.setStyleSheet("""
            CompactColorLegendWidget {
                background: rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                padding: 2px;
            }
        """)
        
        button_row.addWidget(macro_btn)
        button_row.addWidget(micro_btn)
        button_row.addSpacing(15)
        button_row.addWidget(legend_widget)
        button_row.addStretch()
        
        demo_layout.addLayout(button_row)
        main_layout.addWidget(demo_frame)
        
        # 改进总结
        summary_label = QLabel("""
✅ 最终改进内容：

🔲 颜色方块：20x20 像素，白色边框，圆角设计
📝 文字显示：完整状态名称（"待检"、"检测中"、"合格"）
🎨 字体样式：10pt 加粗，纯白色，清晰易读
📏 布局优化：更大间距，半透明深色背景
🏷️ 标题标识：清晰的"状态:"标签提供上下文

🎯 显示效果：
⬜ 待检   🔵 检测中   🟢 合格

💡 解决的问题：
• 颜色方块从极小变为清晰可见
• 文字从单字缩写变为完整描述
• 对比度大幅提升，深色背景下清晰可读
• 整体视觉层次更加分明
        """)
        
        summary_label.setStyleSheet("""
            QLabel {
                background-color: #2E3440;
                border: 1px solid #4C566A;
                border-radius: 8px;
                padding: 20px;
                line-height: 1.5;
                color: #ECEFF4;
            }
        """)
        summary_label.setWordWrap(True)
        main_layout.addWidget(summary_label)
        
        window.show()
        
        print("🎯 最终改进的图例演示已启动")
        print("\n📊 主要改进：")
        print("   ✅ 颜色方块：20x20px，白色边框")
        print("   ✅ 完整文字：显示完整状态名称")
        print("   ✅ 字体优化：10pt 加粗白色文字")
        print("   ✅ 布局改进：更大间距和背景")
        print("   ✅ 视觉层次：半透明背景分离")
        print("\n💡 现在应该非常清晰易读了！")
        
        # 5秒后自动关闭
        from PySide6.QtCore import QTimer
        timer = QTimer()
        timer.timeout.connect(app.quit)
        timer.start(8000)
        
        return app.exec()
        
    except Exception as e:
        print(f"❌ 创建演示失败: {e}")
        return 1

def main():
    """主函数"""
    print("=" * 70)
    print("🎯 最终改进的颜色图例测试")
    print("=" * 70)
    
    print("\n🚀 关键改进点：")
    print("• 颜色方块：20x20像素（原来几乎看不见）")
    print("• 文字显示：完整状态名称（原来只有单字）")
    print("• 字体大小：10pt加粗（原来7pt细体）")
    print("• 边框设计：白色边框增强对比度")
    print("• 背景优化：半透明深色背景分离")
    
    try:
        result = create_final_legend_demo()
        if result == 0:
            print("\n✅ 演示完成 - 图例现在应该清晰易读了！")
        return result
        
    except KeyboardInterrupt:
        print("\n⚠️ 演示被中断")
        return 0
    except Exception as e:
        print(f"\n❌ 演示失败: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())