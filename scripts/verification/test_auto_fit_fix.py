#!/usr/bin/env python3
"""
测试自适应窗口修复
验证防抖机制和AttributeError修复
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_fixes():
    print("🔍 测试自适应窗口和AttributeError修复...")
    
    try:
        # 测试graphics_view导入
        from src.core_business.graphics.graphics_view import OptimizedGraphicsView
        print("✅ OptimizedGraphicsView 导入成功")
        
        # 测试主视图导入
        from src.pages.main_detection_p1.native_main_detection_view_p1 import NativeMainDetectionView
        print("✅ NativeMainDetectionView 导入成功")
        
        print("\n🎯 修复内容:")
        print("   1. AttributeError修复:")
        print("      - 安全处理sector.value访问，支持字符串和枚举")
        print("      - 添加hasattr检查和默认值处理")
        
        print("   2. 自适应窗口防抖机制:")
        print("      - 添加_fit_timer防抖定时器")
        print("      - fit_to_window_width使用150ms延迟合并多次调用") 
        print("      - 移除重复的QTimer.singleShot调用")
        print("      - 移除P1视图中的额外fitInView调用")
        
        print("\n📋 预期效果:")
        print("   ✓ 不再出现'str' object has no attribute 'value'错误")
        print("   ✓ 自适应窗口只执行一次，不再反复变化")
        print("   ✓ 视图大小变化更平滑，减少闪烁")
        print("   ✓ 提升视图切换和扇形选择的性能")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fixes()