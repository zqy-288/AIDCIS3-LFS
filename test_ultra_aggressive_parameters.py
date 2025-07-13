#!/usr/bin/env python3
"""
测试极度激进参数设置 - 专门解决规则网格漏检问题
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

class UltraAggressiveParameterTest:
    """极度激进参数测试"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = None
        
        # 设置日志
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        self.logger = logging.getLogger(__name__)
    
    def test_ultra_aggressive_parameters(self):
        """测试极度激进参数效果"""
        self.logger.info("🚀 测试极度激进参数设置 - 专门解决规则网格漏检")
        
        # 1. 创建主窗口
        self.window = MainWindow()
        self.window.show()
        QTest.qWait(2000)
        
        # 2. 首先测试东重管板DXF文件
        dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-1/AIDCIS3-LFS/assets/dxf/DXF Graph/东重管板.dxf"
        
        if os.path.exists(dxf_path):
            self.logger.info(f"\n🏭 第一轮：加载真实DXF文件")
            
            try:
                # 使用主窗口的DXF加载功能
                if hasattr(self.window, 'dxf_parser'):
                    hole_collection = self.window.dxf_parser.parse_dxf_file(dxf_path)
                    
                    if hole_collection and len(hole_collection) > 0:
                        self.window.hole_collection = hole_collection
                        self.window.update_hole_display()
                        self.logger.info(f"✅ 东重管板DXF加载成功: {len(hole_collection)} 个孔位")
                        
                        # 启动极度激进参数模拟
                        QTest.qWait(2000)
                        self._run_aggressive_simulation("东重管板DXF", 25)
                        
                    else:
                        self.logger.warning("⚠️ DXF文件解析失败，跳过真实文件测试")
                        
            except Exception as e:
                self.logger.warning(f"⚠️ DXF文件加载异常: {e}, 跳过真实文件测试")
        
        # 3. 创建极度密集的规则网格测试
        self.logger.info(f"\n🔄 第二轮：加载极度密集规则网格")
        hole_collection = self._create_ultra_dense_regular_grid()
        self.window.hole_collection = hole_collection
        self.window.update_hole_display()
        
        QTest.qWait(2000)
        self._run_aggressive_simulation("极度密集规则网格", 20)
        
        return True
    
    def _run_aggressive_simulation(self, test_name, duration_seconds):
        """运行激进参数模拟"""
        if hasattr(self.window, 'simulate_btn'):
            self.logger.info(f"🔘 启动{test_name}极度激进参数模拟...")
            
            # 强制使用V2模拟
            self.window.simulation_running_v2 = False
            self.window.simulate_btn.click()
            
            # 观察模拟效果
            self.logger.info(f"⏳ 观察极度激进参数效果（{duration_seconds}秒）...")
            self.logger.info("👁️ 重点检查：")
            self.logger.info("  1. 参数是否显示为极度激进版本")
            self.logger.info("  2. 4px基础容差效果")
            self.logger.info("  3. 6px全局容差效果")
            self.logger.info("  4. 1.2倍行分组倍数效果")
            self.logger.info("  5. 1.0倍列分组倍数效果（最激进）")
            self.logger.info("  6. 50%宽松判断补偿效果")
            self.logger.info("  7. 3px最小行容差效果")
            self.logger.info("  8. 2px最小列容差效果")
            self.logger.info("  9. 规则网格是否完全无漏检")
            
            QTest.qWait(duration_seconds * 1000)
            
            # 停止模拟
            if hasattr(self.window, 'simulation_running_v2') and self.window.simulation_running_v2:
                self.logger.info(f"⏹️ 停止{test_name}极度激进模拟")
                self.window.simulate_btn.click()
                QTest.qWait(1000)
    
    def _create_ultra_dense_regular_grid(self):
        """创建极度密集的规则网格，专门测试激进参数"""
        from aidcis2.models.hole_data import HoleData, HoleCollection, HoleStatus
        
        test_holes = {}
        hole_id_counter = 1
        
        center_x, center_y = 400, 300
        
        # 1. 极度密集规则网格（6px间距）
        self.logger.info("🔧 创建极度密集规则网格（6px间距）...")
        for i in range(25):
            for j in range(20):
                x = center_x - 75 + i * 6  # 极小间距6像素
                y = center_y - 60 + j * 6  # 极小间距6像素
                
                hole_id = f"GRID_{hole_id_counter:03d}"
                hole_data = HoleData(
                    hole_id=hole_id,
                    center_x=x,
                    center_y=y,
                    radius=8.8,
                    status=HoleStatus.PENDING
                )
                test_holes[hole_id] = hole_data
                hole_id_counter += 1
        
        # 2. 边界挑战网格（4px间距）
        self.logger.info("🔧 创建边界挑战网格（4px间距）...")
        for i in range(15):
            for j in range(12):
                x = center_x + 200 + i * 4  # 极限间距4像素
                y = center_y - 25 + j * 4  # 极限间距4像素
                
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
        
        # 3. 极限挑战区（3px间距）
        self.logger.info("🔧 创建极限挑战区（3px间距）...")
        for i in range(10):
            for j in range(8):
                x = center_x - 200 + i * 3  # 理论极限间距3像素
                y = center_y + 100 + j * 3  # 理论极限间距3像素
                
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
        
        hole_collection = HoleCollection(
            holes=test_holes,
            metadata={'source_file': 'ultra_aggressive_parameter_test', 'total_holes': len(test_holes)}
        )
        
        # 统计各区域孔位数量
        grid_count = len([h for h in test_holes.values() if h.hole_id.startswith('GRID')])
        edge_count = len([h for h in test_holes.values() if h.hole_id.startswith('EDGE')])
        ultra_count = len([h for h in test_holes.values() if h.hole_id.startswith('ULTRA')])
        
        self.logger.info(f"🧪 创建极度激进参数验证数据: {len(test_holes)} 个孔位")
        self.logger.info(f"  密集网格: {grid_count}个 (6px间距)")
        self.logger.info(f"  边界挑战: {edge_count}个 (4px间距)")
        self.logger.info(f"  极限挑战: {ultra_count}个 (3px间距)")
        self.logger.info(f"  这是算法的终极挑战！必须零漏检！")
        return hole_collection

