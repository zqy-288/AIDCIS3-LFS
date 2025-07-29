#!/usr/bin/env python3
"""
简单的导入测试
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("🚀 开始导入测试...")

try:
    print("1. 测试导入可滚动文本标签...")
    from src.pages.history_analytics_p3.components.scrollable_text_label import ScrollableTextLabel
    print("   ✅ 可滚动文本标签导入成功")
    
    print("2. 测试导入侧边栏面板...")
    from src.pages.history_analytics_p3.components.sidebar_panel import SidebarPanel
    print("   ✅ 侧边栏面板导入成功")
    
    print("3. 测试导入数据表格面板...")
    from src.pages.history_analytics_p3.components.data_table_panel import DataTablePanel
    print("   ✅ 数据表格面板导入成功")
    
    print("4. 测试导入可视化面板...")
    from src.pages.history_analytics_p3.components.visualization_panel import VisualizationPanel
    print("   ✅ 可视化面板导入成功")
    
    print("5. 测试导入历史数据页面...")
    from src.pages.history_analytics_p3.history_analytics_page import HistoryAnalyticsPage
    print("   ✅ 历史数据页面导入成功")
    
    print("🎉 所有导入测试通过！")
    
except Exception as e:
    print(f"❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()
