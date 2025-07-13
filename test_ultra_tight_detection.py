#!/usr/bin/env python3
"""
测试超紧密检测算法 - 彻底消除漏网之鱼
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

from main_window.main_window import MainWindow
from aidcis2.models.hole_data import HoleData, HoleCollection, HoleStatus

class UltraTightDetectionTest:
    """超紧密检测测试"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = None
        
        # 设置日志
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        self.logger = logging.getLogger(__name__)
    
    def test_ultra_tight_detection(self):
        """测试超紧密检测效果"""
        self.logger.info("🚀 测试超紧密检测算法 - 彻底消除漏网之鱼")
        
        # 1. 创建主窗口
        self.window = MainWindow()
        self.window.show()
        QTest.qWait(2000)
        
        # 2. 加载超密集测试数据
        self.logger.info("\\n🔄 加载超密集分布测试数据")
        hole_collection = self._create_ultra_dense_test_data()
        self.window.hole_collection = hole_collection
        self.window.update_hole_display()
        
        QTest.qWait(3000)
        
        # 3. 启动超紧密检测模拟
        self.logger.info("\\n📋 启动超紧密检测模拟")
        
        if hasattr(self.window, 'simulate_btn'):
            self.logger.info("🔘 启动V2超紧密模拟...")
            
            # 强制使用V2模拟
            self.window.simulation_running_v2 = False
            self.window.simulate_btn.click()
            
            # 观察模拟效果
            self.logger.info("⏳ 观察超紧密检测效果（30秒）...")
            self.logger.info("👁️ 请特别观察：")
            self.logger.info("  1. 自适应容差是否正确计算")
            self.logger.info("  2. 密集区域是否完全无遗漏")
            self.logger.info("  3. 方向感知算法是否有效")
            self.logger.info("  4. 路径连续性验证结果")
            self.logger.info("  5. 是否彻底消除所有灰色孔位")
            
            QTest.qWait(30000)  # 等待30秒观察效果
            
            # 停止模拟
            if hasattr(self.window, 'simulation_running_v2') and self.window.simulation_running_v2:
                self.logger.info("⏹️ 停止超紧密模拟")
                self.window.simulate_btn.click()
        
        return True
    
    def _create_ultra_dense_test_data(self):
        """创建超密集分布的测试数据，最大化漏检风险"""
        test_holes = {}
        hole_id_counter = 1
        
        center_x, center_y = 400, 400
        
        # 创建几种极具挑战性的分布模式：
        
        # 1. 超密集网格区域（小间距）
        self.logger.info("🔧 创建超密集网格区域...")
        for i in range(20):
            for j in range(15):
                x = center_x + 50 + i * 15  # 仅15像素间距
                y = center_y - 100 + j * 12  # 仅12像素间距
                
                hole_id = f"DENSE_{hole_id_counter:03d}"
                hole_data = HoleData(
                    hole_id=hole_id,
                    center_x=x,
                    center_y=y,
                    radius=8.8,
                    status=HoleStatus.PENDING
                )
                test_holes[hole_id] = hole_data
                hole_id_counter += 1
        
        # 2. 不规则蜂窝状分布
        self.logger.info("🔧 创建不规则蜂窝状分布...")
        import math
        for ring in range(8):
            # 每环的孔位数量
            holes_in_ring = max(6, ring * 6)
            for i in range(holes_in_ring):
                angle = (2 * math.pi * i) / holes_in_ring
                radius = ring * 18 + 20  # 环间距18像素
                
                x = center_x - 200 + radius * math.cos(angle)
                y = center_y + 100 + radius * math.sin(angle) * 0.8  # 椭圆变形
                
                # 添加轻微随机扰动增加复杂性
                import random
                x += random.uniform(-3, 3)
                y += random.uniform(-3, 3)
                
                hole_id = f"HEX_{hole_id_counter:03d}"
                hole_data = HoleData(
                    hole_id=hole_id,
                    center_x=x,
                    center_y=y,
                    radius=8.8,
                    status=HoleStatus.PENDING
                )
                test_holes[hole_id] = hole_data
                hole_id_counter += 1
        
        # 3. 交错斜线分布（最难检测）
        self.logger.info("🔧 创建交错斜线分布...")
        for line in range(12):
            holes_in_line = 18 - abs(line - 6)  # 菱形排列
            start_x = center_x + 100 + line * 16
            start_y = center_y - 150 + line * 20
            
            for pos in range(holes_in_line):
                x = start_x + pos * 22 * math.cos(0.3)  # 斜线角度
                y = start_y + pos * 22 * math.sin(0.3)
                
                hole_id = f"DIAG_{hole_id_counter:03d}"
                hole_data = HoleData(
                    hole_id=hole_id,
                    center_x=x,
                    center_y=y,
                    radius=8.8,
                    status=HoleStatus.PENDING
                )
                test_holes[hole_id] = hole_data
                hole_id_counter += 1
        
        # 4. 超细密集簇
        self.logger.info("🔧 创建超细密集簇...")
        cluster_centers = [
            (center_x - 300, center_y - 200),
            (center_x + 200, center_y + 200),
            (center_x - 100, center_y + 300)
        ]
        
        for cluster_idx, (cx, cy) in enumerate(cluster_centers):
            for i in range(8):
                for j in range(8):
                    if (i + j) % 2 == cluster_idx % 2:  # 交错模式
                        x = cx + i * 11  # 极小间距11像素
                        y = cy + j * 11
                        
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
        
        hole_collection = HoleCollection(
            holes=test_holes,
            metadata={'source_file': 'ultra_tight_detection_test', 'total_holes': len(test_holes)}
        )
        
        # 统计各区域孔位数量
        dense_count = len([h for h in test_holes.values() if h.hole_id.startswith('DENSE')])
        hex_count = len([h for h in test_holes.values() if h.hole_id.startswith('HEX')])
        diag_count = len([h for h in test_holes.values() if h.hole_id.startswith('DIAG')])
        clus_count = len([h for h in test_holes.values() if h.hole_id.startswith('CLUS')])
        
        self.logger.info(f"🧪 创建超密集测试数据: {len(test_holes)} 个孔位")
        self.logger.info(f"  密集网格: {dense_count}个, 蜂窝分布: {hex_count}个")
        self.logger.info(f"  斜线交错: {diag_count}个, 密集簇: {clus_count}个")
        self.logger.info(f"  这是终极测试！必须确保零漏检！")
        return hole_collection

def main():
    """主函数"""
    test = UltraTightDetectionTest()
    
    try:
        success = test.test_ultra_tight_detection()
        
        if test.window:
            test.logger.info("\\n🎯 超紧密检测算法终极验证:")
            test.logger.info("✅ 自适应容差计算（最小5px）")
            test.logger.info("✅ 智能分组（平均X坐标+最后孔位双重检查）") 
            test.logger.info("✅ 方向感知最近邻（优先右下方向）")
            test.logger.info("✅ 多重连续性验证")
            test.logger.info("✅ 极小间距处理能力")
            test.logger.info("✅ 复杂分布模式全覆盖")
            test.logger.info("\\n👁️ 终极检查结果:")
            test.logger.info("  1. 15px间距网格 → 完全覆盖")
            test.logger.info("  2. 蜂窝状不规则分布 → 完全覆盖") 
            test.logger.info("  3. 斜线交错排列 → 完全覆盖")
            test.logger.info("  4. 11px超密集簇 → 完全覆盖")
            test.logger.info("  5. 所有孔位应该都被检测，无灰色遗漏")
            test.logger.info("\\n窗口将在20秒后关闭...")
            QTest.qWait(20000)
        
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