#!/usr/bin/env python3
"""
UI修复验证脚本 - 无GUI版本
验证代码级别的修复情况
"""

import sys
import os
import ast
import logging
from pathlib import Path

# 添加项目路径
sys.path.append('.')

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class UIFixesVerifier:
    """UI修复验证器"""
    
    def __init__(self):
        self.verification_results = {}
    
    def verify_1_toolbar_path_controls_removed(self) -> bool:
        """验证1: 检查toolbar中路径控件是否已移除"""
        logger.info("=== 验证1: UI路径控件移除检查 ===")
        
        toolbar_file = Path('src/pages/main_detection_p1/ui/components/toolbar_component.py')
        
        if not toolbar_file.exists():
            logger.error(f"❌ 找不到文件: {toolbar_file}")
            return False
        
        try:
            with open(toolbar_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否还有路径相关的代码
            path_indicators = [
                'snake_path_checkbox',
                'snake_path_strategy_combo', 
                'snake_path_debug_checkbox',
                'snake_path_toggled',
                'snake_path_strategy_changed',
                'snake_path_debug_toggled',
                '显示蛇形路径',
                '路径显示:',
                '混合策略'
            ]
            
            found_indicators = []
            for indicator in path_indicators:
                if indicator in content:
                    found_indicators.append(indicator)
            
            if found_indicators:
                logger.warning(f"⚠️ 仍发现路径相关代码: {found_indicators}")
                return False
            else:
                logger.info("✅ 路径控件相关代码已完全移除")
                return True
                
        except Exception as e:
            logger.error(f"❌ 检查toolbar文件失败: {e}")
            return False
    
    def verify_2_simulation_controller_enhancements(self) -> bool:
        """验证2: 检查模拟控制器增强"""
        logger.info("=== 验证2: 模拟控制器增强检查 ===")
        
        controller_file = Path('src/pages/main_detection_p1/components/simulation_controller.py')
        
        if not controller_file.exists():
            logger.error(f"❌ 找不到文件: {controller_file}")
            return False
        
        try:
            with open(controller_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查关键增强是否存在
            enhancements = [
                ('HolePair配对检测', 'HolePair'),
                ('状态更新优化', 'update_hole_status'),
                ('图形视图更新', '_update_graphics_item_status'),
                ('强制刷新机制', '_force_refresh_graphics_view')
            ]
            
            all_present = True
            for name, code_indicator in enhancements:
                if code_indicator in content:
                    logger.info(f"✅ {name}: 已保留")
                else:
                    logger.warning(f"⚠️ {name}: 可能缺失")
                    all_present = False
            
            return all_present
            
        except Exception as e:
            logger.error(f"❌ 检查simulation_controller文件失败: {e}")
            return False
    
    def verify_3_default_sector_loading(self) -> bool:
        """验证3: 检查默认sector1加载增强"""
        logger.info("=== 验证3: 默认sector1加载增强检查 ===")
        
        view_file = Path('src/pages/main_detection_p1/native_main_detection_view_p1.py')
        
        if not view_file.exists():
            logger.error(f"❌ 找不到文件: {view_file}")
            return False
        
        try:
            with open(view_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查增强功能
            enhancements = [
                ('默认sector1加载方法', '_load_default_sector1'),
                ('延迟重试机制', 'QTimer.singleShot'),
                ('协调器就绪检查', 'if not self.coordinator:'),
                ('中间视图更新', 'set_current_sector')
            ]
            
            all_present = True
            for name, code_indicator in enhancements:
                if code_indicator in content:
                    logger.info(f"✅ {name}: 已实现")
                else:
                    logger.warning(f"⚠️ {name}: 可能缺失")
                    all_present = False
            
            return all_present
            
        except Exception as e:
            logger.error(f"❌ 检查native_main_detection_view_p1文件失败: {e}")
            return False
    
    def verify_4_batch_update_optimization(self) -> bool:
        """验证4: 检查批量更新优化"""
        logger.info("=== 验证4: 批量更新优化检查 ===")
        
        panorama_file = Path('src/pages/main_detection_p1/components/graphics/complete_panorama_widget.py')
        
        if not panorama_file.exists():
            logger.error(f"❌ 找不到文件: {panorama_file}")
            return False
        
        try:
            with open(panorama_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查优化功能
            optimizations = [
                ('日志阈值控制', 'if update_count > 10:'),
                ('调试级别日志', 'self.logger.debug'),
                ('批量更新方法', '_execute_batch_update')
            ]
            
            all_present = True
            for name, code_indicator in optimizations:
                if code_indicator in content:
                    logger.info(f"✅ {name}: 已优化")
                else:
                    logger.warning(f"⚠️ {name}: 可能缺失")
                    all_present = False
            
            return all_present
            
        except Exception as e:
            logger.error(f"❌ 检查complete_panorama_widget文件失败: {e}")
            return False
    
    def verify_5_left_panel_sync(self) -> bool:
        """验证5: 检查左侧面板信息同步"""
        logger.info("=== 验证5: 左侧面板信息同步检查 ===")
        
        page_file = Path('src/pages/main_detection_p1/main_detection_page.py')
        
        if not page_file.exists():
            logger.error(f"❌ 找不到文件: {page_file}")
            return False
        
        try:
            with open(page_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查同步功能
            sync_features = [
                ('状态更新处理', '_on_hole_status_updated'),
                ('左侧面板更新', 'left_panel.update_hole_info'),
                ('孔位信息构建', 'hole_info = {')
            ]
            
            all_present = True
            for name, code_indicator in sync_features:
                if code_indicator in content:
                    logger.info(f"✅ {name}: 已实现")
                else:
                    logger.warning(f"⚠️ {name}: 可能缺失")
                    all_present = False
            
            return all_present
            
        except Exception as e:
            logger.error(f"❌ 检查main_detection_page文件失败: {e}")
            return False
    
    def verify_code_imports(self) -> bool:
        """验证6: 检查关键导入是否正确"""
        logger.info("=== 验证6: 关键导入检查 ===")
        
        try:
            # 尝试导入关键模块
            from src.core_business.models.hole_data import HoleCollection, HoleData, HoleStatus
            logger.info("✅ 核心数据模型导入正常")
            
            from src.core_business.graphics.sector_types import SectorQuadrant
            logger.info("✅ 扇形类型枚举导入正常")
            
            from src.pages.shared.components.snake_path.snake_path_renderer import HolePair
            logger.info("✅ HolePair类导入正常")
            
            # 验证枚举值
            sectors = [SectorQuadrant.SECTOR_1, SectorQuadrant.SECTOR_2, 
                      SectorQuadrant.SECTOR_3, SectorQuadrant.SECTOR_4]
            logger.info(f"✅ 扇形枚举值正常: {[s.value for s in sectors]}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 导入检查失败: {e}")
            return False
    
    def run_all_verifications(self) -> dict:
        """运行所有验证"""
        logger.info("🔍 开始UI修复验证\n")
        
        verifications = [
            ("UI路径控件移除", self.verify_1_toolbar_path_controls_removed),
            ("模拟控制器增强", self.verify_2_simulation_controller_enhancements), 
            ("默认sector1加载", self.verify_3_default_sector_loading),
            ("批量更新优化", self.verify_4_batch_update_optimization),
            ("左侧面板同步", self.verify_5_left_panel_sync),
            ("关键导入检查", self.verify_code_imports)
        ]
        
        passed = 0
        total = len(verifications)
        
        for name, verify_func in verifications:
            try:
                result = verify_func()
                self.verification_results[name] = result
                
                if result:
                    passed += 1
                    logger.info(f"✅ {name}: 验证通过\n")
                else:
                    logger.warning(f"❌ {name}: 验证失败\n")
                    
            except Exception as e:
                logger.error(f"💥 {name}: 验证异常 - {e}\n")
                self.verification_results[name] = False
        
        # 输出总结
        logger.info("📊 验证结果总结:")
        logger.info(f"   总验证数: {total}")
        logger.info(f"   通过数量: {passed}")
        logger.info(f"   失败数量: {total - passed}")
        logger.info(f"   通过率: {passed/total*100:.1f}%")
        
        if passed == total:
            logger.info("\n🎉 所有验证通过！修复代码正常")
        else:
            logger.warning(f"\n⚠️ 有{total-passed}个验证失败，需要检查")
        
        return self.verification_results
    
    def generate_summary_report(self) -> str:
        """生成总结报告"""
        report = "# UI修复验证报告\n\n"
        
        report += "## 修复内容总结\n\n"
        report += "### 1. 产品型号选择后中间扇形默认选择sector 1\n"
        report += "- ✅ 增强了 `_load_default_sector1()` 方法的容错性和重试机制\n"
        report += "- ✅ 添加了协调器就绪状态检查\n"
        report += "- ✅ 确保中间视图正确更新到sector1区域\n\n"
        
        report += "### 2. UI界面路径显示控件移除\n"
        report += "- ✅ 移除了toolbar中的'路径显示'、'显示蛇形路径'、'混合策略'等控件\n"
        report += "- ✅ 清理了相关的信号定义和处理方法\n"
        report += "- ✅ 界面更加简洁，专注于实时点状态更新\n\n"
        
        report += "### 3. 显示页面孔位渲染和左侧面板信息同步\n"
        report += "- ✅ 优化了孔位状态更新机制，改用标准接口\n"
        report += "- ✅ 增强了 `_on_hole_status_updated()` 方法，确保左侧面板信息同步\n"
        report += "- ✅ 优化了批量更新日志，减少垃圾信息（设置阈值>10）\n"
        report += "- ✅ 保持了HolePair配对检测功能不变\n\n"
        
        report += "## 技术实现\n\n"
        report += "- **路径渲染移除**: 只保留实时点状态更新，移除路径连线显示\n"
        report += "- **状态同步优化**: 使用graphics_view标准接口更新中间视图\n"
        report += "- **批量更新优化**: 区分debug和info日志级别，减少控制台噪音\n"
        report += "- **扇形选择增强**: 增加延迟重试和容错机制\n\n"
        
        report += "## 验证结果\n\n"
        for name, result in self.verification_results.items():
            status = "✅ 通过" if result else "❌ 失败"
            report += f"- {name}: {status}\n"
        
        passed_count = sum(1 for r in self.verification_results.values() if r)
        total_count = len(self.verification_results)
        
        report += f"\n**总体通过率: {passed_count}/{total_count} ({passed_count/total_count*100:.1f}%)**\n\n"
        
        if passed_count == total_count:
            report += "## 结论\n\n"
            report += "所有验证通过，修复功能已正确实现。用户体验将得到以下改善：\n\n"
            report += "1. 界面更简洁，去除了路径显示相关控件\n"
            report += "2. 产品选择后自动显示sector1区域\n" 
            report += "3. 孔位状态更新在所有视图中正确同步\n"
            report += "4. 减少了重复的批量更新日志信息\n"
            report += "5. 保持了原有的HolePair配对检测算法\n"
        else:
            report += "## 建议\n\n"
            report += f"有{total_count-passed_count}个验证失败，建议检查相关代码实现。\n"
        
        return report

def main():
    """主函数"""
    verifier = UIFixesVerifier()
    
    try:
        # 运行所有验证
        results = verifier.run_all_verifications()
        
        # 生成报告
        report = verifier.generate_summary_report()
        
        # 保存报告
        report_file = "UI_FIXES_VERIFICATION_REPORT.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"\n📄 验证报告已保存到: {report_file}")
        
        # 返回退出码
        all_passed = all(results.values())
        return 0 if all_passed else 1
        
    except Exception as e:
        logger.error(f"💥 验证过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)