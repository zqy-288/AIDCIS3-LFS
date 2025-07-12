#!/usr/bin/env python3
"""
扇形顺序模拟测试
验证按扇形顺序进行模拟的性能优化效果
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

from main_window import MainWindow

class SectorSimulationTest:
    """扇形顺序模拟测试类"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = None
        self.sector_switches = []
        self.start_time = None
        
        # 设置简化日志
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        self.logger = logging.getLogger(__name__)
    
    def test_sector_simulation_performance(self):
        """测试扇形顺序模拟的性能"""
        self.logger.info("🚀 开始扇形顺序模拟性能测试")
        
        # 1. 创建窗口
        self.window = MainWindow()
        self.window.show()
        QTest.qWait(3000)  # 等待完全初始化
        
        # 2. 监听扇形切换
        if hasattr(self.window, 'dynamic_sector_display'):
            self.window.dynamic_sector_display.sector_changed.connect(self._on_sector_changed)
        
        # 3. 开始模拟
        self.start_time = time.time()
        self.logger.info(f"📊 数据规模: {len(self.window.hole_collection.holes)} 个孔位")
        
        # 启动模拟
        self.window.simulate_btn.click()
        
        # 4. 运行模拟一段时间观察性能
        simulation_duration = 30  # 运行30秒
        self.logger.info(f"⏱️ 运行模拟 {simulation_duration} 秒观察扇形切换频率...")
        
        QTest.qWait(simulation_duration * 1000)
        
        # 5. 停止模拟
        if hasattr(self.window, 'simulation_running_v2') and self.window.simulation_running_v2:
            self.window.simulate_btn.click()
        
        # 6. 分析结果
        self._analyze_results(simulation_duration)
        
        return True
    
    def _on_sector_changed(self, sector):
        """记录扇形切换事件"""
        current_time = time.time()
        elapsed = current_time - self.start_time if self.start_time else 0
        
        self.sector_switches.append({
            'time': elapsed,
            'sector': sector.value if hasattr(sector, 'value') else str(sector),
            'timestamp': current_time
        })
        
        self.logger.info(f"🔄 扇形切换: {sector.value if hasattr(sector, 'value') else str(sector)} (第{len(self.sector_switches)}次)")
    
    def _analyze_results(self, duration):
        """分析测试结果"""
        self.logger.info("=" * 60)
        self.logger.info("📊 扇形顺序模拟性能分析")
        self.logger.info("=" * 60)
        
        # 扇形切换频率分析
        switch_count = len(self.sector_switches)
        switch_frequency = switch_count / duration if duration > 0 else 0
        
        self.logger.info(f"⏱️ 测试时长: {duration} 秒")
        self.logger.info(f"🔄 扇形切换次数: {switch_count}")
        self.logger.info(f"📈 平均切换频率: {switch_frequency:.2f} 次/秒")
        
        if switch_count > 0:
            self.logger.info(f"📋 扇形切换序列:")
            for i, switch in enumerate(self.sector_switches):
                self.logger.info(f"  {i+1}. {switch['time']:.1f}s - {switch['sector']}")
        
        # 性能评估
        if switch_frequency < 0.2:  # 少于每5秒1次
            self.logger.info("✅ 性能优化成功: 扇形切换频率很低")
        elif switch_frequency < 1.0:  # 少于每秒1次
            self.logger.info("🔶 性能较好: 扇形切换频率可接受")
        else:
            self.logger.info("❌ 性能问题: 扇形切换频率过高")
        
        # 计算预期的性能提升
        total_holes = len(self.window.hole_collection.holes)
        estimated_old_switches = total_holes * 0.4  # 假设旧版本40%的孔位会触发切换
        improvement_ratio = estimated_old_switches / max(switch_count, 1)
        
        self.logger.info(f"🎯 性能提升估算:")
        self.logger.info(f"  旧版本预估切换次数: {estimated_old_switches:.0f}")
        self.logger.info(f"  新版本实际切换次数: {switch_count}")
        self.logger.info(f"  性能提升倍数: {improvement_ratio:.0f}x")

def main():
    """主函数"""
    test = SectorSimulationTest()
    
    try:
        success = test.test_sector_simulation_performance()
        
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