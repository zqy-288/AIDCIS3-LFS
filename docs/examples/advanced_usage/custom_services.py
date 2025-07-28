#!/usr/bin/env python3
"""
示例名称: 自定义服务实现

功能描述:
- 演示如何创建自定义的业务服务
- 展示服务的注册和使用方法
- 演示依赖注入和接口实现
- 展示服务扩展和插件化开发

使用方法:
python custom_services.py

依赖要求:
- Python 3.8+
- PySide6 >= 6.0.0
- AIDCIS3-LFS项目源码

作者: AIDCIS3-LFS团队
创建时间: 2025-07-25
"""

import sys
import os
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QObject, Signal, QTimer
except ImportError as e:
    print(f"❌ PySide6导入失败: {e}")
    sys.exit(1)

try:
    from src.controllers.coordinators.main_window_coordinator import MainWindowCoordinator
    from src.controllers.main_business_controller import MainBusinessController
except ImportError as e:
    print(f"❌ 项目模块导入失败: {e}")
    sys.exit(1)


# 1. 定义自定义检测算法接口
class ICustomDetectionAlgorithm(ABC):
    """自定义检测算法接口"""
    
    @abstractmethod
    def get_algorithm_name(self) -> str:
        """获取算法名称"""
        pass
    
    @abstractmethod
    def detect_hole(self, hole_data: Dict[str, Any]) -> Dict[str, Any]:
        """检测单个孔位"""
        pass
    
    @abstractmethod
    def get_algorithm_parameters(self) -> Dict[str, Any]:
        """获取算法参数"""
        pass


