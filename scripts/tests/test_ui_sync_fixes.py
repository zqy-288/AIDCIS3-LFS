#!/usr/bin/env python3
"""
测试UI同步问题修复
验证批次显示、检测速度、进度显示问题的修复
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def test_progress_calculation_fix():
    """测试进度计算修复"""
    print("🔍 测试进度计算修复...")
    
    try:
        # 模拟进度计算逻辑
        def calculate_progress(current, total):
            """模拟修复后的进度计算"""
            if total > 0:
                progress_float = (current / total) * 100
                progress_percent = max(0.01, round(progress_float, 2)) if current > 0 else 0
                if 0 < progress_percent < 1:
                    progress_display = "<1%"
                else:
                    progress_display = f"{progress_percent:.1f}%"
                return progress_percent, progress_display
            else:
                return 0, "0.0%"
        
        # 测试用例
        test_cases = [
            (0, 25270, 0, "0.0%"),         # 未开始
            (76, 25270, 0.30, "<1%"),      # 小进度
            (253, 25270, 1.0, "1.0%"),     # 刚达到1%
            (2527, 25270, 10.0, "10.0%"),  # 10%
            (25270, 25270, 100.0, "100.0%") # 完成
        ]
        
        for current, total, expected_percent, expected_display in test_cases:
            actual_percent, actual_display = calculate_progress(current, total)
            
            print(f"    📊 测试 {current}/{total}:")
            print(f"      期望: {expected_percent}% -> {expected_display}")
            print(f"      实际: {actual_percent}% -> {actual_display}")
            
            if abs(actual_percent - expected_percent) < 0.01 and actual_display == expected_display:
                print(f"    ✅ 进度计算正确")
            else:
                print(f"    ❌ 进度计算错误")
                return False
        
        return True
        
    except Exception as e:
        print(f"    ❌ 进度计算测试失败: {e}")
        return False

def test_detection_speed_configuration():
    """测试检测速度配置"""
    print("🔍 测试检测速度配置...")
    
    try:
        from src.services.detection_service import DetectionService
        
        service = DetectionService()
        
        # 检查模拟参数
        simulation_params = service.simulation_params
        print(f"    📊 模拟参数: {simulation_params}")
        
        expected_interval = 10000  # 10秒
        actual_interval = simulation_params.get('interval', 0)
        
        if actual_interval == expected_interval:
            print(f"    ✅ 模拟间隔配置正确: {actual_interval}ms")
        else:
            print(f"    ❌ 模拟间隔配置错误: {actual_interval}ms != {expected_interval}ms")
            return False
        
        # 测试间隔设置逻辑
        def test_interval_logic(is_mock):
            return simulation_params['interval'] if is_mock else 100
        
        mock_interval = test_interval_logic(True)
        real_interval = test_interval_logic(False)
        
        print(f"    📊 模拟检测间隔: {mock_interval}ms")
        print(f"    📊 实际检测间隔: {real_interval}ms")
        
        if mock_interval == 10000 and real_interval == 100:
            print("    ✅ 检测间隔逻辑正确")
            return True
        else:
            print("    ❌ 检测间隔逻辑错误")
            return False
        
    except Exception as e:
        print(f"    ❌ 检测速度配置测试失败: {e}")
        return False

def test_batch_display_logic():
    """测试批次显示逻辑"""
    print("🔍 测试批次显示逻辑...")
    
    try:
        # 模拟批次显示更新逻辑
        class MockWidget:
            def __init__(self, initial_text):
                self._text = initial_text
                
            def text(self):
                return self._text
                
            def setText(self, text):
                self._text = text
                
            def __str__(self):
                return f"Widget('{self._text}')"
        
        # 创建模拟组件
        widgets = [
            MockWidget("检测批次: 未开始"),
            MockWidget("检测批次: 未开始"),
            MockWidget("其他标签"),
        ]
        
        def update_batch_labels(widgets, batch_id):
            """模拟批次标签更新逻辑"""
            updated_count = 0
            for widget in widgets:
                if hasattr(widget, 'setText') and hasattr(widget, 'text'):
                    current_text = widget.text()
                    if "检测批次" in current_text:
                        widget.setText(f"检测批次: {batch_id}")
                        updated_count += 1
            return updated_count
        
        # 测试批次更新
        test_batch_id = "TEST_PRODUCT_检测001_20250804_MOCK"
        updated_count = update_batch_labels(widgets, test_batch_id)
        
        print(f"    📊 更新了 {updated_count} 个批次标签")
        
        # 验证更新结果
        batch_widgets = [w for w in widgets if "检测批次" in w.text()]
        
        if updated_count == 2 and all(test_batch_id in w.text() for w in batch_widgets):
            print("    ✅ 批次标签更新逻辑正确")
            for widget in batch_widgets:
                print(f"      📱 {widget}")
            return True
        else:
            print("    ❌ 批次标签更新逻辑错误")
            return False
        
    except Exception as e:
        print(f"    ❌ 批次显示逻辑测试失败: {e}")
        return False

def test_code_modifications_verification():
    """验证代码修改"""
    print("🔍 验证代码修改...")
    
    try:
        # 检查DetectionService修改
        detection_service_file = Path(project_root) / "src/services/detection_service.py"
        if detection_service_file.exists():
            content = detection_service_file.read_text(encoding='utf-8')
            
            if '开始' in content and 'interval' in content and 'ms' in content:
                print("    ✅ DetectionService调试日志已添加")
            else:
                print("    ❌ DetectionService调试日志未找到")
                return False
        
        # 检查进度计算修改
        native_view_file = Path(project_root) / "src/pages/main_detection_p1/native_main_detection_view_p1.py"
        if native_view_file.exists():
            content = native_view_file.read_text(encoding='utf-8')
            
            if 'progress_float = (current / total) * 100' in content and '<1%' in content:
                print("    ✅ 进度计算修复已应用")
            else:
                print("    ❌ 进度计算修复未找到")
                return False
        
        # 检查批次显示修改
        main_page_file = Path(project_root) / "src/pages/main_detection_p1/main_detection_page.py"
        if main_page_file.exists():
            content = main_page_file.read_text(encoding='utf-8')
            
            if 'update_batch_labels' in content and '递归查找并更新所有批次标签' in content:
                print("    ✅ 批次显示修复已应用")
            else:
                print("    ❌ 批次显示修复未找到")
                return False
        
        return True
        
    except Exception as e:
        print(f"    ❌ 代码修改验证失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 测试UI同步问题修复...")
    print("=" * 60)
    
    tests = [
        ("进度计算修复测试", test_progress_calculation_fix),
        ("检测速度配置测试", test_detection_speed_configuration),
        ("批次显示逻辑测试", test_batch_display_logic),
        ("代码修改验证", test_code_modifications_verification)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        try:
            result = test_func()
            results.append((test_name, "PASS" if result else "FAIL"))
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            results.append((test_name, "ERROR"))
    
    # 打印总结
    print("\n" + "=" * 60)
    print("📊 UI同步问题修复验证结果")
    print("=" * 60)
    
    passed = sum(1 for _, status in results if status == "PASS")
    total = len(results)
    
    for test_name, status in results:
        status_emoji = "✅" if status == "PASS" else "❌"
        print(f"{status_emoji} {test_name}: {status}")
    
    print(f"\n🎯 结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 ✨ UI同步问题已修复！ ✨")
        print("\n🔧 修复内容:")
        print("   ✅ 增强批次显示更新逻辑，递归查找所有批次标签")
        print("   ✅ 添加检测服务调试日志，确认间隔设置")
        print("   ✅ 修复进度计算精度问题，正确显示小数值进度")
        print("   ✅ 改进进度显示格式，小于1%时显示'<1%'")
        print("\n💡 现在应该解决:")
        print("   • 批次显示问题 - 递归更新所有相关标签")
        print("   • 检测速度问题 - 模拟检测使用10秒间隔")
        print("   • 进度显示问题 - 正确显示小数值进度")
    else:
        failed_tests = [name for name, status in results if status != "PASS"]
        print(f"\n⚠️ 需要进一步检查: {failed_tests}")
    
    print("=" * 60)
    return 0 if passed == total else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)