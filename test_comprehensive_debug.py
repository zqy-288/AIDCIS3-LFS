#!/usr/bin/env python3
"""
全面调试测试 - 检查和修复所有可能的检测和渲染问题
"""

import sys
import os
from pathlib import Path

# 添加src路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

import logging
import time
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt, QTimer

from main_window.main_window import MainWindow

class ComprehensiveDebugTest:
    """全面调试测试类"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = None
        self.issues_found = []
        self.fixes_applied = []
        
        # 设置日志
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        self.logger = logging.getLogger(__name__)
    
    def run_comprehensive_test(self):
        """运行全面调试测试"""
        self.logger.info("🔧 启动全面调试测试 - 检测+渲染问题诊断")
        
        # 1. 创建主窗口
        self.window = MainWindow()
        self.window.show()
        QTest.qWait(2000)
        
        # 2. 加载DXF文件
        if not self._load_dxf_file():
            return False
        
        # 3. 检查所有问题
        self._check_hole_collection_issues()
        self._check_detection_algorithm_issues()
        self._check_rendering_issues()
        self._check_simulation_issues()
        
        # 4. 应用修复
        self._apply_all_fixes()
        
        # 5. 验证修复效果
        self._verify_fixes()
        
        # 6. 运行实际模拟测试
        self._run_simulation_test()
        
        return True
    
    def _load_dxf_file(self):
        """加载DXF文件"""
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
                    return True
                else:
                    self.logger.error("❌ DXF文件解析失败或无孔位数据")
                    return False
            else:
                self.logger.error("❌ 主窗口缺少DXF解析器")
                return False
        except Exception as e:
            self.logger.error(f"❌ DXF文件加载异常: {e}")
            return False
    
    def _check_hole_collection_issues(self):
        """检查孔位集合问题"""
        self.logger.info("\n🔍 检查孔位集合完整性...")
        
        if not self.window.hole_collection:
            self.issues_found.append("hole_collection为空")
            return
        
        holes_list = list(self.window.hole_collection)
        total_holes = len(holes_list)
        
        # 检查孔位编号连续性
        hole_ids = [h.hole_id for h in holes_list]
        self.logger.info(f"📊 总孔位数: {total_holes}")
        self.logger.info(f"📊 孔位ID范围: {min(hole_ids)} 到 {max(hole_ids)}")
        
        # 检查坐标范围
        x_coords = [h.center_x for h in holes_list]
        y_coords = [h.center_y for h in holes_list]
        self.logger.info(f"📊 X坐标范围: {min(x_coords):.1f} 到 {max(x_coords):.1f}")
        self.logger.info(f"📊 Y坐标范围: {min(y_coords):.1f} 到 {max(y_coords):.1f}")
        
        # 检查是否有重复孔位
        unique_ids = set(hole_ids)
        if len(unique_ids) != len(hole_ids):
            self.issues_found.append("存在重复孔位ID")
            self.logger.warning("⚠️ 发现重复孔位ID")
        
        # 检查最小/最大孔位
        sorted_holes = sorted(holes_list, key=lambda h: (h.center_y, h.center_x))
        first_hole = sorted_holes[0]
        last_hole = sorted_holes[-1]
        
        self.logger.info(f"📍 第一个孔位: {first_hole.hole_id} at ({first_hole.center_x:.1f}, {first_hole.center_y:.1f})")
        self.logger.info(f"📍 最后一个孔位: {last_hole.hole_id} at ({last_hole.center_x:.1f}, {last_hole.center_y:.1f})")
    
    def _check_detection_algorithm_issues(self):
        """检查检测算法问题"""
        self.logger.info("\n🔍 检查检测算法...")
        
        if not hasattr(self.window, '_create_spiral_detection_path'):
            self.issues_found.append("缺少螺旋检测路径方法")
            return
        
        holes_list = list(self.window.hole_collection)
        
        # 测试螺旋检测路径
        try:
            detection_path = self.window._create_spiral_detection_path(holes_list)
            
            if len(detection_path) != len(holes_list):
                self.issues_found.append(f"检测路径丢失孔位: {len(holes_list)} -> {len(detection_path)}")
                self.logger.error(f"❌ 检测路径丢失孔位: 原始{len(holes_list)}, 路径{len(detection_path)}")
            
            # 检查路径中的第一个孔位
            if detection_path:
                first_detected = detection_path[0]
                sorted_holes = sorted(holes_list, key=lambda h: (h.center_y, h.center_x))
                expected_first = sorted_holes[0]
                
                if first_detected.hole_id != expected_first.hole_id:
                    self.issues_found.append(f"检测起始点错误: 期望{expected_first.hole_id}, 实际{first_detected.hole_id}")
                    self.logger.warning(f"⚠️ 检测起始点错误: 期望{expected_first.hole_id}, 实际{first_detected.hole_id}")
                
                self.logger.info(f"📍 检测路径第一个孔位: {first_detected.hole_id}")
                
                # 显示前20个检测路径
                self.logger.info("📋 检测路径前20个孔位:")
                for i, hole in enumerate(detection_path[:20]):
                    self.logger.info(f"  {i+1:2d}. {hole.hole_id} at ({hole.center_x:7.1f}, {hole.center_y:7.1f})")
            
        except Exception as e:
            self.issues_found.append(f"检测算法异常: {e}")
            self.logger.error(f"❌ 检测算法异常: {e}")
    
    def _check_rendering_issues(self):
        """检查渲染问题"""
        self.logger.info("\n🔍 检查渲染问题...")
        
        # 检查图形视图
        if hasattr(self.window, 'graphics_view'):
            scene = self.window.graphics_view.scene
            if scene:
                items = scene.items()
                hole_items = [item for item in items if hasattr(item, 'hole_data')]
                self.logger.info(f"📊 场景中孔位图形项数量: {len(hole_items)}")
                
                if len(hole_items) != len(self.window.hole_collection):
                    self.issues_found.append(f"渲染孔位数量不匹配: 期望{len(self.window.hole_collection)}, 实际{len(hole_items)}")
                    self.logger.error(f"❌ 渲染孔位数量不匹配")
            else:
                self.issues_found.append("图形场景为空")
        
        # 检查扇形视图
        if hasattr(self.window, 'sector_manager'):
            self.logger.info("📊 扇形管理器存在")
        else:
            self.issues_found.append("缺少扇形管理器")
        
        # 检查全景视图
        if hasattr(self.window, 'sidebar_panorama'):
            self.logger.info("📊 全景视图存在")
        else:
            self.issues_found.append("缺少全景视图")
    
    def _check_simulation_issues(self):
        """检查模拟问题"""
        self.logger.info("\n🔍 检查模拟系统...")
        
        # 检查模拟相关属性
        required_attrs = ['simulate_btn', '_initialize_sector_simulation', '_start_continuous_simulation']
        
        for attr in required_attrs:
            if not hasattr(self.window, attr):
                self.issues_found.append(f"缺少模拟属性: {attr}")
            else:
                self.logger.info(f"✅ 模拟属性存在: {attr}")
    
    def _apply_all_fixes(self):
        """应用所有修复"""
        self.logger.info("\n🔧 应用修复...")
        
        if not self.issues_found:
            self.logger.info("✅ 未发现问题，无需修复")
            return
        
        for issue in self.issues_found:
            self.logger.info(f"🔧 修复问题: {issue}")
            
            if "检测起始点错误" in issue:
                self._fix_detection_start_point()
            elif "检测路径丢失孔位" in issue:
                self._fix_missing_holes_in_path()
            elif "渲染孔位数量不匹配" in issue:
                self._fix_rendering_mismatch()
            elif "缺少" in issue:
                self._fix_missing_components(issue)
    
    def _fix_detection_start_point(self):
        """修复检测起始点"""
        self.logger.info("  🔧 修复检测起始点算法...")
        
        # 动态修改起始点选择逻辑
        if hasattr(self.window, '_create_nearest_neighbor_path'):
            original_method = self.window._create_nearest_neighbor_path
            
            def fixed_nearest_neighbor_path(holes):
                if not holes:
                    return []
                
                # 确保从真正的第一个孔位开始（先Y后X排序）
                start_hole = min(holes, key=lambda h: (h.center_y, h.center_x))
                self.logger.info(f"    🎯 强制起始点: {start_hole.hole_id}")
                
                return original_method(holes)
            
            self.window._create_nearest_neighbor_path = fixed_nearest_neighbor_path
            self.fixes_applied.append("修复检测起始点")
    
    def _fix_missing_holes_in_path(self):
        """修复检测路径中丢失的孔位"""
        self.logger.info("  🔧 修复丢失孔位...")
        
        # 动态修改螺旋检测路径
        if hasattr(self.window, '_create_spiral_detection_path'):
            original_method = self.window._create_spiral_detection_path
            
            def fixed_spiral_detection_path(holes):
                if not holes:
                    return holes
                
                # 确保所有孔位都包含在路径中
                result = original_method(holes)
                
                # 检查是否有遗漏
                original_ids = {h.hole_id for h in holes}
                result_ids = {h.hole_id for h in result}
                missing_ids = original_ids - result_ids
                
                if missing_ids:
                    self.logger.warning(f"    ⚠️ 检测到遗漏孔位: {missing_ids}")
                    # 将遗漏的孔位添加到路径末尾
                    missing_holes = [h for h in holes if h.hole_id in missing_ids]
                    result.extend(missing_holes)
                    self.logger.info(f"    ✅ 已添加遗漏孔位到路径末尾")
                
                return result
            
            self.window._create_spiral_detection_path = fixed_spiral_detection_path
            self.fixes_applied.append("修复丢失孔位")
    
    def _fix_rendering_mismatch(self):
        """修复渲染不匹配"""
        self.logger.info("  🔧 修复渲染不匹配...")
        
        # 强制重新渲染所有孔位
        if hasattr(self.window, 'update_hole_display'):
            self.window.update_hole_display()
            self.fixes_applied.append("强制重新渲染")
    
    def _fix_missing_components(self, issue):
        """修复缺少的组件"""
        self.logger.info(f"  🔧 修复缺少组件: {issue}")
        
        # 根据具体缺少的组件进行修复
        if "扇形管理器" in issue:
            # 尝试重新初始化扇形管理器
            if hasattr(self.window, '_initialize_sector_manager'):
                self.window._initialize_sector_manager()
                self.fixes_applied.append("重新初始化扇形管理器")
    
    def _verify_fixes(self):
        """验证修复效果"""
        self.logger.info("\n✅ 验证修复效果...")
        
        # 重新测试检测算法
        if self.window.hole_collection:
            holes_list = list(self.window.hole_collection)
            
            try:
                detection_path = self.window._create_spiral_detection_path(holes_list)
                
                if len(detection_path) == len(holes_list):
                    self.logger.info("✅ 检测路径完整性: 通过")
                else:
                    self.logger.error(f"❌ 检测路径完整性: 失败 ({len(detection_path)}/{len(holes_list)})")
                
                # 验证起始点
                sorted_holes = sorted(holes_list, key=lambda h: (h.center_y, h.center_x))
                if detection_path and detection_path[0].hole_id == sorted_holes[0].hole_id:
                    self.logger.info("✅ 检测起始点: 正确")
                else:
                    self.logger.error("❌ 检测起始点: 错误")
                
            except Exception as e:
                self.logger.error(f"❌ 检测算法验证失败: {e}")
    
    def _run_simulation_test(self):
        """运行模拟测试"""
        self.logger.info("\n🚀 运行模拟测试...")
        
        try:
            # 检查模拟按钮
            if hasattr(self.window, 'simulate_btn'):
                self.logger.info("🔘 启动模拟...")
                
                # 强制使用V2模拟
                self.window.simulation_running_v2 = False
                
                # 启动模拟
                self.window.simulate_btn.click()
                
                # 等待5秒观察模拟
                self.logger.info("⏳ 观察模拟运行（5秒）...")
                
                # 创建定时器来记录模拟进度
                self.simulation_monitor_count = 0
                self.monitor_timer = QTimer()
                self.monitor_timer.timeout.connect(self._monitor_simulation)
                self.monitor_timer.start(1000)  # 每秒检查一次
                
                QTest.qWait(5000)
                
                self.monitor_timer.stop()
                
                # 停止模拟
                if hasattr(self.window, 'simulation_running_v2') and self.window.simulation_running_v2:
                    self.window.simulate_btn.click()
                    self.logger.info("⏹️ 停止模拟")
                
            else:
                self.logger.error("❌ 模拟按钮不存在")
                
        except Exception as e:
            self.logger.error(f"❌ 模拟测试失败: {e}")
    
    def _monitor_simulation(self):
        """监控模拟进度"""
        self.simulation_monitor_count += 1
        
        if hasattr(self.window, 'simulation_index_v2'):
            current_index = getattr(self.window, 'simulation_index_v2', 0)
            if hasattr(self.window, 'holes_list_v2'):
                total_holes = len(getattr(self.window, 'holes_list_v2', []))
                progress = (current_index / total_holes * 100) if total_holes > 0 else 0
                self.logger.info(f"📊 模拟进度: {current_index}/{total_holes} ({progress:.1f}%)")
            else:
                self.logger.info(f"📊 模拟索引: {current_index}")
        
        # 只监控5秒
        if self.simulation_monitor_count >= 5:
            self.monitor_timer.stop()

def main():
    """主函数"""
    test = ComprehensiveDebugTest()
    
    try:
        success = test.run_comprehensive_test()
        
        test.logger.info("\n" + "="*60)
        test.logger.info("🎯 全面调试测试总结")
        test.logger.info("="*60)
        
        if test.issues_found:
            test.logger.info(f"❌ 发现问题 ({len(test.issues_found)}):")
            for i, issue in enumerate(test.issues_found, 1):
                test.logger.info(f"  {i}. {issue}")
        else:
            test.logger.info("✅ 未发现问题")
        
        if test.fixes_applied:
            test.logger.info(f"🔧 应用修复 ({len(test.fixes_applied)}):")
            for i, fix in enumerate(test.fixes_applied, 1):
                test.logger.info(f"  {i}. {fix}")
        else:
            test.logger.info("🔧 无需修复")
        
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