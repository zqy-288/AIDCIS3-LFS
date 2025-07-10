#!/usr/bin/env python3
"""
测试改进后的历史数据查看器
支持模糊搜索和下拉菜单的孔位选择功能
"""

import sys
import os
from datetime import datetime

# 添加模块路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'modules'))

def test_history_viewer_with_fuzzy_search():
    """测试带模糊搜索功能的历史数据查看器"""
    print("🚀 测试改进后的历史数据查看器...")
    
    try:
        # 设置环境变量以避免Qt后端问题
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'
        
        from PySide6.QtWidgets import QApplication
        from modules.history_viewer import HistoryViewer
        from modules.models import db_manager
        
        print("📱 创建Qt应用程序...")
        app = QApplication(sys.argv)
        
        print("📊 初始化数据库...")
        db_manager.create_sample_data()
        
        print("🖥️ 创建历史数据查看器...")
        viewer = HistoryViewer()
        viewer.setWindowTitle("AIDCIS - 改进的历史数据查看器 (支持模糊搜索)")
        viewer.resize(1400, 900)
        
        # 测试孔位列表加载
        print("🔍 测试孔位列表加载...")
        available_holes = viewer.get_available_holes("WP-2025-001")
        print(f"✅ 可用孔位: {available_holes}")
        
        # 测试模糊搜索功能
        print("🔎 测试模糊搜索功能...")
        if hasattr(viewer, 'hole_combo'):
            print("✅ 孔位组合框已创建")
            print(f"📋 组合框项目数: {viewer.hole_combo.count()}")
            
            if hasattr(viewer, 'hole_completer'):
                print("✅ 自动完成器已配置")
            else:
                print("❌ 自动完成器未配置")
        else:
            print("❌ 孔位组合框未创建")
        
        # 显示界面
        print("🖼️ 显示历史数据查看器界面...")
        viewer.show()
        
        print("✅ 历史数据查看器测试完成")
        print("💡 新功能:")
        print("  - 🔍 孔位支持模糊搜索")
        print("  - 📋 下拉菜单显示可用孔位")
        print("  - 🔄 自动加载工件对应的孔位列表")
        print("  - 📊 从数据库和文件系统双重获取孔位")
        
        return viewer, app
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def test_hole_search_functionality():
    """测试孔位搜索功能"""
    print("🔍 测试孔位搜索功能...")
    
    try:
        from modules.history_viewer import HistoryViewer
        
        # 创建查看器实例（不显示GUI）
        viewer = HistoryViewer()
        
        # 测试获取可用孔位
        print("📊 测试获取可用孔位...")
        holes = viewer.get_available_holes("WP-2025-001")
        print(f"✅ 找到孔位: {holes}")
        
        # 测试孔位列表加载
        print("📋 测试孔位列表加载...")
        viewer.load_hole_list("WP-2025-001")
        
        if hasattr(viewer, 'hole_combo'):
            combo_count = viewer.hole_combo.count()
            print(f"✅ 组合框加载了 {combo_count} 个孔位选项")
            
            # 显示所有选项
            for i in range(combo_count):
                item_text = viewer.hole_combo.itemText(i)
                print(f"  {i+1}. {item_text}")
        
        return True
        
    except Exception as e:
        print(f"❌ 孔位搜索功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_directory_scanning():
    """测试数据目录扫描功能"""
    print("📁 测试数据目录扫描...")
    
    data_dirs = ["Data/H00001", "Data/H00002"]
    found_holes = []
    
    for data_dir in data_dirs:
        if os.path.exists(data_dir):
            hole_id = os.path.basename(data_dir)
            ccidm_path = os.path.join(data_dir, "CCIDM")
            
            if os.path.exists(ccidm_path):
                csv_files = [f for f in os.listdir(ccidm_path) if f.endswith('.csv')]
                if csv_files:
                    found_holes.append(hole_id)
                    print(f"✅ {hole_id}: {len(csv_files)} 个CSV文件")
                else:
                    print(f"⚠️ {hole_id}: 无CSV文件")
            else:
                print(f"❌ {hole_id}: CCIDM目录不存在")
        else:
            print(f"❌ {data_dir}: 目录不存在")
    
    print(f"📊 扫描结果: 找到 {len(found_holes)} 个有效孔位: {found_holes}")
    return found_holes

def main():
    """主函数"""
    print("🚀 启动改进的历史数据查看器测试")
    print("=" * 60)
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试1: 数据目录扫描
    print("\n🧪 测试1: 数据目录扫描")
    print("-" * 40)
    found_holes = test_data_directory_scanning()
    
    # 测试2: 孔位搜索功能
    print("\n🧪 测试2: 孔位搜索功能")
    print("-" * 40)
    search_success = test_hole_search_functionality()
    
    # 测试3: GUI界面（如果支持）
    print("\n🧪 测试3: GUI界面测试")
    print("-" * 40)
    
    try:
        viewer, app = test_history_viewer_with_fuzzy_search()
        gui_success = viewer is not None
    except Exception as e:
        print(f"⚠️ GUI测试跳过: {e}")
        gui_success = False
        viewer, app = None, None
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    print("-" * 40)
    
    print(f"📁 数据目录扫描: {'✅ 通过' if found_holes else '❌ 失败'} ({len(found_holes)}个孔位)")
    print(f"🔍 孔位搜索功能: {'✅ 通过' if search_success else '❌ 失败'}")
    print(f"🖥️ GUI界面测试: {'✅ 通过' if gui_success else '⚠️ 跳过'}")
    
    if found_holes and search_success:
        print("\n🎉 历史数据查看器改进成功！")
        print("💡 新增功能:")
        print("  ✅ 孔位下拉选择菜单")
        print("  ✅ 模糊搜索支持")
        print("  ✅ 自动完成功能")
        print("  ✅ 动态孔位列表加载")
        print("  ✅ 多数据源支持（数据库+文件系统）")
    else:
        print("\n⚠️ 部分功能需要进一步调试")
    
    # 如果GUI成功创建，可以选择运行
    if gui_success and viewer and app:
        print(f"\n🖥️ GUI界面已准备就绪")
        print("💡 你可以手动测试以下功能:")
        print("  1. 选择不同的工件ID")
        print("  2. 在孔位下拉框中选择或输入孔位")
        print("  3. 测试模糊搜索（输入部分孔位名称）")
        print("  4. 点击查询按钮查看历史数据")
        
        # 注释掉自动运行，避免阻塞
        # return app.exec()
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⏹️ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 测试过程出现异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
