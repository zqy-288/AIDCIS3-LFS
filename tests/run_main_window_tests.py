"""
主窗口测试运行脚本
提供多种测试运行方式
"""

import subprocess
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_unit_tests():
    """运行单元测试"""
    print("\n" + "="*60)
    print("运行主窗口单元测试")
    print("="*60)
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_main_window_desktop.py",
        "-v", "-s",
        "--tb=short"
    ]
    
    subprocess.run(cmd)
    

def run_integration_tests():
    """运行集成测试"""
    print("\n" + "="*60)
    print("运行主窗口集成测试")
    print("="*60)
    
    # 启动应用并进行测试
    from src.main_window import MainWindowEnhanced
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = MainWindowEnhanced()
    
    # 执行测试场景
    print("\n测试场景1: 加载DXF文件")
    window.show()
    
    # 模拟用户操作
    print("- 点击'加载DXF'按钮")
    print("- 选择测试DXF文件")
    print("- 验证数据加载")
    
    print("\n测试场景2: 三栏布局验证")
    print("- 检查左侧信息面板")
    print("- 检查中间可视化面板")
    print("- 检查右侧操作面板")
    
    print("\n测试场景3: 检测流程")
    print("- 开始检测")
    print("- 暂停/继续")
    print("- 停止检测")
    
    # 保持窗口打开以供手动测试
    print("\n窗口已打开，请进行手动测试...")
    print("按Ctrl+C退出")
    
    try:
        app.exec()
    except KeyboardInterrupt:
        print("\n测试结束")
        

def run_performance_tests():
    """运行性能测试"""
    print("\n" + "="*60)
    print("运行主窗口性能测试")
    print("="*60)
    
    import time
    from src.main_window import MainWindowEnhanced
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # 测试启动时间
    start_time = time.time()
    window = MainWindowEnhanced()
    window.show()
    init_time = time.time() - start_time
    
    print(f"\n✓ 窗口初始化时间: {init_time:.3f}秒")
    
    # 测试大数据加载
    print("\n测试大数据集加载性能...")
    # TODO: 加载大型DXF文件并测量时间
    
    # 测试内存使用
    import psutil
    process = psutil.Process()
    memory_info = process.memory_info()
    print(f"\n✓ 内存使用: {memory_info.rss / 1024 / 1024:.2f} MB")
    
    window.close()
    

def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("运行主窗口完整测试套件")
    print("="*60)
    
    # 1. 单元测试
    run_unit_tests()
    
    # 2. 性能测试
    run_performance_tests()
    
    # 3. 集成测试（需要手动交互）
    print("\n是否运行集成测试？(需要手动交互) [y/N]: ", end="")
    if input().lower() == 'y':
        run_integration_tests()
        

def main():
    """主函数"""
    print("\n主窗口测试运行器")
    print("================")
    print("1. 运行单元测试")
    print("2. 运行集成测试")
    print("3. 运行性能测试")
    print("4. 运行所有测试")
    print("0. 退出")
    
    while True:
        print("\n请选择 [0-4]: ", end="")
        choice = input().strip()
        
        if choice == '0':
            break
        elif choice == '1':
            run_unit_tests()
        elif choice == '2':
            run_integration_tests()
        elif choice == '3':
            run_performance_tests()
        elif choice == '4':
            run_all_tests()
        else:
            print("无效选择，请重试")
            

if __name__ == "__main__":
    main()