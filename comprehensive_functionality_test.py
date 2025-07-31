#!/usr/bin/env python3
"""
全面功能检测脚本
验证扇形导航删除、文件路径修复、新功能添加等所有修改
"""

import sys
import os
import traceback
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

# 设置项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComprehensiveFunctionalityTest:
    """全面功能测试类"""
    
    def __init__(self):
        self.test_results: List[Dict[str, Any]] = []
        self.app = None
        
    def setup_qt_application(self):
        """设置Qt应用程序"""
        try:
            from PySide6.QtWidgets import QApplication
            if not QApplication.instance():
                self.app = QApplication([])
            else:
                self.app = QApplication.instance()
            return True
        except Exception as e:
            self.log_test_result("Qt应用程序设置", False, f"设置失败: {e}")
            return False
    
    def log_test_result(self, test_name: str, passed: bool, details: str = ""):
        """记录测试结果"""
        result = {
            'test_name': test_name,
            'passed': passed,
            'details': details,
            'status': '✅ PASS' if passed else '❌ FAIL'
        }
        self.test_results.append(result)
        print(f"{result['status']} {test_name}: {details}")
    
    def test_sector_navigation_removal(self):
        """测试1: 验证扇形导航功能是否完全移除"""
        print("\n🔍 测试1: 扇形导航功能移除验证")
        
        try:
            # 测试1.1: 检查CenterVisualizationPanel
            from src.pages.main_detection_p1.components.center_visualization_panel import CenterVisualizationPanel
            panel = CenterVisualizationPanel()
            
            has_prev_btn = hasattr(panel, 'prev_sector_btn') and getattr(panel, 'prev_sector_btn', None) is not None
            has_next_btn = hasattr(panel, 'next_sector_btn') and getattr(panel, 'next_sector_btn', None) is not None
            has_nav_signal = hasattr(panel, 'sector_navigation_requested')
            
            if not (has_prev_btn or has_next_btn or has_nav_signal):
                self.log_test_result("CenterVisualizationPanel扇形导航移除", True, "所有扇形导航元素已移除")
            else:
                self.log_test_result("CenterVisualizationPanel扇形导航移除", False, 
                                   f"仍有残留: prev_btn={has_prev_btn}, next_btn={has_next_btn}, signal={has_nav_signal}")
            
            panel.close()
            
            # 测试1.2: 检查VisualizationPanelComponent
            from src.pages.main_detection_p1.ui.components.visualization_panel_component import VisualizationPanelComponent
            viz_panel = VisualizationPanelComponent()
            
            view_controls = viz_panel.view_controls
            has_prev_btn_vc = hasattr(view_controls, 'prev_sector_btn') and getattr(view_controls, 'prev_sector_btn', None) is not None
            has_next_btn_vc = hasattr(view_controls, 'next_sector_btn') and getattr(view_controls, 'next_sector_btn', None) is not None
            has_nav_signal_vc = hasattr(view_controls, 'sector_navigation_requested')
            
            if not (has_prev_btn_vc or has_next_btn_vc) and not has_nav_signal_vc:
                self.log_test_result("VisualizationPanelComponent扇形导航移除", True, "ViewControlsWidget中扇形导航已移除")
            else:
                self.log_test_result("VisualizationPanelComponent扇形导航移除", False, 
                                   f"ViewControlsWidget仍有残留: prev_btn={has_prev_btn_vc}, next_btn={has_next_btn_vc}, signal={has_nav_signal_vc}")
            
            viz_panel.close()
            
            # 测试1.3: 检查NativeMainDetectionView
            from src.pages.main_detection_p1.native_main_detection_view import NativeMainDetectionView
            native_view = NativeMainDetectionView()
            
            center_panel = native_view.center_panel
            has_sector_nav_center = (hasattr(center_panel, 'prev_sector_btn') and center_panel.prev_sector_btn is not None) or \
                                  (hasattr(center_panel, 'next_sector_btn') and center_panel.next_sector_btn is not None)
            
            if not has_sector_nav_center:
                self.log_test_result("NativeMainDetectionView扇形导航移除", True, "中间面板扇形导航已移除")
            else:
                self.log_test_result("NativeMainDetectionView扇形导航移除", False, "中间面板仍有扇形导航残留")
            
            native_view.close()
            
        except Exception as e:
            self.log_test_result("扇形导航移除测试", False, f"测试异常: {e}")
            traceback.print_exc()
    
    def test_new_view_mode_functionality(self):
        """测试2: 验证新的宏观/微观视图切换功能"""
        print("\n🔍 测试2: 宏观/微观视图切换功能验证")
        
        try:
            from src.pages.main_detection_p1.components.center_visualization_panel import CenterVisualizationPanel
            panel = CenterVisualizationPanel()
            
            # 测试2.1: 检查默认视图模式
            default_mode = panel.current_view_mode
            if default_mode == "micro":
                self.log_test_result("默认视图模式", True, f"默认为微观视图: {default_mode}")
            else:
                self.log_test_result("默认视图模式", False, f"默认视图模式不正确: {default_mode}")
            
            # 测试2.2: 检查按钮状态
            macro_checked = panel.macro_view_btn.isChecked()
            micro_checked = panel.micro_view_btn.isChecked()
            
            if not macro_checked and micro_checked:
                self.log_test_result("按钮默认状态", True, "微观视图按钮默认选中，宏观视图按钮默认未选中")
            else:
                self.log_test_result("按钮默认状态", False, f"按钮状态不正确: macro={macro_checked}, micro={micro_checked}")
            
            # 测试2.3: 测试视图模式切换
            initial_mode = panel.current_view_mode
            
            # 切换到宏观视图
            panel.macro_view_btn.click()
            macro_mode = panel.current_view_mode
            
            # 切换到微观视图
            panel.micro_view_btn.click()
            micro_mode = panel.current_view_mode
            
            if macro_mode == "macro" and micro_mode == "micro":
                self.log_test_result("视图模式切换", True, "宏观/微观视图切换正常")
            else:
                self.log_test_result("视图模式切换", False, f"视图切换异常: macro_mode={macro_mode}, micro_mode={micro_mode}")
            
            # 测试2.4: 检查视图切换方法
            has_show_panorama = hasattr(panel, '_show_panorama_view') and callable(getattr(panel, '_show_panorama_view'))
            has_show_sector = hasattr(panel, '_show_sector_view') and callable(getattr(panel, '_show_sector_view'))
            has_create_panorama = hasattr(panel, '_create_panorama_widget') and callable(getattr(panel, '_create_panorama_widget'))
            
            if has_show_panorama and has_show_sector and has_create_panorama:
                self.log_test_result("视图切换方法", True, "所有视图切换方法存在")
            else:
                self.log_test_result("视图切换方法", False, 
                                   f"视图切换方法缺失: panorama={has_show_panorama}, sector={has_show_sector}, create={has_create_panorama}")
            
            panel.close()
            
        except Exception as e:
            self.log_test_result("视图模式功能测试", False, f"测试异常: {e}")
            traceback.print_exc()
    
    def test_file_structure_and_imports(self):
        """测试3: 验证文件移动和导入路径修复"""
        print("\n🔍 测试3: 文件结构和导入路径验证")
        
        try:
            # 测试3.1: 检查文件是否在正确位置
            viz_panel_path = project_root / "src/pages/main_detection_p1/ui/components/visualization_panel_component.py"
            native_view_path = project_root / "src/pages/main_detection_p1/native_main_detection_view.py"
            
            if viz_panel_path.exists():
                self.log_test_result("visualization_panel_component文件位置", True, "文件在正确位置")
            else:
                self.log_test_result("visualization_panel_component文件位置", False, "文件不在预期位置")
            
            if native_view_path.exists():
                self.log_test_result("native_main_detection_view文件位置", True, "文件在正确位置")
            else:
                self.log_test_result("native_main_detection_view文件位置", False, "文件不在预期位置")
            
            # 测试3.2: 检查导入路径是否正确
            try:
                from src.pages.main_detection_p1.ui.components.visualization_panel_component import VisualizationPanelComponent
                self.log_test_result("VisualizationPanelComponent导入", True, "导入成功")
            except ImportError as e:
                self.log_test_result("VisualizationPanelComponent导入", False, f"导入失败: {e}")
            
            try:
                from src.pages.main_detection_p1.native_main_detection_view import NativeMainDetectionView
                self.log_test_result("NativeMainDetectionView导入", True, "导入成功")
            except ImportError as e:
                self.log_test_result("NativeMainDetectionView导入", False, f"导入失败: {e}")
            
            # 测试3.3: 检查其他文件的导入引用是否更新
            try:
                from src.ui.main_view_controller import MainViewController
                self.log_test_result("MainViewController导入", True, "导入成功（导入路径已修复）")
            except ImportError as e:
                self.log_test_result("MainViewController导入", False, f"导入失败，可能导入路径未修复: {e}")
            
        except Exception as e:
            self.log_test_result("文件结构测试", False, f"测试异常: {e}")
            traceback.print_exc()
    
    def test_dynamic_sector_display_widget(self):
        """测试4: 验证DynamicSectorDisplayWidget修复"""
        print("\n🔍 测试4: DynamicSectorDisplayWidget修复验证")
        
        try:
            # 测试4.1: 核心版本
            from src.core_business.graphics.dynamic_sector_view import DynamicSectorDisplayWidget as CoreWidget
            core_widget = CoreWidget()
            
            if core_widget is not None and hasattr(core_widget, 'mini_panorama'):
                self.log_test_result("核心版本DynamicSectorDisplayWidget", True, "创建成功，mini_panorama存在")
            else:
                self.log_test_result("核心版本DynamicSectorDisplayWidget", False, "创建失败或mini_panorama缺失")
            
            core_widget.close()
            
            # 测试4.2: P1版本
            from src.pages.main_detection_p1.components.graphics.dynamic_sector_view import DynamicSectorDisplayWidget as P1Widget
            p1_widget = P1Widget()
            
            if p1_widget is not None and hasattr(p1_widget, 'mini_panorama'):
                self.log_test_result("P1版本DynamicSectorDisplayWidget", True, "创建成功，mini_panorama存在")
            else:
                self.log_test_result("P1版本DynamicSectorDisplayWidget", False, "创建失败或mini_panorama缺失")
            
            p1_widget.close()
            
        except Exception as e:
            self.log_test_result("DynamicSectorDisplayWidget测试", False, f"测试异常: {e}")
            traceback.print_exc()
    
    def test_integration_functionality(self):
        """测试5: 集成功能测试"""
        print("\n🔍 测试5: 集成功能验证")
        
        try:
            # 测试5.1: 主检测页面集成
            from src.pages.main_detection_p1.main_detection_page import MainDetectionPage
            page = MainDetectionPage()
            
            has_native_view = hasattr(page, 'native_view') and page.native_view is not None
            if has_native_view:
                center_panel = page.native_view.center_panel
                has_proper_center = center_panel is not None
                
                if has_proper_center:
                    # 检查是否有正确的视图模式按钮
                    has_macro_btn = hasattr(center_panel, 'macro_view_btn') and center_panel.macro_view_btn is not None
                    has_micro_btn = hasattr(center_panel, 'micro_view_btn') and center_panel.micro_view_btn is not None
                    
                    if has_macro_btn and has_micro_btn:
                        self.log_test_result("主检测页面集成", True, "原生视图和视图模式按钮正常")
                    else:
                        self.log_test_result("主检测页面集成", False, f"视图模式按钮缺失: macro={has_macro_btn}, micro={has_micro_btn}")
                else:
                    self.log_test_result("主检测页面集成", False, "中间面板为空")
            else:
                self.log_test_result("主检测页面集成", False, "原生视图为空")
            
            page.close()
            
            # 测试5.2: 全景预览位置变更
            from src.pages.main_detection_p1.native_main_detection_view_p1 import NativeLeftInfoPanel
            left_panel = NativeLeftInfoPanel()
            
            # 检查左侧面板是否移除了全景预览组
            has_panorama_group = hasattr(left_panel, 'panorama_group')
            if not has_panorama_group:
                self.log_test_result("全景预览位置变更", True, "左侧面板全景预览组已移除")
            else:
                self.log_test_result("全景预览位置变更", False, "左侧面板仍有全景预览组")
            
            left_panel.close()
            
        except Exception as e:
            self.log_test_result("集成功能测试", False, f"测试异常: {e}")
            traceback.print_exc()
    
    def test_backwards_compatibility(self):
        """测试6: 向后兼容性测试"""
        print("\n🔍 测试6: 向后兼容性验证")
        
        try:
            # 测试6.1: 检查测试文件是否存在
            test_file_path = project_root / "tests/test_native_main_detection_view.py"
            if test_file_path.exists():
                self.log_test_result("测试文件存在性", True, "测试文件存在于正确位置")
                
                # 尝试导入测试模块（如果存在的话）
                try:
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("test_module", test_file_path)
                    test_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(test_module)
                    self.log_test_result("测试文件导入", True, "测试文件可以成功导入")
                except Exception as e:
                    self.log_test_result("测试文件导入", False, f"测试文件导入失败: {e}")
            else:
                self.log_test_result("测试文件存在性", False, "测试文件不存在")
            
            # 测试6.2: 遗留代码兼容性
            try:
                from src.modules.legacy_main_detection_view import LegacyMainDetectionView
                self.log_test_result("遗留代码兼容性", True, "遗留主检测视图仍可导入")
            except Exception as e:
                self.log_test_result("遗留代码兼容性", False, f"遗留代码导入失败: {e}")
            
        except Exception as e:
            self.log_test_result("向后兼容性测试", False, f"测试异常: {e}")
            traceback.print_exc()
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始运行全面功能测试")
        print("=" * 80)
        
        if not self.setup_qt_application():
            return
        
        # 运行所有测试
        self.test_sector_navigation_removal()
        self.test_new_view_mode_functionality()
        self.test_file_structure_and_imports()
        self.test_dynamic_sector_display_widget()
        self.test_integration_functionality()
        self.test_backwards_compatibility()
        
        # 输出测试摘要
        self.print_test_summary()
    
    def print_test_summary(self):
        """打印测试摘要"""
        print("\n" + "=" * 80)
        print("📊 测试结果摘要")
        print("=" * 80)
        
        passed_count = sum(1 for result in self.test_results if result['passed'])
        total_count = len(self.test_results)
        
        print(f"总测试数: {total_count}")
        print(f"通过数: {passed_count}")
        print(f"失败数: {total_count - passed_count}")
        print(f"通过率: {passed_count/total_count*100:.1f}%")
        
        print("\n详细结果:")
        for result in self.test_results:
            print(f"{result['status']} {result['test_name']}")
            if result['details'] and not result['passed']:
                print(f"    细节: {result['details']}")
        
        print("\n" + "=" * 80)
        if passed_count == total_count:
            print("🎉 所有测试通过！功能修改验证成功！")
        else:
            print("⚠️  部分测试失败，需要检查和修复！")
        print("=" * 80)

if __name__ == "__main__":
    tester = ComprehensiveFunctionalityTest()
    tester.run_all_tests()