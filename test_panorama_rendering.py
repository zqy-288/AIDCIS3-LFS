#!/usr/bin/env python3
"""
全景图渲染测试脚本
测试全景图组件的数据加载和渲染过程
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
from aidcis2.dxf_parser import DXFParser
from aidcis2.models.hole_data import HoleCollection

class PanoramaRenderingTest:
    """全景图渲染测试类"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = None
        self.dxf_parser = DXFParser()
        
        # 设置日志
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        self.logger = logging.getLogger(__name__)
    
    def test_panorama_rendering(self):
        """测试全景图渲染"""
        self.logger.info("🚀 开始全景图渲染测试")
        
        # 1. 创建窗口
        self.window = MainWindow()
        self.window.show()
        QTest.qWait(2000)  # 等待完全初始化
        
        # 2. 尝试加载DXF文件
        self.logger.info("\n📂 加载DXF文件")
        
        # 查找可用的DXF文件
        dxf_paths = [
            "DXF Graph/测试管板.dxf",
            "test_data/sample.dxf"
        ]
        
        dxf_file = None
        for path in dxf_paths:
            if os.path.exists(path):
                dxf_file = path
                break
        
        if not dxf_file:
            self.logger.info("⚠️ 没有找到DXF文件，创建测试数据")
            # 创建测试数据
            hole_collection = self._create_test_hole_collection()
        else:
            self.logger.info(f"📄 加载DXF文件: {dxf_file}")
            try:
                hole_collection = self.dxf_parser.parse_dxf_file(dxf_file)
                self.logger.info(f"✅ DXF文件解析成功，获得 {len(hole_collection)} 个孔位")
            except Exception as e:
                self.logger.info(f"❌ DXF文件解析失败: {e}")
                self.logger.info("🔄 使用测试数据替代")
                hole_collection = self._create_test_hole_collection()
        
        # 3. 手动加载数据到主窗口
        self.logger.info(f"\n🔄 加载 {len(hole_collection)} 个孔位到主窗口")
        
        try:
            # 直接调用主窗口的数据更新方法
            self.window.hole_collection = hole_collection
            self.window.update_hole_display()
            
            self.logger.info("✅ 数据已加载到主窗口")
            
        except Exception as e:
            self.logger.error(f"❌ 数据加载失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 4. 等待渲染完成
        QTest.qWait(3000)
        
        # 5. 检查各组件的状态
        self.logger.info("\n🔍 检查渲染状态")
        
        # 检查主视图组件
        if hasattr(self.window, 'dynamic_sector_display'):
            dynamic_display = self.window.dynamic_sector_display
            
            # 检查是否有扇形管理器
            if hasattr(dynamic_display, 'sector_graphics_manager') and dynamic_display.sector_graphics_manager:
                self.logger.info("✅ 主视图: 扇形管理器已创建")
                
                # 检查扇形视图缓存
                sector_views = dynamic_display.sector_views
                self.logger.info(f"📊 主视图: 扇形视图缓存包含 {len(sector_views)} 个扇形")
                
                for sector, info in sector_views.items():
                    hole_count = info.get('hole_count', 0)
                    self.logger.info(f"  🔵 {sector.value}: {hole_count} 个孔位")
                    
            else:
                self.logger.info("❌ 主视图: 扇形管理器未创建")
        
        # 检查侧边栏全景图
        if hasattr(self.window, 'sidebar_panorama'):
            panorama = self.window.sidebar_panorama
            
            # 检查信息标签
            info_text = panorama.info_label.text()
            self.logger.info(f"📊 侧边栏全景图信息: {info_text}")
            
            # 检查全景图视图
            panorama_view = panorama.panorama_view
            scene = panorama_view.scene
            
            if scene:
                items_count = len(scene.items())
                scene_rect = scene.sceneRect()
                
                self.logger.info(f"🎨 全景图场景状态:")
                self.logger.info(f"  📦 图形项数量: {items_count}")
                self.logger.info(f"  📏 场景边界: {scene_rect}")
                
                if items_count > 0:
                    self.logger.info("✅ 全景图场景包含图形项")
                    
                    # 检查视图变换
                    transform = panorama_view.transform()
                    scale = transform.m11()
                    self.logger.info(f"🔍 全景图缩放比例: {scale:.3f}")
                    
                    # 检查视口
                    viewport_rect = panorama_view.viewport().rect()
                    self.logger.info(f"👁️ 视口大小: {viewport_rect}")
                    
                    # 强制更新视图
                    self.logger.info("🔄 强制更新全景图视图...")
                    panorama_view.viewport().update()
                    panorama_view.update()
                    
                else:
                    self.logger.info("❌ 全景图场景为空")
            else:
                self.logger.info("❌ 全景图场景不存在")
        
        # 6. 尝试修复全景图渲染
        self.logger.info("\n🔧 尝试修复全景图渲染")
        
        if hasattr(self.window, 'sidebar_panorama') and hole_collection:
            try:
                panorama = self.window.sidebar_panorama
                
                # 清空现有内容
                self.logger.info("🗑️ 清空全景图现有内容")
                panorama.panorama_view.scene.clear()
                
                # 重新加载数据
                self.logger.info("🔄 重新加载全景图数据")
                panorama.load_complete_view(hole_collection)
                
                # 强制适应视图
                QTest.qWait(500)
                self.logger.info("🎯 强制适应全景图视图")
                panorama.panorama_view.fit_in_view()
                panorama.panorama_view.viewport().update()
                
                # 再次检查场景
                items_count = len(panorama.panorama_view.scene.items())
                self.logger.info(f"🔍 修复后全景图项数量: {items_count}")
                
            except Exception as e:
                self.logger.error(f"❌ 全景图修复失败: {e}")
                import traceback
                traceback.print_exc()
        
        return True
    
    def _create_test_hole_collection(self):
        """创建测试孔位集合"""
        from aidcis2.models.hole_data import HoleData, HoleStatus
        
        test_holes = {}
        
        # 创建一个简单的网格模式的孔位
        hole_id = 1
        for row in range(10):
            for col in range(10):
                x = col * 50 + 100  # 50mm间距，从100mm开始
                y = row * 50 + 100
                
                hole_data = HoleData(
                    hole_id=f"H{hole_id:05d}",
                    center_x=x,
                    center_y=y,
                    radius=8.8,  # 17.6mm diameter = 8.8mm radius
                    status=HoleStatus.PENDING
                )
                
                test_holes[hole_data.hole_id] = hole_data
                hole_id += 1
        
        hole_collection = HoleCollection(
            holes=test_holes,
            metadata={
                'source_file': 'test_data',
                'total_holes': len(test_holes),
                'created_by': 'test_script'
            }
        )
        
        self.logger.info(f"🧪 创建测试数据: {len(test_holes)} 个孔位")
        return hole_collection
    
    def show_summary(self, success):
        """显示测试总结"""
        self.logger.info("=" * 60)
        self.logger.info("📊 全景图渲染测试总结")
        self.logger.info("=" * 60)
        
        if success:
            self.logger.info("✅ 全景图渲染测试完成")
            self.logger.info("\n🔧 发现的问题：")
            self.logger.info("  - 检查全景图场景是否包含图形项")
            self.logger.info("  - 验证视图缩放和适应设置")
            self.logger.info("  - 确认视口更新机制")
            
            self.logger.info("\n📝 可能的解决方案：")
            self.logger.info("  - 确保load_holes方法正确创建图形项")
            self.logger.info("  - 验证scene.addItem调用成功")
            self.logger.info("  - 检查视图渲染设置")
            self.logger.info("  - 添加强制视图更新")
        else:
            self.logger.info("❌ 全景图渲染测试失败")

def main():
    """主函数"""
    test = PanoramaRenderingTest()
    
    try:
        success = test.test_panorama_rendering()
        
        # 显示总结
        test.show_summary(success)
        
        # 保持窗口打开以便观察
        if test.window:
            test.logger.info("\n窗口将在10秒后关闭...")
            QTest.qWait(10000)
        
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