#!/usr/bin/env python3
"""
UI交互测试：DXF加载与UI集成
UI Interaction Tests: DXF Loading and UI Integration
"""

import unittest
import tempfile
import shutil
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 模拟Qt组件（避免Qt依赖）
class MockQKeyEvent:
    """模拟QKeyEvent"""
    def __init__(self, key, modifiers=0):
        self._key = key
        self._modifiers = modifiers
    
    def key(self):
        return self._key
    
    def modifiers(self):
        return self._modifiers

class MockQt:
    """模拟Qt常量"""
    Key_Escape = 16777216
    Key_A = 65
    Key_Delete = 16777223
    Key_Enter = 16777220
    Key_Return = 16777221
    ControlModifier = 67108864

class MockQToolTip:
    """模拟QToolTip"""
    @staticmethod
    def hideText():
        pass

# 模拟交互组件
class MockInteractionHandler:
    """模拟交互处理器"""
    
    def __init__(self):
        self.selected_holes = set()
        self.hovered_hole = None
        self.tooltip_timer = Mock()
        self.dxf_integration = None
        
        # 回调函数
        self.selection_changed_callback = None
        self.navigation_callback = None
        
    def set_dxf_integration(self, integration_adapter):
        """设置DXF集成适配器"""
        self.dxf_integration = integration_adapter
    
    def set_callbacks(self, selection_changed=None, navigation=None):
        """设置回调函数"""
        self.selection_changed_callback = selection_changed
        self.navigation_callback = navigation
    
    def _clear_hover(self):
        """清除悬停状态"""
        self.hovered_hole = None
    
    def _clear_selection(self):
        """清除选择"""
        self.selected_holes.clear()
        if self.selection_changed_callback:
            self.selection_changed_callback(list(self.selected_holes))
    
    def _select_all(self):
        """全选"""
        if self.dxf_integration:
            try:
                hole_list = self.dxf_integration.get_hole_list()
                self.selected_holes = {hole["hole_id"] for hole in hole_list}
                if self.selection_changed_callback:
                    self.selection_changed_callback(list(self.selected_holes))
            except Exception as e:
                # 优雅处理错误，不抛出异常
                print(f"全选操作失败: {e}")
                self.selected_holes.clear()
                if self.selection_changed_callback:
                    self.selection_changed_callback([])
    
    def _delete_selected(self):
        """删除选择（标记为删除状态）"""
        if self.dxf_integration:
            for hole_id in self.selected_holes:
                self.dxf_integration.update_hole_status_ui(hole_id, "deleted", "用户删除")
    
    def _navigate_to_realtime(self, hole_id):
        """导航到实时监控"""
        if self.dxf_integration and self.navigation_callback:
            result = self.dxf_integration.navigate_to_realtime(hole_id)
            self.navigation_callback(hole_id, result)
            return result
        return {"success": False, "error": "未设置集成适配器"}
    
    def select_hole(self, hole_id):
        """选择孔位"""
        self.selected_holes.add(hole_id)
        if self.selection_changed_callback:
            self.selection_changed_callback(list(self.selected_holes))
    
    def hover_hole(self, hole_id):
        """悬停孔位"""
        self.hovered_hole = hole_id
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        self._clear_hover()
        MockQToolTip.hideText()
        self.tooltip_timer.stop()
    
    def keyPressEvent(self, event):
        """键盘按下事件"""
        if event.key() == MockQt.Key_Escape:
            # ESC键清除选择
            self._clear_selection()
        elif event.key() == MockQt.Key_A and event.modifiers() & MockQt.ControlModifier:
            # Ctrl+A全选
            self._select_all()
        elif event.key() == MockQt.Key_Delete:
            # Delete键删除选择
            self._delete_selected()
        elif event.key() in [MockQt.Key_Enter, MockQt.Key_Return]:
            # Enter键导航到实时监控
            if len(self.selected_holes) == 1:
                hole_id = list(self.selected_holes)[0]
                return self._navigate_to_realtime(hole_id)
        
        return {"handled": True}


