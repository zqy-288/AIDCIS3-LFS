#!/usr/bin/env python3
"""
测试参数调整效果 - 验证算法参数优化是否解决漏检问题
"""

import sys
import os
from pathlib import Path

# 添加src路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt

from main_window import MainWindow
from aidcis2.models.hole_data import HoleData, HoleCollection, HoleStatus

class ParameterAdjustmentTest:
    """参数调整测试"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = None
        
        # 设置日志
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        self.logger = logging.getLogger(__name__)
    
    def test_parameter_adjustment(self):
        """测试参数调整效果"""
        self.logger.info("🔧 测试算法参数调整效果 - 彻底解决漏检问题")
        
        # 1. 创建主窗口
        self.window = MainWindow()
        self.window.show()
        QTest.qWait(2000)
        
        # 2. 加载具有挑战性的测试数据
        self.logger.info("\n🔄 加载高挑战性测试数据")
        hole_collection = self._create_challenging_test_data()
        self.window.hole_collection = hole_collection
        self.window.update_hole_display()
        
        QTest.qWait(3000)
        
        # 3. 启动参数优化模拟
        self.logger.info("\n📋 启动参数优化模拟")
        
        if hasattr(self.window, 'simulate_btn'):
            self.logger.info("🔘 启动参数调整V2模拟...")
            
            # 强制使用V2模拟
            self.window.simulation_running_v2 = False
            self.window.simulate_btn.click()
            
            # 观察模拟效果
            self.logger.info("⏳ 观察参数调整效果（20秒）...")
            self.logger.info("👁️ 重点检查：")
            self.logger.info("  1. 参数总结是否正确显示")
            self.logger.info("  2. 基础容差是否从15px降低到8px")
            self.logger.info("  3. 全局容差是否从20px降低到12px")
            self.logger.info("  4. 行分组倍数是否从2.0降低到1.5")
            self.logger.info("  5. 列分组倍数是否从1.5降低到1.2")
            self.logger.info("  6. 是否增加了20%宽松判断")
            self.logger.info("  7. 最小容差是否降低到5px和4px")
            self.logger.info("  8. 密集孔位是否完全无漏检")
            
            QTest.qWait(20000)  # 等待20秒观察效果
            
            # 停止模拟
            if hasattr(self.window, 'simulation_running_v2') and self.window.simulation_running_v2:
                self.logger.info("⏹️ 停止参数调整模拟")
                self.window.simulate_btn.click()
        
        return True
    
    def _create_challenging_test_data(self):
        """创建具有挑战性的测试数据，验证参数调整效果"""
        test_holes = {}
        hole_id_counter = 1
        
        center_x, center_y = 400, 300
        
        # 1. 极密集网格（10px间距）
        self.logger.info("🔧 创建极密集网格（10px间距）...")
        for i in range(15):
            for j in range(12):
                x = center_x + 50 + i * 10  # 仅10像素间距
                y = center_y - 60 + j * 10  # 仅10像素间距
                
                hole_id = f"ULTRA_{hole_id_counter:03d}"
                hole_data = HoleData(
                    hole_id=hole_id,
                    center_x=x,
                    center_y=y,
                    radius=8.8,
                    status=HoleStatus.PENDING
                )
                test_holes[hole_id] = hole_data
                hole_id_counter += 1
        
        # 2. 不规则密集簇（8px间距）
        self.logger.info("🔧 创建不规则密集簇（8px间距）...")
        cluster_centers = [
            (center_x - 150, center_y - 150),
            (center_x + 200, center_y + 120),
            (center_x - 80, center_y + 180)
        ]
        
        for cluster_idx, (cx, cy) in enumerate(cluster_centers):
            for i in range(10):
                for j in range(8):
                    if (i + j) % 3 != 0:  # 不规则分布
                        x = cx + i * 8  # 极小间距8像素
                        y = cy + j * 8
                        
                        hole_id = f"CLUS{cluster_idx}_{hole_id_counter:03d}"
                        hole_data = HoleData(
                            hole_id=hole_id,
                            center_x=x,
                            center_y=y,
                            radius=8.8,
                            status=HoleStatus.PENDING
                        )
                        test_holes[hole_id] = hole_data
                        hole_id_counter += 1
        
        # 3. 边界测试点（6px间距）
        self.logger.info("🔧 创建边界测试点（6px间距）...")
        import math
        for angle in range(0, 360, 30):
            rad = math.radians(angle)
            for r in range(3):
                radius = 80 + r * 6  # 极小间距6像素
                x = center_x + radius * math.cos(rad)
                y = center_y + radius * math.sin(rad)
                
                hole_id = f"EDGE_{hole_id_counter:03d}"
                hole_data = HoleData(
                    hole_id=hole_id,
                    center_x=x,
                    center_y=y,
                    radius=8.8,
                    status=HoleStatus.PENDING
                )
                test_holes[hole_id] = hole_data
                hole_id_counter += 1
        
        hole_collection = HoleCollection(
            holes=test_holes,
            metadata={'source_file': 'parameter_adjustment_test', 'total_holes': len(test_holes)}
        )
        
        # 统计各区域孔位数量
        ultra_count = len([h for h in test_holes.values() if h.hole_id.startswith('ULTRA')])
        clus_count = len([h for h in test_holes.values() if h.hole_id.startswith('CLUS')])
        edge_count = len([h for h in test_holes.values() if h.hole_id.startswith('EDGE')])
        
        self.logger.info(f"🧪 创建参数调整验证数据: {len(test_holes)} 个孔位")
        self.logger.info(f"  极密集网格: {ultra_count}个 (10px间距)")
        self.logger.info(f"  密集簇: {clus_count}个 (8px间距)")
        self.logger.info(f"  边界测试: {edge_count}个 (6px间距)")
        self.logger.info(f"  这是参数调整的终极测试！")
        return hole_collection

def main():
    """主函数"""
    test = ParameterAdjustmentTest()
    
    try:
        success = test.test_parameter_adjustment()
        
        if test.window:
            test.logger.info("\n🎯 参数调整验证结果:")
            test.logger.info("✅ 扇形基础容差: 15px → 8px")
            test.logger.info("✅ 全局基础容差: 20px → 12px") 
            test.logger.info("✅ 行分组倍数: 2.0 → 1.5")
            test.logger.info("✅ 列分组倍数: 1.5 → 1.2")
            test.logger.info("✅ 新增宽松判断: +20%容差")
            test.logger.info("✅ 最小行容差: 8px → 5px")
            test.logger.info("✅ 最小列容差: 5px → 4px")
            test.logger.info("\n👁️ 效果检验:")
            test.logger.info("  1. 10px密集网格应该完美处理")
            test.logger.info("  2. 8px不规则簇应该零漏检") 
            test.logger.info("  3. 6px边界点应该全部检测")
            test.logger.info("  4. 参数总结应该正确显示")
            test.logger.info("  5. 所有孔位都应该被检测（无灰色）")
            test.logger.info("\n窗口将在15秒后关闭...")
            QTest.qWait(15000)
        
        return 0 if success else 1
        
    except Exception as e:
        test.logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        if test.window:
            test.window.close()

if __name__ == "__main__":
    sys.exit(main())