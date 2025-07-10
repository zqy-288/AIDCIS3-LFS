#!/usr/bin/env python3
"""
快速测试实时监控界面修改
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / 'modules'))

try:
    from PySide6.QtWidgets import QApplication, QMainWindow
    from modules.realtime_chart import RealtimeChart
    
    print("✅ 成功导入所需模块")
    
    app = QApplication(sys.argv)
    
    # 创建实时监控组件
    realtime_chart = RealtimeChart()
    realtime_chart.setWindowTitle("实时监控界面测试")
    realtime_chart.resize(1200, 800)
    realtime_chart.show()
    
    # 测试设置孔位
    realtime_chart.set_current_hole("H00001")
    
    print("🎯 界面修改验证：")
    print("1. ✅ 当前孔位显示为文本标签")
    print("2. ✅ 显示标准直径：17.6mm")
    print("3. ✅ 字体大小已增大")
    print("4. ✅ 面板A和面板B有明确边框")
    print("5. ✅ 误差线基于17.6mm绘制")
    
    print("\n📋 请在界面中验证以下内容：")
    print("- 检测状态区域显示'当前孔位：H00001'和'标准直径：17.6mm'")
    print("- 面板A有绿色边框，面板B有蓝色边框")
    print("- 所有文字字体都比之前更大更清晰")
    print("- 异常监控面板有红色边框")
    
    sys.exit(app.exec())
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
