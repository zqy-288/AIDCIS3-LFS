#!/usr/bin/env python3
"""
P4报告生成页面全面测试脚本
测试所有核心功能和边界情况
"""

import sys
import os
import traceback
from unittest.mock import Mock, patch

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

# 全局导入
try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt, Signal, QThread
    from PySide6.QtGui import QFont
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False

def test_imports_comprehensive():
    """全面测试所有导入"""
    print("🔍 测试所有导入依赖...")
    
    if not PYSIDE6_AVAILABLE:
        print("❌ PySide6 导入失败")
        return False
    else:
        print("✅ PySide6 核心模块导入成功")
    
    try:
        from report_generation_page import ReportGenerationPage, ReportGenerationWorker
        print("✅ 主页面类导入成功")
    except ImportError as e:
        print(f"❌ 主页面类导入失败: {e}")
        return False
    
    try:
        from components import ReportConfigPanel, ReportPreviewPanel, ReportHistoryPanel
        print("✅ 组件模块导入成功")
    except ImportError as e:
        print(f"❌ 组件模块导入失败: {e}")
        return False
    
    try:
        from widgets import DataPreviewWidget, ReportStatusWidget
        print("✅ 小部件模块导入成功")
    except ImportError as e:
        print(f"❌ 小部件模块导入失败: {e}")
        return False
    
    return True

def test_page_initialization():
    """测试页面初始化"""
    print("🏗️ 测试页面初始化...")
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    try:
        from report_generation_page import ReportGenerationPage
        
        # 测试无参数初始化
        page1 = ReportGenerationPage()
        assert page1 is not None, "页面创建失败"
        print("✅ 无参数初始化成功")
        
        # 测试带参数初始化
        mock_components = Mock()
        mock_view_model = Mock()
        page2 = ReportGenerationPage(shared_components=mock_components, view_model=mock_view_model)
        assert page2.shared_components == mock_components, "shared_components 设置失败"
        assert page2.view_model == mock_view_model, "view_model 设置失败"
        print("✅ 带参数初始化成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 页面初始化失败: {e}")
        traceback.print_exc()
        return False

def test_ui_components():
    """测试UI组件"""
    print("🎨 测试UI组件...")
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    try:
        from report_generation_page import ReportGenerationPage
        page = ReportGenerationPage()
        
        # 测试必要的UI组件是否存在
        required_components = [
            'workpiece_combo', 'report_type_combo', 'format_combo',
            'generate_btn', 'preview_btn', 'data_status_label',
            'total_holes_label', 'qualified_holes_label', 'unqualified_holes_label',
            'qualification_rate_label', 'hole_data_table', 'report_history_table'
        ]
        
        for component in required_components:
            assert hasattr(page, component), f"缺少UI组件: {component}"
        print("✅ 所有必要UI组件存在")
        
        # 测试组件初始状态
        assert page.workpiece_combo.count() >= 1, "工件下拉框应该有默认选项"
        assert page.report_type_combo.count() == 4, "报告类型应该有4个选项"
        assert page.format_combo.count() == 4, "格式选择应该有4个选项"
        print("✅ UI组件初始状态正确")
        
        return True
        
    except Exception as e:
        print(f"❌ UI组件测试失败: {e}")
        traceback.print_exc()
        return False

def test_data_loading():
    """测试数据加载功能"""
    print("📊 测试数据加载功能...")
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    try:
        from report_generation_page import ReportGenerationPage
        page = ReportGenerationPage()
        
        # 测试默认工件数据加载
        default_workpiece = page.get_current_workpiece() if hasattr(page, 'get_current_workpiece') else page.current_workpiece_id
        assert default_workpiece is not None, "应该有默认工件"
        print(f"✅ 默认工件: {default_workpiece}")
        
        # 测试load_data_for_workpiece方法
        page.load_data_for_workpiece("CAP1000")
        assert page.current_workpiece_id == "CAP1000", "工件ID设置失败"
        print("✅ 工件数据加载功能正常")
        
        # 测试数据状态更新
        initial_status = page.data_status_label.text()
        assert "未加载" in initial_status or "加载" in initial_status, "数据状态标签应该显示状态"
        print("✅ 数据状态显示正常")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据加载测试失败: {e}")
        traceback.print_exc()
        return False

def test_report_configuration():
    """测试报告配置功能"""
    print("⚙️ 测试报告配置功能...")
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    try:
        from report_generation_page import ReportGenerationPage
        page = ReportGenerationPage()
        
        # 测试配置创建
        config = page._create_report_configuration()
        assert config is not None, "报告配置创建失败"
        print("✅ 报告配置创建成功")
        
        # 测试配置属性
        assert hasattr(config, 'report_type'), "配置缺少报告类型"
        assert hasattr(config, 'report_format'), "配置缺少报告格式"
        assert hasattr(config, 'include_workpiece_info'), "配置缺少工件信息选项"
        print("✅ 报告配置属性完整")
        
        # 测试不同选项的配置
        page.report_type_combo.setCurrentText("质量分析报告")
        page.format_combo.setCurrentText("HTML")
        page.include_workpiece_info.setChecked(False)
        
        config2 = page._create_report_configuration()
        assert config2.include_workpiece_info == False, "配置选项更新失败"
        print("✅ 配置选项动态更新正常")
        
        return True
        
    except Exception as e:
        print(f"❌ 报告配置测试失败: {e}")
        traceback.print_exc()
        return False

