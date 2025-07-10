#!/usr/bin/env python3
"""
UI同步问题诊断脚本
"""

import sys
import time
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def diagnose_ui_components():
    """诊断UI组件状态"""
    print("🔍 UI组件诊断")
    print("=" * 60)
    
    try:
        from main_window import MainWindow
        from PySide6.QtWidgets import QApplication
        
        # 创建应用和窗口
        if not QApplication.instance():
            app = QApplication([])
        else:
            app = QApplication.instance()
        
        window = MainWindow()
        
        print("✅ 主窗口创建成功")
        
        # 检查UI标签组件
        ui_components = [
            ('selected_hole_id_label', window.selected_hole_id_label),
            ('selected_hole_position_label', window.selected_hole_position_label),
            ('selected_hole_status_label', window.selected_hole_status_label),
            ('selected_hole_radius_label', window.selected_hole_radius_label)
        ]
        
        print("\n📋 UI标签组件检查:")
        for name, component in ui_components:
            if component is not None:
                current_text = component.text()
                print(f"✅ {name}: 存在, 当前文本='{current_text}'")
            else:
                print(f"❌ {name}: 不存在")
                return False
        
        # 检查按钮组件
        button_components = [
            ('goto_realtime_btn', window.goto_realtime_btn),
            ('goto_history_btn', window.goto_history_btn),
            ('mark_defective_btn', window.mark_defective_btn)
        ]
        
        print("\n🎮 按钮组件检查:")
        for name, component in button_components:
            if component is not None:
                enabled = component.isEnabled()
                tooltip = component.toolTip()
                print(f"✅ {name}: 存在, 启用={enabled}, 工具提示='{tooltip}'")
            else:
                print(f"❌ {name}: 不存在")
                return False
        
        return window
        
    except Exception as e:
        print(f"❌ UI组件诊断失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")
        return None

def test_ui_update_manually(window):
    """手动测试UI更新"""
    print("\n🧪 手动UI更新测试")
    print("=" * 60)
    
    try:
        from aidcis2.models.hole_data import HoleData, HoleStatus
        
        # 创建测试孔位
        test_hole = HoleData('H00001', 100.0, 200.0, 5.0, HoleStatus.PENDING)
        
        print(f"📝 创建测试孔位: {test_hole.hole_id}")
        
        # 设置选中孔位
        window.selected_hole = test_hole
        print(f"📝 设置selected_hole: {window.selected_hole.hole_id if window.selected_hole else 'None'}")
        
        # 手动调用UI更新
        print("🔄 调用update_hole_info_display()...")
        window.update_hole_info_display()
        
        # 检查更新结果
        print("\n📊 更新后的UI状态:")
        ui_results = [
            ('ID标签', window.selected_hole_id_label.text()),
            ('位置标签', window.selected_hole_position_label.text()),
            ('状态标签', window.selected_hole_status_label.text()),
            ('半径标签', window.selected_hole_radius_label.text())
        ]
        
        for name, text in ui_results:
            print(f"  {name}: '{text}'")
        
        # 验证是否更新成功
        id_updated = 'H00001' in window.selected_hole_id_label.text()
        position_updated = '100.0' in window.selected_hole_position_label.text()
        status_updated = 'PENDING' in window.selected_hole_status_label.text()
        radius_updated = '5.000' in window.selected_hole_radius_label.text()
        
        print(f"\n✅ 更新验证:")
        print(f"  ID更新: {id_updated}")
        print(f"  位置更新: {position_updated}")
        print(f"  状态更新: {status_updated}")
        print(f"  半径更新: {radius_updated}")
        
        return all([id_updated, position_updated, status_updated, radius_updated])
        
    except Exception as e:
        print(f"❌ 手动UI更新测试失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")
        return False

