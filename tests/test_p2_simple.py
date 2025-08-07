"""
P2实时监控页面简化测试
验证核心功能和布局恢复
"""

import sys
import os
import logging

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 设置测试环境
import matplotlib
matplotlib.use('Agg')  # 无GUI后端

def mock_numpy():
    """模拟numpy以避免依赖"""
    class MockNumpy:
        def __init__(self):
            pass
        def c_(self, x, y):
            return [[a, b] for a, b in zip(x, y)]
        def empty(self, shape):
            return [[0, 0]]
        def cos(self, x):
            import math
            return math.cos(x)
        def sin(self, x):
            import math
            return math.sin(x)
        def radians(self, x):
            import math
            return math.radians(x)
    return MockNumpy()

# 模拟numpy
sys.modules['numpy'] = mock_numpy()

class MockSharedComponents:
    """模拟共享组件"""
    def __init__(self):
        self.business_service = self
        self.current_product = self
        self.standard_diameter = 17.60
        self.tolerance_upper = 0.070
        self.tolerance_lower = 0.001
        self.model_name = "CAP1000"

def test_p2_page_basic():
    """基础功能测试"""
    print("🧪 开始P2页面基础功能测试")
    
    try:
        # 创建模拟应用程序上下文
        from PySide6.QtWidgets import QApplication
        if not QApplication.instance():
            app = QApplication(sys.argv)
        
        # 创建模拟依赖
        shared_components = MockSharedComponents()
        
        # 导入并创建P2页面
        from src.pages.realtime_monitoring_p2.realtime_monitoring_page import RealtimeMonitoringPage
        page = RealtimeMonitoringPage(shared_components=shared_components)
        
        print("✅ P2页面创建成功")
        
        # 测试基本属性
        assert hasattr(page, 'depth_data'), "缺少depth_data属性"
        assert hasattr(page, 'diameter_data'), "缺少diameter_data属性"
        assert hasattr(page, 'is_monitoring'), "缺少is_monitoring属性"
        print("✅ 基本属性检查通过")
        
        # 测试UI组件
        ui_components = [
            'canvas', 'figure', 'ax', 'endoscope_view',
            'hole_combo', 'start_stop_btn', 'clear_btn', 'export_btn',
            'std_diameter_input', 'upper_tolerance_input', 'lower_tolerance_input',
            'status_display', 'depth_display', 'stats_label'
        ]
        
        for component in ui_components:
            assert hasattr(page, component), f"缺少UI组件: {component}"
        print("✅ UI组件检查通过")
        
        # 测试参数加载
        assert page.standard_diameter == 17.60, "标准直径加载错误"
        assert page.tolerance_upper == 0.070, "上限公差加载错误"
        assert page.tolerance_lower == 0.001, "下限公差加载错误"
        print("✅ 参数加载检查通过")
        
        # 测试监控状态切换
        initial_state = page.is_monitoring
        page.start_stop_btn.setChecked(True)
        page._toggle_monitoring()
        assert page.is_monitoring != initial_state, "监控状态切换失败"
        print("✅ 监控状态切换测试通过")
        
        # 测试数据模拟
        page.is_monitoring = True
        initial_count = page.data_counter
        page._update_monitoring_data()
        assert page.data_counter == initial_count + 1, "数据计数更新失败"
        assert len(page.depth_data) > 0, "深度数据未添加"
        assert len(page.diameter_data) > 0, "直径数据未添加"
        print("✅ 数据模拟测试通过")
        
        # 测试数据清除
        page._clear_data()
        assert len(page.depth_data) == 0, "深度数据清除失败"
        assert len(page.diameter_data) == 0, "直径数据清除失败"
        assert page.data_counter == 0, "数据计数重置失败"
        print("✅ 数据清除测试通过")
        
        # 测试孔位设置
        test_hole = "AC001R001"
        page._on_hole_changed(test_hole)
        assert page.current_hole == test_hole, "孔位设置失败"
        print("✅ 孔位设置测试通过")
        
        # 测试参数更新
        new_diameter = 18.0
        page.std_diameter_input.setText(str(new_diameter))
        page._update_standard_diameter()
        assert page.standard_diameter == new_diameter, "标准直径更新失败"
        print("✅ 参数更新测试通过")
        
        # 测试公共接口
        stats = page.get_monitoring_statistics()
        assert isinstance(stats, dict), "统计信息获取失败"
        assert 'current_hole' in stats, "统计信息缺少current_hole"
        assert 'data_count' in stats, "统计信息缺少data_count"
        print("✅ 公共接口测试通过")
        
        # 关闭页面
        page.close()
        print("✅ P2页面关闭成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_p2_layout_structure():
    """布局结构测试"""
    print("\\n🧪 开始P2页面布局结构测试")
    
    try:
        from PySide6.QtWidgets import QApplication
        if not QApplication.instance():
            app = QApplication(sys.argv)
        
        shared_components = MockSharedComponents()
        from src.pages.realtime_monitoring_p2.realtime_monitoring_page import RealtimeMonitoringPage
        page = RealtimeMonitoringPage(shared_components=shared_components)
        
        # 检查左右分割布局
        assert hasattr(page, 'canvas'), "缺少matplotlib图表组件"
        assert hasattr(page, 'endoscope_view'), "缺少内窥镜视图组件"
        print("✅ 左右分割布局检查通过")
        
        # 检查控制面板结构
        control_elements = [
            'hole_combo',           # 孔位选择
            'status_display',       # 状态显示  
            'depth_display',        # 深度显示
            'start_stop_btn',       # 开始/停止按钮
            'clear_btn',           # 清除按钮
            'export_btn',          # 导出按钮
        ]
        
        for element in control_elements:
            assert hasattr(page, element), f"缺少控制元素: {element}"
        print("✅ 控制面板结构检查通过")
        
        # 检查参数配置区域
        param_elements = [
            'std_diameter_input',    # 标准直径输入
            'upper_tolerance_input', # 上限公差输入
            'lower_tolerance_input', # 下限公差输入
        ]
        
        for element in param_elements:
            assert hasattr(page, element), f"缺少参数元素: {element}"
        print("✅ 参数配置区域检查通过")
        
        page.close()
        return True
        
    except Exception as e:
        print(f"❌ 布局测试失败: {str(e)}")
        return False

def test_p2_original_features():
    """原版功能特性测试"""
    print("\\n🧪 开始P2页面原版功能特性测试")
    
    try:
        from PySide6.QtWidgets import QApplication
        if not QApplication.instance():
            app = QApplication(sys.argv)
            
        shared_components = MockSharedComponents()
        from src.pages.realtime_monitoring_p2.realtime_monitoring_page import RealtimeMonitoringPage
        page = RealtimeMonitoringPage(shared_components=shared_components)
        
        # 测试原版特性1: matplotlib图表
        assert hasattr(page, 'figure'), "缺少matplotlib Figure"
        assert hasattr(page, 'ax'), "缺少matplotlib轴"
        assert hasattr(page, 'diameter_line'), "缺少直径数据线"
        assert hasattr(page, 'anomaly_points'), "缺少异常点"
        print("✅ matplotlib图表特性检查通过")
        
        # 测试原版特性2: 标准线和公差带
        page._update_standard_lines()
        assert hasattr(page, 'standard_line'), "缺少标准线"
        assert hasattr(page, 'upper_limit_line'), "缺少上限线"
        assert hasattr(page, 'lower_limit_line'), "缺少下限线"
        assert hasattr(page, 'tolerance_patch'), "缺少公差带"
        print("✅ 标准线和公差带特性检查通过")
        
        # 测试原版特性3: 实时数据更新
        page.is_monitoring = True
        initial_depth = page.current_depth
        page._update_monitoring_data()
        assert page.current_depth > initial_depth, "深度未更新"
        print("✅ 实时数据更新特性检查通过")
        
        # 测试原版特性4: 内窥镜视图集成
        assert hasattr(page, 'endoscope_view'), "缺少内窥镜视图"
        page.endoscope_view.set_hole_id("AC001R001")  # 应该不报错
        print("✅ 内窥镜视图集成特性检查通过")
        
        # 测试原版特性5: 信号机制
        assert hasattr(page, 'monitoring_started'), "缺少monitoring_started信号"
        assert hasattr(page, 'monitoring_stopped'), "缺少monitoring_stopped信号"
        assert hasattr(page, 'hole_changed'), "缺少hole_changed信号"
        assert hasattr(page, 'data_exported'), "缺少data_exported信号"
        print("✅ 信号机制特性检查通过")
        
        page.close()
        return True
        
    except Exception as e:
        print(f"❌ 原版功能特性测试失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("🧪 P2实时监控页面恢复度测试")
    print("=" * 60)
    
    test_results = []
    
    # 运行基础功能测试
    try:
        result1 = test_p2_page_basic()
        test_results.append(("基础功能测试", result1))
    except Exception as e:
        print(f"❌ 基础功能测试异常: {e}")
        test_results.append(("基础功能测试", False))
    
    # 运行布局结构测试
    try:
        result2 = test_p2_layout_structure()
        test_results.append(("布局结构测试", result2))
    except Exception as e:
        print(f"❌ 布局结构测试异常: {e}")
        test_results.append(("布局结构测试", False))
    
    # 运行原版功能特性测试
    try:
        result3 = test_p2_original_features()
        test_results.append(("原版功能特性测试", result3))
    except Exception as e:
        print(f"❌ 原版功能特性测试异常: {e}")
        test_results.append(("原版功能特性测试", False))
    
    # 总结测试结果
    print("\\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    success_rate = (passed / total) * 100 if total > 0 else 0
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    print(f"\\n📈 总体成功率: {success_rate:.1f}% ({passed}/{total})")
    
    if success_rate >= 90:
        print("🎉 P2界面恢复度优秀！与原版高度一致！")
    elif success_rate >= 80:
        print("👍 P2界面恢复度良好！基本功能完整！")
    elif success_rate >= 70:
        print("⚠️ P2界面恢复度一般，需要进一步优化")
    else:
        print("❌ P2界面恢复度较差，需要重点修复")
    
    print("=" * 60)
    
    return success_rate >= 80

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)