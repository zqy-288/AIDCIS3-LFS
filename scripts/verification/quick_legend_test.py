#!/usr/bin/env python3
"""
快速测试修复后的图例效果
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def main():
    """快速测试"""
    try:
        from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
        from src.pages.main_detection_p1.components.color_legend_widget import CompactColorLegendWidget
        
        app = QApplication(sys.argv)
        
        window = QWidget()
        window.setWindowTitle("修复后的图例测试")
        window.resize(400, 200)
        window.setStyleSheet("background-color: #2B2B2B;")
        
        layout = QVBoxLayout(window)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 添加图例组件
        legend = CompactColorLegendWidget()
        legend.setStyleSheet("""
            CompactColorLegendWidget {
                background: rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                padding: 5px;
            }
        """)
        layout.addWidget(legend)
        
        window.show()
        
        print("✅ 修复后的图例测试启动")
        print("📋 现在应该能看到：")
        print("   • 清晰的20x20颜色方块（灰、蓝、绿）")
        print("   • 白色的文字（待检、检测中、合格）")
        print("   • 白色边框围绕颜色方块")
        
        # 3秒后自动关闭
        from PySide6.QtCore import QTimer
        timer = QTimer()
        timer.timeout.connect(app.quit)
        timer.start(3000)
        
        result = app.exec()
        print("✅ 测试完成")
        return result
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    print(f"退出代码: {exit_code}")
    sys.exit(exit_code)