# 2. 实现高精度检测算法
class HighPrecisionDetectionAlgorithm(ICustomDetectionAlgorithm):
    """高精度检测算法实现"""
    
    def __init__(self, precision_level: float = 0.95):
        self.precision_level = precision_level
        self.detection_count = 0
        print(f"🔬 高精度检测算法初始化，精度级别: {precision_level}")
    
    def get_algorithm_name(self) -> str:
        return "高精度检测算法 v2.0"
    
    def detect_hole(self, hole_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行高精度检测"""
        self.detection_count += 1
        
        # 模拟高精度检测逻辑
        hole_id = hole_data.get('id', 'Unknown')
        diameter = hole_data.get('diameter', 10.0)
        
        # 模拟复杂的检测算法
        time.sleep(0.05)  # 模拟检测时间
        
        # 基于精度级别的检测结果
        import random
        confidence = random.uniform(self.precision_level - 0.1, self.precision_level + 0.05)
        
        # 根据置信度判断结果
        if confidence >= self.precision_level:
            status = "passed"
        elif confidence >= self.precision_level - 0.2:
            status = "warning"
        else:
            status = "failed"
        
        result = {
            'hole_id': hole_id,
            'algorithm': self.get_algorithm_name(),
            'status': status,
            'confidence': confidence,
            'diameter_measured': diameter + random.uniform(-0.1, 0.1),
            'detection_time': 0.05,
            'additional_metrics': {
                'roughness': random.uniform(0.1, 0.5),
                'circularity': random.uniform(0.95, 1.0),
                'depth_accuracy': random.uniform(0.98, 1.0)
            }
        }
        
        print(f"🔍 {hole_id} 检测完成: {status} (置信度: {confidence:.3f})")
        return result
    
    def get_algorithm_parameters(self) -> Dict[str, Any]:
        return {
            'precision_level': self.precision_level,
            'detection_count': self.detection_count,
            'algorithm_version': '2.0',
            'supports_batch': True
        }


# 3. 实现快速检测算法
class FastDetectionAlgorithm(ICustomDetectionAlgorithm):
    """快速检测算法实现"""
    
    def __init__(self, speed_factor: float = 2.0):
        self.speed_factor = speed_factor
        self.detection_count = 0
        print(f"⚡ 快速检测算法初始化，速度因子: {speed_factor}")
    
    def get_algorithm_name(self) -> str:
        return f"快速检测算法 v1.5 (速度x{self.speed_factor})"
    
    def detect_hole(self, hole_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行快速检测"""
        self.detection_count += 1
        
        hole_id = hole_data.get('id', 'Unknown')
        diameter = hole_data.get('diameter', 10.0)
        
        # 模拟快速检测
        detection_time = 0.02 / self.speed_factor
        time.sleep(detection_time)
        
        # 快速检测的结果（精度稍低但速度快）
        import random
        confidence = random.uniform(0.75, 0.90)
        
        if confidence >= 0.85:
            status = "passed"
        elif confidence >= 0.75:
            status = "warning"
        else:
            status = "failed"
        
        result = {
            'hole_id': hole_id,
            'algorithm': self.get_algorithm_name(),
            'status': status,
            'confidence': confidence,
            'diameter_measured': diameter + random.uniform(-0.2, 0.2),
            'detection_time': detection_time,
            'speed_factor': self.speed_factor
        }
        
        print(f"⚡ {hole_id} 快速检测: {status} (用时: {detection_time:.3f}s)")
        return result
    
    def get_algorithm_parameters(self) -> Dict[str, Any]:
        return {
            'speed_factor': self.speed_factor,
            'detection_count': self.detection_count,
            'algorithm_version': '1.5',
            'optimized_for': 'speed'
        }


# 4. 自定义检测服务
class CustomDetectionService(QObject):
    """自定义检测服务"""
    
    # 定义信号
    detection_started = Signal(str)  # 算法名称
    detection_progress = Signal(float, str)  # 进度，算法名称
    detection_completed = Signal(dict)  # 检测结果
    algorithm_switched = Signal(str, str)  # 从算法，到算法
    
    def __init__(self):
        super().__init__()
        self.algorithms = {}
        self.current_algorithm = None
        self.is_running = False
        self.results = []
        
        # 注册默认算法
        self.register_algorithm("high_precision", HighPrecisionDetectionAlgorithm())
        self.register_algorithm("fast_detection", FastDetectionAlgorithm())
        
        # 设置默认算法
        self.set_current_algorithm("high_precision")
        
        print("🛠️ 自定义检测服务初始化完成")
    
    def register_algorithm(self, name: str, algorithm: ICustomDetectionAlgorithm):
        """注册检测算法"""
        self.algorithms[name] = algorithm
        print(f"📝 算法已注册: {name} -> {algorithm.get_algorithm_name()}")
    
    def set_current_algorithm(self, algorithm_name: str) -> bool:
        """设置当前使用的算法"""
        if algorithm_name not in self.algorithms:
            print(f"❌ 算法不存在: {algorithm_name}")
            return False
        
        old_algorithm = self.current_algorithm.get_algorithm_name() if self.current_algorithm else "None"
        self.current_algorithm = self.algorithms[algorithm_name]
        new_algorithm = self.current_algorithm.get_algorithm_name()
        
        self.algorithm_switched.emit(old_algorithm, new_algorithm)
        print(f"🔄 算法切换: {old_algorithm} -> {new_algorithm}")
        return True
    
    def get_available_algorithms(self) -> List[str]:
        """获取可用算法列表"""
        return list(self.algorithms.keys())
    
    def start_detection(self, hole_data_list: List[Dict[str, Any]], algorithm_name: Optional[str] = None):
        """开始检测"""
        if self.is_running:
            print("⚠️ 检测已在进行中")
            return
        
        # 切换算法（如果指定）
        if algorithm_name and algorithm_name in self.algorithms:
            self.set_current_algorithm(algorithm_name)
        
        if not self.current_algorithm:
            print("❌ 没有设置检测算法")
            return
        
        self.is_running = True
        self.results = []
        
        algorithm_name = self.current_algorithm.get_algorithm_name()
        self.detection_started.emit(algorithm_name)
        
        print(f"🚀 开始检测 - 算法: {algorithm_name}")
        print(f"📊 待检测孔位数量: {len(hole_data_list)}")
        
        # 使用定时器模拟逐个检测
        self._start_batch_detection(hole_data_list)
    
    def _start_batch_detection(self, hole_data_list: List[Dict[str, Any]]):
        """开始批量检测"""
        self.hole_queue = hole_data_list.copy()
        self.total_holes = len(hole_data_list)
        self.processed_holes = 0
        
        # 开始处理第一个孔位
        self._process_next_hole()
    
    def _process_next_hole(self):
        """处理下一个孔位"""
        if not self.hole_queue or not self.is_running:
            # 检测完成
            self._complete_detection()
            return
        
        # 取出下一个孔位
        hole_data = self.hole_queue.pop(0)
        
        # 执行检测
        try:
            result = self.current_algorithm.detect_hole(hole_data)
            self.results.append(result)
            self.processed_holes += 1
            
            # 计算进度
            progress = (self.processed_holes / self.total_holes) * 100
            algorithm_name = self.current_algorithm.get_algorithm_name()
            self.detection_progress.emit(progress, algorithm_name)
            
            # 继续处理下一个孔位
            QTimer.singleShot(10, self._process_next_hole)
            
        except Exception as e:
            print(f"❌ 检测失败: {e}")
            self.is_running = False
    
    def _complete_detection(self):
        """完成检测"""
        self.is_running = False
        
        # 生成统计结果
        summary = self._generate_summary()
        
        result_data = {
            'algorithm': self.current_algorithm.get_algorithm_name(),
            'algorithm_params': self.current_algorithm.get_algorithm_parameters(),
            'total_holes': self.total_holes,
            'processed_holes': self.processed_holes,
            'results': self.results,
            'summary': summary,
            'completion_time': time.time()
        }
        
        self.detection_completed.emit(result_data)
        print(f"✅ 检测完成 - 共处理 {self.processed_holes} 个孔位")
    
    def _generate_summary(self) -> Dict[str, Any]:
        """生成检测摘要"""
        if not self.results:
            return {}
        
        status_counts = {}
        total_confidence = 0
        total_time = 0
        
        for result in self.results:
            status = result.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
            total_confidence += result.get('confidence', 0)
            total_time += result.get('detection_time', 0)
        
        return {
            'status_counts': status_counts,
            'average_confidence': total_confidence / len(self.results),
            'total_detection_time': total_time,
            'average_detection_time': total_time / len(self.results),
            'success_rate': status_counts.get('passed', 0) / len(self.results)
        }
    
    def stop_detection(self):
        """停止检测"""
        if self.is_running:
            self.is_running = False
            print("🛑 检测已停止")


# 5. 自定义业务控制器扩展
class ExtendedBusinessController(MainBusinessController):
    """扩展的业务控制器"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 添加自定义检测服务
        self.custom_detection_service = CustomDetectionService()
        
        # 连接自定义服务信号
        self._setup_custom_signals()
        
        print("🔧 扩展业务控制器初始化完成")
    
    def _setup_custom_signals(self):
        """设置自定义信号连接"""
        self.custom_detection_service.detection_started.connect(
            lambda alg: self.message_occurred.emit(f"开始使用算法: {alg}", "info")
        )
        
        self.custom_detection_service.detection_progress.connect(
            lambda progress, alg: self.message_occurred.emit(f"检测进度: {progress:.1f}% ({alg})", "info")
        )
        
        self.custom_detection_service.detection_completed.connect(
            self._on_custom_detection_completed
        )
        
        self.custom_detection_service.algorithm_switched.connect(
            lambda old, new: self.message_occurred.emit(f"算法切换: {old} -> {new}", "info")
        )
    
    def _on_custom_detection_completed(self, result_data: Dict[str, Any]):
        """处理自定义检测完成"""
        algorithm = result_data.get('algorithm', 'Unknown')
        summary = result_data.get('summary', {})
        
        print(f"\n📊 {algorithm} 检测结果:")
        print(f"  - 总孔位: {result_data.get('total_holes', 0)}")
        print(f"  - 处理完成: {result_data.get('processed_holes', 0)}")
        
        if summary:
            status_counts = summary.get('status_counts', {})
            print(f"  - 检测结果分布:")
            for status, count in status_counts.items():
                print(f"    * {status}: {count} 个")
            
            print(f"  - 平均置信度: {summary.get('average_confidence', 0):.3f}")
            print(f"  - 成功率: {summary.get('success_rate', 0):.1%}")
            print(f"  - 总检测时间: {summary.get('total_detection_time', 0):.3f}s")
        
        # 发送完成消息
        self.message_occurred.emit(f"自定义检测完成 - {algorithm}", "info")
    
    def handle_user_action(self, action: str, params: Dict[str, Any]):
        """扩展用户动作处理"""
        
        # 处理自定义检测动作
        if action == "start_custom_detection":
            self._start_custom_detection(params)
        elif action == "switch_detection_algorithm":
            self._switch_detection_algorithm(params)
        elif action == "list_algorithms":
            self._list_available_algorithms()
        else:
            # 调用父类方法处理标准动作
            super().handle_user_action(action, params)
    
    def _start_custom_detection(self, params: Dict[str, Any]):
        """开始自定义检测"""
        algorithm_name = params.get('algorithm', None)
        
        # 获取孔位数据
        view_model = self.view_model_manager.view_model
        if not view_model.hole_collection:
            self.message_occurred.emit("没有可检测的孔位数据", "warning")
            return
        
        # 转换孔位数据格式
        hole_data_list = []
        if hasattr(view_model.hole_collection, '__iter__'):
            for i, hole in enumerate(view_model.hole_collection):
                if isinstance(hole, dict):
                    hole_data_list.append(hole)
                else:
                    # 如果不是字典，创建默认数据
                    hole_data_list.append({
                        'id': f'H{i:03d}',
                        'diameter': 10.0,
                        'x': i * 10,
                        'y': 0
                    })
        
        # 开始自定义检测
        self.custom_detection_service.start_detection(hole_data_list, algorithm_name)
    
    def _switch_detection_algorithm(self, params: Dict[str, Any]):
        """切换检测算法"""
        algorithm_name = params.get('algorithm')
        if not algorithm_name:
            self.message_occurred.emit("未指定算法名称", "warning")
            return
        
        success = self.custom_detection_service.set_current_algorithm(algorithm_name)
        if success:
            self.message_occurred.emit(f"已切换到算法: {algorithm_name}", "info")
        else:
            self.message_occurred.emit(f"算法切换失败: {algorithm_name}", "error")
    
    def _list_available_algorithms(self):
        """列出可用算法"""
        algorithms = self.custom_detection_service.get_available_algorithms()
        algorithm_info = []
        
        for alg_name in algorithms:
            alg = self.custom_detection_service.algorithms[alg_name]
            algorithm_info.append(f"{alg_name}: {alg.get_algorithm_name()}")
        
        message = "可用检测算法:\n" + "\n".join(algorithm_info)
        self.message_occurred.emit(message, "info")


# 6. 演示类
class CustomServiceDemo(QObject):
    """自定义服务演示"""
    
    def __init__(self):
        super().__init__()
        self.coordinator = None
        self.demo_steps = [
            "创建扩展业务控制器",
            "列出可用算法",
            "使用高精度算法检测",
            "切换到快速算法",
            "使用快速算法检测",
            "比较检测结果"
        ]
        self.current_step = 0
        
    def start_demo(self):
        """开始演示"""
        print("🎬 自定义服务演示开始")
        print("=" * 60)
        
        # 创建应用
        app = QApplication(sys.argv)
        app.setApplicationName("Custom Services Demo")
        
        # 创建扩展的协调器
        self._create_extended_coordinator()
        
        # 开始演示步骤
        self._execute_next_step()
        
        return app.exec()
    
    def _create_extended_coordinator(self):
        """创建扩展的协调器"""
        print("\n📋 步骤 1: 创建扩展业务控制器")
        print("-" * 40)
        
        # 创建扩展的业务控制器
        extended_controller = ExtendedBusinessController()
        
        # 创建协调器并替换业务控制器
        from src.ui.main_view_controller import MainViewController
        
        view_controller = MainViewController()
        
        # 手动设置连接
        view_controller.user_action.connect(extended_controller.handle_user_action)
        extended_controller.view_model_changed.connect(view_controller.update_display)
        extended_controller.message_occurred.connect(view_controller.show_message)
        
        self.coordinator = type('MockCoordinator', (), {
            'view_controller': view_controller,
            'business_controller': extended_controller,
            'show': lambda: view_controller.show(),
            'close': lambda: view_controller.close()
        })()
        
        # 创建测试数据
        self._create_test_data()
        
        print("✅ 扩展业务控制器创建完成")
        self.current_step += 1
        
        # 显示窗口
        self.coordinator.show()
        QTimer.singleShot(2000, self._execute_next_step)
    
    def _create_test_data(self):
        """创建测试数据"""
        test_holes = []
        for i in range(10):
            test_holes.append({
                'id': f'H{i:03d}',
                'diameter': 10.0 + (i % 3) * 2,  # 变化的直径
                'x': i * 10,
                'y': 0,
                'status': 'pending'
            })
        
        # 更新ViewModel
        view_model = self.coordinator.business_controller.view_model_manager.view_model
        view_model.hole_collection = test_holes
        view_model.file_info = {'holes': len(test_holes)}
        
    def _execute_next_step(self):
        """执行下一步"""
        if self.current_step >= len(self.demo_steps):
            self._demo_completed()
            return
        
        step_name = self.demo_steps[self.current_step]
        print(f"\n📋 步骤 {self.current_step + 1}: {step_name}")
        print("-" * 40)
        
        if self.current_step == 1:
            self._list_algorithms()
        elif self.current_step == 2:
            self._test_high_precision_detection()
        elif self.current_step == 3:
            self._switch_to_fast_algorithm()
        elif self.current_step == 4:
            self._test_fast_detection()
        elif self.current_step == 5:
            self._compare_results()
        
        self.current_step += 1
    
    def _list_algorithms(self):
        """列出算法"""
        self.coordinator.business_controller.handle_user_action("list_algorithms", {})
        QTimer.singleShot(2000, self._execute_next_step)
    
    def _test_high_precision_detection(self):
        """测试高精度检测"""
        print("🔬 开始高精度检测...")
        self.coordinator.business_controller.handle_user_action(
            "start_custom_detection", 
            {"algorithm": "high_precision"}
        )
        QTimer.singleShot(8000, self._execute_next_step)
    
    def _switch_to_fast_algorithm(self):
        """切换到快速算法"""
        print("⚡ 切换到快速算法...")
        self.coordinator.business_controller.handle_user_action(
            "switch_detection_algorithm", 
            {"algorithm": "fast_detection"}
        )
        QTimer.singleShot(2000, self._execute_next_step)
    
    def _test_fast_detection(self):
        """测试快速检测"""
        print("⚡ 开始快速检测...")
        self.coordinator.business_controller.handle_user_action(
            "start_custom_detection", 
            {"algorithm": "fast_detection"}
        )
        QTimer.singleShot(5000, self._execute_next_step)
    
    def _compare_results(self):
        """比较结果"""
        print("📊 检测结果比较:")
        print("  高精度算法:")
        print("    - 优势: 高精度、详细指标")
        print("    - 劣势: 检测时间较长")
        print("  快速算法:")
        print("    - 优势: 检测速度快")
        print("    - 劣势: 精度稍低")
        
        QTimer.singleShot(3000, self._execute_next_step)
    
    def _demo_completed(self):
        """演示完成"""
        print("\n🎉 自定义服务演示完成！")
        print("=" * 60)
        print("📝 演示总结:")
        print("  ✅ 自定义检测算法实现")
        print("  ✅ 服务注册和切换")
        print("  ✅ 业务控制器扩展")
        print("  ✅ 算法性能比较")
        print("\n💡 这展示了AIDCIS3-LFS的扩展能力和插件化设计")
        
        QTimer.singleShot(3000, QApplication.instance().quit)


def main():
    """主函数"""
    print("🛠️ AIDCIS3-LFS 自定义服务演示")
    print("=" * 60)
    print("💡 这个演示将展示：")
    print("  🔬 自定义检测算法实现")
    print("  🔄 算法注册和切换")
    print("  🔧 业务控制器扩展")
    print("  📊 性能对比分析")
    print()
    
    try:
        demo = CustomServiceDemo()
        return demo.start_demo()
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        print(f"\n👋 自定义服务演示结束，退出代码: {exit_code}")
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n⚠️  用户中断演示")
        sys.exit(0)
        
    except Exception as e:
        print(f"💥 演示异常: {e}")
        sys.exit(1)