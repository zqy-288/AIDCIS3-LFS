#!/usr/bin/env python3
"""
测试最终优化效果
包括：
1. 移除鼠标悬停显示点编号
2. 进一步缩小扇形区域显示
3. 大扇形显示移动到左上角
4. 模拟进度同步到多个面板
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PySide6.QtWidgets import QApplication
from main_window import MainWindow


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    print("\n=== 最终优化测试 ===")
    print("\n检查点：")
    print("1. 鼠标悬停在孔位上时，不应显示工具提示")
    print("2. 扇形区域进度显示应该更小（半径10px，字体3pt）")
    print("3. 右侧大扇形显示应该在左上角")
    print("4. 点击扇形区域时，显示内容应严格对应")
    print("5. 运行模拟进度时，应同步更新：")
    print("   - 扇形区域进度")
    print("   - 状态统计显示")
    print("   - 孔位颜色变化")
    
    print("\n操作提示：")
    print("1. 按 Ctrl+T 加载默认DXF文件")
    print("2. 点击'使用模拟进度'测试数据同步")
    print("3. 点击不同扇形区域验证显示对应关系")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()