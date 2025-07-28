#!/usr/bin/env python3
"""
添加全景图旋转调试代码
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core_business.graphics.rotation_config import get_rotation_manager


def add_debug_logging():
    """在关键位置添加调试日志"""
    print("🔧 添加全景图旋转调试代码")
    print("=" * 40)
    
    # 启用全局调试
    manager = get_rotation_manager()
    manager.update_config(debug_enabled=True)
    print("✅ 已启用全局旋转调试")
    
    print("\n📝 建议在以下位置添加调试代码：")
    
    print("\n1. 在 CompletePanoramaWidget.load_complete_view() 中：")
    print("   - 调用 apply_sidebar_panorama_scale 后")
    print("   - 检查 self.panorama_view.transform()")
    
    print("\n2. 在 scale_manager.py 的 apply_scale_safely() 中：")
    print("   - 已经有详细的调试日志")
    
    print("\n3. 检查是否有其他代码在后续覆盖了变换")
    
    print("\n💡 临时调试方案：")
    print("   在 dynamic_sector_view.py 的 load_complete_view 成功后添加：")
    print("""
    # 调试：检查变换是否正确应用
    QTimer.singleShot(100, lambda: self._debug_panorama_transform())
    
    def _debug_panorama_transform(self):
        transform = self.panorama_view.transform()
        print(f"🔍 [全景图变换检查] m11={transform.m11():.3f}, m12={transform.m12():.3f}")
        print(f"🔍 [全景图变换检查] m21={transform.m21():.3f}, m22={transform.m22():.3f}")
        if abs(transform.m12()) > 0.01:
            print("✅ [全景图变换检查] 检测到旋转")
        else:
            print("❌ [全景图变换检查] 未检测到旋转")
    """)


if __name__ == "__main__":
    add_debug_logging()
    
    print("\n🎯 下一步操作：")
    print("   1. 重新加载数据")
    print("   2. 观察控制台的旋转调试输出")
    print("   3. 特别注意 apply_scale_safely 的输出")