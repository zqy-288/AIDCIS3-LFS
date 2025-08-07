#!/usr/bin/env python3
"""
搜索功能完整数据流诊断工具
检查搜索框输入处理、搜索服务数据设置、业务协调器搜索方法和信号连接链路
"""

import sys
import logging
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 设置环境变量避免GUI问题
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

# 初始化Qt应用
import PySide6.QtWidgets as QtWidgets
app = QtWidgets.QApplication.instance()
if app is None:
    app = QtWidgets.QApplication([])

def diagnose_search_data_flow():
    """诊断搜索功能的完整数据流"""
    print("=" * 80)
    print("🔍 搜索功能完整数据流诊断")
    print("=" * 80)
    
    # 1. 检查搜索服务
    print("\n1️⃣ 检查搜索服务 (SearchService)")
    print("-" * 50)
    
    try:
        from src.shared.services.search_service import SearchService
        search_service = SearchService()
        print("✅ SearchService 导入成功")
        
        # 检查搜索服务基本功能
        print(f"   - 当前查询: '{search_service.current_query}'")
        print(f"   - 当前结果数量: {len(search_service.current_results)}")
        print(f"   - 孔位集合状态: {search_service._hole_collection is not None}")
        print(f"   - 搜索数据数量: {len(search_service._searchable_data)}")
        
        # 测试空搜索
        empty_results = search_service.search("")
        print(f"   - 空搜索结果: {len(empty_results)} 个")
        
        # 获取调试信息
        debug_info = search_service.debug_search_data()
        print(f"   - 调试信息: {debug_info}")
        
    except Exception as e:
        print(f"❌ SearchService 检查失败: {e}")
    
    # 2. 检查业务协调器
    print("\n2️⃣ 检查业务协调器 (BusinessCoordinator)")
    print("-" * 50)
    
    try:
        from src.shared.services.business_coordinator import get_business_coordinator
        coordinator = get_business_coordinator()
        print("✅ BusinessCoordinator 获取成功")
        
        # 检查搜索服务
        if coordinator._search_service:
            print("   - SearchService 已初始化")
            search_debug = coordinator._search_service.debug_search_data() 
            print(f"   - 搜索数据状态: {search_debug}")
        else:
            print("❌ SearchService 未初始化")
        
        # 检查search_holes方法
        if hasattr(coordinator, 'search_holes'):
            print("   - search_holes 方法存在")
            # 测试搜索
            test_results = coordinator.search_holes("test")
            print(f"   - 测试搜索结果: {len(test_results)} 个")
        else:
            print("❌ search_holes 方法不存在")
            
    except Exception as e:
        print(f"❌ BusinessCoordinator 检查失败: {e}")
    
    # 3. 检查控制器
    print("\n3️⃣ 检查控制器 (MainWindowController)")
    print("-" * 50)
    
    try:
        from src.pages.main_detection_p1.controllers.main_window_controller import MainWindowController
        controller = MainWindowController()
        print("✅ MainWindowController 导入成功")
        
        # 检查search_hole方法
        if hasattr(controller, 'search_hole'):
            print("   - search_hole 方法存在")
            
            # 检查业务协调器连接
            if hasattr(controller, 'business_coordinator') and controller.business_coordinator:
                print("   - BusinessCoordinator 已连接")
                # 测试搜索调用
                test_results = controller.search_hole("test")
                print(f"   - 测试搜索结果: {len(test_results)} 个")
            else:
                print("❌ BusinessCoordinator 未连接")
        else:
            print("❌ search_hole 方法不存在")
            
    except Exception as e:
        print(f"❌ MainWindowController 检查失败: {e}")
    
    # 4. 检查工具栏组件
    print("\n4️⃣ 检查工具栏组件 (ToolbarComponent)")
    print("-" * 50)
    
    try:
        from src.pages.main_detection_p1.ui.components.toolbar_component import ToolbarComponent as P1Toolbar
        print("✅ P1 ToolbarComponent 导入成功")
        
        # 检查信号
        toolbar = P1Toolbar()
        if hasattr(toolbar, 'search_requested'):
            print("   - search_requested 信号存在")
        else:
            print("❌ search_requested 信号不存在")
            
        if hasattr(toolbar, 'search_input'):
            print("   - search_input 输入框存在")
        else:
            print("❌ search_input 输入框不存在")
            
        if hasattr(toolbar, 'search_btn'):
            print("   - search_btn 按钮存在")
        else:
            print("❌ search_btn 按钮不存在")
            
    except Exception as e:
        print(f"❌ P1 ToolbarComponent 检查失败: {e}")
        
        # 尝试shared版本
        try:
            from src.shared.components.base_components.toolbar_component import ToolbarComponent as SharedToolbar
            print("✅ Shared ToolbarComponent 导入成功")
            
            toolbar = SharedToolbar()
            if hasattr(toolbar, 'search_requested'):
                print("   - search_requested 信号存在")
            else:
                print("❌ search_requested 信号不存在")
                
        except Exception as e2:
            print(f"❌ Shared ToolbarComponent 检查失败: {e2}")
    
    # 5. 检查主检测页面信号连接
    print("\n5️⃣ 检查主检测页面信号连接")
    print("-" * 50)
    
    try:
        from src.pages.main_detection_p1.main_detection_page import MainDetectionPage
        print("✅ MainDetectionPage 导入成功")
        
        # 检查_on_search_hole方法
        if hasattr(MainDetectionPage, '_on_search_hole'):
            print("   - _on_search_hole 方法存在")
        else:
            print("❌ _on_search_hole 方法不存在")
            
    except Exception as e:
        print(f"❌ MainDetectionPage 检查失败: {e}")
    
    # 6. 模拟完整搜索流程
    print("\n6️⃣ 模拟完整搜索流程")
    print("-" * 50)
    
    try:
        # 创建模拟孔位数据
        from src.shared.models.hole_data import HoleData, HoleCollection
        
        print("   - 创建模拟孔位数据...")
        holes = {}
        for i in range(10):
            hole = HoleData(
                hole_id=f"A{i+1}",
                center_x=i * 10,
                center_y=i * 5,
                radius=2.5
            )
            holes[hole.hole_id] = hole
        
        hole_collection = HoleCollection(holes)
        print(f"   - 创建了 {len(holes)} 个模拟孔位")
        
        # 设置搜索服务数据
        search_service = SearchService()
        search_service.set_hole_collection(hole_collection)
        print("   - 已设置搜索服务数据")
        
        # 测试搜索
        results_a1 = search_service.search("A1")
        results_a = search_service.search("A")
        results_1 = search_service.search("1")
        
        print(f"   - 搜索 'A1': {len(results_a1)} 个结果: {results_a1}")
        print(f"   - 搜索 'A': {len(results_a)} 个结果: {results_a[:5]}...")  # 只显示前5个
        print(f"   - 搜索 '1': {len(results_1)} 个结果: {results_1}")
        
        print("✅ 搜索功能基本正常")
        
    except Exception as e:
        print(f"❌ 模拟搜索流程失败: {e}")
    
    # 7. 检查数据同步问题
    print("\n7️⃣ 检查数据同步问题")
    print("-" * 50)
    
    try:
        # 检查业务协调器的孔位数据更新
        coordinator = get_business_coordinator()
        
        print("   - 检查业务协调器数据更新方法...")
        if hasattr(coordinator, 'update_search_data'):
            print("   - update_search_data 方法存在")
        else:
            print("❌ update_search_data 方法不存在")
            
        # 检查业务服务的孔位集合
        if hasattr(coordinator, 'business_service'):
            business_service = coordinator.business_service
            if hasattr(business_service, 'get_hole_collection'):
                print("   - business_service.get_hole_collection 方法存在")
                hole_collection = business_service.get_hole_collection()
                if hole_collection:
                    print(f"   - 当前孔位集合: {len(hole_collection.holes) if hasattr(hole_collection, 'holes') else '未知'} 个孔位")
                else:
                    print("   - 当前无孔位集合")
            else:
                print("❌ business_service.get_hole_collection 方法不存在")
        else:
            print("❌ business_service 不存在")
            
    except Exception as e:
        print(f"❌ 数据同步检查失败: {e}")
    
    # 8. 生成修复建议
    print("\n8️⃣ 修复建议")
    print("-" * 50)
    
    print("基于诊断结果，建议以下修复措施:")
    print()
    print("🔧 1. 确保孔位数据正确传递到搜索服务")
    print("   - 在加载DXF文件后，调用 coordinator.update_search_data()")
    print("   - 在产品选择后，确保孔位数据同步到搜索服务")
    print()
    print("🔧 2. 验证工具栏信号连接")
    print("   - 确保 toolbar.search_requested 信号正确连接到处理方法")
    print("   - 检查 MainDetectionPage._on_search_hole 方法实现")
    print()
    print("🔧 3. 增强搜索服务调试信息")
    print("   - 在搜索前输出可搜索数据状态")
    print("   - 记录搜索请求和结果")
    print()
    print("🔧 4. 添加搜索结果高亮显示")
    print("   - 在找到搜索结果时，自动切换到相应视图")
    print("   - 高亮显示匹配的孔位")
    
    print("\n" + "=" * 80)
    print("🎯 诊断完成")
    print("=" * 80)

if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    diagnose_search_data_flow()