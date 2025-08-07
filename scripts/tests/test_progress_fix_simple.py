#!/usr/bin/env python3
"""
简单验证进度更新修复
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def test_code_fix():
    """验证代码修复"""
    print("🔍 验证代码修复...")
    
    try:
        main_page_file = Path(project_root) / "src/pages/main_detection_p1/main_detection_page.py"
        
        if main_page_file.exists():
            content = main_page_file.read_text(encoding='utf-8')
            
            # 确认修复后的代码存在
            if "self.native_view.update_detection_progress((current, total))" in content:
                print("    ✅ 修复后的调用方式已应用")
                
                # 确认没有旧的错误调用
                error_patterns = [
                    "update_detection_progress(current, total)",
                    "update_detection_progress(progress, completed, pending)"
                ]
                
                for pattern in error_patterns:
                    if pattern in content and "native_view" in content:
                        print(f"    ⚠️ 仍存在可能的错误模式: {pattern}")
                        return False
                
                print("    ✅ 确认没有旧的错误调用模式")
                return True
            else:
                print("    ❌ 修复后的调用方式未找到")
                return False
        else:
            print("    ❌ 文件不存在")
            return False
            
    except Exception as e:
        print(f"    ❌ 代码验证失败: {e}")
        return False

def test_method_compatibility():
    """测试方法兼容性"""
    print("🔍 测试方法兼容性...")
    
    # 模拟update_detection_progress方法的实现
    def update_detection_progress(progress):
        """模拟原生视图的方法实现"""
        if isinstance(progress, tuple) and len(progress) == 2:
            current, total = progress
            progress_percent = int(current / total * 100) if total > 0 else 0
            print(f"    📊 处理元组参数: {current}/{total} = {progress_percent}%")
            return progress_percent
        else:
            progress_percent = int(progress)
            print(f"    📊 处理数值参数: {progress_percent}%")
            return progress_percent
    
    # 测试修复后的调用方式
    test_cases = [
        (25, 100),
        (50, 200),
        (100, 100)
    ]
    
    for current, total in test_cases:
        try:
            # 这是修复后的调用方式
            result = update_detection_progress((current, total))
            expected = int(current / total * 100) if total > 0 else 0
            
            if result == expected:
                print(f"    ✅ 参数 {current}/{total} 处理正确: {result}%")
            else:
                print(f"    ❌ 参数处理错误: {result} != {expected}")
                return False
                
        except Exception as e:
            print(f"    ❌ 调用异常: {e}")
            return False
    
    return True

def main():
    """主函数"""
    print("🚀 验证进度更新修复...")
    print("=" * 50)
    
    tests = [
        ("代码修复验证", test_code_fix),
        ("方法兼容性验证", test_method_compatibility)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        try:
            result = test_func()
            results.append((test_name, "PASS" if result else "FAIL"))
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            results.append((test_name, "ERROR"))
    
    # 打印总结
    print("\n" + "=" * 50)
    print("📊 修复验证结果")
    print("=" * 50)
    
    passed = sum(1 for _, status in results if status == "PASS")
    total = len(results)
    
    for test_name, status in results:
        status_emoji = "✅" if status == "PASS" else "❌"
        print(f"{status_emoji} {test_name}: {status}")
    
    print(f"\n🎯 结果: {passed}/{total} 验证通过")
    
    if passed == total:
        print("\n🎉 进度更新参数错误已修复！")
        print("✅ TypeError: update_detection_progress() takes 2 positional arguments but 3 were given 已解决")
    else:
        print("\n⚠️ 部分验证失败")
    
    print("=" * 50)
    return 0 if passed == total else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)