def test_search_workflow(window):
    """测试搜索工作流"""
    print("\n🔍 搜索工作流测试")
    print("=" * 60)
    
    try:
        # 创建模拟孔位集合
        from aidcis2.models.hole_data import HoleData, HoleStatus
        from unittest.mock import Mock
        
        test_holes = {
            'H00001': HoleData('H00001', 100.0, 200.0, 5.0, HoleStatus.PENDING),
            'H00002': HoleData('H00002', 150.0, 250.0, 5.5, HoleStatus.QUALIFIED),
            'H00003': HoleData('H00003', 200.0, 300.0, 4.8, HoleStatus.DEFECTIVE)
        }
        
        # 设置模拟孔位集合
        mock_collection = Mock()
        mock_collection.holes = test_holes
        mock_collection.__len__ = Mock(return_value=len(test_holes))
        window.hole_collection = mock_collection
        
        # 模拟图形视图
        window.graphics_view = Mock()
        window.graphics_view.highlight_holes = Mock()
        window.graphics_view.clear_search_highlight = Mock()
        
        print("✅ 模拟数据设置完成")
        
        # 测试搜索H00001
        print("\n🔍 测试搜索H00001:")
        window.search_input.setText('H00001')
        print(f"  搜索框文本: '{window.search_input.text()}'")
        
        # 执行搜索
        window.perform_search()
        
        # 检查结果
        print(f"  选中孔位: {window.selected_hole.hole_id if window.selected_hole else 'None'}")
        
        if window.selected_hole:
            print(f"  ID标签: '{window.selected_hole_id_label.text()}'")
            print(f"  位置标签: '{window.selected_hole_position_label.text()}'")
            print(f"  状态标签: '{window.selected_hole_status_label.text()}'")
            print(f"  半径标签: '{window.selected_hole_radius_label.text()}'")
            
            # 检查按钮状态
            print(f"  实时监控按钮启用: {window.goto_realtime_btn.isEnabled()}")
            print(f"  历史数据按钮启用: {window.goto_history_btn.isEnabled()}")
            
            return True
        else:
            print("❌ 搜索后未选中孔位")
            return False
            
    except Exception as e:
        print(f"❌ 搜索工作流测试失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")
        return False

def test_right_click_workflow(window):
    """测试右键选择工作流"""
    print("\n🎯 右键选择工作流测试")
    print("=" * 60)
    
    try:
        from aidcis2.models.hole_data import HoleData, HoleStatus
        
        # 创建测试孔位
        test_hole = HoleData('H00002', 150.0, 250.0, 5.5, HoleStatus.QUALIFIED)
        
        print(f"🎯 模拟右键选择: {test_hole.hole_id}")
        
        # 调用右键选择处理
        window.on_hole_selected(test_hole)
        
        # 检查结果
        print(f"  选中孔位: {window.selected_hole.hole_id if window.selected_hole else 'None'}")
        
        if window.selected_hole:
            print(f"  ID标签: '{window.selected_hole_id_label.text()}'")
            print(f"  位置标签: '{window.selected_hole_position_label.text()}'")
            print(f"  状态标签: '{window.selected_hole_status_label.text()}'")
            print(f"  半径标签: '{window.selected_hole_radius_label.text()}'")
            
            # 检查按钮状态
            print(f"  实时监控按钮启用: {window.goto_realtime_btn.isEnabled()}")
            print(f"  历史数据按钮启用: {window.goto_history_btn.isEnabled()}")
            
            return True
        else:
            print("❌ 右键选择后未选中孔位")
            return False
            
    except Exception as e:
        print(f"❌ 右键选择工作流测试失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")
        return False

def provide_solutions():
    """提供解决方案"""
    print("\n💡 解决方案")
    print("=" * 60)
    
    print("如果UI仍然不同步，请尝试以下方法:")
    print()
    print("1. 🔄 强制UI刷新:")
    print("   在update_hole_info_display()方法末尾添加:")
    print("   self.update()  # 刷新整个窗口")
    print("   QApplication.processEvents()  # 处理事件队列")
    print()
    print("2. 🎯 检查Qt信号连接:")
    print("   确认graphics_view.hole_clicked信号正确连接到on_hole_selected")
    print()
    print("3. 📝 添加更多调试信息:")
    print("   在关键位置添加print()语句追踪执行流程")
    print()
    print("4. 🔧 检查UI线程:")
    print("   确保UI更新在主线程中执行")
    print()
    print("5. 🖥️ 检查UI布局:")
    print("   确认标签在正确的布局容器中")

def main():
    """主函数"""
    print("🔍 UI同步问题诊断")
    print("=" * 60)
    
    # 1. 诊断UI组件
    window = diagnose_ui_components()
    if not window:
        print("❌ UI组件诊断失败，无法继续")
        return False
    
    # 2. 手动测试UI更新
    manual_success = test_ui_update_manually(window)
    print(f"\n📊 手动UI更新: {'✅ 成功' if manual_success else '❌ 失败'}")
    
    # 3. 测试搜索工作流
    search_success = test_search_workflow(window)
    print(f"📊 搜索工作流: {'✅ 成功' if search_success else '❌ 失败'}")
    
    # 4. 测试右键选择工作流
    click_success = test_right_click_workflow(window)
    print(f"📊 右键选择工作流: {'✅ 成功' if click_success else '❌ 失败'}")
    
    # 5. 总结
    all_success = manual_success and search_success and click_success
    
    print(f"\n🎯 总体诊断结果: {'✅ 所有功能正常' if all_success else '❌ 存在问题'}")
    
    if not all_success:
        provide_solutions()
    
    return all_success

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n🎉 UI同步功能正常！")
        print("如果在实际使用中仍有问题，请检查DXF文件加载和数据设置。")
    else:
        print("\n💥 发现UI同步问题！")
        print("请根据上述解决方案进行修复。")
