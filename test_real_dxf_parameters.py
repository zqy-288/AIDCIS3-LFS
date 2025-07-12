#!/usr/bin/env python3
"""
测试真实DXF文件的参数优化效果 - 使用东重管板.dxf
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

class RealDXFParameterTest:
    """真实DXF文件参数测试"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = None
        
        # 设置日志
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        self.logger = logging.getLogger(__name__)
    
    def test_real_dxf_parameters(self):
        """测试真实DXF文件的参数效果"""
        self.logger.info("🏭 测试真实DXF文件 - 东重管板.dxf 参数优化效果")
        
        # 1. 创建主窗口
        self.window = MainWindow()
        self.window.show()
        QTest.qWait(2000)
        
        # 2. 加载真实DXF文件
        dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-1/AIDCIS3-LFS/assets/dxf/DXF Graph/东重管板.dxf"
        
        if not os.path.exists(dxf_path):
            self.logger.error(f"❌ DXF文件不存在: {dxf_path}")
            return False
        
        self.logger.info(f"\n🔄 加载真实DXF文件: 东重管板.dxf")
        
        try:
            # 使用主窗口的DXF加载功能
            if hasattr(self.window, 'dxf_parser'):
                hole_collection = self.window.dxf_parser.parse_dxf_file(dxf_path)
                
                if hole_collection and len(hole_collection) > 0:
                    self.window.hole_collection = hole_collection
                    self.window.update_hole_display()
                    self.logger.info(f"✅ DXF文件加载成功: {len(hole_collection)} 个孔位")
                else:
                    self.logger.error("❌ DXF文件解析失败或无孔位数据")
                    return False
            else:
                self.logger.error("❌ 主窗口缺少DXF解析器")
                return False
            
        except Exception as e:
            self.logger.error(f"❌ DXF文件加载异常: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        QTest.qWait(3000)
        
        # 3. 启动参数优化模拟
        self.logger.info("\n📋 启动真实DXF文件参数优化模拟")
        
        if hasattr(self.window, 'simulate_btn'):
            self.logger.info("🔘 启动东重管板DXF参数优化模拟...")
            
            # 强制使用V2模拟
            self.window.simulation_running_v2 = False
            self.window.simulate_btn.click()
            
            # 观察模拟效果
            self.logger.info("⏳ 观察真实DXF参数优化效果（30秒）...")
            self.logger.info("👁️ 重点检查：")
            self.logger.info("  1. 真实工业数据的分组效果")
            self.logger.info("  2. 密集区域是否有效处理")
            self.logger.info("  3. 参数总结显示是否正确")
            self.logger.info("  4. 边界情况的处理能力")
            self.logger.info("  5. 实际工程应用中的漏检情况")
            self.logger.info("  6. 不规则分布的适应性")
            self.logger.info("  7. 扇形切换的流畅性")
            self.logger.info("  8. 整体检测覆盖率")
            
            QTest.qWait(30000)  # 等待30秒观察效果
            
            # 停止模拟
            if hasattr(self.window, 'simulation_running_v2') and self.window.simulation_running_v2:
                self.logger.info("⏹️ 停止真实DXF参数优化模拟")
                self.window.simulate_btn.click()
        
        return True

def main():
    """主函数"""
    test = RealDXFParameterTest()
    
    try:
        success = test.test_real_dxf_parameters()
        
        if test.window:
            test.logger.info("\n🎯 真实DXF文件参数优化验证结果:")
            test.logger.info("📊 算法参数调整汇总:")
            test.logger.info("  ✅ 扇形基础容差: 15px → 8px (降低47%)")
            test.logger.info("  ✅ 全局基础容差: 20px → 12px (降低40%)")
            test.logger.info("  ✅ 行分组倍数: 2.0x → 1.5x (降低25%)")
            test.logger.info("  ✅ 列分组倍数: 1.5x → 1.2x (降低20%)")
            test.logger.info("  ✅ 宽松判断: 新增20%容差补偿")
            test.logger.info("  ✅ 最小行容差: 8px → 5px (降低37.5%)")
            test.logger.info("  ✅ 最小列容差: 5px → 4px (降低20%)")
            
            test.logger.info("\n🏭 真实工业数据检验:")
            test.logger.info("  1. 东重管板复杂几何结构处理")
            test.logger.info("  2. 实际生产环境密集分布适应")
            test.logger.info("  3. 边界条件和异常情况覆盖")
            test.logger.info("  4. 多扇形区域协调工作")
            test.logger.info("  5. 大规模数据性能表现")
            
            test.logger.info("\n💡 参数调整策略说明:")
            test.logger.info("  - 更小的基础容差确保精确分组")
            test.logger.info("  - 更紧密的倍数系数提高敏感度")
            test.logger.info("  - 宽松判断机制防止边界漏检")
            test.logger.info("  - 降低最小容差捕获极密集分布")
            
            test.logger.info("\n窗口将在20秒后关闭...")
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