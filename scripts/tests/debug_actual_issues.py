#!/usr/bin/env python3
"""
调试实际问题
找出为什么修复没有生效
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def debug_detection_service():
    """调试检测服务"""
    print("🔍 调试检测服务...")
    
    # 检查所有检测服务文件
    detection_services = [
        "src/services/detection_service.py",
        "src/controllers/services/detection_service.py"
    ]
    
    for service_path in detection_services:
        full_path = Path(project_root) / service_path
        if full_path.exists():
            print(f"\n📋 检查 {service_path}:")
            content = full_path.read_text(encoding='utf-8')
            
            # 查找间隔设置
            if "'interval': 10000" in content:
                print("  ✅ 找到10秒间隔设置")
            elif "interval = 10000" in content:
                print("  ✅ 找到10秒间隔变量")
            elif "1000" in content and "timer" in content:
                print("  ⚠️ 找到1秒定时器设置")
                # 打印相关行
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if "1000" in line and "timer" in line.lower():
                        print(f"    第{i+1}行: {line.strip()}")
            
            # 查找调试日志
            if "开始" in content and "间隔" in content:
                print("  ✅ 找到调试日志")
            else:
                print("  ❌ 没有调试日志")

def debug_batch_display():
    """调试批次显示"""
    print("\n🔍 调试批次显示...")
    
    # 检查控制器的批次信号
    controller_file = Path(project_root) / "src/pages/main_detection_p1/controllers/main_window_controller.py"
    if controller_file.exists():
        content = controller_file.read_text(encoding='utf-8')
        
        print("  📋 检查批次信号:")
        if "batch_created = Signal(str)" in content:
            print("    ✅ batch_created信号定义存在")
        else:
            print("    ❌ batch_created信号定义不存在")
            
        if "self.batch_created.emit" in content:
            print("    ✅ 找到信号发射代码")
            # 查找发射位置
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "self.batch_created.emit" in line:
                    print(f"    第{i+1}行: {line.strip()}")
        else:
            print("    ❌ 没有找到信号发射代码")
    
    # 检查主页面的信号连接
    main_page_file = Path(project_root) / "src/pages/main_detection_p1/main_detection_page.py"
    if main_page_file.exists():
        content = main_page_file.read_text(encoding='utf-8')
        
        print("\n  📋 检查信号连接:")
        if "batch_created.connect" in content:
            print("    ✅ 找到批次信号连接")
            # 查找连接代码
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "batch_created.connect" in line:
                    print(f"    第{i+1}行: {line.strip()}")
        else:
            print("    ❌ 没有找到批次信号连接")
            
        if "def _on_batch_created" in content:
            print("    ✅ 找到批次处理方法")
            # 检查方法内容
            in_method = False
            method_lines = []
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "def _on_batch_created" in line:
                    in_method = True
                elif in_method and line.strip() and not line.startswith('    '):
                    break
                elif in_method:
                    method_lines.append(f"    第{i+1}行: {line.rstrip()}")
            
            if len(method_lines) > 5:
                print("    方法内容（前5行）:")
                for line in method_lines[:5]:
                    print(line)
        else:
            print("    ❌ 没有找到批次处理方法")

def debug_progress_display():
    """调试进度显示"""
    print("\n🔍 调试进度显示...")
    
    native_view_file = Path(project_root) / "src/pages/main_detection_p1/native_main_detection_view_p1.py"
    if native_view_file.exists():
        content = native_view_file.read_text(encoding='utf-8')
        
        print("  📋 检查进度计算:")
        if "progress_float = (current / total) * 100" in content:
            print("    ✅ 找到浮点进度计算")
        else:
            print("    ❌ 没有找到浮点进度计算")
            
        if "<1%" in content:
            print("    ✅ 找到<1%显示逻辑")
        else:
            print("    ❌ 没有找到<1%显示逻辑")
            
        # 查找进度更新方法
        if "def update_detection_progress" in content:
            print("    ✅ 找到进度更新方法")
            # 查找方法中的计算逻辑
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "int(current / total * 100)" in line:
                    print(f"    ⚠️ 第{i+1}行: 仍在使用整数计算: {line.strip()}")

def check_actual_imports():
    """检查实际导入"""
    print("\n🔍 检查实际导入路径...")
    
    # 检查哪些文件导入了StatusManager
    print("  📋 StatusManager导入:")
    import_patterns = [
        ("业务服务", "src/services/business_service.py"),
        ("主控制器", "src/controllers/main_window_controller.py"),
        ("P1控制器", "src/pages/main_detection_p1/controllers/main_window_controller.py")
    ]
    
    for name, file_path in import_patterns:
        full_path = Path(project_root) / file_path
        if full_path.exists():
            content = full_path.read_text(encoding='utf-8')
            if "StatusManager" in content:
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if "from" in line and "status_manager" in line and "import" in line:
                        print(f"    {name}: {line.strip()}")

def main():
    """主函数"""
    print("🚀 调试实际问题...")
    print("=" * 70)
    
    debug_detection_service()
    debug_batch_display()
    debug_progress_display()
    check_actual_imports()
    
    print("\n" + "=" * 70)
    print("📊 调试总结")
    print("=" * 70)
    
    print("\n💡 可能的问题:")
    print("1. 检测服务可能有多个实现，实际使用的可能不是修改的那个")
    print("2. 批次信号可能在某个环节断开了")
    print("3. 进度计算可能在其他地方被覆盖")
    print("4. 可能需要重启应用才能使修改生效")

if __name__ == "__main__":
    main()