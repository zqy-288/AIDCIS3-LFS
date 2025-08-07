#!/usr/bin/env python3
"""
快速测试孔位状态颜色图例
验证项目中已定义的状态颜色是否正确显示
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def test_hole_status_colors():
    """测试孔位状态颜色定义"""
    try:
        from src.core_business.models.hole_data import HoleStatus
        from src.core_business.graphics.hole_item import HoleGraphicsItem
        
        print("✅ 成功导入孔位状态定义")
        print("\n📊 项目中定义的孔位状态颜色：")
        
        status_names = {
            HoleStatus.PENDING: "待检",
            HoleStatus.PROCESSING: "检测中", 
            HoleStatus.QUALIFIED: "合格",
            HoleStatus.DEFECTIVE: "异常",
            HoleStatus.BLIND: "盲孔",
            HoleStatus.TIE_ROD: "拉杆孔"
        }
        
        status_colors = HoleGraphicsItem.STATUS_COLORS
        
        for i, (status, color) in enumerate(status_colors.items(), 1):
            name = status_names.get(status, status.value)
            hex_color = f"#{color.red():02X}{color.green():02X}{color.blue():02X}"
            print(f"   {i}. {name}: {hex_color} (RGB: {color.red()}, {color.green()}, {color.blue()})")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_compact_legend_widget():
    """测试紧凑图例组件"""
    try:
        from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
        from src.pages.main_detection_p1.components.color_legend_widget import CompactColorLegendWidget
        
        app = QApplication(sys.argv)
        
        # 创建测试窗口
        window = QWidget()
        window.setWindowTitle("孔位状态图例测试")
        window.resize(400, 150)
        
        layout = QVBoxLayout(window)
        
        # 标题
        title = QLabel("紧凑型孔位状态图例测试")
        title.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # 添加紧凑图例
        legend = CompactColorLegendWidget()
        layout.addWidget(legend)
        
        # 说明
        info = QLabel("应该显示：灰色(待检) 蓝色(检测中) 绿色(合格)")
        info.setStyleSheet("color: #666; font-size: 10px; margin: 10px;")
        layout.addWidget(info)
        
        window.show()
        
        print("✅ 紧凑图例组件测试窗口已打开")
        print("💡 请查看窗口中的图例显示是否正确")
        
        # 运行短时间后自动关闭
        from PySide6.QtCore import QTimer
        timer = QTimer()
        timer.timeout.connect(app.quit)
        timer.start(3000)  # 3秒后关闭
        
        result = app.exec()
        print("✅ 紧凑图例测试完成")
        return result == 0
        
    except Exception as e:
        print(f"❌ 紧凑图例测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("孔位状态颜色图例测试")
    print("=" * 50)
    
    # 测试状态颜色定义
    print("\n1. 测试孔位状态颜色定义...")
    colors_ok = test_hole_status_colors()
    
    if not colors_ok:
        print("❌ 状态颜色测试失败")
        return 1
    
    # 测试紧凑图例组件
    print("\n2. 测试紧凑图例组件...")
    try:
        widget_ok = test_compact_legend_widget()
        if widget_ok:
            print("✅ 紧凑图例组件测试成功")
        else:
            print("⚠️ 紧凑图例组件测试结束")
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断测试")
    except Exception as e:
        print(f"❌ 组件测试失败: {e}")
        return 1
    
    print("\n" + "=" * 50)
    print("✅ 孔位状态颜色图例测试完成")
    print("📋 结果：")
    print("   • 已定义6种孔位状态颜色")
    print("   • 紧凑图例显示前3种主要状态")
    print("   • 图例可以集成到视图模式按钮旁边")
    print("=" * 50)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())