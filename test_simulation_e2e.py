#!/usr/bin/env python3
"""
模拟功能端到端测试
验证修复后的模拟功能是否正常工作
"""

import sys
import os
import time
from pathlib import Path

# 添加src路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QEventLoop
from PySide6.QtTest import QTest

from main_window.main_window import MainWindow

class SimulationE2ETest:
    """模拟功能端到端测试类"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = None
        self.test_results = []
        
        # 设置简化日志
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        self.logger = logging.getLogger(__name__)
    
    def log_result(self, test_name: str, success: bool, message: str = ""):
        """记录测试结果"""
        status = "✅ PASS" if success else "❌ FAIL"
        full_message = f"{status}: {test_name}"
        if message:
            full_message += f" - {message}"
        
        self.logger.info(full_message)
        self.test_results.append({
            'name': test_name,
            'success': success,
            'message': message
        })
    
    def wait_for_condition(self, condition_func, timeout_ms=5000, interval_ms=100):
        """等待条件满足"""
        start_time = time.time()
        while time.time() - start_time < timeout_ms / 1000:
            if condition_func():
                return True
            QTest.qWait(interval_ms)
        return False
    
    def test_window_creation(self):
        """测试窗口创建"""
        try:
            self.window = MainWindow()
            self.window.show()
            
            # 等待窗口完全初始化
            QTest.qWait(2000)
            
            self.log_result("窗口创建", True, f"主窗口成功创建并显示")
            return True
        except Exception as e:
            self.log_result("窗口创建", False, str(e))
            return False
    
    def test_data_loading(self):
        """测试数据加载"""
        try:
            # 检查hole_collection
            if not hasattr(self.window, 'hole_collection') or not self.window.hole_collection:
                self.log_result("数据加载", False, "hole_collection不存在")
                return False
            
            hole_count = len(self.window.hole_collection.holes)
            if hole_count == 0:
                self.log_result("数据加载", False, "没有孔位数据")
                return False
            
            self.log_result("数据加载", True, f"成功加载 {hole_count} 个孔位")
            return True
        except Exception as e:
            self.log_result("数据加载", False, str(e))
            return False
    
    def test_graphics_view(self):
        """测试图形视图"""
        try:
            # 检查graphics_view
            if not hasattr(self.window, 'graphics_view') or not self.window.graphics_view:
                self.log_result("图形视图", False, "graphics_view不存在")
                return False
            
            # 检查hole_items
            hole_items_count = len(self.window.graphics_view.hole_items)
            hole_data_count = len(self.window.hole_collection.holes)
            
            if hole_items_count == 0:
                self.log_result("图形视图", False, "没有图形项")
                return False
            
            # 对于扇形视图，允许图形项数量少于总数据数量（因为可能只显示一个扇形）
            if hole_items_count > hole_data_count:
                self.log_result("图形视图", False, 
                              f"图形项数量({hole_items_count})超过数据数量({hole_data_count})")
                return False
            
            # 如果图形项数量合理，则认为测试通过
            coverage_ratio = hole_items_count / hole_data_count
            self.log_result("图形视图", True, 
                          f"图形项数量: {hole_items_count}/{hole_data_count} (覆盖率: {coverage_ratio:.1%})")
            return True
        except Exception as e:
            self.log_result("图形视图", False, str(e))
            return False
    
    def test_simulate_button(self):
        """测试模拟按钮状态"""
        try:
            if not hasattr(self.window, 'simulate_btn') or not self.window.simulate_btn:
                self.log_result("模拟按钮", False, "simulate_btn不存在")
                return False
            
            if not self.window.simulate_btn.isEnabled():
                self.log_result("模拟按钮", False, "模拟按钮未启用")
                return False
            
            button_text = self.window.simulate_btn.text()
            self.log_result("模拟按钮", True, f"按钮状态正常: '{button_text}'")
            return True
        except Exception as e:
            self.log_result("模拟按钮", False, str(e))
            return False
    
    def test_simulation_start(self):
        """测试模拟启动"""
        try:
            initial_text = self.window.simulate_btn.text()
            
            # 点击模拟按钮
            self.window.simulate_btn.click()
            
            # 等待模拟开始
            QTest.qWait(1000)
            
            # 检查按钮文本是否改变
            new_text = self.window.simulate_btn.text()
            if new_text == initial_text:
                self.log_result("模拟启动", False, "按钮文本未改变，模拟可能未启动")
                return False
            
            # 检查模拟状态
            if not hasattr(self.window, 'simulation_running_v2') or not self.window.simulation_running_v2:
                self.log_result("模拟启动", False, "模拟运行状态为False")
                return False
            
            self.log_result("模拟启动", True, f"模拟已启动，按钮文本: '{new_text}'")
            return True
        except Exception as e:
            self.log_result("模拟启动", False, str(e))
            return False
    
    def test_simulation_progress(self):
        """测试模拟进度"""
        try:
            # 等待几个模拟周期
            initial_index = getattr(self.window, 'simulation_index_v2', 0)
            
            # 等待模拟进度
            QTest.qWait(3000)  # 等待3秒
            
            current_index = getattr(self.window, 'simulation_index_v2', 0)
            
            if current_index <= initial_index:
                self.log_result("模拟进度", False, f"模拟进度未推进: {initial_index} -> {current_index}")
                return False
            
            # 检查是否有图形项更新
            processed_holes = current_index - initial_index
            self.log_result("模拟进度", True, f"模拟进度正常，已处理 {processed_holes} 个孔位")
            return True
        except Exception as e:
            self.log_result("模拟进度", False, str(e))
            return False
    
    def test_simulation_stop(self):
        """测试模拟停止"""
        try:
            # 再次点击按钮停止模拟
            self.window.simulate_btn.click()
            
            # 等待停止
            QTest.qWait(1000)
            
            # 检查模拟状态
            if hasattr(self.window, 'simulation_running_v2') and self.window.simulation_running_v2:
                self.log_result("模拟停止", False, "模拟仍在运行")
                return False
            
            button_text = self.window.simulate_btn.text()
            self.log_result("模拟停止", True, f"模拟已停止，按钮文本: '{button_text}'")
            return True
        except Exception as e:
            self.log_result("模拟停止", False, str(e))
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        self.logger.info("=" * 60)
        self.logger.info("开始模拟功能端到端测试")
        self.logger.info("=" * 60)
        
        tests = [
            self.test_window_creation,
            self.test_data_loading,
            self.test_graphics_view,
            self.test_simulate_button,
            self.test_simulation_start,
            self.test_simulation_progress,
            self.test_simulation_stop,
        ]
        
        for test in tests:
            if not test():
                break  # 如果测试失败，停止后续测试
            QTest.qWait(500)  # 测试间隔
        
        self.print_summary()
    
    def print_summary(self):
        """打印测试总结"""
        self.logger.info("=" * 60)
        self.logger.info("测试总结")
        self.logger.info("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            self.logger.info(f"{status} {result['name']}")
            if result['message']:
                self.logger.info(f"   {result['message']}")
        
        self.logger.info("-" * 60)
        self.logger.info(f"测试结果: {passed}/{total} 通过")
        
        if passed == total:
            self.logger.info("🎉 所有测试通过！模拟功能工作正常。")
        else:
            self.logger.info("⚠️ 部分测试失败，需要进一步修复。")
        
        return passed == total

def main():
    """主函数"""
    test_runner = SimulationE2ETest()
    
    try:
        success = test_runner.run_all_tests()
        
        # 保持窗口打开一段时间以便观察
        if test_runner.window:
            test_runner.logger.info("\n窗口将在5秒后关闭...")
            QTest.qWait(5000)
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        test_runner.logger.info("\n⏹️ 测试被用户中断")
        return 1
    except Exception as e:
        test_runner.logger.error(f"❌ 测试执行失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        if test_runner.window:
            test_runner.window.close()

if __name__ == "__main__":
    sys.exit(main())