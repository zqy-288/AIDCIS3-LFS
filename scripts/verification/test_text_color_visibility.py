#!/usr/bin/env python3
"""
专门测试图例文字和颜色的可见性
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def test_text_and_color_visibility():
    """测试文字和颜色的可见性"""
    try:
        from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, 
                                     QHBoxLayout, QLabel, QFrame)
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QFont, QColor, QPalette
        
        app = QApplication(sys.argv)
        
        # 创建测试窗口
        window = QWidget()
        window.setWindowTitle("文字和颜色可见性测试")
        window.resize(600, 400)
        
        # 深色背景模拟实际环境
        window.setStyleSheet("""
            QWidget {
                background-color: #2B2B2B;
            }
        """)
        
        layout = QVBoxLayout(window)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # 标题
        title = QLabel("🔍 文字和颜色可见性测试")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #FFFFFF; margin-bottom: 20px;")
        layout.addWidget(title)
        
        # 测试1：直接创建图例项
        test1_frame = QFrame()
        test1_frame.setStyleSheet("""
            QFrame {
                background-color: #333333;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 15px;
            }
        """)
        test1_layout = QVBoxLayout(test1_frame)
        
        test1_title = QLabel("测试1：手动创建的图例项")
        test1_title.setFont(QFont("Arial", 12, QFont.Bold))
        test1_title.setStyleSheet("color: #FFFFFF; margin-bottom: 10px;")
        test1_layout.addWidget(test1_title)
        
        # 手动创建图例项
        legend_row = QHBoxLayout()
        
        # 状态标题
        status_label = QLabel("状态:")
        status_label.setFont(QFont("Arial", 11, QFont.Bold))
        status_label.setStyleSheet("color: #FFFFFF !important;")
        legend_row.addWidget(status_label)
        
        # 创建三个测试项
        test_items = [
            ("#C8C8C8", "待检"),
            ("#6496FF", "检测中"), 
            ("#32C832", "合格")
        ]
        
        for color, text in test_items:
            # 颜色方块
            color_block = QLabel()
            color_block.setFixedSize(20, 20)
            color_block.setStyleSheet(f"""
                QLabel {{
                    background-color: {color};
                    border: 2px solid #FFFFFF;
                    border-radius: 3px;
                }}
            """)
            
            # 文字标签
            text_label = QLabel(text)
            text_label.setFont(QFont("Arial", 10, QFont.Bold))
            text_label.setStyleSheet("""
                QLabel {
                    color: #FFFFFF !important;
                    background: transparent !important;
                    border: none !important;
                    padding: 2px !important;
                }
            """)
            
            # 强制设置调色板
            palette = text_label.palette()
            palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
            palette.setColor(QPalette.Text, QColor(255, 255, 255))
            text_label.setPalette(palette)
            
            # 添加到布局
            item_layout = QHBoxLayout()
            item_layout.setSpacing(4)
            item_layout.addWidget(color_block)
            item_layout.addWidget(text_label)
            
            item_widget = QWidget()
            item_widget.setLayout(item_layout)
            legend_row.addWidget(item_widget)
        
        legend_row.addStretch()
        test1_layout.addLayout(legend_row)
        layout.addWidget(test1_frame)
        
        # 测试2：使用组件
        test2_frame = QFrame()
        test2_frame.setStyleSheet("""
            QFrame {
                background-color: #333333;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 15px;
            }
        """)
        test2_layout = QVBoxLayout(test2_frame)
        
        test2_title = QLabel("测试2：使用图例组件")
        test2_title.setFont(QFont("Arial", 12, QFont.Bold))
        test2_title.setStyleSheet("color: #FFFFFF; margin-bottom: 10px;")
        test2_layout.addWidget(test2_title)
        
        try:
            from src.pages.main_detection_p1.components.color_legend_widget import CompactColorLegendWidget
            legend_widget = CompactColorLegendWidget()
            legend_widget.setStyleSheet("""
                CompactColorLegendWidget {
                    background: rgba(0, 0, 0, 0.3);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 6px;
                    padding: 5px;
                }
            """)
            test2_layout.addWidget(legend_widget)
            print("✅ 成功加载图例组件")
        except Exception as e:
            error_label = QLabel(f"❌ 组件加载失败: {e}")
            error_label.setStyleSheet("color: #FF6B6B;")
            test2_layout.addWidget(error_label)
            print(f"❌ 组件加载失败: {e}")
        
        layout.addWidget(test2_frame)
        
        # 说明
        info_label = QLabel("""
📋 检查项目：
• 颜色方块是否清晰可见（灰色、蓝色、绿色）
• 文字是否为白色且清晰可读
• "状态:"标题是否可见
• 整体对比度是否足够

如果文字不可见，可能是主题或父组件覆盖了样式。
        """)
        info_label.setStyleSheet("""
            QLabel {
                background-color: #1E1E1E;
                color: #CCCCCC;
                border: 1px solid #444444;
                border-radius: 5px;
                padding: 15px;
            }
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        window.show()
        
        print("🔍 文字和颜色可见性测试已启动")
        print("📋 请检查：")
        print("   1. 颜色方块是否清晰（灰、蓝、绿）")
        print("   2. 文字是否为白色且可读")
        print("   3. 对比度是否足够")
        
        return app.exec()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return 1

def main():
    """主函数"""
    print("=" * 50)
    print("🔍 图例文字和颜色可见性测试")
    print("=" * 50)
    
    try:
        result = test_text_and_color_visibility()
        if result == 0:
            print("✅ 可见性测试完成")
        return result
        
    except KeyboardInterrupt:
        print("\n⚠️ 测试被中断")
        return 0
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())