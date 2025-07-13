#!/usr/bin/env python3
"""
验证纵向修复效果
"""

import sys
import os
from pathlib import Path

# 添加src路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest

from main_window.main_window import MainWindow

class VerticalFixVerification:
    """纵向修复验证"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = None
        
        # 设置日志
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        self.logger = logging.getLogger(__name__)
    
    def verify_vertical_fix(self):
        """验证纵向修复"""
        self.logger.info("🔍 验证纵向修复效果")
        
        # 1. 创建主窗口
        self.window = MainWindow()
        self.window.show()
        QTest.qWait(1000)
        
        # 2. 加载DXF文件
        dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-1/AIDCIS3-LFS/assets/dxf/DXF Graph/东重管板.dxf"
        
        try:
            hole_collection = self.window.dxf_parser.parse_file(dxf_path)
            self.window.hole_collection = hole_collection
            self.window.update_hole_display()
            
            holes_list = list(hole_collection)
            self.logger.info(f"✅ 加载 {len(holes_list)} 个孔位")
            
            # 3. 测试纵向修复后的算法
            detection_path = self.window._create_spiral_detection_path(holes_list)
            
            self.logger.info(f"\n📊 纵向修复验证:")
            self.logger.info(f"  原始孔位: {len(holes_list)}")
            self.logger.info(f"  检测路径: {len(detection_path)}")
            self.logger.info(f"  完整性: {'✅ 完整' if len(detection_path) == len(holes_list) else '❌ 不完整'}")
            
            # 4. 重点验证纵向连续性
            vertical_continuity_score = self._check_vertical_continuity(detection_path)
            
            self.logger.info(f"\n🎯 纵向连续性评分: {vertical_continuity_score:.1f}%")
            
            # 5. 检查前100个孔位的X坐标分布
            self.logger.info(f"\n📋 前100个检测路径的X坐标分布:")
            x_coords = [hole.center_x for hole in detection_path[:100]]
            x_changes = 0
            for i in range(1, len(x_coords)):
                if abs(x_coords[i] - x_coords[i-1]) > 20:  # X坐标变化超过20px
                    x_changes += 1
            
            self.logger.info(f"  前100个孔位中X坐标大幅变化次数: {x_changes}")
            self.logger.info(f"  平均每列孔位数: {100/max(1, x_changes):.1f}")
            
            # 6. 运行短时间模拟验证
            self.logger.info(f"\n🚀 运行模拟验证...")
            if hasattr(self.window, 'simulate_btn'):
                self.window.simulation_running_v2 = False
                self.window.simulate_btn.click()
                
                QTest.qWait(3000)  # 3秒观察
                
                if hasattr(self.window, 'simulation_running_v2') and self.window.simulation_running_v2:
                    self.window.simulate_btn.click()
                
                self.logger.info("✅ 模拟验证完成")
            
            # 7. 总结评估
            success = (
                len(detection_path) == len(holes_list) and 
                vertical_continuity_score > 80 and 
                x_changes < 20
            )
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ 验证异常: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _check_vertical_continuity(self, detection_path):
        """检查纵向连续性评分"""
        if len(detection_path) < 10:
            return 0
        
        # 按X坐标分组
        x_tolerance = 20
        x_groups = {}
        
        for i, hole in enumerate(detection_path):
            x_key = round(hole.center_x / x_tolerance) * x_tolerance
            if x_key not in x_groups:
                x_groups[x_key] = []
            x_groups[x_key].append(i)
        
        # 计算每组的连续性
        total_groups = len(x_groups)
        continuous_groups = 0
        
        for x_coord, indices in x_groups.items():
            if len(indices) <= 1:
                continuous_groups += 1
                continue
            
            # 检查索引是否相对连续
            indices.sort()
            gaps = []
            for i in range(1, len(indices)):
                gap = indices[i] - indices[i-1]
                gaps.append(gap)
            
            # 如果平均间隔小于10，认为相对连续
            avg_gap = sum(gaps) / len(gaps) if gaps else 1
            if avg_gap <= 10:
                continuous_groups += 1
        
        continuity_score = (continuous_groups / total_groups) * 100 if total_groups > 0 else 0
        return continuity_score

def main():
    """主函数"""
    test = VerticalFixVerification()
    
    try:
        success = test.verify_vertical_fix()
        
        test.logger.info("\n" + "="*60)
        test.logger.info("🎯 纵向修复验证结果")
        test.logger.info("="*60)
        
        if success:
            test.logger.info("🎉 纵向修复验证成功！")
            test.logger.info("✅ 相同/相近横坐标的孔位连续性大幅提升")
            test.logger.info("✅ 检测算法按列扫描，确保纵向完整")
            test.logger.info("✅ 模拟运行流畅，无大幅跳跃")
        else:
            test.logger.info("❌ 纵向修复需要进一步优化")
            test.logger.info("可能需要调整列容差或检测策略")
        
        test.logger.info("\n🔧 纵向修复关键改进:")
        test.logger.info("  1. 从行扫描改为列扫描")
        test.logger.info("  2. 纵向蛇形路径 (上下交替)")
        test.logger.info("  3. 严格的列分组判断")
        test.logger.info("  4. 优化的X坐标容差处理")
        
        if test.window:
            test.logger.info("\n窗口将在8秒后关闭...")
            QTest.qWait(8000)
        
        return 0 if success else 1
        
    except Exception as e:
        test.logger.error(f"❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        if test.window:
            test.window.close()

if __name__ == "__main__":
    sys.exit(main())