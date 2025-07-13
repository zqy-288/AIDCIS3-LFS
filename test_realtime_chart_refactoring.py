"""测试重构后的实时图表模块"""
import sys
import os
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_imports():
    """测试导入是否正常"""
    print("=" * 60)
    print("测试实时图表模块重构")
    print("=" * 60)
    
    errors = []
    
    # 测试兼容层导入
    print("\n1. 测试兼容层导入 (旧方式):")
    try:
        from modules.realtime_chart import RealtimeChart
        print("  ✓ from modules.realtime_chart import RealtimeChart - 成功")
    except Exception as e:
        print(f"  ✗ 兼容层导入失败: {e}")
        errors.append(("兼容层导入", str(e)))
    
    # 测试新模块结构导入
    print("\n2. 测试新模块结构导入:")
    modules_to_test = [
        ("utils", "modules.realtime_chart.utils", "setup_safe_chinese_font, ChartConfig"),
        ("managers", "modules.realtime_chart.managers", "DataManager, CSVManager, EndoscopeManager"),
        ("components", "modules.realtime_chart.components", "ChartWidget, StatusPanel"),
        ("主模块", "modules.realtime_chart.realtime_chart", "RealtimeChart"),
    ]
    
    for name, module_path, items in modules_to_test:
        try:
            exec(f"from {module_path} import {items}")
            print(f"  ✓ {name} - 导入成功")
        except Exception as e:
            print(f"  ✗ {name} - 导入失败: {e}")
            errors.append((name, str(e)))
    
    # 测试实例化
    print("\n3. 测试类实例化:")
    try:
        from modules.realtime_chart import RealtimeChart
        from PySide6.QtWidgets import QApplication
        
        # 创建应用实例（如果还没有）
        if not QApplication.instance():
            app = QApplication(sys.argv)
        
        # 创建实时图表实例
        chart = RealtimeChart()
        print("  ✓ RealtimeChart 实例创建成功")
        
        # 测试主要方法是否存在
        methods_to_check = [
            'update_data',
            'update_status',
            'set_current_hole',
            'start_measurement_for_hole',
            'stop_measurement',
            'clear_data',
            'set_tolerance_limits',
            'get_current_statistics',
            'load_data_for_hole',
        ]
        
        missing_methods = []
        for method in methods_to_check:
            if not hasattr(chart, method):
                missing_methods.append(method)
        
        if missing_methods:
            print(f"  ✗ 缺少方法: {', '.join(missing_methods)}")
            errors.append(("方法检查", f"缺少方法: {missing_methods}"))
        else:
            print("  ✓ 所有主要方法都存在")
        
        # 清理
        chart.cleanup()
        
    except Exception as e:
        print(f"  ✗ 实例化失败: {e}")
        errors.append(("实例化", str(e)))
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结:")
    if errors:
        print(f"✗ 发现 {len(errors)} 个错误:")
        for name, error in errors:
            print(f"  - {name}: {error}")
        return False
    else:
        print("✅ 所有测试通过！重构成功。")
        return True

def test_functionality():
    """测试基本功能"""
    print("\n4. 测试基本功能:")
    
    try:
        from modules.realtime_chart import RealtimeChart
        from PySide6.QtWidgets import QApplication
        
        if not QApplication.instance():
            app = QApplication(sys.argv)
        
        chart = RealtimeChart()
        
        # 测试设置公差
        chart.set_tolerance_limits(17.6, 0.2)
        print("  ✓ 设置公差成功")
        
        # 测试设置当前孔位
        chart.set_current_hole("H00001")
        print("  ✓ 设置当前孔位成功")
        
        # 测试更新数据
        chart.update_data(10.0, 17.5)
        chart.update_data(20.0, 17.6)
        chart.update_data(30.0, 17.7)
        print("  ✓ 更新数据成功")
        
        # 测试获取统计信息
        stats = chart.get_current_statistics()
        print(f"  ✓ 获取统计信息成功: {stats}")
        
        # 测试清除数据
        chart.clear_data()
        print("  ✓ 清除数据成功")
        
        chart.cleanup()
        
        return True
        
    except Exception as e:
        print(f"  ✗ 功能测试失败: {e}")
        return False

if __name__ == "__main__":
    # 运行测试
    import_success = test_imports()
    
    if import_success:
        function_success = test_functionality()
        
        if function_success:
            print("\n🎉 实时图表模块重构完成并测试通过！")
            sys.exit(0)
        else:
            print("\n❌ 功能测试失败")
            sys.exit(1)
    else:
        print("\n❌ 导入测试失败")
        sys.exit(1)