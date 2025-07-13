#!/usr/bin/env python3
"""
快速模拟测试
验证0.1秒一个点的加速模拟效果
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

class FastSimulationTest:
    """快速模拟测试类"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = None
        self.simulation_points = []
        self.start_time = None
        
        # 设置日志
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        self.logger = logging.getLogger(__name__)
    
    def test_simulation_speed(self):
        """测试模拟速度"""
        self.logger.info("🚀 开始快速模拟速度测试")
        
        # 1. 创建窗口
        self.window = MainWindow()
        self.window.show()
        QTest.qWait(3000)  # 等待完全初始化
        
        self.logger.info(f"📊 数据规模: {len(self.window.hole_collection.holes)} 个孔位")
        
        # 2. 记录开始时间
        self.start_time = time.time()
        
        # 3. 启动模拟
        self.window.simulate_btn.click()
        self.logger.info("⏱️ 模拟已启动，测试0.1秒/点的速度...")
        
        # 4. 运行10秒观察模拟点数
        test_duration = 10
        QTest.qWait(test_duration * 1000)
        
        # 5. 停止模拟
        if hasattr(self.window, 'simulation_running_v2') and self.window.simulation_running_v2:
            self.window.simulate_btn.click()
        
        # 6. 计算实际速度
        end_time = time.time()
        elapsed_time = end_time - self.start_time
        
        # 获取处理的孔位数
        processed_holes = getattr(self.window, 'simulation_index_v2', 0)
        
        self._analyze_speed_results(elapsed_time, processed_holes, test_duration)
        
        return True
    
    def _analyze_speed_results(self, elapsed_time, processed_holes, expected_duration):
        """分析速度测试结果"""
        self.logger.info("=" * 60)
        self.logger.info("📊 快速模拟速度分析")
        self.logger.info("=" * 60)
        
        # 计算实际速度
        actual_speed = processed_holes / elapsed_time if elapsed_time > 0 else 0
        expected_speed = 10.0  # 0.1秒/点 = 10点/秒
        
        self.logger.info(f"⏱️ 实际测试时长: {elapsed_time:.1f} 秒")
        self.logger.info(f"📈 处理孔位数量: {processed_holes} 个")
        self.logger.info(f"🎯 实际处理速度: {actual_speed:.1f} 点/秒")
        self.logger.info(f"📋 期望处理速度: {expected_speed:.1f} 点/秒")
        
        # 计算性能指标
        if actual_speed > 0:
            speed_ratio = actual_speed / expected_speed
            self.logger.info(f"📊 速度达成率: {speed_ratio:.1%}")
            
            if speed_ratio >= 0.9:  # 90%以上算成功
                self.logger.info("✅ 速度测试通过: 达到预期0.1秒/点的处理速度")
            elif speed_ratio >= 0.7:  # 70%以上算可接受
                self.logger.info("🔶 速度测试基本通过: 接近预期处理速度")
            else:
                self.logger.info("❌ 速度测试未达标: 处理速度偏慢")
        
        # 计算完成时间预估
        total_holes = len(self.window.hole_collection.holes)
        estimated_total_time = total_holes / actual_speed if actual_speed > 0 else float('inf')
        
        self.logger.info(f"🎯 完成全部模拟预估时间:")
        self.logger.info(f"  总孔位数: {total_holes}")
        self.logger.info(f"  预估完成时间: {estimated_total_time/60:.1f} 分钟")
        
        # 与原来1秒/点的速度对比
        old_speed = 1.0  # 1点/秒
        speedup_factor = actual_speed / old_speed
        self.logger.info(f"⚡ 相比1秒/点模式的加速倍数: {speedup_factor:.1f}x")

def main():
    """主函数"""
    test = FastSimulationTest()
    
    try:
        success = test.test_simulation_speed()
        
        # 保持窗口打开一段时间以便观察
        if test.window:
            test.logger.info("\\n窗口将在3秒后关闭...")
            QTest.qWait(3000)
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        test.logger.info("\\n⏹️ 测试被用户中断")
        return 1
    except Exception as e:
        test.logger.error(f"❌ 测试执行失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        if test.window:
            test.window.close()

if __name__ == "__main__":
    sys.exit(main())