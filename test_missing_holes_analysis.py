#!/usr/bin/env python3
"""
分析缺失孔位的具体位置
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

class MissingHolesAnalysis:
    """缺失孔位分析"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = None
        
        # 设置日志
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        self.logger = logging.getLogger(__name__)
    
    def analyze_missing_holes(self):
        """分析缺失的孔位"""
        self.logger.info("🔍 分析缺失孔位")
        
        # 1. 创建主窗口
        self.window = MainWindow()
        self.window.show()
        QTest.qWait(1000)
        
        # 2. 加载DXF文件
        dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-1/AIDCIS3-LFS/assets/dxf/DXF Graph/东重管板.dxf"
        
        try:
            hole_collection = self.window.dxf_parser.parse_file(dxf_path)
            self.window.hole_collection = hole_collection
            
            holes_list = list(hole_collection)
            
            # 3. 分析第一行的孔位
            first_row_holes = [h for h in holes_list if abs(h.center_y - (-2092.9)) < 5]
            first_row_holes.sort(key=lambda h: h.center_x)
            
            self.logger.info(f"\n📍 第一行孔位分析 (Y≈-2092.9):")
            self.logger.info(f"第一行总孔位数: {len(first_row_holes)}")
            
            # 找出X坐标范围
            x_coords = [h.center_x for h in first_row_holes]
            self.logger.info(f"X坐标范围: {min(x_coords):.1f} 到 {max(x_coords):.1f}")
            
            # 检查孔位编号的连续性
            hole_numbers = []
            for hole in first_row_holes:
                # hole_id 可能是字符串格式 "(col,row)"
                hole_id_str = str(hole.hole_id)
                self.logger.info(f"孔位ID格式: {hole_id_str} (类型: {type(hole.hole_id)})")
                
                if isinstance(hole.hole_id, tuple):
                    col, row = hole.hole_id
                else:
                    # 如果是字符串，需要解析
                    import re
                    match = re.search(r'\((\d+),(\d+)\)', hole_id_str)
                    if match:
                        col, row = int(match.group(1)), int(match.group(2))
                    else:
                        continue
                
                hole_numbers.append(col)
                break  # 只检查第一个，了解格式
            
            hole_numbers.sort()
            self.logger.info(f"孔位编号范围: {min(hole_numbers)} 到 {max(hole_numbers)}")
            
            # 找出缺失的孔位编号
            expected_range = list(range(min(hole_numbers), max(hole_numbers) + 1))
            missing_numbers = set(expected_range) - set(hole_numbers)
            
            if missing_numbers:
                self.logger.info(f"❌ 缺失的孔位编号: {sorted(missing_numbers)}")
                self.logger.info(f"缺失数量: {len(missing_numbers)}")
                
                # 分析缺失区域
                missing_sorted = sorted(missing_numbers)
                consecutive_groups = []
                current_group = [missing_sorted[0]]
                
                for i in range(1, len(missing_sorted)):
                    if missing_sorted[i] == missing_sorted[i-1] + 1:
                        current_group.append(missing_sorted[i])
                    else:
                        consecutive_groups.append(current_group)
                        current_group = [missing_sorted[i]]
                consecutive_groups.append(current_group)
                
                self.logger.info(f"缺失区域分析:")
                for i, group in enumerate(consecutive_groups):
                    if len(group) == 1:
                        self.logger.info(f"  区域 {i+1}: 孔位 {group[0]}")
                    else:
                        self.logger.info(f"  区域 {i+1}: 孔位 {group[0]}-{group[-1]} ({len(group)}个)")
                        
                        # 计算缺失区域的X坐标
                        if group[0] > min(hole_numbers) and group[-1] < max(hole_numbers):
                            # 找到缺失区域前后的孔位
                            before_holes = [h for h in first_row_holes if h.hole_id[0] == group[0] - 1]
                            after_holes = [h for h in first_row_holes if h.hole_id[0] == group[-1] + 1]
                            
                            if before_holes and after_holes:
                                before_x = before_holes[0].center_x
                                after_x = after_holes[0].center_x
                                gap_size = after_x - before_x
                                self.logger.info(f"    X坐标间隙: {before_x:.1f} 到 {after_x:.1f} (间隙: {gap_size:.1f}px)")
                
            else:
                self.logger.info("✅ 第一行孔位编号连续，无缺失")
            
            # 4. 显示第一行前20个和后20个孔位
            self.logger.info(f"\n📋 第一行前20个孔位:")
            for i, hole in enumerate(first_row_holes[:20]):
                self.logger.info(f"  {i+1:2d}. {hole.hole_id} at ({hole.center_x:7.1f}, {hole.center_y:7.1f})")
            
            if len(first_row_holes) > 40:
                self.logger.info(f"\n📋 第一行后20个孔位:")
                for i, hole in enumerate(first_row_holes[-20:]):
                    idx = len(first_row_holes) - 20 + i + 1
                    self.logger.info(f"  {idx:2d}. {hole.hole_id} at ({hole.center_x:7.1f}, {hole.center_y:7.1f})")
            
            return len(missing_numbers) == 0
            
        except Exception as e:
            self.logger.error(f"❌ 分析异常: {e}")
            return False

def main():
    """主函数"""
    test = MissingHolesAnalysis()
    
    try:
        success = test.analyze_missing_holes()
        
        if success:
            test.logger.info("\n✅ 分析完成：孔位连续")
        else:
            test.logger.info("\n❌ 分析完成：发现缺失孔位")
        
        if test.window:
            test.window.close()
        
        return 0 if success else 1
        
    except Exception as e:
        test.logger.error(f"❌ 分析失败: {e}")
        return 1
    finally:
        if test.window:
            test.window.close()

if __name__ == "__main__":
    sys.exit(main())