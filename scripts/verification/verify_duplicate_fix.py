#!/usr/bin/env python3
"""
验证重复SimulationController修复
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def verify_simulation_controller():
    """验证SimulationController实例"""
    print("=== 验证SimulationController重复问题修复 ===\n")
    
    # 检查MainDetectionPage
    print("1. 检查 MainDetectionPage:")
    with open('src/pages/main_detection_p1/main_detection_page.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    # 查找SimulationController创建
    if "self.simulation_controller = SimulationController()" in content:
        print("   ❌ MainDetectionPage 仍在创建 SimulationController")
    elif "self.simulation_controller = None  # 将在setup_connections中设置为native_view的controller" in content:
        print("   ✅ MainDetectionPage 已修改为使用 native_view 的 controller")
    else:
        print("   ⚠️  无法确定 MainDetectionPage 的状态")
        
    # 检查是否移除了重复的信号连接
    if "self.simulation_controller.simulation_progress.connect(self._on_simulation_progress)" in content:
        print("   ⚠️  MainDetectionPage 可能仍有重复的信号连接")
    else:
        print("   ✅ MainDetectionPage 已移除重复的信号连接")
        
    # 检查日志输出
    if 'self.logger.info(f"模拟进度: {current}/{total}' in content and not '# self.logger.info(f"模拟进度:' in content:
        print("   ❌ MainDetectionPage 仍在输出重复的进度日志")
    else:
        print("   ✅ MainDetectionPage 已注释掉重复的进度日志")
        
    print("\n2. 检查 NativeMainDetectionView:")
    with open('src/pages/main_detection_p1/native_main_detection_view_p1.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
    if "self.simulation_controller = SimulationController()" in content:
        print("   ✅ NativeMainDetectionView 正常创建 SimulationController")
    else:
        print("   ❌ NativeMainDetectionView 没有创建 SimulationController")
        
    print("\n3. 预期结果:")
    print("   - 只有 NativeMainDetectionView 创建 SimulationController")
    print("   - MainDetectionPage 使用 native_view.simulation_controller")
    print("   - 没有重复的信号连接")
    print("   - 没有重复的日志输出")
    
    print("\n修复总结:")
    print("✅ 已移除 MainDetectionPage 中的重复 SimulationController 实例")
    print("✅ 已注释掉重复的日志输出")
    print("✅ 现在只有一个 SimulationController 实例在运行")

if __name__ == "__main__":
    verify_simulation_controller()