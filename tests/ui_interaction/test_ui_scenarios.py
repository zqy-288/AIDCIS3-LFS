#!/usr/bin/env python3
"""
UI场景测试：真实用户场景模拟
UI Scenario Tests: Real User Scenario Simulation
"""

import unittest
import time
import sys
import os
from pathlib import Path
from unittest.mock import Mock

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入测试基础组件
from test_dxf_ui_integration import MockInteractionHandler, MockQKeyEvent, MockQt


class TestUIScenarios(unittest.TestCase):
    """UI场景测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.interaction_handler = MockInteractionHandler()
        
        # 创建真实场景适配器
        self.scenario_adapter = self._create_scenario_adapter()
        self.interaction_handler.set_dxf_integration(self.scenario_adapter)
        
        # 场景记录
        self.scenario_logs = []
        
        # 设置回调记录
        def log_selection(selected_holes):
            self.scenario_logs.append(f"选择变更: {len(selected_holes)} 个孔位")
        
        def log_navigation(hole_id, result):
            status = "成功" if result.get("success") else "失败"
            self.scenario_logs.append(f"导航到 {hole_id}: {status}")
        
        self.interaction_handler.set_callbacks(
            selection_changed=log_selection,
            navigation=log_navigation
        )
    
    def _create_scenario_adapter(self):
        """创建场景适配器"""
        adapter = Mock()
        
        # 模拟真实项目的孔位分布
        holes = []
        
        # 区域A：密集分布 (50个孔位)
        for i in range(50):
            hole = {
                "hole_id": f"A{i+1:03d}",
                "position": {"x": float(i % 10) * 5, "y": float(i // 10) * 5},
                "status": "pending",
                "region": "A"
            }
            holes.append(hole)
        
        # 区域B：稀疏分布 (20个孔位)
        for i in range(20):
            hole = {
                "hole_id": f"B{i+1:03d}",
                "position": {"x": float(i % 5) * 20 + 100, "y": float(i // 5) * 20 + 100},
                "status": "pending",
                "region": "B"
            }
            holes.append(hole)
        
        # 区域C：线性分布 (30个孔位)
        for i in range(30):
            hole = {
                "hole_id": f"C{i+1:03d}",
                "position": {"x": float(i) * 3, "y": 200.0},
                "status": "pending",
                "region": "C"
            }
            holes.append(hole)
        
        adapter.get_hole_list.return_value = holes
        adapter.update_hole_status_ui.return_value = True
        
        # 模拟导航成功率（90%）
        def mock_navigate(hole_id):
            import random
            success = random.random() < 0.9  # 90% 成功率
            return {"success": success, "hole_id": hole_id}
        
        adapter.navigate_to_realtime.side_effect = mock_navigate
        
        return adapter
    
    def _log_scenario_step(self, step_name, details=""):
        """记录场景步骤"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {step_name}"
        if details:
            log_entry += f": {details}"
        self.scenario_logs.append(log_entry)
        print(f"   {log_entry}")
    
    def test_typical_inspection_workflow(self):
        """测试典型检测工作流场景"""
        print("\n🔍 场景1：典型检测工作流")
        
        self._log_scenario_step("开始检测工作流")
        
        # 1. 用户加载DXF文件后，查看所有孔位
        self._log_scenario_step("查看项目概况")
        hole_list = self.scenario_adapter.get_hole_list()
        total_holes = len(hole_list)
        self._log_scenario_step("项目信息", f"共 {total_holes} 个孔位")
        
        # 2. 全选查看整体分布
        self._log_scenario_step("全选查看分布")
        event = MockQKeyEvent(MockQt.Key_A, MockQt.ControlModifier)
        self.interaction_handler.keyPressEvent(event)
        self.assertEqual(len(self.interaction_handler.selected_holes), total_holes)
        
        # 3. 清除选择，开始区域检测
        self._log_scenario_step("清除选择，准备区域检测")
        clear_event = MockQKeyEvent(MockQt.Key_Escape)
        self.interaction_handler.keyPressEvent(clear_event)
        
        # 4. 选择区域A的孔位进行检测
        self._log_scenario_step("选择区域A孔位")
        region_a_holes = [h["hole_id"] for h in hole_list if h["region"] == "A"]
        for hole_id in region_a_holes[:5]:  # 选择前5个
            self.interaction_handler.select_hole(hole_id)
        
        # 5. 逐个检测选中的孔位
        self._log_scenario_step("开始逐个检测")
        detection_results = []
        
        for hole_id in list(self.interaction_handler.selected_holes):
            # 清除其他选择，只选择当前孔位
            self.interaction_handler._clear_selection()
            self.interaction_handler.select_hole(hole_id)
            
            # 导航到实时监控
            nav_event = MockQKeyEvent(MockQt.Key_Enter)
            result = self.interaction_handler.keyPressEvent(event)
            
            # 模拟检测结果
            detection_success = self.scenario_adapter.navigate_to_realtime(hole_id)["success"]
            detection_results.append((hole_id, detection_success))
            
            if detection_success:
                self._log_scenario_step("检测完成", f"{hole_id} 成功")
            else:
                self._log_scenario_step("检测失败", f"{hole_id} 需要重试")
        
        # 6. 统计检测结果
        successful_detections = sum(1 for _, success in detection_results if success)
        success_rate = successful_detections / len(detection_results) * 100
        
        self._log_scenario_step("检测统计", f"{successful_detections}/{len(detection_results)} 成功 ({success_rate:.1f}%)")
        
        # 验证工作流完整性
        self.assertGreater(len(self.scenario_logs), 10, "工作流步骤不够完整")
        self.assertGreater(success_rate, 70, "检测成功率过低")
        
        print(f"   ✅ 典型检测工作流完成，成功率: {success_rate:.1f}%")
    
    def test_error_recovery_scenario(self):
        """测试错误恢复场景"""
        print("\n🚨 场景2：错误恢复场景")
        
        self._log_scenario_step("开始错误恢复测试")
        
        # 1. 模拟系统错误：适配器失效
        self._log_scenario_step("模拟系统错误")
        failing_adapter = Mock()
        failing_adapter.get_hole_list.side_effect = Exception("系统错误：数据库连接失败")
        failing_adapter.navigate_to_realtime.return_value = {"success": False, "error": "连接超时"}
        
        # 2. 用户尝试全选（应该失败但不崩溃）
        self._log_scenario_step("尝试全选操作")
        self.interaction_handler.set_dxf_integration(failing_adapter)
        
        try:
            event = MockQKeyEvent(MockQt.Key_A, MockQt.ControlModifier)
            self.interaction_handler.keyPressEvent(event)
            self._log_scenario_step("全选操作", "系统错误但未崩溃")
        except Exception as e:
            self._log_scenario_step("全选操作", f"异常: {e}")
        
        # 3. 恢复正常适配器
        self._log_scenario_step("恢复系统连接")
        self.interaction_handler.set_dxf_integration(self.scenario_adapter)
        
        # 4. 验证系统恢复
        self._log_scenario_step("验证系统恢复")
        event = MockQKeyEvent(MockQt.Key_A, MockQt.ControlModifier)
        self.interaction_handler.keyPressEvent(event)
        
        hole_count = len(self.interaction_handler.selected_holes)
        if hole_count > 0:
            self._log_scenario_step("系统恢复", f"成功选择 {hole_count} 个孔位")
        else:
            self._log_scenario_step("系统恢复", "失败")
        
        # 验证恢复效果
        self.assertGreater(hole_count, 0, "系统未能正确恢复")
        
        print("   ✅ 错误恢复场景测试通过")
    
    def test_high_frequency_operation_scenario(self):
        """测试高频操作场景"""
        print("\n⚡ 场景3：高频操作场景")
        
        self._log_scenario_step("开始高频操作测试")
        
        # 模拟用户快速操作：频繁选择和清除
        operation_count = 50
        start_time = time.time()
        
        for i in range(operation_count):
            # 快速全选和清除
            select_event = MockQKeyEvent(MockQt.Key_A, MockQt.ControlModifier)
            self.interaction_handler.keyPressEvent(select_event)
            
            clear_event = MockQKeyEvent(MockQt.Key_Escape)
            self.interaction_handler.keyPressEvent(clear_event)
            
            if i % 10 == 0:
                self._log_scenario_step("高频操作进度", f"{i}/{operation_count}")
        
        total_time = time.time() - start_time
        avg_time = total_time / operation_count
        
        self._log_scenario_step("高频操作完成", f"{operation_count}次操作，耗时{total_time:.2f}秒")
        self._log_scenario_step("平均操作时间", f"{avg_time*1000:.2f}毫秒/次")
        
        # 性能验证
        self.assertLess(avg_time, 0.1, "高频操作平均时间过长")
        self.assertLess(total_time, 5.0, "高频操作总时间过长")
        
        print(f"   ✅ 高频操作场景测试通过，平均{avg_time*1000:.2f}ms/次")
    
    def test_multi_region_inspection_scenario(self):
        """测试多区域检测场景"""
        print("\n🗺️ 场景4：多区域检测场景")
        
        self._log_scenario_step("开始多区域检测")
        
        hole_list = self.scenario_adapter.get_hole_list()
        regions = ["A", "B", "C"]
        region_results = {}
        
        for region in regions:
            self._log_scenario_step(f"检测区域{region}")
            
            # 获取区域孔位
            region_holes = [h["hole_id"] for h in hole_list if h["region"] == region]
            self._log_scenario_step(f"区域{region}孔位", f"{len(region_holes)} 个")
            
            # 选择区域孔位
            self.interaction_handler._clear_selection()
            for hole_id in region_holes:
                self.interaction_handler.select_hole(hole_id)
            
            # 模拟区域检测
            region_start = time.time()
            successful_count = 0
            
            for hole_id in region_holes[:3]:  # 检测前3个作为代表
                result = self.scenario_adapter.navigate_to_realtime(hole_id)
                if result["success"]:
                    successful_count += 1
            
            region_time = time.time() - region_start
            success_rate = successful_count / min(3, len(region_holes)) * 100
            
            region_results[region] = {
                "holes": len(region_holes),
                "tested": min(3, len(region_holes)),
                "successful": successful_count,
                "success_rate": success_rate,
                "time": region_time
            }
            
            self._log_scenario_step(f"区域{region}完成", f"成功率{success_rate:.1f}%")
        
        # 生成检测报告
        self._log_scenario_step("生成检测报告")
        total_tested = sum(r["tested"] for r in region_results.values())
        total_successful = sum(r["successful"] for r in region_results.values())
        overall_success_rate = total_successful / total_tested * 100 if total_tested > 0 else 0
        
        self._log_scenario_step("整体统计", f"{total_successful}/{total_tested} 成功 ({overall_success_rate:.1f}%)")
        
        # 验证多区域检测
        self.assertEqual(len(region_results), 3, "未完成所有区域检测")
        self.assertGreater(overall_success_rate, 60, "整体成功率过低")
        
        print(f"   ✅ 多区域检测场景完成，整体成功率: {overall_success_rate:.1f}%")
    
    def test_user_learning_curve_scenario(self):
        """测试用户学习曲线场景"""
        print("\n📈 场景5：用户学习曲线场景")
        
        self._log_scenario_step("模拟新用户学习过程")
        
        # 阶段1：新手操作（慢速、有错误）
        self._log_scenario_step("阶段1：新手操作")
        
        # 模拟新手错误：尝试无效操作
        invalid_operations = [
            MockQKeyEvent(MockQt.Key_A, 0),  # 忘记按Ctrl
            MockQKeyEvent(MockQt.Key_Delete, 0),  # 没有选择就删除
        ]
        
        for i, event in enumerate(invalid_operations):
            self._log_scenario_step(f"新手错误{i+1}", "无效操作")
            self.interaction_handler.keyPressEvent(event)
            time.sleep(0.1)  # 模拟思考时间
        
        # 阶段2：学习正确操作
        self._log_scenario_step("阶段2：学习正确操作")
        
        correct_operations = [
            ("全选", MockQKeyEvent(MockQt.Key_A, MockQt.ControlModifier)),
            ("清除", MockQKeyEvent(MockQt.Key_Escape)),
            ("全选", MockQKeyEvent(MockQt.Key_A, MockQt.ControlModifier)),
            ("删除", MockQKeyEvent(MockQt.Key_Delete)),
        ]
        
        learning_times = []
        
        for op_name, event in correct_operations:
            start_time = time.time()
            self.interaction_handler.keyPressEvent(event)
            op_time = time.time() - start_time
            learning_times.append(op_time)
            
            self._log_scenario_step(f"学习操作：{op_name}", f"{op_time*1000:.2f}ms")
            time.sleep(0.2)  # 模拟学习间隔
        
        # 阶段3：熟练操作（快速、准确）
        self._log_scenario_step("阶段3：熟练操作")
        
        expert_start = time.time()
        
        # 快速操作序列
        for _ in range(5):
            select_event = MockQKeyEvent(MockQt.Key_A, MockQt.ControlModifier)
            self.interaction_handler.keyPressEvent(select_event)
            
            clear_event = MockQKeyEvent(MockQt.Key_Escape)
            self.interaction_handler.keyPressEvent(clear_event)
        
        expert_time = time.time() - expert_start
        avg_expert_time = expert_time / 10  # 10次操作
        
        self._log_scenario_step("熟练操作完成", f"平均{avg_expert_time*1000:.2f}ms/次")
        
        # 学习效果分析
        initial_avg = sum(learning_times) / len(learning_times)
        improvement_ratio = initial_avg / avg_expert_time if avg_expert_time > 0 else 1
        
        self._log_scenario_step("学习效果", f"操作速度提升{improvement_ratio:.1f}倍")
        
        # 验证学习曲线
        self.assertGreater(improvement_ratio, 2.0, "学习效果不明显")
        self.assertLess(avg_expert_time, 0.05, "熟练操作仍然过慢")
        
        print(f"   ✅ 用户学习曲线场景完成，速度提升{improvement_ratio:.1f}倍")
    
    def print_scenario_summary(self):
        """打印场景测试总结"""
        print("\n📋 场景测试日志总结")
        print("-" * 60)
        
        for i, log_entry in enumerate(self.scenario_logs[-20:], 1):  # 显示最后20条
            print(f"   {i:2d}. {log_entry}")


if __name__ == '__main__':
    # 运行场景测试
    unittest.main(verbosity=2)
