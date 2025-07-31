#!/usr/bin/env python3
"""
诊断渲染层级问题 - 非GUI版本
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'rendering_diagnosis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RenderingDiagnosis:
    """非GUI渲染诊断"""
    
    def __init__(self):
        self.components = {}
        self.app = QApplication(sys.argv)
        
    def run(self):
        """运行诊断"""
        logger.info("=== 开始渲染层级诊断 ===\n")
        
        # 加载组件
        if not self.load_components():
            return False
            
        # 运行诊断测试
        self.diagnose_blue_color_issue()
        
        # 检查蛇形路径渲染器
        self.check_snake_path_components()
        
        # 分析结果
        self.analyze_results()
        
        return True
        
    def load_components(self):
        """加载所有相关组件"""
        logger.info("1. 加载组件")
        
        try:
            # 加载图形视图
            from src.core_business.graphics.graphics_view import OptimizedGraphicsView
            self.components['graphics_view'] = OptimizedGraphicsView()
            logger.info("   ✅ 图形视图加载成功")
            
            # 加载全景图
            from src.pages.main_detection_p1.components.graphics.complete_panorama_widget import CompletePanoramaWidget
            self.components['panorama_widget'] = CompletePanoramaWidget()
            logger.info("   ✅ 全景图组件加载成功")
            
            # 加载孔位数据
            from src.core_business.models.hole_data import HoleCollection, HoleData, HoleStatus
            
            # 创建测试孔位
            test_holes = [
                HoleData(center_x=0, center_y=0, radius=10, hole_id="C001R001", layer="管孔"),
                HoleData(center_x=50, center_y=0, radius=10, hole_id="C002R001", layer="管孔"),
                HoleData(center_x=100, center_y=0, radius=10, hole_id="C003R001", layer="管孔"),
            ]
            
            # 创建孔位字典
            holes_dict = {hole.hole_id: hole for hole in test_holes}
            
            # 创建 HoleCollection
            hole_collection = HoleCollection(holes=holes_dict)
            
            for hole in test_holes:
                hole.status = HoleStatus.PENDING
                
            self.components['hole_collection'] = hole_collection
            logger.info(f"   ✅ 创建 {len(test_holes)} 个测试孔位")
            
            # 加载数据到视图
            self.components['graphics_view'].load_holes(hole_collection)
            if hasattr(self.components['panorama_widget'], 'load_hole_collection'):
                self.components['panorama_widget'].load_hole_collection(hole_collection)
            elif hasattr(self.components['panorama_widget'], 'load_holes'):
                self.components['panorama_widget'].load_holes(hole_collection)
            logger.info("   ✅ 数据加载完成\n")
            
            return True
            
        except Exception as e:
            logger.error(f"   ❌ 组件加载失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
            
    def diagnose_blue_color_issue(self):
        """诊断蓝色问题"""
        logger.info("2. 诊断蓝色渲染问题")
        
        graphics_view = self.components['graphics_view']
        panorama_widget = self.components['panorama_widget']
        hole_collection = self.components['hole_collection']
        
        # 选择测试孔位
        test_hole = list(hole_collection.holes.values())[0]
        hole_id = test_hole.hole_id
        
        logger.info(f"   测试孔位: {hole_id}")
        
        # 初始状态
        logger.info("\n   a) 初始状态:")
        self.check_hole_states(hole_id)
        
        # 设置蓝色
        logger.info("\n   b) 设置蓝色覆盖:")
        blue_color = QColor(33, 150, 243)
        
        # 更新状态
        from src.core_business.models.hole_data import HoleStatus
        graphics_view.update_hole_status(hole_id, HoleStatus.PENDING, blue_color)
        if hasattr(panorama_widget, 'update_hole_status'):
            panorama_widget.update_hole_status(hole_id, HoleStatus.PENDING, blue_color)
            
        # 强制处理事件
        self.app.processEvents()
        
        self.check_hole_states(hole_id)
        
        # 清除蓝色
        logger.info("\n   c) 清除蓝色覆盖:")
        graphics_view.update_hole_status(hole_id, HoleStatus.QUALIFIED, None)
        if hasattr(panorama_widget, 'update_hole_status'):
            panorama_widget.update_hole_status(hole_id, HoleStatus.QUALIFIED, None)
            
        # 强制处理事件
        self.app.processEvents()
        
        self.check_hole_states(hole_id)
        
        # 检查场景中的所有孔位项
        logger.info("\n   d) 场景分析:")
        self.analyze_scene_items()
        
    def check_hole_states(self, hole_id):
        """检查孔位状态"""
        graphics_view = self.components['graphics_view']
        panorama_widget = self.components['panorama_widget']
        
        # 检查图形视图
        if hasattr(graphics_view, 'hole_items') and hole_id in graphics_view.hole_items:
            item = graphics_view.hole_items[hole_id]
            color = item.brush().color()
            logger.info(f"      图形视图:")
            logger.info(f"        颜色: RGB({color.red()}, {color.green()}, {color.blue()}) [{color.name()}]")
            logger.info(f"        颜色覆盖: {item._color_override}")
            logger.info(f"        状态: {item.hole_data.status.value}")
            
            # 判断颜色类型
            if color.red() == 33 and color.green() == 150 and color.blue() == 243:
                logger.warning("        ⚠️ 显示为蓝色!")
            elif color.green() > 150 and color.red() < 100:
                logger.info("        ✅ 显示为绿色(合格)")
            elif color.red() > 200:
                logger.info("        ✅ 显示为红色(异常)")
            else:
                logger.info("        ✅ 显示为灰色(待检)")
                
        # 检查全景图
        if hasattr(panorama_widget, 'scene'):
            scene = panorama_widget.scene
            found_items = []
            
            for item in scene.items():
                if hasattr(item, 'hole_data') and item.hole_data.hole_id == hole_id:
                    found_items.append(item)
                    
            logger.info(f"      全景图: 找到 {len(found_items)} 个孔位项")
            
            for i, item in enumerate(found_items):
                color = item.brush().color()
                logger.info(f"        项{i+1}:")
                logger.info(f"          颜色: RGB({color.red()}, {color.green()}, {color.blue()}) [{color.name()}]")
                logger.info(f"          颜色覆盖: {getattr(item, '_color_override', 'N/A')}")
                logger.info(f"          Z值: {item.zValue()}")
                
    def analyze_scene_items(self):
        """分析场景中的项"""
        graphics_view = self.components['graphics_view']
        
        if hasattr(graphics_view, 'scene'):
            scene = graphics_view.scene
            
            # 统计不同类型的项
            item_types = {}
            for item in scene.items():
                class_name = type(item).__name__
                item_types[class_name] = item_types.get(class_name, 0) + 1
                
            logger.info("      场景项统计:")
            for class_name, count in sorted(item_types.items()):
                logger.info(f"        {class_name}: {count} 个")
                
            # 检查Z值层级
            z_layers = {}
            for item in scene.items():
                z = item.zValue()
                if z not in z_layers:
                    z_layers[z] = []
                z_layers[z].append(type(item).__name__)
                
            logger.info("      Z值层级:")
            for z in sorted(z_layers.keys(), reverse=True):
                unique_types = set(z_layers[z])
                logger.info(f"        Z={z}: {', '.join(unique_types)}")
                
    def check_snake_path_components(self):
        """检查蛇形路径组件"""
        logger.info("\n3. 检查蛇形路径组件")
        
        # 检查是否有蛇形路径渲染器
        graphics_view = self.components['graphics_view']
        
        # 检查属性
        if hasattr(graphics_view, 'snake_path_renderer'):
            logger.info("   ✅ 图形视图包含蛇形路径渲染器属性")
        else:
            logger.info("   ℹ️ 图形视图不包含蛇形路径渲染器属性")
            
        # 检查导入
        try:
            from src.core_business.graphics.snake_path_renderer import SnakePathRenderer
            logger.info("   ✅ 蛇形路径渲染器模块可导入")
            
            # 检查是否在场景中
            if hasattr(graphics_view, 'scene'):
                for item in graphics_view.scene.items():
                    if 'snake' in type(item).__name__.lower() or 'path' in type(item).__name__.lower():
                        logger.info(f"   📍 场景中发现: {type(item).__name__}")
                        
        except ImportError as e:
            logger.error(f"   ❌ 无法导入蛇形路径渲染器: {e}")
            
    def analyze_results(self):
        """分析结果"""
        logger.info("\n4. 分析结果")
        
        # 读取日志文件，查找关键问题
        problems = []
        
        # 检查是否有蓝色持续问题
        log_file = f'rendering_diagnosis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        
        logger.info("\n=== 诊断完成 ===")
        logger.info("\n可能的问题:")
        logger.info("1. 如果清除颜色覆盖后仍显示蓝色，可能是:")
        logger.info("   - Qt渲染缓存问题")
        logger.info("   - 多个图形项重叠")
        logger.info("   - 事件处理顺序问题")
        logger.info("\n2. 建议的解决方案:")
        logger.info("   - 在清除颜色覆盖后强制调用 prepareGeometryChange()")
        logger.info("   - 确保场景更新: scene.update()")
        logger.info("   - 检查是否有其他组件在设置颜色")


def main():
    """主函数"""
    diagnosis = RenderingDiagnosis()
    
    try:
        if diagnosis.run():
            logger.info("\n诊断成功完成!")
        else:
            logger.error("\n诊断失败!")
            return 1
    except Exception as e:
        logger.error(f"\n诊断过程中出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1
        
    return 0


if __name__ == "__main__":
    sys.exit(main())