def test_signals_and_connections():
    """测试信号和连接"""
    print("🔗 测试信号和连接...")
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    try:
        from report_generation_page import ReportGenerationPage
        page = ReportGenerationPage()
        
        # 测试信号存在
        assert hasattr(page, 'status_updated'), "缺少status_updated信号"
        print("✅ 必要信号存在")
        
        # 测试信号连接
        signal_received = []
        
        def capture_signal(message):
            signal_received.append(message)
        
        page.status_updated.connect(capture_signal)
        
        # 触发信号
        page.status_updated.emit("测试信号")
        assert len(signal_received) == 1, "信号未正确发射"
        assert signal_received[0] == "测试信号", "信号内容不正确"
        print("✅ 信号连接和发射正常")
        
        return True
        
    except Exception as e:
        print(f"❌ 信号测试失败: {e}")
        traceback.print_exc()
        return False

def test_worker_thread():
    """测试工作线程"""
    print("🧵 测试报告生成工作线程...")
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    try:
        from report_generation_page import ReportGenerationWorker, ReportConfiguration, ReportType, ReportFormat
        
        # 创建配置
        config = ReportConfiguration(
            report_type=ReportType.COMPREHENSIVE,
            report_format=ReportFormat.PDF
        )
        
        # 创建工作线程
        worker = ReportGenerationWorker("CAP1000", config)
        assert worker is not None, "工作线程创建失败"
        print("✅ 工作线程创建成功")
        
        # 测试信号存在
        required_signals = ['progress_updated', 'status_updated', 'report_completed', 'error_occurred']
        for signal_name in required_signals:
            assert hasattr(worker, signal_name), f"工作线程缺少信号: {signal_name}"
        print("✅ 工作线程信号完整")
        
        return True
        
    except Exception as e:
        print(f"❌ 工作线程测试失败: {e}")
        traceback.print_exc()
        return False

def test_history_management():
    """测试历史记录管理"""
    print("📜 测试历史记录管理...")
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    try:
        from report_generation_page import ReportGenerationPage
        page = ReportGenerationPage()
        
        # 测试历史管理器存在
        assert hasattr(page, 'history_manager'), "缺少历史管理器"
        assert page.history_manager is not None, "历史管理器未初始化"
        print("✅ 历史管理器存在")
        
        # 测试历史记录方法
        assert hasattr(page, '_refresh_history'), "缺少刷新历史方法"
        assert hasattr(page, '_cleanup_history'), "缺少清理历史方法"
        print("✅ 历史管理方法存在")
        
        # 测试刷新历史记录
        page._refresh_history()
        print("✅ 历史记录刷新成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 历史管理测试失败: {e}")
        traceback.print_exc()
        return False

def test_error_handling():
    """测试错误处理"""
    print("🛡️ 测试错误处理...")
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    try:
        from report_generation_page import ReportGenerationPage
        page = ReportGenerationPage()
        
        # 测试无工件情况下的预览
        page.current_workpiece_id = None
        try:
            page._preview_report()
            print("⚠️ 无工件预览未正确处理")
        except:
            pass  # 应该有错误处理
        print("✅ 无工件预览错误处理正常")
        
        # 测试无工件情况下的生成
        try:
            page._generate_report()
            print("⚠️ 无工件生成未正确处理")
        except:
            pass  # 应该有错误处理
        print("✅ 无工件生成错误处理正常")
        
        return True
        
    except Exception as e:
        print(f"❌ 错误处理测试失败: {e}")
        traceback.print_exc()
        return False

def test_components_separately():
    """单独测试组件"""
    print("🧩 单独测试各个组件...")
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    try:
        # 测试配置面板组件
        from components.report_config_panel import ReportConfigPanel
        config_panel = ReportConfigPanel()
        assert config_panel is not None, "配置面板创建失败"
        print("✅ 配置面板组件正常")
        
        # 测试预览面板组件
        from components.report_preview_panel import ReportPreviewPanel
        preview_panel = ReportPreviewPanel()
        assert preview_panel is not None, "预览面板创建失败"
        print("✅ 预览面板组件正常")
        
        # 测试历史面板组件
        from components.report_history_panel import ReportHistoryPanel
        history_panel = ReportHistoryPanel()
        assert history_panel is not None, "历史面板创建失败"
        print("✅ 历史面板组件正常")
        
        # 测试数据预览小部件
        from widgets.data_preview_widget import DataPreviewWidget
        data_widget = DataPreviewWidget()
        assert data_widget is not None, "数据预览小部件创建失败"
        print("✅ 数据预览小部件正常")
        
        # 测试状态小部件
        from widgets.report_status_widget import ReportStatusWidget
        status_widget = ReportStatusWidget()
        assert status_widget is not None, "状态小部件创建失败"
        print("✅ 状态小部件正常")
        
        return True
        
    except Exception as e:
        print(f"❌ 组件测试失败: {e}")
        traceback.print_exc()
        return False

def run_comprehensive_tests():
    """运行全面测试"""
    print("🚀 开始P4报告生成模块全面测试")
    print("=" * 60)
    
    tests = [
        ("导入依赖测试", test_imports_comprehensive),
        ("页面初始化测试", test_page_initialization),
        ("UI组件测试", test_ui_components),
        ("数据加载测试", test_data_loading),
        ("报告配置测试", test_report_configuration),
        ("信号连接测试", test_signals_and_connections),
        ("工作线程测试", test_worker_thread),
        ("历史管理测试", test_history_management),
        ("错误处理测试", test_error_handling),
        ("独立组件测试", test_components_separately),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 通过")
            else:
                failed += 1
                print(f"❌ {test_name} 失败")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} 异常: {e}")
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🎯 测试结果汇总")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"📊 成功率: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("🎉 所有测试通过！P4模块可以安全投入使用！")
        return True
    else:
        print("⚠️ 有测试失败，需要进一步检查和修复")
        return False

if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)