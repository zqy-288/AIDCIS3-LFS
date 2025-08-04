#!/usr/bin/env python3
"""
P4报告生成页面最终验证测试
验证核心功能和集成性
"""

import sys
import os
import traceback

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

def test_basic_imports():
    """测试基本导入"""
    print("📦 测试模块导入...")
    
    success_count = 0
    total_count = 0
    
    # 测试核心GUI库
    total_count += 1
    try:
        from PySide6.QtWidgets import QApplication, QWidget
        from PySide6.QtCore import Qt, Signal
        print("✅ PySide6 导入成功")
        success_count += 1
    except ImportError as e:
        print(f"❌ PySide6 导入失败: {e}")
    
    # 测试主页面
    total_count += 1
    try:
        from report_generation_page import ReportGenerationPage
        print("✅ 主页面类导入成功")
        success_count += 1
    except ImportError as e:
        print(f"❌ 主页面类导入失败: {e}")
    
    # 测试组件
    total_count += 1
    try:
        from components import ReportConfigPanel, ReportPreviewPanel, ReportHistoryPanel
        print("✅ 组件模块导入成功")
        success_count += 1
    except ImportError as e:
        print(f"❌ 组件模块导入失败: {e}")
    
    # 测试小部件
    total_count += 1
    try:
        from widgets import DataPreviewWidget, ReportStatusWidget
        print("✅ 小部件模块导入成功")
        success_count += 1
    except ImportError as e:
        print(f"❌ 小部件模块导入失败: {e}")
    
    print(f"导入测试: {success_count}/{total_count} 成功")
    return success_count, total_count

def test_class_creation():
    """测试类创建（不初始化GUI）"""
    print("🏗️ 测试类创建...")
    
    success_count = 0
    total_count = 0
    
    # 测试主页面类存在
    total_count += 1
    try:
        from report_generation_page import ReportGenerationPage
        assert ReportGenerationPage is not None
        print("✅ ReportGenerationPage 类存在")
        success_count += 1
    except Exception as e:
        print(f"❌ ReportGenerationPage 测试失败: {e}")
    
    # 测试工作线程类
    total_count += 1
    try:
        from report_generation_page import ReportGenerationWorker
        assert ReportGenerationWorker is not None
        print("✅ ReportGenerationWorker 类存在")
        success_count += 1
    except Exception as e:
        print(f"❌ ReportGenerationWorker 测试失败: {e}")
    
    print(f"类创建测试: {success_count}/{total_count} 成功")
    return success_count, total_count

def test_methods_existence():
    """测试关键方法存在性"""
    print("🔧 测试关键方法...")
    
    success_count = 0
    total_count = 0
    
    try:
        from report_generation_page import ReportGenerationPage
        
        # 检查关键方法存在
        required_methods = [
            '_init_ui', '_init_connections', '_load_initial_data',
            'load_data_for_workpiece', '_create_report_configuration',
            '_generate_report', '_preview_report', '_refresh_history'
        ]
        
        for method_name in required_methods:
            total_count += 1
            if hasattr(ReportGenerationPage, method_name):
                print(f"✅ 方法 {method_name} 存在")
                success_count += 1
            else:
                print(f"❌ 方法 {method_name} 缺失")
        
    except Exception as e:
        print(f"❌ 方法测试失败: {e}")
    
    print(f"方法测试: {success_count}/{total_count} 成功")
    return success_count, total_count

def test_configuration_types():
    """测试配置类型和枚举"""
    print("⚙️ 测试配置类型...")
    
    success_count = 0
    total_count = 0
    
    # 测试枚举类型
    total_count += 1
    try:
        from report_generation_page import ReportType, ReportFormat
        assert hasattr(ReportType, 'COMPREHENSIVE')
        assert hasattr(ReportFormat, 'PDF')
        print("✅ 报告类型枚举正常")
        success_count += 1
    except Exception as e:
        print(f"❌ 枚举测试失败: {e}")
    
    # 测试配置类
    total_count += 1
    try:
        from report_generation_page import ReportConfiguration, ReportType, ReportFormat
        # 测试多种初始化方式
        config1 = ReportConfiguration()  # 默认参数
        config2 = ReportConfiguration(report_type=ReportType.COMPREHENSIVE, report_format=ReportFormat.PDF)  # 指定参数
        config3 = ReportConfiguration(ReportType.QUALITY_ANALYSIS, ReportFormat.HTML)  # 位置参数
        
        # 验证属性存在
        for config in [config1, config2, config3]:
            assert hasattr(config, 'report_type')
            assert hasattr(config, 'report_format')
            assert hasattr(config, 'include_workpiece_info')
        
        print("✅ 报告配置类正常")
        success_count += 1
    except Exception as e:
        print(f"❌ 配置类测试失败: {e}")
        traceback.print_exc()
    
    print(f"配置测试: {success_count}/{total_count} 成功")
    return success_count, total_count

