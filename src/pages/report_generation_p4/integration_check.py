#!/usr/bin/env python3
"""
P4报告生成模块集成检查
验证模块可以被正确导入和使用
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

def check_main_window_integration():
    """检查与主窗口的集成"""
    print("🔗 检查主窗口集成...")
    
    try:
        # 模拟主窗口导入P4页面
        from src.pages.report_generation_p4.report_generation_page import ReportGenerationPage
        
        print("✅ 主窗口可以成功导入P4页面")
        
        # 检查关键集成接口
        page = ReportGenerationPage()
        
        # 检查导航方法
        assert hasattr(page, 'load_data_for_workpiece'), "缺少导航接口方法"
        print("✅ 导航接口方法存在")
        
        # 检查状态信号
        assert hasattr(page, 'status_updated'), "缺少状态更新信号"
        print("✅ 状态更新信号存在")
        
        # 测试导航方法调用
        page.load_data_for_workpiece("CAP1000")
        print("✅ 导航方法调用成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 主窗口集成失败: {e}")
        return False

def check_module_structure():
    """检查模块结构完整性"""
    print("📦 检查模块结构...")
    
    try:
        from src.pages.report_generation_p4 import ReportGenerationPage
        print("✅ 可以通过包路径导入主页面")
        
        # 检查是否可以通过components导入组件
        from src.pages.report_generation_p4.components import ReportConfigPanel
        print("✅ 可以导入配置面板组件")
        
        from src.pages.report_generation_p4.widgets import DataPreviewWidget
        print("✅ 可以导入数据预览小部件")
        
        return True
        
    except Exception as e:
        print(f"❌ 模块结构检查失败: {e}")
        return False

def check_functionality():
    """检查基本功能"""
    print("⚙️ 检查基本功能...")
    
    try:
        from src.pages.report_generation_p4.report_generation_page import ReportGenerationPage
        
        # 创建页面实例
        page = ReportGenerationPage()
        
        # 检查初始状态
        assert page.current_workpiece_id is None or page.current_workpiece_id == "CAP1000"
        print("✅ 初始状态正确")
        
        # 检查配置创建
        config = page._create_report_configuration()
        assert config is not None
        print("✅ 可以创建报告配置")
        
        # 检查UI组件
        assert hasattr(page, 'workpiece_combo')
        assert hasattr(page, 'generate_btn')
        print("✅ UI组件存在")
        
        return True
        
    except Exception as e:
        print(f"❌ 功能检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主检查函数"""
    print("🚀 P4报告生成模块集成检查")
    print("=" * 50)
    
    checks = [
        ("主窗口集成", check_main_window_integration),
        ("模块结构", check_module_structure), 
        ("基本功能", check_functionality)
    ]
    
    passed = 0
    total = len(checks)
    
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}")
        print("-" * 30)
        
        if check_func():
            passed += 1
            print(f"✅ {check_name} 通过")
        else:
            print(f"❌ {check_name} 失败")
    
    print("\n" + "=" * 50)
    print("🎯 集成检查结果")
    print(f"✅ 通过: {passed}/{total}")
    print(f"📊 成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 P4模块集成检查全部通过！")
        print("✨ 模块已准备好集成到主应用程序中")
        return True
    else:
        print("⚠️ 部分检查失败，建议修复后再集成")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)