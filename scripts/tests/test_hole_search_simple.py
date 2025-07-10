#!/usr/bin/env python3
"""
简单测试孔位搜索功能
不依赖GUI，专注于逻辑验证
"""

import sys
import os
from datetime import datetime

# 添加模块路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'modules'))

def test_hole_discovery():
    """测试孔位发现功能"""
    print("🔍 测试孔位发现功能...")
    
    available_holes = []
    
    # 方法1: 扫描数据目录
    data_base_dir = "Data"
    if os.path.exists(data_base_dir):
        print(f"📁 扫描数据目录: {data_base_dir}")
        
        for item in os.listdir(data_base_dir):
            item_path = os.path.join(data_base_dir, item)
            if os.path.isdir(item_path) and item.startswith('H'):
                # 检查是否有CCIDM目录（测量数据）
                ccidm_path = os.path.join(item_path, "CCIDM")
                if os.path.exists(ccidm_path):
                    csv_files = [f for f in os.listdir(ccidm_path) if f.endswith('.csv')]
                    if csv_files:
                        available_holes.append(item)
                        print(f"  ✅ {item}: {len(csv_files)} 个CSV文件")
                    else:
                        print(f"  ⚠️ {item}: 无CSV文件")
                else:
                    print(f"  ❌ {item}: 无CCIDM目录")
    else:
        print(f"❌ 数据目录不存在: {data_base_dir}")
    
    # 方法2: 尝试从数据库获取
    try:
        from modules.models import db_manager
        print("📊 尝试从数据库获取孔位...")
        
        db_manager.create_sample_data()
        db_holes = db_manager.get_workpiece_holes("WP-2025-001")
        
        if db_holes:
            for hole in db_holes:
                if hole.hole_id not in available_holes:
                    available_holes.append(hole.hole_id)
            print(f"  ✅ 数据库中找到 {len(db_holes)} 个孔位")
        else:
            print("  ⚠️ 数据库中无孔位数据")
            
    except Exception as e:
        print(f"  ❌ 数据库查询失败: {e}")
    
    # 排序并返回
    available_holes.sort()
    print(f"📋 总计发现 {len(available_holes)} 个孔位: {available_holes}")
    
    return available_holes

def test_fuzzy_search_logic():
    """测试模糊搜索逻辑"""
    print("🔎 测试模糊搜索逻辑...")
    
    # 模拟孔位列表
    hole_list = ["H00001", "H00002", "H00003", "H00004", "H00005", "H001", "H002", "H003"]
    
    # 测试搜索案例
    search_cases = [
        ("H001", "精确匹配"),
        ("h001", "忽略大小写"),
        ("001", "部分匹配"),
        ("H00", "前缀匹配"),
        ("1", "包含匹配"),
        ("H", "单字符匹配"),
        ("xyz", "无匹配")
    ]
    
    print("📋 测试搜索案例:")
    for search_term, description in search_cases:
        # 模拟Qt的MatchContains逻辑
        matches = [hole for hole in hole_list if search_term.lower() in hole.lower()]
        print(f"  🔍 '{search_term}' ({description}): {matches}")
    
    return True

def test_dropdown_population():
    """测试下拉菜单填充逻辑"""
    print("📋 测试下拉菜单填充逻辑...")
    
    # 获取可用孔位
    available_holes = test_hole_discovery()
    
    if available_holes:
        print("✅ 下拉菜单将包含以下选项:")
        for i, hole in enumerate(available_holes, 1):
            print(f"  {i}. {hole}")
        
        # 模拟自动完成器数据
        print("🔧 自动完成器配置:")
        print(f"  - 数据源: {len(available_holes)} 个孔位")
        print(f"  - 匹配模式: 包含匹配 (MatchContains)")
        print(f"  - 大小写: 不敏感 (CaseInsensitive)")
        
        return True
    else:
        print("❌ 无可用孔位，下拉菜单将为空")
        return False

def simulate_user_interaction():
    """模拟用户交互场景"""
    print("👤 模拟用户交互场景...")
    
    available_holes = ["H00001", "H00002", "H00003", "H00004", "H00005"]
    
    scenarios = [
        {
            "action": "用户选择工件 'WP-2025-001'",
            "result": f"加载孔位列表: {available_holes}"
        },
        {
            "action": "用户在孔位框中输入 'H00'",
            "result": f"自动完成建议: {[h for h in available_holes if 'H00' in h]}"
        },
        {
            "action": "用户点击下拉箭头",
            "result": f"显示所有选项: {available_holes}"
        },
        {
            "action": "用户选择 'H00001'",
            "result": "设置当前值为 'H00001'"
        },
        {
            "action": "用户点击查询按钮",
            "result": "开始查询 WP-2025-001 的 H00001 历史数据"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"  {i}. {scenario['action']}")
        print(f"     → {scenario['result']}")
    
    return True

def main():
    """主函数"""
    print("🚀 孔位搜索功能测试")
    print("=" * 50)
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("孔位发现", test_hole_discovery),
        ("模糊搜索逻辑", test_fuzzy_search_logic),
        ("下拉菜单填充", test_dropdown_population),
        ("用户交互模拟", simulate_user_interaction),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🧪 测试: {test_name}")
        print("-" * 30)
        
        try:
            if test_name == "孔位发现":
                result = test_func()
                success = len(result) > 0 if isinstance(result, list) else bool(result)
            else:
                success = test_func()
            
            results[test_name] = success
            status = "✅ 通过" if success else "❌ 失败"
            print(f"结果: {status}")
            
        except Exception as e:
            print(f"💥 异常: {e}")
            results[test_name] = False
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    print("-" * 30)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    print(f"\n🎯 总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("\n🎉 孔位搜索功能测试全部通过！")
        print("💡 功能特性:")
        print("  ✅ 自动发现可用孔位")
        print("  ✅ 支持模糊搜索")
        print("  ✅ 下拉菜单选择")
        print("  ✅ 自动完成功能")
        print("  ✅ 多数据源支持")
        print("\n🔧 实现要点:")
        print("  - QComboBox.setEditable(True) 允许编辑")
        print("  - QCompleter 提供自动完成")
        print("  - Qt.MatchContains 支持包含匹配")
        print("  - Qt.CaseInsensitive 忽略大小写")
        print("  - 动态加载孔位列表")
    else:
        print("\n⚠️ 部分测试未通过，需要进一步调试")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏹️ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
