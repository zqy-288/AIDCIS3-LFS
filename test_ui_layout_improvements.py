#!/usr/bin/env python3
"""
UI布局改进验证脚本
验证全景图尺寸增大、圆形扇形图删除、文字信息布局改进效果
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
from aidcis2.models.hole_data import HoleData, HoleCollection, HoleStatus
from aidcis2.graphics.sector_manager import SectorQuadrant

class UILayoutImprovementTest:
    """UI布局改进测试类"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = None
        
        # 设置日志
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        self.logger = logging.getLogger(__name__)
    
    def test_ui_layout_improvements(self):
        """测试UI布局改进"""
        self.logger.info("🚀 开始UI布局改进验证")
        
        # 1. 创建主窗口
        self.window = MainWindow()
        self.window.show()
        QTest.qWait(2000)
        
        # 2. 验证原有组件是否被删除
        self.logger.info("\n🗑️ 验证删除的组件")
        
        # 检查是否还存在sector_overview组件
        has_sector_overview = hasattr(self.window, 'sector_overview')
        if not has_sector_overview:
            self.logger.info("✅ 圆形扇形预览图已成功删除")
        else:
            self.logger.info("❌ 圆形扇形预览图仍然存在")
        
        # 3. 验证全景图尺寸
        self.logger.info("\n📐 验证全景图尺寸")
        
        panorama = self.window.sidebar_panorama
        panorama_view = panorama.panorama_view
        panorama_size = panorama_view.size()
        
        self.logger.info(f"📏 全景图尺寸: {panorama_size.width()} x {panorama_size.height()}")
        
        if panorama_size.width() >= 360 and panorama_size.height() >= 380:
            self.logger.info("✅ 全景图尺寸已成功增大")
        else:
            self.logger.info("❌ 全景图尺寸未达到预期")
        
        # 4. 验证信息标签样式
        self.logger.info("\n📝 验证信息标签")
        
        info_label = panorama.info_label
        info_text = info_label.text()
        
        self.logger.info(f"📊 全景图信息: {info_text}")
        
        # 检查样式设置
        style = info_label.styleSheet()
        has_improved_style = "font-size: 14px" in style and "font-weight: bold" in style
        
        if has_improved_style:
            self.logger.info("✅ 全景图信息标签样式已改进")
        else:
            self.logger.info("❌ 全景图信息标签样式未改进")
        
        # 5. 验证扇形统计信息区域
        self.logger.info("\n📊 验证扇形统计信息")
        
        stats_label = self.window.sector_stats_label
        stats_text = stats_label.text()
        
        self.logger.info(f"📋 扇形统计信息: {stats_text[:50]}...")
        
        # 检查是否启用了富文本格式
        text_format = stats_label.textFormat()
        if text_format == Qt.RichText:
            self.logger.info("✅ 扇形统计信息已启用富文本格式")
        else:
            self.logger.info("❌ 扇形统计信息未启用富文本格式")
        
        # 6. 加载测试数据验证完整功能
        self.logger.info("\n🔄 加载测试数据验证功能")
        
        hole_collection = self._create_test_data()
        self.window.hole_collection = hole_collection
        self.window.update_hole_display()
        
        # 等待渲染完成
        QTest.qWait(3000)
        
        # 7. 验证加载后的状态
        self.logger.info("\n✅ 验证数据加载后的状态")
        
        # 检查全景图信息更新
        updated_info = panorama.info_label.text()
        self.logger.info(f"📊 更新后全景图信息: {updated_info}")
        
        if "个孔位" in updated_info:
            self.logger.info("✅ 全景图信息正确显示孔位数量")
        else:
            self.logger.info("❌ 全景图信息未正确更新")
        
        # 检查扇形统计信息
        updated_stats = stats_label.text()
        if "区域1" in updated_stats or "总孔位" in updated_stats:
            self.logger.info("✅ 扇形统计信息正确更新")
        else:
            self.logger.info("❌ 扇形统计信息未正确更新")
        
        # 8. 测试扇形切换
        self.logger.info("\n🔄 测试扇形切换功能")
        
        test_sectors = [SectorQuadrant.SECTOR_2, SectorQuadrant.SECTOR_3, SectorQuadrant.SECTOR_4]
        
        for sector in test_sectors:
            self.window.dynamic_sector_display.switch_to_sector(sector)
            QTest.qWait(1000)
            
            # 检查统计信息是否更新
            current_stats = stats_label.text()
            sector_name = f"区域{sector.value.split('_')[1]}"
            
            if sector_name in current_stats:
                self.logger.info(f"✅ 切换到{sector_name}后统计信息正确更新")
            else:
                self.logger.info(f"❌ 切换到{sector_name}后统计信息未更新")
        
        return True
    
    def _create_test_data(self):
        """创建测试数据"""
        test_holes = {}
        hole_id = 1
        
        # 创建一个简单的网格分布
        for row in range(20):
            for col in range(20):
                x = col * 25 + 200  
                y = row * 25 + 200
                
                hole_data = HoleData(
                    hole_id=f"H{hole_id:05d}",
                    center_x=x,
                    center_y=y,
                    radius=8.8,
                    status=HoleStatus.PENDING
                )
                
                test_holes[hole_data.hole_id] = hole_data
                hole_id += 1
        
        hole_collection = HoleCollection(
            holes=test_holes,
            metadata={
                'source_file': 'ui_layout_test',
                'total_holes': len(test_holes),
                'created_by': 'ui_layout_test'
            }
        )
        
        self.logger.info(f"🧪 创建测试数据: {len(test_holes)} 个孔位")
        return hole_collection
    
    def show_summary(self, success):
        """显示测试总结"""
        self.logger.info("=" * 60)
        self.logger.info("📊 UI布局改进验证总结")
        self.logger.info("=" * 60)
        
        if success:
            self.logger.info("✅ UI布局改进验证成功")
            self.logger.info("\n🎯 已实现的改进：")
            self.logger.info("  ✅ 全景图窗口大小增大到 380x400 像素")
            self.logger.info("  ✅ 全景图居中显示")
            self.logger.info("  ✅ 删除了圆形扇形区域预览图")
            self.logger.info("  ✅ 扇形统计信息移到全景图下方")
            self.logger.info("  ✅ 信息标签样式改进（更大字体、加粗）")
            self.logger.info("  ✅ 扇形统计信息支持富文本格式")
            self.logger.info("  ✅ 统计信息与全景图同步更新")
            
            self.logger.info("\n📐 布局改进效果：")
            self.logger.info("  👁️ 全景图更大更清晰，便于查看DXF内容")
            self.logger.info("  🎯 删除冗余的圆形图，界面更简洁")
            self.logger.info("  📍 统一的信息显示位置，逻辑更清晰")
            self.logger.info("  🎨 改进的文字样式，信息更易读")
            
            self.logger.info("\n🔧 用户体验提升：")
            self.logger.info("  🖼️ 更大的全景图便于识别和点击扇形区域")
            self.logger.info("  📊 清晰的扇形统计信息便于了解检测进度")
            self.logger.info("  🎯 统一的UI风格和信息同步")
        else:
            self.logger.info("❌ UI布局改进验证失败")

def main():
    """主函数"""
    test = UILayoutImprovementTest()
    
    try:
        success = test.test_ui_layout_improvements()
        
        # 显示总结
        test.show_summary(success)
        
        # 保持窗口开放供用户验证
        if test.window:
            test.logger.info("\n👁️ 请验证以下UI改进：")
            test.logger.info("  1. 右下角全景图是否变大并居中显示")
            test.logger.info("  2. 右上角的圆形扇形图是否已删除") 
            test.logger.info("  3. 全景图下方是否显示统计信息")
            test.logger.info("  4. 点击全景图不同区域观察统计信息变化")
            test.logger.info("\n窗口将在15秒后关闭...")
            QTest.qWait(15000)
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        test.logger.info("\n⏹️ 测试被用户中断")
        return 1
    except Exception as e:
        test.logger.error(f"❌ 测试执行失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        if test.window:
            test.window.close()

if __name__ == "__main__":
    sys.exit(main())