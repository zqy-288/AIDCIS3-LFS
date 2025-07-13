#!/usr/bin/env python3
"""
简化版启动脚本 - 测试东重管板DXF加载和扇形进度显示
"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(src_dir / 'modules'))
sys.path.insert(0, str(src_dir / 'models'))

try:
    from PySide6.QtWidgets import QApplication
    from main_window.main_window import MainWindow
    import logging
    
    # 设置简化的日志
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 启动管孔检测系统...")
    print("📋 功能特点:")
    print("   ✅ 自动加载东重管板.dxf文件")
    print("   ✅ 扇形进度视图（中间400x400px）")
    print("   ✅ 完整孔位图（右上角280x350px）")
    print("   ✅ 可点击扇形查看详细信息")
    
    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("管孔检测系统")
    app.setApplicationVersion("1.0.0")
    
    print("🔄 正在初始化主窗口...")
    
    # 创建主窗口
    window = MainWindow()
    
    print("✅ 主窗口初始化完成")
    
    # 检查关键组件
    if hasattr(window, 'hole_collection') and window.hole_collection:
        print(f"✅ DXF数据加载成功: {len(window.hole_collection)} 个孔位")
        
        # 检查扇形分配
        if hasattr(window, 'sector_manager'):
            assignments = window.sector_manager.sector_assignments
            print(f"✅ 扇形区域分配完成: {len(assignments)} 个孔位")
    
    print("🎯 显示主窗口...")
    
    # 显示窗口
    window.show()
    window.raise_()
    window.activateWindow()
    
    print("🎉 系统启动成功！")
    print("\n💡 操作提示:")
    print("   • 中间的扇形图显示4个区域的检测进度")
    print("   • 右上角显示完整的孔位分布图")
    print("   • 点击任意扇形区域可查看详细信息")
    print("   • 系统已自动模拟部分检测进度用于演示")
    
    # 运行应用
    sys.exit(app.exec())

except KeyboardInterrupt:
    print("\n⏹️ 用户中断程序")
    sys.exit(0)
except Exception as e:
    print(f"❌ 启动失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)