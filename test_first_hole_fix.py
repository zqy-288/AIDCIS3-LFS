#!/usr/bin/env python3
"""
测试第一第二个洞漏检问题的修复
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

class FirstHoleFixTest:
    """第一第二个洞漏检修复测试"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = None
        
        # 设置日志
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        self.logger = logging.getLogger(__name__)
    
    def test_first_hole_detection(self):
        """测试第一第二个洞的检测"""
        self.logger.info("🔍 测试第一第二个洞漏检修复")
        
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
                    
                    # 3. 分析前10个孔位的坐标
                    holes_list = list(hole_collection)
                    sorted_holes = sorted(holes_list, key=lambda h: (h.center_y, h.center_x))
                    
                    self.logger.info("\n📍 前10个孔位坐标分析:")
                    for i, hole in enumerate(sorted_holes[:10]):
                        self.logger.info(f"  {i+1}. 孔位{hole.hole_id}: X={hole.center_x:.1f}, Y={hole.center_y:.1f}")
                    
                    # 4. 测试算法路径
                    if hasattr(self.window, '_create_spiral_detection_path'):
                        detection_path = self.window._create_spiral_detection_path(holes_list)
                        
                        self.logger.info("\n🛤️ 算法检测路径前10个:")
                        for i, hole in enumerate(detection_path[:10]):
                            self.logger.info(f"  {i+1}. 孔位{hole.hole_id}: X={hole.center_x:.1f}, Y={hole.center_y:.1f}")
                        
                        # 5. 检查是否有遗漏
                        first_10_sorted_ids = {h.hole_id for h in sorted_holes[:10]}
                        first_10_path_ids = {h.hole_id for h in detection_path[:10]}
                        
                        missing_holes = first_10_sorted_ids - first_10_path_ids
                        if missing_holes:
                            self.logger.error(f"❌ 发现漏检的孔位: {missing_holes}")
                            return False
                        else:
                            self.logger.info("✅ 前10个孔位全部包含在检测路径中")
                            return True
                else:
                    self.logger.error("❌ DXF文件解析失败")
                    return False
            else:
                self.logger.error("❌ 主窗口缺少DXF解析器")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """主函数"""
    test = FirstHoleFixTest()
    
    try:
        success = test.test_first_hole_detection()
        
        if success:
            test.logger.info("\n🎯 第一第二个洞漏检问题测试结果: ✅ 通过")
        else:
            test.logger.info("\n🎯 第一第二个洞漏检问题测试结果: ❌ 失败")
            test.logger.info("\n💡 建议的修复步骤:")
            test.logger.info("1. 修改起始点选择算法")
            test.logger.info("2. 调整行分组容差参数") 
            test.logger.info("3. 添加前10个孔位特殊处理")
        
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