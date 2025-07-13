#!/usr/bin/env python3
"""
验证漏检修复效果
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

class FixVerificationTest:
    """修复效果验证测试"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = None
        
        # 设置日志
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        self.logger = logging.getLogger(__name__)
    
    def verify_fix(self):
        """验证修复效果"""
        self.logger.info("🔧 验证漏检修复效果")
        
        # 1. 创建主窗口
        self.window = MainWindow()
        self.window.show()
        QTest.qWait(2000)
        
        # 2. 加载DXF文件
        dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-1/AIDCIS3-LFS/assets/dxf/DXF Graph/东重管板.dxf"
        
        if not os.path.exists(dxf_path):
            self.logger.error(f"❌ DXF文件不存在: {dxf_path}")
            return False
        
        try:
            if hasattr(self.window, 'dxf_parser'):
                hole_collection = self.window.dxf_parser.parse_file(dxf_path)
                
                if hole_collection and len(hole_collection) > 0:
                    self.window.hole_collection = hole_collection
                    self.window.update_hole_display()
                    self.logger.info(f"✅ DXF文件加载成功: {len(hole_collection)} 个孔位")
                    
                    holes_list = list(hole_collection)
                    
                    # 3. 测试检测算法
                    detection_path = self.window._create_spiral_detection_path(holes_list)
                    
                    self.logger.info(f"\n📊 检测路径分析:")
                    self.logger.info(f"  原始孔位数: {len(holes_list)}")
                    self.logger.info(f"  检测路径数: {len(detection_path)}")
                    self.logger.info(f"  是否完整: {'✅ 是' if len(detection_path) == len(holes_list) else '❌ 否'}")
                    
                    # 4. 检查前50个孔位的连续性
                    self.logger.info(f"\n📋 检测路径前50个孔位:")
                    for i, hole in enumerate(detection_path[:50]):
                        self.logger.info(f"  {i+1:2d}. {hole.hole_id} at ({hole.center_x:7.1f}, {hole.center_y:7.1f})")
                    
                    # 5. 检查是否还有跳跃
                    has_jumps = False
                    max_jump = 0
                    for i in range(1, min(100, len(detection_path))):
                        prev_hole = detection_path[i-1]
                        curr_hole = detection_path[i]
                        
                        # 计算X坐标跳跃距离
                        x_jump = abs(curr_hole.center_x - prev_hole.center_x)
                        if x_jump > max_jump:
                            max_jump = x_jump
                        
                        # 如果在同一行（Y坐标相近）但X跳跃过大，说明有问题
                        y_diff = abs(curr_hole.center_y - prev_hole.center_y)
                        if y_diff < 5 and x_jump > 100:  # 同一行内跳跃超过100像素
                            self.logger.warning(f"  ⚠️ 发现跳跃: {prev_hole.hole_id} -> {curr_hole.hole_id}, X跳跃: {x_jump:.1f}px")
                            has_jumps = True
                    
                    self.logger.info(f"\n🎯 跳跃检测结果:")
                    self.logger.info(f"  最大X跳跃: {max_jump:.1f}px")
                    self.logger.info(f"  是否有异常跳跃: {'❌ 是' if has_jumps else '✅ 否'}")
                    
                    # 6. 运行短时间模拟验证
                    self.logger.info(f"\n🚀 运行模拟验证...")
                    if hasattr(self.window, 'simulate_btn'):
                        self.window.simulation_running_v2 = False
                        self.window.simulate_btn.click()
                        
                        # 等待3秒观察
                        QTest.qWait(3000)
                        
                        # 停止模拟
                        if hasattr(self.window, 'simulation_running_v2') and self.window.simulation_running_v2:
                            self.window.simulate_btn.click()
                        
                        self.logger.info("✅ 模拟验证完成")
                    
                    # 7. 总结
                    success = (len(detection_path) == len(holes_list)) and not has_jumps
                    return success
                    
                else:
                    self.logger.error("❌ DXF文件解析失败")
                    return False
            else:
                self.logger.error("❌ 主窗口缺少DXF解析器")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 验证异常: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """主函数"""
    test = FixVerificationTest()
    
    try:
        success = test.verify_fix()
        
        test.logger.info("\n" + "="*60)
        test.logger.info("🎯 漏检修复验证结果")
        test.logger.info("="*60)
        
        if success:
            test.logger.info("✅ 修复成功！")
            test.logger.info("✅ 检测算法已完整覆盖所有孔位")
            test.logger.info("✅ 无异常跳跃，路径连续")
        else:
            test.logger.info("❌ 修复失败！")
            test.logger.info("❌ 仍存在漏检或跳跃问题")
        
        test.logger.info("\n🔧 已应用的修复:")
        test.logger.info("  1. 扇形基础容差：4px → 15px")
        test.logger.info("  2. 全局基础容差：6px → 20px") 
        test.logger.info("  3. 行分组倍数：1.2x → 2.0x")
        test.logger.info("  4. 列分组倍数：1.0x → 1.5x")
        test.logger.info("  5. 宽松判断：1.5x → 2.0x")
        test.logger.info("  6. 最小行容差：3px → 8px")
        test.logger.info("  7. 最小列容差：2px → 5px")
        
        if test.window:
            test.logger.info("\n窗口将在10秒后关闭...")
            QTest.qWait(10000)
        
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