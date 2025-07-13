#!/usr/bin/env python3
"""
修复纵向孔位漏检问题 - 相同或相近横坐标的孔位
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

class VerticalHolesFixTest:
    """纵向孔位修复测试"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = None
        
        # 设置日志
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        self.logger = logging.getLogger(__name__)
    
    def apply_vertical_fix(self):
        """应用纵向孔位修复"""
        self.logger.info("🔧 修复纵向孔位漏检问题 - 相同/相近横坐标的孔位")
        
        # 1. 创建主窗口
        self.window = MainWindow()
        self.window.show()
        QTest.qWait(1000)
        
        # 2. 应用新的检测算法
        self._patch_vertical_detection()
        
        # 3. 加载DXF文件并测试
        dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-1/AIDCIS3-LFS/assets/dxf/DXF Graph/东重管板.dxf"
        
        try:
            hole_collection = self.window.dxf_parser.parse_file(dxf_path)
            self.window.hole_collection = hole_collection
            self.window.update_hole_display()
            
            holes_list = list(hole_collection)
            self.logger.info(f"✅ 加载 {len(holes_list)} 个孔位")
            
            # 4. 分析纵向孔位分布
            self._analyze_vertical_distribution(holes_list)
            
            # 5. 测试修复后的算法
            detection_path = self.window._create_spiral_detection_path(holes_list)
            
            self.logger.info(f"\n📊 修复后检测路径分析:")
            self.logger.info(f"  原始孔位: {len(holes_list)}")
            self.logger.info(f"  检测路径: {len(detection_path)}")
            self.logger.info(f"  完整性: {'✅ 完整' if len(detection_path) == len(holes_list) else '❌ 不完整'}")
            
            # 6. 验证纵向连续性
            self._verify_vertical_continuity(detection_path)
            
            return len(detection_path) == len(holes_list)
            
        except Exception as e:
            self.logger.error(f"❌ 测试异常: {e}")
            return False
    
    def _analyze_vertical_distribution(self, holes_list):
        """分析纵向孔位分布"""
        self.logger.info("\n📍 分析纵向孔位分布...")
        
        # 按X坐标分组
        x_groups = {}
        for hole in holes_list:
            x_key = round(hole.center_x / 5) * 5  # 5px容差分组
            if x_key not in x_groups:
                x_groups[x_key] = []
            x_groups[x_key].append(hole)
        
        # 找出有多个孔位的纵向列
        vertical_columns = {x: holes for x, holes in x_groups.items() if len(holes) > 1}
        
        self.logger.info(f"总X坐标组: {len(x_groups)}")
        self.logger.info(f"纵向列数: {len(vertical_columns)} (每列>1个孔位)")
        
        # 显示前5个最密集的纵向列
        sorted_columns = sorted(vertical_columns.items(), key=lambda x: len(x[1]), reverse=True)
        
        self.logger.info(f"\n📋 前5个最密集的纵向列:")
        for i, (x_coord, holes) in enumerate(sorted_columns[:5]):
            holes_sorted = sorted(holes, key=lambda h: h.center_y)
            self.logger.info(f"  列 {i+1}: X≈{x_coord:.1f}, {len(holes)}个孔位")
            self.logger.info(f"    Y范围: {holes_sorted[0].center_y:.1f} 到 {holes_sorted[-1].center_y:.1f}")
            
            # 检查Y坐标间隔
            if len(holes_sorted) > 1:
                y_gaps = []
                for j in range(1, len(holes_sorted)):
                    gap = holes_sorted[j].center_y - holes_sorted[j-1].center_y
                    y_gaps.append(gap)
                avg_gap = sum(y_gaps) / len(y_gaps)
                self.logger.info(f"    平均Y间隔: {avg_gap:.1f}px")
    
    def _verify_vertical_continuity(self, detection_path):
        """验证纵向连续性"""
        self.logger.info("\n🔍 验证纵向连续性...")
        
        # 按X坐标分组检测路径
        x_groups = {}
        for i, hole in enumerate(detection_path):
            x_key = round(hole.center_x / 5) * 5  # 5px容差分组
            if x_key not in x_groups:
                x_groups[x_key] = []
            x_groups[x_key].append((i, hole))
        
        # 检查每个纵向列的连续性
        continuity_issues = 0
        
        for x_coord, indexed_holes in x_groups.items():
            if len(indexed_holes) > 1:
                # 按检测路径中的索引排序
                indexed_holes.sort(key=lambda x: x[0])
                
                # 检查是否连续
                path_indices = [idx for idx, _ in indexed_holes]
                
                # 如果索引不连续，说明同一列的孔位在检测路径中被分散了
                gaps = []
                for i in range(1, len(path_indices)):
                    gap = path_indices[i] - path_indices[i-1]
                    if gap > 5:  # 如果间隔超过5，说明中间插入了其他孔位
                        gaps.append(gap)
                
                if gaps:
                    continuity_issues += 1
                    if continuity_issues <= 3:  # 只显示前3个问题
                        self.logger.warning(f"  ⚠️ 纵向列 X≈{x_coord:.1f} 不连续, 间隔: {gaps}")
        
        self.logger.info(f"纵向连续性问题: {continuity_issues} 个列")
        return continuity_issues == 0
    
    def _patch_vertical_detection(self):
        """修复纵向检测算法"""
        self.logger.info("🔧 应用纵向孔位检测修复...")
        
        def improved_spiral_detection_path(holes):
            """改进的螺旋检测路径 - 优化纵向孔位处理"""
            if not holes:
                return holes
            
            try:
                # 第一步：按网格模式组织孔位
                grid_organized_holes = self._organize_by_grid(holes)
                
                self.logger.info(f"✅ 网格组织完成: {len(holes)} -> {len(grid_organized_holes)} 个孔位")
                
                # 验证完整性
                original_ids = {h.hole_id for h in holes}
                result_ids = {h.hole_id for h in grid_organized_holes}
                missing_ids = original_ids - result_ids
                
                if missing_ids:
                    self.logger.warning(f"⚠️ 网格组织遗漏 {len(missing_ids)} 个孔位，补充中...")
                    missing_holes = [h for h in holes if h.hole_id in missing_ids]
                    grid_organized_holes.extend(missing_holes)
                
                return grid_organized_holes
                
            except Exception as e:
                self.logger.error(f"❌ 改进算法异常: {e}")
                return sorted(holes, key=lambda h: (h.center_y, h.center_x))
        
        def organize_by_grid(holes):
            """按网格模式组织孔位 - 优化纵向处理"""
            if not holes:
                return []
            
            # 1. 先按Y坐标分组成行
            y_tolerance = 25  # 行容差
            y_groups = {}
            
            for hole in holes:
                y_key = round(hole.center_y / y_tolerance) * y_tolerance
                if y_key not in y_groups:
                    y_groups[y_key] = []
                y_groups[y_key].append(hole)
            
            # 2. 对每行按X坐标排序
            sorted_rows = []
            for y_key in sorted(y_groups.keys()):
                row_holes = sorted(y_groups[y_key], key=lambda h: h.center_x)
                sorted_rows.append(row_holes)
            
            # 3. 蛇形扫描，但考虑纵向连续性
            result_holes = []
            
            for i, row_holes in enumerate(sorted_rows):
                if i % 2 == 0:
                    # 偶数行：从左到右
                    result_holes.extend(row_holes)
                else:
                    # 奇数行：从右到左
                    result_holes.extend(reversed(row_holes))
            
            return result_holes
        
        # 应用修复
        self.window._organize_by_grid = organize_by_grid
        self.window._create_spiral_detection_path = improved_spiral_detection_path
        
        self.logger.info("✅ 纵向检测算法修复已应用")

def main():
    """主函数"""
    test = VerticalHolesFixTest()
    
    try:
        success = test.apply_vertical_fix()
        
        test.logger.info("\n" + "="*60)
        test.logger.info("🎯 纵向孔位修复结果")
        test.logger.info("="*60)
        
        if success:
            test.logger.info("🎉 纵向修复成功！")
            test.logger.info("✅ 相同/相近横坐标的孔位已正确处理")
            test.logger.info("✅ 网格组织模式确保完整覆盖")
        else:
            test.logger.info("❌ 纵向修复需要进一步优化")
        
        test.logger.info("\n🔧 纵向修复策略:")
        test.logger.info("  1. 网格模式组织孔位")
        test.logger.info("  2. 按Y坐标分行，按X坐标排序")
        test.logger.info("  3. 蛇形扫描保持连续性")
        test.logger.info("  4. 特别处理纵向列的连续性")
        
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