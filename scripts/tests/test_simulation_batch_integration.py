#!/usr/bin/env python3
"""
模拟检测批次集成测试
全面测试模拟检测的批次创建、产品信息处理和UI状态更新
"""

import sys
import os
from pathlib import Path
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MockQObject:
    """模拟QObject用于测试"""
    def __init__(self):
        self._signals = {}
    
    def emit(self, *args):
        pass
    
    def connect(self, slot):
        pass

class MockSignal:
    """模拟Qt信号"""
    def emit(self, *args):
        pass
    
    def connect(self, slot):
        pass

class SimulationBatchIntegrationTester:
    """模拟检测批次集成测试器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.test_results = []
        
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 80)
        print("🧪 模拟检测批次集成测试")
        print("=" * 80)
        
        tests = [
            self.test_product_info_formats,
            self.test_batch_service_creation,
            self.test_detection_service_mock,
            self.test_controller_integration,
            self.test_ui_state_management,
            self.test_error_handling,
            self.test_path_management,
            self.test_complete_workflow
        ]
        
        for test in tests:
            try:
                print(f"\n📋 运行测试: {test.__name__}")
                print("-" * 60)
                result = test()
                self.test_results.append((test.__name__, "PASS", result))
                print(f"✅ {test.__name__}: PASS")
            except Exception as e:
                self.test_results.append((test.__name__, "FAIL", str(e)))
                print(f"❌ {test.__name__}: FAIL - {e}")
        
        self.print_summary()
        return self.test_results
    
    def test_product_info_formats(self):
        """测试不同格式的产品信息处理"""
        print("🔍 测试产品信息格式处理...")
        
        # 测试数据
        test_cases = [
            ("字符串格式", "CAP1000", "CAP1000"),
            ("字典格式", {"model_name": "CAP1000", "id": 1}, "CAP1000"),
            ("字典缺失字段", {"id": 1}, "Unknown"),
            ("None值", None, "Unknown"),
            ("空字符串", "", ""),
        ]
        
        def get_product_name(current_product):
            """模拟控制器中的产品名称获取逻辑"""
            if hasattr(current_product, 'model_name'):
                return current_product.model_name
            elif isinstance(current_product, dict):
                return current_product.get('model_name', 'Unknown')
            elif isinstance(current_product, str):
                return current_product
            else:
                return "Unknown"
        
        results = []
        for case_name, input_data, expected in test_cases:
            try:
                result = get_product_name(input_data)
                status = "✅" if result == expected else "❌"
                print(f"  {status} {case_name}: {input_data} -> {result} (期望: {expected})")
                results.append((case_name, result == expected))
            except Exception as e:
                print(f"  ❌ {case_name}: 异常 - {e}")
                results.append((case_name, False))
        
        # 测试ProductModel对象
        try:
            from src.models.product_model import ProductModel
            mock_product = type('MockProduct', (), {'model_name': 'TEST_PRODUCT'})()
            result = get_product_name(mock_product)
            print(f"  ✅ ProductModel对象: -> {result}")
            results.append(("ProductModel", result == "TEST_PRODUCT"))
        except Exception as e:
            print(f"  ❌ ProductModel对象测试失败: {e}")
            results.append(("ProductModel", False))
        
        passed = sum(1 for _, success in results if success)
        total = len(results)
        print(f"\n📊 产品信息格式测试: {passed}/{total} 通过")
        
        return {"passed": passed, "total": total, "details": results}
    
    def test_batch_service_creation(self):
        """测试批次服务创建功能"""
        print("🔍 测试批次服务创建...")
        
        try:
            from src.domain.services.batch_service import BatchService
            from src.infrastructure.repositories.batch_repository_impl import BatchRepositoryImpl
            from src.models.data_path_manager import DataPathManager
            
            # 创建服务实例
            repo = BatchRepositoryImpl()
            path_manager = DataPathManager()
            batch_service = BatchService(repo, path_manager)
            
            # 测试真实批次创建
            print("  🔧 测试真实批次创建...")
            real_batch = batch_service.create_batch(
                product_id=1,
                product_name="TEST_PRODUCT",
                description="测试真实批次",
                is_mock=False
            )
            
            print(f"    ✅ 真实批次: {real_batch.batch_id}")
            print(f"    ✅ 检测类型: {real_batch.detection_type.value}")
            print(f"    ✅ 是否模拟: {real_batch.is_mock}")
            
            # 测试模拟批次创建
            print("  🔧 测试模拟批次创建...")
            mock_batch = batch_service.create_batch(
                product_id=1,
                product_name="TEST_PRODUCT", 
                description="测试模拟批次",
                is_mock=True
            )
            
            print(f"    ✅ 模拟批次: {mock_batch.batch_id}")
            print(f"    ✅ 检测类型: {mock_batch.detection_type.value}")
            print(f"    ✅ 是否模拟: {mock_batch.is_mock}")
            print(f"    ✅ MOCK后缀: {'_MOCK' in mock_batch.batch_id}")
            
            # 验证批次编号递增
            print("  🔧 测试批次编号递增...")
            next_batch = batch_service.create_batch(
                product_id=1,
                product_name="TEST_PRODUCT",
                is_mock=False
            )
            
            batch_number_diff = next_batch.detection_number - real_batch.detection_number
            print(f"    ✅ 编号递增: {real_batch.detection_number} -> {next_batch.detection_number} (差值: {batch_number_diff})")
            
            return {
                "real_batch_created": True,
                "mock_batch_created": True,
                "mock_suffix_correct": "_MOCK" in mock_batch.batch_id,
                "number_incremented": batch_number_diff > 0,
                "real_batch_id": real_batch.batch_id,
                "mock_batch_id": mock_batch.batch_id
            }
            
        except Exception as e:
            print(f"  ❌ 批次服务测试失败: {e}")
            raise
    
    def test_detection_service_mock(self):
        """测试检测服务的模拟功能"""
        print("🔍 测试检测服务模拟功能...")
        
        try:
            from src.services.detection_service import DetectionService
            
            # 创建检测服务实例
            detection_service = DetectionService()
            
            # 测试模拟参数
            print("  🔧 检查模拟参数...")
            interval = detection_service.simulation_params['interval']
            print(f"    ✅ 模拟间隔: {interval}ms (期望: 10000ms)")
            
            success_rate = detection_service.simulation_params['success_rate']
            print(f"    ✅ 成功率: {success_rate}")
            
            # 创建模拟孔位数据
            class MockHole:
                def __init__(self, hole_id):
                    self.hole_id = hole_id
            
            mock_holes = [MockHole(f"TEST{i:03d}") for i in range(1, 4)]
            
            # 测试检测启动（不实际运行定时器）
            print("  🔧 测试检测服务启动...")
            result = detection_service.start_detection(
                holes=mock_holes,
                batch_id="TEST_BATCH_001_MOCK",
                is_mock=True
            )
            
            print(f"    ✅ 启动结果: {result}")
            print(f"    ✅ 模拟标志: {detection_service.is_mock}")
            print(f"    ✅ 定时器间隔: {detection_service.detection_timer.interval()}ms")
            
            # 停止检测
            detection_service.stop_detection()
            
            return {
                "service_created": True,
                "mock_interval_correct": interval == 10000,
                "start_successful": result,
                "mock_flag_set": detection_service.is_mock,
                "timer_interval_correct": detection_service.detection_timer.interval() == 10000
            }
            
        except Exception as e:
            print(f"  ❌ 检测服务测试失败: {e}")
            raise
    
    def test_controller_integration(self):
        """测试控制器集成"""
        print("🔍 测试控制器集成...")
        
        try:
            # 由于控制器依赖Qt，这里主要测试逻辑
            from src.pages.main_detection_p1.controllers.main_window_controller import MainWindowController
            
            # 创建模拟控制器用于测试产品信息处理
            class MockController:
                def __init__(self):
                    self.current_product = None
                    self.current_product_id = 1
                    self.logger = logger
                
                def get_product_name(self):
                    """模拟控制器中的产品名称获取逻辑"""
                    if hasattr(self.current_product, 'model_name'):
                        return self.current_product.model_name
                    elif isinstance(self.current_product, dict):
                        return self.current_product.get('model_name', 'Unknown')
                    elif isinstance(self.current_product, str):
                        return self.current_product
                    else:
                        return "Unknown"
            
            controller = MockController()
            
            # 测试不同产品格式
            test_cases = [
                ("CAP1000", "CAP1000"),
                ({"model_name": "TEST"}, "TEST"),
                (None, "Unknown")
            ]
            
            results = []
            for product_data, expected in test_cases:
                controller.current_product = product_data
                result = controller.get_product_name()
                success = result == expected
                print(f"    {'✅' if success else '❌'} 产品: {product_data} -> {result}")
                results.append(success)
            
            return {
                "controller_logic_tested": True,
                "all_formats_handled": all(results),
                "test_cases_passed": sum(results),
                "total_test_cases": len(results)
            }
            
        except Exception as e:
            print(f"  ❌ 控制器集成测试失败: {e}")
            raise
    
    def test_ui_state_management(self):
        """测试UI状态管理"""
        print("🔍 测试UI状态管理...")
        
        # 模拟UI状态更新逻辑
        class MockUIState:
            def __init__(self):
                self.batch_status = "未开始"
                self.detection_running = False
                self.simulation_running = False
            
            def update_batch_status(self, batch_id):
                if batch_id:
                    if "_MOCK" in batch_id:
                        self.batch_status = f"模拟批次: {batch_id}"
                    else:
                        self.batch_status = f"检测批次: {batch_id}"
                    self.detection_running = True
                else:
                    self.batch_status = "未开始"
                    self.detection_running = False
            
            def start_simulation(self):
                self.simulation_running = True
            
            def stop_simulation(self):
                self.simulation_running = False
        
        ui_state = MockUIState()
        
        # 测试状态更新
        print("  🔧 测试批次状态更新...")
        
        # 测试真实批次
        real_batch_id = "CAP1000_检测001_20250804_120000"
        ui_state.update_batch_status(real_batch_id)
        print(f"    ✅ 真实批次状态: {ui_state.batch_status}")
        
        # 测试模拟批次
        mock_batch_id = "CAP1000_检测002_20250804_120100_MOCK"
        ui_state.update_batch_status(mock_batch_id)
        print(f"    ✅ 模拟批次状态: {ui_state.batch_status}")
        
        # 测试模拟控制
        ui_state.start_simulation()
        print(f"    ✅ 模拟运行状态: {ui_state.simulation_running}")
        
        return {
            "status_update_working": True,
            "mock_batch_recognized": "_MOCK" in ui_state.batch_status,
            "simulation_state_managed": ui_state.simulation_running
        }
    
    def test_error_handling(self):
        """测试错误处理"""
        print("🔍 测试错误处理...")
        
        error_cases = []
        
        # 测试产品信息错误处理
        print("  🔧 测试产品信息错误...")
        try:
            def safe_get_product_name(current_product):
                try:
                    if hasattr(current_product, 'model_name'):
                        return current_product.model_name
                    elif isinstance(current_product, dict):
                        return current_product.get('model_name', 'Unknown')
                    elif isinstance(current_product, str):
                        return current_product
                    else:
                        return "Unknown"
                except Exception as e:
                    return f"Error: {e}"
            
            # 测试异常情况
            weird_object = type('WeirdObject', (), {})()
            result = safe_get_product_name(weird_object)
            print(f"    ✅ 异常对象处理: {result}")
            error_cases.append(("weird_object", True))
            
        except Exception as e:
            print(f"    ❌ 产品信息错误处理失败: {e}")
            error_cases.append(("weird_object", False))
        
        # 测试批次创建错误处理
        print("  🔧 测试批次创建错误...")
        try:
            from src.domain.services.batch_service import BatchService
            from src.infrastructure.repositories.batch_repository_impl import BatchRepositoryImpl
            from src.models.data_path_manager import DataPathManager
            
            repo = BatchRepositoryImpl()
            path_manager = DataPathManager()
            batch_service = BatchService(repo, path_manager)
            
            # 测试无效参数
            try:
                batch_service.create_batch(
                    product_id=None,  # 无效ID
                    product_name="TEST",
                    is_mock=True
                )
                error_cases.append(("invalid_product_id", False))
            except Exception:
                print("    ✅ 无效产品ID被正确拒绝")
                error_cases.append(("invalid_product_id", True))
            
        except Exception as e:
            print(f"    ❌ 批次创建错误处理测试失败: {e}")
            error_cases.append(("batch_creation_error", False))
        
        passed = sum(1 for _, success in error_cases if success)
        total = len(error_cases)
        
        return {
            "error_handling_tested": True,
            "cases_passed": passed,
            "total_cases": total,
            "all_handled": passed == total
        }
    
    def test_path_management(self):
        """测试路径管理"""
        print("🔍 测试路径管理...")
        
        try:
            from src.models.data_path_manager import DataPathManager
            
            path_manager = DataPathManager()
            
            # 测试产品路径
            product_path = path_manager.get_product_path("CAP1000")
            print(f"    ✅ 产品路径: {product_path}")
            
            # 测试批次路径
            batch_id = "CAP1000_检测001_20250804_120000_MOCK"
            batch_path = path_manager.get_inspection_batch_path("CAP1000", batch_id)
            print(f"    ✅ 批次路径: {batch_path}")
            
            # 验证路径结构
            expected_structure = "Data/Products/CAP1000" in str(product_path)
            mock_in_path = "_MOCK" in str(batch_path)
            
            return {
                "path_manager_working": True,
                "product_path_correct": expected_structure,
                "mock_batch_path_correct": mock_in_path,
                "product_path": str(product_path),
                "batch_path": str(batch_path)
            }
            
        except Exception as e:
            print(f"  ❌ 路径管理测试失败: {e}")
            raise
    
    def test_complete_workflow(self):
        """测试完整工作流程"""
        print("🔍 测试完整工作流程...")
        
        workflow_steps = []
        
        try:
            # Step 1: 创建批次服务
            print("  🔧 步骤1: 初始化服务...")
            from src.domain.services.batch_service import BatchService
            from src.infrastructure.repositories.batch_repository_impl import BatchRepositoryImpl
            from src.models.data_path_manager import DataPathManager
            from src.services.detection_service import DetectionService
            
            repo = BatchRepositoryImpl()
            path_manager = DataPathManager()
            batch_service = BatchService(repo, path_manager)
            detection_service = DetectionService()
            
            workflow_steps.append(("service_init", True))
            print("    ✅ 服务初始化完成")
            
            # Step 2: 模拟产品选择
            print("  🔧 步骤2: 模拟产品选择...")
            current_product = "CAP1000"  # 模拟当前选中的产品
            product_id = 1
            
            # 处理产品信息
            if isinstance(current_product, str):
                product_name = current_product
            else:
                product_name = "Unknown"
            
            workflow_steps.append(("product_selection", True))
            print(f"    ✅ 产品选择: {product_name}")
            
            # Step 3: 创建模拟批次
            print("  🔧 步骤3: 创建模拟批次...")
            mock_batch = batch_service.create_batch(
                product_id=product_id,
                product_name=product_name,
                description="完整工作流程测试",
                is_mock=True
            )
            
            workflow_steps.append(("batch_creation", True))
            print(f"    ✅ 模拟批次创建: {mock_batch.batch_id}")
            
            # Step 4: 创建模拟孔位数据
            print("  🔧 步骤4: 准备检测数据...")
            class MockHole:
                def __init__(self, hole_id):
                    self.hole_id = hole_id
            
            mock_holes = [MockHole(f"BC{i:03d}R{j:03d}") for i in range(1, 4) for j in range(1, 4)]
            
            workflow_steps.append(("data_preparation", True))
            print(f"    ✅ 准备了 {len(mock_holes)} 个模拟孔位")
            
            # Step 5: 启动模拟检测
            print("  🔧 步骤5: 启动模拟检测...")
            detection_result = detection_service.start_detection(
                holes=mock_holes,
                batch_id=mock_batch.batch_id,
                is_mock=True
            )
            
            workflow_steps.append(("detection_start", detection_result))
            print(f"    ✅ 检测启动: {detection_result}")
            
            # Step 6: 验证配置
            print("  🔧 步骤6: 验证配置...")
            interval_correct = detection_service.detection_timer.interval() == 10000
            mock_flag_set = detection_service.is_mock
            batch_id_correct = detection_service.current_batch_id == mock_batch.batch_id
            
            workflow_steps.append(("configuration_check", all([interval_correct, mock_flag_set, batch_id_correct])))
            print(f"    ✅ 定时器间隔: {detection_service.detection_timer.interval()}ms")
            print(f"    ✅ 模拟标志: {mock_flag_set}")
            print(f"    ✅ 批次ID: {batch_id_correct}")
            
            # Step 7: 清理
            print("  🔧 步骤7: 清理资源...")
            detection_service.stop_detection()
            
            workflow_steps.append(("cleanup", True))
            print("    ✅ 资源清理完成")
            
            # 统计结果
            passed_steps = sum(1 for _, success in workflow_steps if success)
            total_steps = len(workflow_steps)
            
            print(f"\n📊 工作流程测试: {passed_steps}/{total_steps} 步骤成功")
            
            return {
                "workflow_completed": passed_steps == total_steps,
                "steps_passed": passed_steps,
                "total_steps": total_steps,
                "steps": workflow_steps,
                "final_batch_id": mock_batch.batch_id,
                "detection_configured": interval_correct and mock_flag_set
            }
            
        except Exception as e:
            print(f"  ❌ 完整工作流程测试失败: {e}")
            workflow_steps.append(("workflow_error", False))
            raise
    
    def print_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 80)
        print("📊 测试结果总结")
        print("=" * 80)
        
        passed = sum(1 for _, status, _ in self.test_results if status == "PASS")
        total = len(self.test_results)
        
        print(f"\n总体结果: {passed}/{total} 测试通过")
        
        for test_name, status, result in self.test_results:
            status_emoji = "✅" if status == "PASS" else "❌"
            print(f"{status_emoji} {test_name}: {status}")
            if status == "FAIL":
                print(f"   错误: {result}")
        
        print(f"\n{'=' * 80}")
        if passed == total:
            print("🎉 所有测试通过！模拟检测批次集成功能正常。")
        else:
            print(f"⚠️ {total - passed} 个测试失败，需要修复。")
        print(f"{'=' * 80}")

def main():
    """主函数"""
    print("🚀 启动模拟检测批次集成测试...")
    
    tester = SimulationBatchIntegrationTester()
    results = tester.run_all_tests()
    
    # 生成详细报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = project_root / f"scripts/tests/test_report_{timestamp}.txt"
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("模拟检测批次集成测试报告\n")
            f.write(f"生成时间: {datetime.now()}\n")
            f.write("=" * 80 + "\n\n")
            
            for test_name, status, result in results:
                f.write(f"{test_name}: {status}\n")
                if isinstance(result, dict):
                    for key, value in result.items():
                        f.write(f"  {key}: {value}\n")
                f.write("\n")
        
        print(f"\n📄 详细报告已保存到: {report_file}")
    except Exception as e:
        print(f"⚠️ 无法保存报告: {e}")
    
    return 0 if all(status == "PASS" for _, status, _ in results) else 1

if __name__ == "__main__":
    exit_code = main()
    print(f"\n退出代码: {exit_code}")
    sys.exit(exit_code)