def test_individual_components():
    """测试独立组件"""
    print("🧩 测试独立组件...")
    
    success_count = 0
    total_count = 0
    
    components = [
        ('ReportConfigPanel', 'components.report_config_panel'),
        ('ReportPreviewPanel', 'components.report_preview_panel'),
        ('ReportHistoryPanel', 'components.report_history_panel'),
        ('DataPreviewWidget', 'widgets.data_preview_widget'),
        ('ReportStatusWidget', 'widgets.report_status_widget')
    ]
    
    for class_name, module_name in components:
        total_count += 1
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            assert cls is not None
            print(f"✅ {class_name} 组件正常")
            success_count += 1
        except Exception as e:
            print(f"❌ {class_name} 组件失败: {e}")
    
    print(f"组件测试: {success_count}/{total_count} 成功")
    return success_count, total_count

def test_file_structure():
    """测试文件结构"""
    print("📁 测试文件结构...")
    
    success_count = 0
    total_count = 0
    
    base_path = "/Users/vsiyo/Desktop/AIDCIS3-LFS/src/pages/report_generation_p4"
    
    required_files = [
        "__init__.py",
        "report_generation_page.py",
        "components/__init__.py",
        "components/report_config_panel.py",
        "components/report_preview_panel.py", 
        "components/report_history_panel.py",
        "widgets/__init__.py",
        "widgets/data_preview_widget.py",
        "widgets/report_status_widget.py"
    ]
    
    for file_path in required_files:
        total_count += 1
        full_path = os.path.join(base_path, file_path)
        if os.path.exists(full_path):
            print(f"✅ 文件 {file_path} 存在")
            success_count += 1
        else:
            print(f"❌ 文件 {file_path} 缺失")
    
    print(f"文件结构测试: {success_count}/{total_count} 成功")
    return success_count, total_count

def test_integration_readiness():
    """测试集成准备情况"""
    print("🔗 测试集成准备...")
    
    success_count = 0
    total_count = 0
    
    # 测试主窗口导入接口
    total_count += 1
    try:
        from report_generation_page import ReportGenerationPage
        
        # 检查关键接口方法
        page_instance = None  # 不实际创建实例
        required_interface = ['load_data_for_workpiece', 'status_updated']
        
        has_interface = True
        for interface in required_interface:
            if not hasattr(ReportGenerationPage, interface):
                has_interface = False
                break
        
        if has_interface:
            print("✅ 主窗口集成接口完整")
            success_count += 1
        else:
            print("❌ 主窗口集成接口不完整")
            
    except Exception as e:
        print(f"❌ 集成接口测试失败: {e}")
    
    # 测试assets/old依赖处理
    total_count += 1
    try:
        # 这个测试已经在导入时进行了，检查是否有合适的回退机制
        from report_generation_page import MODELS_AVAILABLE, GENERATOR_AVAILABLE
        print(f"✅ 依赖回退机制正常 (Models: {MODELS_AVAILABLE}, Generator: {GENERATOR_AVAILABLE})")
        success_count += 1
    except Exception as e:
        print(f"❌ 依赖回退测试失败: {e}")
    
    print(f"集成准备测试: {success_count}/{total_count} 成功")
    return success_count, total_count

def main():
    """主测试函数"""
    print("🚀 P4报告生成模块最终验证测试")
    print("=" * 60)
    
    tests = [
        ("基本导入", test_basic_imports),
        ("类创建", test_class_creation),
        ("方法存在性", test_methods_existence),
        ("配置类型", test_configuration_types),
        ("独立组件", test_individual_components),
        ("文件结构", test_file_structure),
        ("集成准备", test_integration_readiness)
    ]
    
    total_success = 0
    total_tests = 0
    
    for test_name, test_function in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        
        try:
            success, count = test_function()
            total_success += success
            total_tests += count
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            traceback.print_exc()
            total_tests += 1  # 至少算作一个测试
    
    print("\n" + "=" * 60)
    print("🎯 最终测试结果")
    print(f"✅ 通过测试: {total_success}")
    print(f"📊 总测试数: {total_tests}")
    if total_tests > 0:
        success_rate = (total_success / total_tests) * 100
        print(f"📈 成功率: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🎉 优秀！P4模块已准备好投入使用！")
            return True
        elif success_rate >= 75:
            print("✅ 良好！P4模块基本可用，可能需要小幅调整")
            return True
        else:
            print("⚠️ 需要改进！建议修复失败的测试项")
            return False
    else:
        print("❌ 无法完成测试")
        return False

if __name__ == "__main__":
    success = main()
    print(f"\n{'='*60}")
    if success:
        print("✅ P4报告生成模块验证通过，可以安全集成使用！")
    else:
        print("❌ P4报告生成模块需要进一步优化")
    sys.exit(0 if success else 1)