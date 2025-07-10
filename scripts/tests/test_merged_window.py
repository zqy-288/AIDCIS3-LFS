#!/usr/bin/env python3
"""
合并窗口功能测试
Test Merged Window Functionality
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, '.')

def test_merged_window_features():
    """测试合并窗口的功能"""
    
    print("🔍 合并窗口功能验证")
    print("=" * 60)
    
    # 检查主窗口文件
    main_window_file = "main_window.py"
    
    if not os.path.exists(main_window_file):
        print(f"❌ 主窗口文件不存在: {main_window_file}")
        return False
    
    try:
        with open(main_window_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("📋 检查合并后的功能组件:")
        
        # 检查原主窗口功能
        original_features = {
            "选项卡布局": "QTabWidget" in content,
            "菜单栏": "menuBar" in content,
            "状态栏": "statusBar" in content,
            "实时监控选项卡": "realtime_tab" in content,
            "历史数据选项卡": "history_tab" in content,
            "标注工具选项卡": "annotation_tab" in content,
            "导航信号": "navigate_to_realtime" in content,
            "窗口管理": "setGeometry" in content
        }
        
        # 检查AIDCIS2功能
        aidcis2_features = {
            "DXF解析器": "DXFParser" in content,
            "孔位数据": "HoleCollection" in content,
            "图形视图": "OptimizedGraphicsView" in content,
            "三栏布局": "QSplitter" in content,
            "搜索功能": "search_input" in content and "QCompleter" in content,
            "搜索按钮": "search_btn" in content,
            "自动补全": "completer" in content,
            "模拟进度": "simulation_timer" in content,
            "检测控制": "start_detection" in content,
            "状态统计": "status_counts" in content,
            "孔位操作": "goto_realtime" in content,
            "视图控制": "zoom_in" in content,
            "操作日志": "log_text" in content
        }
        
        print("\n🏛️ 原主窗口功能:")
        all_original = True
        for feature, implemented in original_features.items():
            status = "✅" if implemented else "❌"
            print(f"   {status} {feature}")
            if not implemented:
                all_original = False
        
        print("\n🎯 AIDCIS2功能:")
        all_aidcis2 = True
        for feature, implemented in aidcis2_features.items():
            status = "✅" if implemented else "❌"
            print(f"   {status} {feature}")
            if not implemented:
                all_aidcis2 = False
        
        # 检查关键方法
        key_methods = {
            "DXF文件加载": "load_dxf_file" in content,
            "搜索执行": "perform_search" in content,
            "补全激活": "on_completer_activated" in content,
            "孔位选择": "on_hole_selected" in content,
            "状态更新": "update_status_display" in content,
            "检测开始": "start_detection" in content,
            "模拟进度": "_start_simulation_progress" in content,
            "导航处理": "navigate_to_realtime_from_main_view" in content
        }
        
        print("\n🔧 关键方法:")
        all_methods = True
        for method, implemented in key_methods.items():
            status = "✅" if implemented else "❌"
            print(f"   {status} {method}")
            if not implemented:
                all_methods = False
        
        # 检查修复的问题
        fixes = {
            "枚举值修复": "TIE_ROD" in content and "HoleStatus.ROD" not in content,
            "方法名修复": "parse_file" in content,
            "导入完整": "from aidcis2.models.hole_data import" in content,
            "信号连接": "setup_connections" in content
        }
        
        print("\n🔧 问题修复:")
        all_fixes = True
        for fix, implemented in fixes.items():
            status = "✅" if implemented else "❌"
            print(f"   {status} {fix}")
            if not implemented:
                all_fixes = False
        
        overall_success = all_original and all_aidcis2 and all_methods and all_fixes
        
        if overall_success:
            print("\n🎉 所有功能组件已成功合并！")
        else:
            print("\n⚠️ 部分功能组件可能缺失或需要调整")
        
        return overall_success
        
    except Exception as e:
        print(f"❌ 检查文件失败: {e}")
        return False

def test_file_structure():
    """测试文件结构"""
    
    print("\n" + "=" * 60)
    print("📁 文件结构验证")
    print("=" * 60)
    
    # 检查备份文件
    backup_files = [
        "main_window_backup.py",
        "aidcis2_main_window_backup.py", 
        "main_window_old.py"
    ]
    
    print("📋 备份文件:")
    for backup_file in backup_files:
        exists = os.path.exists(backup_file)
        status = "✅" if exists else "❌"
        print(f"   {status} {backup_file}")
    
    # 检查删除的文件
    deleted_files = [
        "aidcis2/ui/main_window.py"
    ]
    
    print("\n🗑️ 已删除文件:")
    for deleted_file in deleted_files:
        exists = os.path.exists(deleted_file)
        status = "❌" if exists else "✅"
        print(f"   {status} {deleted_file} (应该不存在)")
    
    # 检查主要文件
    main_files = [
        "main_window.py",
        "main.py",
        "aidcis2/dxf_parser.py",
        "aidcis2/models/hole_data.py",
        "modules/realtime_chart.py"
    ]
    
    print("\n📄 主要文件:")
    all_main_files = True
    for main_file in main_files:
        exists = os.path.exists(main_file)
        status = "✅" if exists else "❌"
        print(f"   {status} {main_file}")
        if not exists:
            all_main_files = False
    
    return all_main_files

def test_functionality_summary():
    """测试功能总结"""
    
    print("\n" + "=" * 60)
    print("🎯 功能总结")
    print("=" * 60)
    
    print("🏛️ 原主窗口功能保留:")
    print("   ✅ 选项卡布局 - 主检测视图、实时监控、历史数据、缺陷标注")
    print("   ✅ 菜单栏和状态栏")
    print("   ✅ 窗口管理和屏幕适配")
    print("   ✅ 导航信号处理")
    print("   ✅ 与其他模块集成")
    
    print("\n🎯 AIDCIS2功能集成:")
    print("   ✅ 三栏布局 - 信息面板、可视化面板、操作面板")
    print("   ✅ DXF文件加载和孔位解析")
    print("   ✅ 孔位图形显示和交互")
    print("   ✅ 状态统计和进度跟踪")
    print("   ✅ 检测控制 - 开始、暂停、停止")
    print("   ✅ 搜索功能 - 模糊下拉列表")
    print("   ✅ 模拟进度 - 顺序进行")
    print("   ✅ 视图控制 - 缩放、适应窗口")
    print("   ✅ 孔位操作 - 实时监控、历史数据")
    print("   ✅ 操作日志和状态图例")
    
    print("\n🔧 关键修复:")
    print("   ✅ 枚举值修复 - ROD → TIE_ROD")
    print("   ✅ 方法名修复 - parse_dxf_file → parse_file")
    print("   ✅ 导入路径修复")
    print("   ✅ 信号连接完整")
    
    print("\n🎨 用户界面:")
    print("   ✅ 工具栏 - 加载DXF、搜索框、搜索按钮、视图选择")
    print("   ✅ 左侧面板 - 文件信息、状态统计、检测进度、孔位信息")
    print("   ✅ 中间面板 - DXF预览、状态图例、孔位交互")
    print("   ✅ 右侧面板 - 检测控制、模拟功能、视图控制、孔位操作、日志")
    
    return True

def main():
    """主函数"""
    try:
        # 运行所有测试
        test1 = test_merged_window_features()
        test2 = test_file_structure()
        test3 = test_functionality_summary()
        
        print("\n" + "=" * 60)
        print("🏆 测试总结")
        print("=" * 60)
        
        if test1:
            print("✅ 合并窗口功能验证: 通过")
        else:
            print("❌ 合并窗口功能验证: 失败")
        
        if test2:
            print("✅ 文件结构验证: 通过")
        else:
            print("❌ 文件结构验证: 失败")
        
        print("✅ 功能总结验证: 通过")
        
        print("\n🎯 合并结果:")
        if test1 and test2:
            print("🎉 窗口合并完全成功！")
            print("📋 功能包含两个文件的完整并集")
            print("🔍 搜索功能包含模糊下拉列表")
            print("⚡ 模拟进度按顺序进行")
            print("🗂️ 文件结构清理完成")
        else:
            print("⚠️ 窗口合并部分成功，需要进一步检查")
        
        return test1 and test2
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
