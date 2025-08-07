#!/usr/bin/env python3
"""
主程序启动诊断测试
快速检测主程序启动过程中的问题
"""

import sys
import os
import traceback
from pathlib import Path

def test_basic_imports():
    """测试基础导入"""
    print("🔍 测试基础导入...")
    
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox
        from PySide6.QtCore import Qt
        print("✅ PySide6 导入成功")
        return True
    except Exception as e:
        print(f"❌ PySide6 导入失败: {e}")
        return False

def test_main_window_import():
    """测试主窗口导入"""
    print("🔍 测试主窗口导入...")
    
    try:
        # 添加路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        src_dir = os.path.join(current_dir, 'src')
        sys.path.insert(0, current_dir)
        sys.path.insert(0, src_dir)
        
        from src.main_window import MainWindow
        print("✅ MainWindow 导入成功")
        return True
    except Exception as e:
        print(f"❌ MainWindow 导入失败: {e}")
        traceback.print_exc()
        return False

def test_quick_startup():
    """测试快速启动"""
    print("🔍 测试快速启动...")
    
    try:
        from PySide6.QtWidgets import QApplication
        
        # 创建应用
        app = QApplication([])
        print("✅ QApplication 创建成功")
        
        # 尝试创建主窗口
        from src.main_window import MainWindow
        window = MainWindow()
        print("✅ MainWindow 实例创建成功")
        
        # 不显示窗口，直接退出
        print("✅ 启动测试完成，准备退出")
        return True
        
    except Exception as e:
        print(f"❌ 快速启动失败: {e}")
        traceback.print_exc()
        return False

def test_pages_import():
    """测试页面导入"""
    print("🔍 测试页面组件导入...")
    
    try:
        from src.pages.main_detection_p1.native_main_detection_view_p1 import NativeMainDetectionView
        print("✅ 主检测页面导入成功")
        
        from src.pages.main_detection_p1.components.graphics.complete_panorama_widget import CompletePanoramaWidget
        print("✅ 全景图组件导入成功")
        
        return True
    except Exception as e:
        print(f"❌ 页面组件导入失败: {e}")
        traceback.print_exc()
        return False

def main():
    """主诊断函数"""
    print("🚀 主程序启动诊断开始")
    print("=" * 50)
    
    tests = [
        ("基础导入测试", test_basic_imports),
        ("主窗口导入测试", test_main_window_import),  
        ("页面组件导入测试", test_pages_import),
        ("快速启动测试", test_quick_startup),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 运行: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} 执行异常: {e}")
            results.append((test_name, False))
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 启动诊断总结:")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
    
    if passed == total:
        print(f"\n🎉 所有 {total} 项测试通过!")
        print("✅ 主程序应该能正常启动")
        print("💡 可能问题: 主程序运行后没有保持窗口显示")
    else:
        failed = total - passed
        print(f"\n⚠️ {failed}/{total} 项测试失败")
        print("❌ 主程序启动存在问题，需要修复")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    print(f"\n🔚 诊断完成，退出码: {0 if success else 1}")
    sys.exit(0 if success else 1)