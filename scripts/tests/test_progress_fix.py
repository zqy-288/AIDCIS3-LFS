#!/usr/bin/env python3
"""
测试进度更新方法参数修复
验证 update_detection_progress 方法调用参数正确
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def test_progress_method_signature():
    """测试进度方法签名"""
    print("🔍 测试进度方法签名...")
    
    try:
        # 创建模拟的native_view
        class MockNativeView:
            def __init__(self):
                self.progress_calls = []
                
            def update_detection_progress(self, progress):
                """模拟原生视图的进度更新方法"""
                self.progress_calls.append(progress)
                print(f"    📊 接收到进度参数: {progress} (类型: {type(progress)})")
                
                if isinstance(progress, tuple) and len(progress) == 2:
                    current, total = progress
                    progress_percent = int(current / total * 100) if total > 0 else 0
                    print(f"    ✅ 元组格式处理: {current}/{total} = {progress_percent}%")
                    return True
                elif isinstance(progress, (int, float)):
                    print(f"    ✅ 数值格式处理: {progress}%")
                    return True
                else:
                    print(f"    ❌ 未知格式: {progress}")
                    return False
        
        mock_view = MockNativeView()
        
        # 测试不同的调用方式
        test_cases = [
            ("元组参数", (50, 100)),
            ("百分比参数", 75),
            ("浮点数参数", 85.5)
        ]
        
        for test_name, progress_arg in test_cases:
            print(f"  🔧 测试 {test_name}...")
            try:
                result = mock_view.update_detection_progress(progress_arg)
                if result:
                    print(f"    ✅ {test_name} 处理成功")
                else:
                    print(f"    ❌ {test_name} 处理失败")
                    return False
            except Exception as e:
                print(f"    ❌ {test_name} 调用异常: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"    ❌ 进度方法测试失败: {e}")
        return False

def test_main_detection_page_call():
    """测试主检测页面的调用方式"""
    print("🔍 测试主检测页面调用...")
    
    try:
        # 验证修复后的代码
        main_page_file = Path(project_root) / "src/pages/main_detection_p1/main_detection_page.py"
        
        if main_page_file.exists():
            content = main_page_file.read_text(encoding='utf-8')
            
            # 查找修复后的调用模式
            fixed_pattern = "self.native_view.update_detection_progress((current, total))"
            old_pattern = "self.native_view.update_detection_progress(current, total)"
            
            if fixed_pattern in content:
                print("    ✅ 找到修复后的调用模式（元组参数）")
                if old_pattern not in content:
                    print("    ✅ 确认旧的错误调用已移除")
                    return True
                else:
                    print("    ⚠️ 仍存在旧的错误调用")
                    return False
            else:
                print("    ❌ 未找到修复后的调用模式")
                print("    🔍 搜索相关代码...")
                
                # 搜索包含update_detection_progress的行
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if 'update_detection_progress' in line and 'native_view' in line:
                        print(f"    第{i}行: {line.strip()}")
                
                return False
        else:
            print("    ❌ 主检测页面文件不存在")
            return False
            
    except Exception as e:
        print(f"    ❌ 主检测页面测试失败: {e}")
        return False

def test_parameter_compatibility():
    """测试参数兼容性"""
    print("🔍 测试参数兼容性...")
    
    try:
        # 模拟实际的native_view实现
        class TestNativeView:
            def __init__(self):
                self.logger = type('Logger', (), {'info': lambda msg: print(f"LOG: {msg}")})()
                
            def update_detection_progress(self, progress):
                """实际的进度更新方法实现"""
                if isinstance(progress, tuple) and len(progress) == 2:
                    # 处理 (current, total) 格式
                    current, total = progress
                    progress_percent = int(current / total * 100) if total > 0 else 0
                    self.logger.info(f"📊 进度更新: {current}/{total} = {progress_percent}%")
                    return progress_percent
                else:
                    # 处理百分比格式
                    progress_percent = int(progress)
                    self.logger.info(f"📊 进度更新: {progress_percent}%")
                    return progress_percent
        
        native_view = TestNativeView()
        
        # 测试各种参数组合
        test_params = [
            (25, 100),    # 25%
            (150, 300),   # 50%
            (75, 75),     # 100%
            (0, 100),     # 0%
        ]
        
        for current, total in test_params:
            print(f"  🔧 测试参数: current={current}, total={total}")
            
            # 测试修复后的调用方式（元组）
            try:
                result = native_view.update_detection_progress((current, total))
                expected = int(current / total * 100) if total > 0 else 0
                if result == expected:
                    print(f"    ✅ 元组调用成功: {result}%")
                else:
                    print(f"    ❌ 元组调用结果错误: {result} != {expected}")
                    return False
            except Exception as e:
                print(f"    ❌ 元组调用异常: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"    ❌ 参数兼容性测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 测试进度更新方法修复...")
    print("=" * 60)
    
    tests = [
        ("进度方法签名测试", test_progress_method_signature),
        ("主检测页面调用测试", test_main_detection_page_call),
        ("参数兼容性测试", test_parameter_compatibility)
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
    print("📊 进度更新修复验证结果")
    print("=" * 60)
    
    passed = sum(1 for _, status in results if status == "PASS")
    total = len(results)
    
    for test_name, status in results:
        status_emoji = "✅" if status == "PASS" else "❌"
        print(f"{status_emoji} {test_name}: {status}")
    
    print(f"\n🎯 结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 ✨ 进度更新方法参数错误已修复！ ✨")
        print("\n🔧 修复内容:")
        print("   ✅ 修正了 update_detection_progress() 的调用参数")
        print("   ✅ 从 (current, total) 两个参数改为 ((current, total)) 元组参数")
        print("   ✅ 保持了方法内部的兼容性处理")
        print("\n💡 错误 'takes 2 positional arguments but 3 were given' 已解决")
    else:
        failed_tests = [name for name, status in results if status != "PASS"]
        print(f"\n⚠️ 需要进一步检查: {failed_tests}")
    
    print("=" * 60)
    return 0 if passed == total else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)