class TestDXFUIIntegration(unittest.TestCase):
    """DXF UI集成测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp(prefix="test_ui_integration_")
        
        # 创建模拟UI适配器
        self.mock_ui_adapter = self._create_mock_ui_adapter()
        
        # 创建交互处理器
        self.interaction_handler = MockInteractionHandler()
        self.interaction_handler.set_dxf_integration(self.mock_ui_adapter)
        
        # 设置回调
        self.selection_events = []
        self.navigation_events = []
        
        def on_selection_changed(selected_holes):
            self.selection_events.append(("selection_changed", selected_holes))
        
        def on_navigation(hole_id, result):
            self.navigation_events.append(("navigation", hole_id, result))
        
        self.interaction_handler.set_callbacks(
            selection_changed=on_selection_changed,
            navigation=on_navigation
        )
    
    def tearDown(self):
        """测试后清理"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def _create_mock_ui_adapter(self):
        """创建模拟UI适配器"""
        adapter = Mock()
        
        # 模拟孔位列表
        hole_list = [
            {"hole_id": "H00001", "position": {"x": 10.0, "y": 20.0}, "status": "pending"},
            {"hole_id": "H00002", "position": {"x": 30.0, "y": 40.0}, "status": "pending"},
            {"hole_id": "H00003", "position": {"x": 50.0, "y": 60.0}, "status": "pending"},
            {"hole_id": "H00004", "position": {"x": 70.0, "y": 80.0}, "status": "pending"},
            {"hole_id": "H00005", "position": {"x": 90.0, "y": 100.0}, "status": "pending"}
        ]
        
        adapter.get_hole_list.return_value = hole_list
        adapter.update_hole_status_ui.return_value = True
        adapter.navigate_to_realtime.return_value = {"success": True, "hole_id": "H00001"}
        
        return adapter
    
    def test_keyboard_escape_clear_selection(self):
        """测试ESC键清除选择"""
        print("\n🔧 测试ESC键清除选择")
        
        # 先选择一些孔位
        self.interaction_handler.select_hole("H00001")
        self.interaction_handler.select_hole("H00002")
        
        self.assertEqual(len(self.interaction_handler.selected_holes), 2)
        
        # 按ESC键
        event = MockQKeyEvent(MockQt.Key_Escape)
        self.interaction_handler.keyPressEvent(event)
        
        # 验证选择被清除
        self.assertEqual(len(self.interaction_handler.selected_holes), 0)
        
        # 验证回调被调用
        self.assertGreater(len(self.selection_events), 0)
        last_event = self.selection_events[-1]
        self.assertEqual(last_event[0], "selection_changed")
        self.assertEqual(last_event[1], [])
        
        print("   ✅ ESC键清除选择功能正常")
    
    def test_keyboard_ctrl_a_select_all(self):
        """测试Ctrl+A全选"""
        print("\n🔧 测试Ctrl+A全选")
        
        # 按Ctrl+A
        event = MockQKeyEvent(MockQt.Key_A, MockQt.ControlModifier)
        self.interaction_handler.keyPressEvent(event)
        
        # 验证所有孔位被选择
        self.assertEqual(len(self.interaction_handler.selected_holes), 5)
        
        expected_holes = {"H00001", "H00002", "H00003", "H00004", "H00005"}
        self.assertEqual(self.interaction_handler.selected_holes, expected_holes)
        
        # 验证回调被调用
        self.assertGreater(len(self.selection_events), 0)
        last_event = self.selection_events[-1]
        self.assertEqual(last_event[0], "selection_changed")
        self.assertEqual(set(last_event[1]), expected_holes)
        
        print("   ✅ Ctrl+A全选功能正常")
    
    def test_keyboard_delete_selected(self):
        """测试Delete键删除选择"""
        print("\n🔧 测试Delete键删除选择")
        
        # 先选择一些孔位
        self.interaction_handler.select_hole("H00001")
        self.interaction_handler.select_hole("H00003")
        
        # 按Delete键
        event = MockQKeyEvent(MockQt.Key_Delete)
        self.interaction_handler.keyPressEvent(event)
        
        # 验证状态更新被调用
        self.mock_ui_adapter.update_hole_status_ui.assert_any_call("H00001", "deleted", "用户删除")
        self.mock_ui_adapter.update_hole_status_ui.assert_any_call("H00003", "deleted", "用户删除")
        
        print("   ✅ Delete键删除功能正常")
    
    def test_keyboard_enter_navigation(self):
        """测试Enter键导航"""
        print("\n🔧 测试Enter键导航")
        
        # 选择单个孔位
        self.interaction_handler.select_hole("H00001")
        
        # 按Enter键
        event = MockQKeyEvent(MockQt.Key_Enter)
        result = self.interaction_handler.keyPressEvent(event)
        
        # 验证导航被调用
        self.mock_ui_adapter.navigate_to_realtime.assert_called_once_with("H00001")
        
        # 验证导航回调
        self.assertGreater(len(self.navigation_events), 0)
        nav_event = self.navigation_events[-1]
        self.assertEqual(nav_event[0], "navigation")
        self.assertEqual(nav_event[1], "H00001")
        self.assertTrue(nav_event[2]["success"])
        
        print("   ✅ Enter键导航功能正常")
    
    def test_mouse_leave_event(self):
        """测试鼠标离开事件"""
        print("\n🔧 测试鼠标离开事件")
        
        # 设置悬停状态
        self.interaction_handler.hover_hole("H00002")
        self.assertEqual(self.interaction_handler.hovered_hole, "H00002")
        
        # 触发鼠标离开事件
        event = Mock()
        self.interaction_handler.leaveEvent(event)
        
        # 验证悬停状态被清除
        self.assertIsNone(self.interaction_handler.hovered_hole)
        
        # 验证定时器被停止
        self.interaction_handler.tooltip_timer.stop.assert_called_once()
        
        print("   ✅ 鼠标离开事件处理正常")
    
    def test_complex_interaction_workflow(self):
        """测试复杂交互工作流"""
        print("\n🔧 测试复杂交互工作流")
        
        # 1. 全选
        event = MockQKeyEvent(MockQt.Key_A, MockQt.ControlModifier)
        self.interaction_handler.keyPressEvent(event)
        self.assertEqual(len(self.interaction_handler.selected_holes), 5)
        print("   ✅ 步骤1：全选完成")
        
        # 2. 清除选择
        event = MockQKeyEvent(MockQt.Key_Escape)
        self.interaction_handler.keyPressEvent(event)
        self.assertEqual(len(self.interaction_handler.selected_holes), 0)
        print("   ✅ 步骤2：清除选择完成")
        
        # 3. 手动选择两个孔位
        self.interaction_handler.select_hole("H00001")
        self.interaction_handler.select_hole("H00003")
        self.assertEqual(len(self.interaction_handler.selected_holes), 2)
        print("   ✅ 步骤3：手动选择完成")
        
        # 4. 删除选择的孔位
        event = MockQKeyEvent(MockQt.Key_Delete)
        self.interaction_handler.keyPressEvent(event)
        print("   ✅ 步骤4：删除操作完成")
        
        # 5. 选择单个孔位并导航
        self.interaction_handler._clear_selection()
        self.interaction_handler.select_hole("H00002")
        event = MockQKeyEvent(MockQt.Key_Enter)
        self.interaction_handler.keyPressEvent(event)
        print("   ✅ 步骤5：导航操作完成")
        
        # 验证整个工作流的事件序列
        self.assertGreater(len(self.selection_events), 4)  # 至少4次选择变更
        self.assertGreater(len(self.navigation_events), 0)  # 至少1次导航
        
        print("   ✅ 复杂交互工作流验证通过")
    
    def test_error_handling_in_interactions(self):
        """测试交互中的错误处理"""
        print("\n🔧 测试交互错误处理")
        
        # 创建会失败的适配器
        failing_adapter = Mock()
        failing_adapter.get_hole_list.side_effect = Exception("获取孔位列表失败")
        failing_adapter.navigate_to_realtime.return_value = {"success": False, "error": "导航失败"}
        
        # 设置失败的适配器
        self.interaction_handler.set_dxf_integration(failing_adapter)
        
        # 测试全选时的错误处理
        try:
            event = MockQKeyEvent(MockQt.Key_A, MockQt.ControlModifier)
            self.interaction_handler.keyPressEvent(event)
            # 应该不会崩溃，但选择应该为空
            self.assertEqual(len(self.interaction_handler.selected_holes), 0)
            print("   ✅ 全选错误处理正常")
        except Exception as e:
            self.fail(f"全选错误处理失败: {e}")
        
        # 测试导航失败的处理
        self.interaction_handler.select_hole("H00001")
        event = MockQKeyEvent(MockQt.Key_Enter)
        result = self.interaction_handler.keyPressEvent(event)
        
        # 验证导航失败被正确处理
        if len(self.navigation_events) > 0:
            nav_event = self.navigation_events[-1]
            self.assertFalse(nav_event[2]["success"])
        
        print("   ✅ 导航错误处理正常")


if __name__ == '__main__':
    unittest.main(verbosity=2)
