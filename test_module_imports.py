"""测试模块导入是否正常"""
import sys
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_imports():
    """测试所有模块是否能正常导入"""
    print("开始测试模块导入...")
    
    errors = []
    success_count = 0
    
    # 测试UI组件
    ui_modules = [
        ("工具栏", "main_window.ui_components.toolbar", "ToolbarWidget"),
        ("信息面板", "main_window.ui_components.info_panel", "InfoPanel"),
        ("可视化面板", "main_window.ui_components.visualization_panel", "VisualizationPanel"),
        ("操作面板", "main_window.ui_components.operations_panel", "OperationsPanel"),
        ("状态栏", "main_window.ui_components.status_bar", "StatusBarWidget"),
    ]
    
    print("\n1. 测试UI组件导入:")
    for name, module_path, class_name in ui_modules:
        try:
            module = __import__(module_path, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"  ✓ {name} ({class_name}) - 导入成功")
            success_count += 1
        except Exception as e:
            print(f"  ✗ {name} ({class_name}) - 导入失败: {str(e)}")
            errors.append((name, str(e)))
    
    # 测试管理器
    manager_modules = [
        ("检测管理器", "main_window.managers.detection_manager", "DetectionManager"),
        ("模拟管理器", "main_window.managers.simulation_manager", "SimulationManager"),
        ("产品管理器", "main_window.managers.product_manager", "ProductManager"),
        ("DXF管理器", "main_window.managers.dxf_manager", "DXFManager"),
        ("搜索管理器", "main_window.managers.hole_search_manager", "HoleSearchManager"),
    ]
    
    print("\n2. 测试管理器导入:")
    for name, module_path, class_name in manager_modules:
        try:
            module = __import__(module_path, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"  ✓ {name} ({class_name}) - 导入成功")
            success_count += 1
        except Exception as e:
            print(f"  ✗ {name} ({class_name}) - 导入失败: {str(e)}")
            errors.append((name, str(e)))
    
    # 测试服务
    service_modules = [
        ("状态服务", "main_window.services.status_service", "StatusService"),
        ("导航服务", "main_window.services.navigation_service", "NavigationService"),
    ]
    
    print("\n3. 测试服务导入:")
    for name, module_path, class_name in service_modules:
        try:
            module = __import__(module_path, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"  ✓ {name} ({class_name}) - 导入成功")
            success_count += 1
        except Exception as e:
            print(f"  ✗ {name} ({class_name}) - 导入失败: {str(e)}")
            errors.append((name, str(e)))
    
    # 测试主窗口
    print("\n4. 测试主窗口导入:")
    try:
        from main_window.main_window import MainWindow
        print(f"  ✓ 主窗口 (MainWindow) - 导入成功")
        success_count += 1
    except Exception as e:
        print(f"  ✗ 主窗口 (MainWindow) - 导入失败: {str(e)}")
        errors.append(("主窗口", str(e)))
    
    # 总结
    total_tests = len(ui_modules) + len(manager_modules) + len(service_modules) + 1
    print(f"\n========== 测试总结 ==========")
    print(f"总测试数: {total_tests}")
    print(f"成功: {success_count}")
    print(f"失败: {len(errors)}")
    
    if errors:
        print("\n失败的模块:")
        for name, error in errors:
            print(f"  - {name}: {error}")
    else:
        print("\n✅ 所有模块导入成功！重构完成。")
    
    return len(errors) == 0


if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)