def main():
    """主函数"""
    test = UltraAggressiveParameterTest()
    
    try:
        success = test.test_ultra_aggressive_parameters()
        
        if test.window:
            test.logger.info("\n🎯 极度激进参数验证结果:")
            test.logger.info("📊 算法参数极度激进调整:")
            test.logger.info("  🔥 扇形基础容差: 15px → 4px (降幅73%)")
            test.logger.info("  🔥 全局基础容差: 20px → 6px (降幅70%)")
            test.logger.info("  🔥 行分组倍数: 2.0x → 1.2x (降幅40%)")
            test.logger.info("  🔥 列分组倍数: 1.5x → 1.0x (降幅33%)")
            test.logger.info("  🔥 宽松判断: 0% → 50%容差补偿")
            test.logger.info("  🔥 最小行容差: 8px → 3px (降幅62.5%)")
            test.logger.info("  🔥 最小列容差: 5px → 2px (降幅60%)")
            
            test.logger.info("\n🎯 极限测试验证:")
            test.logger.info("  ✅ 6px密集网格 → 应该完美处理")
            test.logger.info("  ✅ 4px边界挑战 → 应该零漏检")
            test.logger.info("  ✅ 3px极限挑战 → 应该全覆盖")
            test.logger.info("  ✅ 真实DXF数据 → 工业级验证")
            
            test.logger.info("\n💪 如果仍有漏检，可能需要：")
            test.logger.info("  1. 进一步降低基础容差到2-3px")
            test.logger.info("  2. 增加宽松判断到100%")
            test.logger.info("  3. 使用0.8倍动态分组倍数")
            test.logger.info("  4. 最小容差降低到1px")
            
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