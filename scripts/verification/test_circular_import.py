#!/usr/bin/env python3
"""
循环导入测试工具
测试关键模块是否可以正常导入而不产生循环依赖
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent / 'src'
sys.path.insert(0, str(project_root))

def test_import(module_name, description):
    """测试单个模块导入"""
    try:
        __import__(module_name)
        print(f"✅ {description}: 导入成功")
        return True
    except ImportError as e:
        if "circular import" in str(e).lower() or "partially initialized" in str(e).lower():
            print(f"❌ {description}: 循环导入错误 - {e}")
            return False
        else:
            print(f"⚠️ {description}: 其他导入错误 - {e}")
            return False
    except Exception as e:
        print(f"❌ {description}: 意外错误 - {e}")
        return False

def main():
    """主测试函数"""
    print("🔍 循环导入测试开始")
    print("=" * 50)
    
    # 定义要测试的模块
    test_modules = [
        ("pages.main_detection_p1.components.graphics.sector_highlight_item", "扇形高亮组件"),
        ("pages.main_detection_p1.components.graphics.complete_panorama_widget", "全景图组件"),
        ("pages.main_detection_p1.components.graphics.dynamic_sector_view", "动态扇形视图"),
        ("modules.panorama_view", "全景图模块"),
        ("modules.panorama_view.components.sector_handler", "扇形处理器"),
        ("modules.panorama_view.components.panorama_widget", "全景图组件"),
    ]
    
    results = []
    for module_name, description in test_modules:
        success = test_import(module_name, description)
        results.append((description, success))
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 循环导入测试总结:")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for description, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {description}")
    
    if passed == total:
        print(f"\n🎉 所有 {total} 个模块导入测试通过!")
        print("✅ 没有循环导入问题")
    else:
        failed = total - passed
        print(f"\n⚠️ {failed}/{total} 个模块导入失败")
        print("❌ 存在循环导入或其他导入问题")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)