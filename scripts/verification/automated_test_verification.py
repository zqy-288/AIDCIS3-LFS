#!/usr/bin/env python3
"""
自动化测试验证脚本
检查面板A和面板B的关键功能点
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def check_file_structure():
    """检查文件结构和数据完整性"""
    print("📁 检查文件结构和数据完整性...")
    
    base_dir = os.getcwd()
    results = {}
    
    # 检查关键文件
    key_files = [
        "main.py",
        "modules/realtime_chart.py", 
        "modules/endoscope_view.py"
    ]
    
    for file_path in key_files:
        exists = os.path.exists(file_path)
        results[f"文件_{file_path}"] = "✅ 存在" if exists else "❌ 缺失"
    
    # 检查数据目录
    data_paths = {
        "H00001_CSV": "data/H00001/CCIDM",
        "H00002_CSV": "data/H00002/CCIDM",
        "H00001_图像": os.path.join(base_dir, "Data/H00001/BISDM/result"),
        "H00002_图像": os.path.join(base_dir, "Data/H00002/BISDM/result")
    }
    
    for name, path in data_paths.items():
        exists = os.path.exists(path)
        results[f"目录_{name}"] = "✅ 存在" if exists else "❌ 缺失"
        
        if exists and os.path.isdir(path):
            try:
                files = os.listdir(path)
                if "CSV" in name:
                    csv_files = [f for f in files if f.endswith('.csv')]
                    results[f"数据_{name}"] = f"✅ {len(csv_files)} 个CSV文件"
                else:
                    image_files = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                    results[f"数据_{name}"] = f"✅ {len(image_files)} 个图像文件"
            except Exception as e:
                results[f"数据_{name}"] = f"❌ 读取失败: {e}"
    
    return results

def check_code_integration():
    """检查代码集成点"""
    print("🔧 检查代码集成点...")
    
    results = {}
    
    try:
        # 检查realtime_chart.py中的关键方法
        with open("modules/realtime_chart.py", "r", encoding="utf-8") as f:
            content = f.read()
            
        # 检查面板A按钮相关方法
        panel_a_methods = [
            "create_panel_a_controls",
            "start_panel_a_animation", 
            "stop_panel_a_animation"
        ]
        
        for method in panel_a_methods:
            if f"def {method}" in content:
                results[f"面板A方法_{method}"] = "✅ 已实现"
            else:
                results[f"面板A方法_{method}"] = "❌ 缺失"
        
        # 检查面板B集成方法
        panel_b_methods = [
            "start_endoscope_image_switching",
            "stop_endoscope_image_switching",
            "update_endoscope_image_by_progress"
        ]
        
        for method in panel_b_methods:
            if f"def {method}" in content:
                results[f"面板B方法_{method}"] = "✅ 已实现"
            else:
                results[f"面板B方法_{method}"] = "❌ 缺失"
        
        # 检查关键变量
        key_vars = [
            "endoscope_switching_enabled",
            "panel_a_start_btn",
            "panel_a_stop_btn"
        ]
        
        for var in key_vars:
            if var in content:
                results[f"变量_{var}"] = "✅ 已定义"
            else:
                results[f"变量_{var}"] = "❌ 缺失"
                
    except Exception as e:
        results["代码检查"] = f"❌ 检查失败: {e}"
    
    try:
        # 检查endoscope_view.py中的按钮集成
        with open("modules/endoscope_view.py", "r", encoding="utf-8") as f:
            content = f.read()
            
        endoscope_methods = [
            "start_algorithm",
            "stop_algorithm"
        ]
        
        for method in endoscope_methods:
            if f"def {method}" in content:
                results[f"内窥镜方法_{method}"] = "✅ 已实现"
            else:
                results[f"内窥镜方法_{method}"] = "❌ 缺失"
                
    except Exception as e:
        results["内窥镜代码检查"] = f"❌ 检查失败: {e}"
    
    return results

def check_import_dependencies():
    """检查导入依赖"""
    print("📦 检查导入依赖...")
    
    results = {}
    
    try:
        # 测试关键模块导入
        import matplotlib.pyplot as plt
        results["matplotlib"] = "✅ 可用"
    except ImportError as e:
        results["matplotlib"] = f"❌ 导入失败: {e}"
    
    try:
        from PySide6.QtWidgets import QApplication
        results["PySide6"] = "✅ 可用"
    except ImportError as e:
        results["PySide6"] = f"❌ 导入失败: {e}"
    
    try:
        import pandas as pd
        results["pandas"] = "✅ 可用"
    except ImportError as e:
        results["pandas"] = f"❌ 导入失败: {e}"
    
    try:
        import numpy as np
        results["numpy"] = "✅ 可用"
    except ImportError as e:
        results["numpy"] = f"❌ 导入失败: {e}"
    
    return results

def generate_test_report(file_results, code_results, import_results):
    """生成测试报告"""
    print("\n" + "="*80)
    print("📋 自动化测试验证报告")
    print("="*80)
    
    print("\n📁 **文件结构检查结果**:")
    print("-" * 50)
    for key, value in file_results.items():
        print(f"  {key}: {value}")
    
    print("\n🔧 **代码集成检查结果**:")
    print("-" * 50)
    for key, value in code_results.items():
        print(f"  {key}: {value}")
    
    print("\n📦 **依赖检查结果**:")
    print("-" * 50)
    for key, value in import_results.items():
        print(f"  {key}: {value}")
    
    # 统计结果
    all_results = {**file_results, **code_results, **import_results}
    total_checks = len(all_results)
    passed_checks = len([v for v in all_results.values() if v.startswith("✅")])
    failed_checks = total_checks - passed_checks
    
    print(f"\n📊 **测试统计**:")
    print("-" * 50)
    print(f"  总检查项: {total_checks}")
    print(f"  通过项: {passed_checks} ✅")
    print(f"  失败项: {failed_checks} ❌")
    print(f"  通过率: {(passed_checks/total_checks)*100:.1f}%")
    
    # 生成建议
    print(f"\n💡 **建议**:")
    print("-" * 50)
    
    if failed_checks == 0:
        print("  🎉 所有检查项都通过！可以开始手动集成测试。")
    else:
        print("  ⚠️ 发现问题，建议先修复以下项目:")
        for key, value in all_results.items():
            if value.startswith("❌"):
                print(f"    - {key}: {value}")
    
    print(f"\n🚀 **下一步**:")
    print("-" * 50)
    if failed_checks == 0:
        print("  1. 运行手动集成测试: python panel_ab_integration_tests.py")
        print("  2. 启动程序进行实际测试: python main.py")
        print("  3. 按照测试计划逐项验证功能")
    else:
        print("  1. 修复上述失败的检查项")
        print("  2. 重新运行此验证脚本")
        print("  3. 确保所有项目通过后再进行手动测试")

def main():
    print("🤖 自动化测试验证开始")
    print("=" * 80)
    
    print("正在执行自动化检查...")
    
    # 执行各项检查
    file_results = check_file_structure()
    code_results = check_code_integration()
    import_results = check_import_dependencies()
    
    # 生成报告
    generate_test_report(file_results, code_results, import_results)
    
    print("\n🎯 **关键功能验证清单**:")
    print("=" * 60)
    print("请手动验证以下关键功能:")
    print()
    print("面板A功能:")
    print("  □ 专用启动/停止按钮显示")
    print("  □ 按钮点击响应正常")
    print("  □ 状态指示器工作")
    print("  □ 图表动画播放")
    print()
    print("面板B功能:")
    print("  □ 算法启动/停止按钮显示")
    print("  □ 图像切换功能启用")
    print("  □ 与面板A数据同步")
    print("  □ 图像显示正确")
    print()
    print("集成功能:")
    print("  □ 孔位选择触发数据加载")
    print("  □ 面板A和B同步工作")
    print("  □ 按钮状态同步")
    print("  □ 错误处理正常")
    print()
    
    print("✅ 自动化验证完成！请继续手动测试。")

if __name__ == "__main__":
    main()
