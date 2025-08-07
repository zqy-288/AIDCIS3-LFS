#!/usr/bin/env python3
"""
CAP1000.dxf 渲染测试界面
专门测试CAP1000.dxf文件的渲染效果，解决重复加载问题并验证蓝色状态显示

功能特点：
1. 简化的GUI界面，专注于渲染测试
2. 避免重复初始化和加载
3. 可调节显示参数（孔位大小、路径显示等）
4. 验证蓝色状态变化效果
5. 性能优化的分层渲染
"""

import sys
import os
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置详细的调试日志 - 便于定位问题
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
test_logger = logging.getLogger(__name__)
test_logger.setLevel(logging.INFO)

# 启用关键组件的调试日志
debug_components = [
    'src.pages.main_detection_p1.components.graphics.complete_panorama_widget',
    'src.services.dxf_loader_service', 
    'src.core_business.graphics.graphics_view',
    'hybrid_simulation_controller',
    '__main__'
]

for component in debug_components:
    logging.getLogger(component).setLevel(logging.INFO)

# PySide6 imports
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
    QWidget, QPushButton, QLabel, QSlider, QCheckBox,
    QGroupBox, QProgressBar, QTextEdit, QSplitter, QComboBox
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, Slot as pyqtSlot
from PySide6.QtGui import QFont, QColor

# 项目导入
from src.core_business.models.hole_data import HoleCollection, HoleData, HoleStatus
from src.pages.main_detection_p1.components.graphics.complete_panorama_widget import CompletePanoramaWidget
from src.core_business.graphics.dynamic_sector_view import DynamicSectorDisplayWidget  # 老版本的直接渲染组件
from src.controllers.main_window_controller import MainWindowController
from hybrid_simulation_controller import HybridSimulationController

# 高质量渲染的图形项
from src.pages.main_detection_p1.components.graphics.hole_item import HoleGraphicsItem
from src.core_business.models.hole_data import HoleData, HoleStatus
from PySide6.QtCore import QRectF
from PySide6.QtGui import QPainter, QPen, QBrush, QColor


class HighQualityHoleGraphicsItem(HoleGraphicsItem):
    """高质量渲染的孔位图形项 - 100%矢量渲染，完全绕过LOD"""
    
    def paint(self, painter: QPainter, option, widget=None):
        """高质量绘制 - 完全绕过LOD优化，强制矢量渲染"""
        # 启用高质量渲染设置
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        
        # 完全绕过父类的LOD优化逻辑，直接调用QGraphicsEllipseItem的绘制
        # 这确保始终使用完整的椭圆矢量渲染
        from PySide6.QtWidgets import QGraphicsEllipseItem
        QGraphicsEllipseItem.paint(self, painter, option, widget)
        
        # 强制高质量绘制标记
        test_logger.debug(f"🎨 强制矢量渲染孔位: {self.hole_data.hole_id}")
    
    def boundingRect(self) -> QRectF:
        """返回边界矩形 - 增加边距以确保抗锯齿效果"""
        rect = super().boundingRect()
        # 增加更多边距以容纳抗锯齿边缘
        margin = 4.0  # 增加边距确保完整显示
        return rect.adjusted(-margin, -margin, margin, margin)
    
    def update_appearance(self):
        """更新外观 - 强制刷新显示"""
        super().update_appearance()
        # 强制重绘以确保高质量显示
        self.update(self.boundingRect())


class HighQualityHoleItemFactory:
    """高质量孔位图形项工厂 - 模拟SectorViewFactory的创建方式"""
    
    @staticmethod
    def create_hole_item(hole_data: HoleData) -> HighQualityHoleGraphicsItem:
        """创建高质量孔位图形项"""
        return HighQualityHoleGraphicsItem(hole_data)
    
    @staticmethod
    def create_batch_items(hole_collection) -> list:
        """批量创建高质量孔位图形项（应用扇形视图质量配置）"""
        items = []
        test_logger.info(f"🎨 创建高质量图形项: {len(hole_collection)} 个孔位")
        
        try:
            from src.core_business.graphics.sector_view_factory import SectorViewConfig
            from PySide6.QtGui import QPen, QBrush
            config = SectorViewConfig()
            
            # 批量创建高质量图形项（模拟SectorViewFactory方式）
            for hole in hole_collection:
                # 确保最小半径（与SectorViewFactory一致）
                effective_radius = max(hole.radius, config.MIN_HOLE_RADIUS)
                
                # 创建高质量图形项
                item = HighQualityHoleGraphicsItem(hole)
                
                # 应用扇形视图的样式配置
                item.setPen(QPen(config.DEFAULT_HOLE_COLOR, 1))
                item.setBrush(QBrush(config.DEFAULT_HOLE_COLOR.lighter(150)))
                
                # 设置工具提示（与SectorViewFactory一致）
                tooltip = f"孔位ID: {hole.hole_id}\n位置: ({hole.center_x:.1f}, {hole.center_y:.1f})"
                item.setToolTip(tooltip)
                
                items.append(item)
            
            test_logger.info(f"✅ 高质量图形项创建完成: {len(items)} 个（应用扇形视图样式）")
        except Exception as e:
            test_logger.warning(f"⚠️ 应用扇形视图样式失败，使用默认样式: {e}")
            # 回退到简单创建
            for hole in hole_collection:
                item = HighQualityHoleGraphicsItem(hole)
                items.append(item)
        
        return items


class SingletonMeta(type):
    """单例元类，防止重复初始化"""
    _instances = {}
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
            test_logger.info(f"✅ 创建单例: {cls.__name__}")
        else:
            test_logger.info(f"♻️  复用单例: {cls.__name__}")
        return cls._instances[cls]


class SectorViewQualityPanoramaWidget(CompletePanoramaWidget):
    """采用扇形视图质量配置的全景图组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._hole_radius_multiplier = 1.0
        self._path_opacity = 0.5
        self._show_paths = True
        
        # 应用扇形视图的高质量配置
        self._apply_sector_view_quality()
        
        test_logger.info("🎨 扇形视图质量全景图组件初始化完成")
    
    def _apply_sector_view_quality(self):
        """应用扇形视图的高质量配置"""
        try:
            from src.core_business.graphics.sector_display_config import SectorDisplayConfig
            from src.core_business.graphics.sector_view_factory import SectorViewConfig
            
            # 应用配置
            config = SectorDisplayConfig()
            sector_config = SectorViewConfig()
            
            if hasattr(self, 'panorama_view') and self.panorama_view:
                # 设置关键质量参数
                self.panorama_view.max_auto_scale = sector_config.MAX_AUTO_SCALE  # 1.5
                self.panorama_view.disable_auto_fit = True  # 禁用自动适配，手动控制缩放
                
                test_logger.info(f"✅ 应用扇形视图质量配置: max_auto_scale={sector_config.MAX_AUTO_SCALE}")
                
                # 启用高质量渲染
                self._enable_high_quality_rendering()
        except Exception as e:
            test_logger.warning(f"⚠️ 应用扇形视图质量配置失败: {e}")
    
    def _force_high_lod_rendering(self):
        """强制高LOD渲染以确保矢量质量（激进策略）"""
        if not hasattr(self, 'hole_collection') or not self.hole_collection:
            return
        
        try:
            # 使用更激进的缩放策略
            scene = self.panorama_view.scene()
            if not scene:
                return
                
            # 计算场景边界
            scene_rect = scene.itemsBoundingRect()
            if scene_rect.isEmpty():
                return
            
            # 激进策略：直接设置高缩放以确保LOD > 1.0
            FORCE_HIGH_SCALE = 2.0  # 强制高缩放，确保触发最高质量渲染
            
            # 应用激进缩放
            self.panorama_view.resetTransform()
            self.panorama_view.scale(FORCE_HIGH_SCALE, FORCE_HIGH_SCALE)
            self.panorama_view.centerOn(scene_rect.center())
            
            test_logger.info(f"🚀 应用激进缩放策略: {FORCE_HIGH_SCALE} (确保LOD>1.0)")
            
            # 强制刷新视图
            self.panorama_view.viewport().update()
            
        except Exception as e:
            test_logger.warning(f"⚠️ 强制高LOD渲染失败: {e}")
    
    def _calculate_optimal_scale(self, scene_rect, viewport_size):
        """计算最优缩放比例（基于SectorViewFactory算法）"""
        try:
            # 计算缩放比例
            width_scale = viewport_size[0] / scene_rect.width()
            height_scale = viewport_size[1] / scene_rect.height()
            
            # 使用较小的缩放比例，确保完全适配
            DEFAULT_SCALE_FACTOR = 0.9  # 与SectorViewFactory一致
            scale = min(width_scale, height_scale) * DEFAULT_SCALE_FACTOR
            
            # 限制缩放范围
            MIN_SCALE = 0.1
            MAX_SCALE = 2.0
            scale = max(MIN_SCALE, min(MAX_SCALE, scale))
            
            return scale
        except Exception as e:
            test_logger.warning(f"⚠️ 计算最优缩放失败: {e}")
            return 1.0


    def _optimize_scene_for_quality(self, hole_collection):
        """优化场景设置以匹配扇形视图质量"""
        try:
            scene = self.panorama_view.scene()
            if not scene or not hole_collection:
                return
            
            # 使用SectorViewFactory的边界计算逻辑
            VIEW_MARGIN = 40  # 与SectorViewConfig一致
            
            holes = list(hole_collection.holes.values())
            if holes:
                # 计算精确边界
                min_x = min(h.center_x - h.radius for h in holes)
                max_x = max(h.center_x + h.radius for h in holes)
                min_y = min(h.center_y - h.radius for h in holes)
                max_y = max(h.center_y + h.radius for h in holes)
                
                # 添加边距
                from PySide6.QtCore import QRectF
                scene_rect = QRectF(
                    min_x - VIEW_MARGIN,
                    min_y - VIEW_MARGIN,
                    max_x - min_x + 2 * VIEW_MARGIN,
                    max_y - min_y + 2 * VIEW_MARGIN
                )
                
                scene.setSceneRect(scene_rect)
                test_logger.info(f"✅ 优化场景边界: {scene_rect.width():.1f}x{scene_rect.height():.1f}")
        except Exception as e:
            test_logger.warning(f"⚠️ 优化场景设置失败: {e}")


class NoLODPanoramaWidget(CompletePanoramaWidget):
    """完全禁用LOD优化的全景图组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 强制禁用LOD优化
        self._disable_lod_optimization()
        
        test_logger.info("🚫 LOD优化已完全禁用的全景图组件创建完成")
    
    def _disable_lod_optimization(self):
        """完全禁用LOD优化"""
        try:
            # 1. 修改全景图视图的LOD设置
            if hasattr(self, 'panorama_view') and self.panorama_view:
                # 禁用自动适配和性能优化
                self.panorama_view.disable_auto_fit = False  # 允许自动适配以确保可见
                self.panorama_view.max_auto_scale = 10.0  # 设置很高的缩放值
                
                # 强制高质量渲染设置
                from PySide6.QtGui import QPainter
                from PySide6.QtWidgets import QGraphicsView
                
                self.panorama_view.setRenderHint(QPainter.Antialiasing, True)
                self.panorama_view.setRenderHint(QPainter.SmoothPixmapTransform, True)
                self.panorama_view.setRenderHint(QPainter.TextAntialiasing, True)
                
                # 禁用性能优化
                self.panorama_view.setOptimizationFlag(QGraphicsView.DontSavePainterState, False)
                self.panorama_view.setOptimizationFlag(QGraphicsView.DontAdjustForAntialiasing, False)
                
                # 设置全视口更新模式
                self.panorama_view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
                
                test_logger.info("✅ 全景图视图LOD优化已禁用")
                
                # 强制设置更大的缩放以显示孔位
                self.panorama_view.setTransform(self.panorama_view.transform().scale(2.0, 2.0))
                test_logger.info("✅ 应用了2倍缩放以显示孔位")
            
        except Exception as e:
            test_logger.warning(f"⚠️ 禁用LOD优化失败: {e}")
    
    
    def _force_better_visibility(self):
        """强制提升孔位可见性"""
        try:
            if hasattr(self, 'panorama_view') and self.panorama_view:
                # 重置变换
                self.panorama_view.resetTransform()
                
                # 应用一个更大的基础缩放 (20% 而不是3-8%)
                base_scale = 0.20  # 20%缩放确保孔位可见
                self.panorama_view.scale(base_scale, base_scale)
                
                # 居中显示
                scene = self.panorama_view.scene()
                if scene:
                    scene_rect = scene.itemsBoundingRect()
                    self.panorama_view.centerOn(scene_rect.center())
                
                test_logger.info(f"✅ 强制应用{base_scale*100}%缩放提升可见性")
                
        except Exception as e:
            test_logger.warning(f"⚠️ 强制提升可见性失败: {e}")
    
    def load_hole_collection(self, hole_collection):
        """加载孔位集合时强制使用无LOD图形项和自定义半径"""
        test_logger.info("🚀 使用无LOD优化方法加载孔位集合")
        
        # 保存原始的CompletePanoramaWidget方法以便拦截半径调整
        original_smart_adjust = None
        try:
            from src.core_business.graphics.complete_panorama_widget import CompletePanoramaWidget
            if hasattr(CompletePanoramaWidget, '_smart_adjust_hole_display_size'):
                original_smart_adjust = CompletePanoramaWidget._smart_adjust_hole_display_size
                # 替换为我们的自定义版本
                CompletePanoramaWidget._smart_adjust_hole_display_size = self._custom_smart_adjust_hole_display_size
                test_logger.info("🎯 已拦截CompletePanoramaWidget的半径调整方法")
        except Exception as e:
            test_logger.warning(f"⚠️ 拦截半径调整方法失败: {e}")
        
        try:
            # 调用父类方法加载数据
            result = super().load_hole_collection(hole_collection)
            
            # 再次确保LOD优化被禁用
            self._disable_lod_optimization()
            
            # 强制应用更大的缩放以显示孔位
            self._force_better_visibility()
            
            test_logger.info("✅ 无LOD优化加载完成")
            return result
        finally:
            # 恢复原方法
            if original_smart_adjust is not None:
                try:
                    from src.core_business.graphics.complete_panorama_widget import CompletePanoramaWidget
                    CompletePanoramaWidget._smart_adjust_hole_display_size = original_smart_adjust
                    test_logger.info("🔄 已恢复原半径调整方法")
                except:
                    pass
    
    def _custom_smart_adjust_hole_display_size(self):
        """自定义的智能半径调整方法 - 使用用户指定的缩放"""
        try:
            if not hasattr(self.panorama_view, 'hole_items') or not self.panorama_view.hole_items:
                return
            
            # 获取用户设定的缩放比例
            current_scale = NoLODHoleGraphicsItem.CURRENT_RADIUS_SCALE
            
            # 基础半径设定为小值以避免重叠
            base_radius = 1.0  # 使用1像素作为基础半径
            adjusted_radius = base_radius / current_scale  # 反向计算以抵消后续的缩放
            
            test_logger.info(f"🎯 自定义半径调整: 用户缩放={current_scale*100:.2f}%, 应用半径={adjusted_radius:.2f}px")
            
            # 调整所有孔位项的显示大小
            updated_count = 0
            for hole_item in self.panorama_view.hole_items.values():
                if hasattr(hole_item, 'setRect'):
                    # 创建新的矩形，使用自定义半径
                    new_rect = QRectF(-adjusted_radius, -adjusted_radius, 
                                     adjusted_radius * 2, adjusted_radius * 2)
                    hole_item.setRect(new_rect)
                    updated_count += 1
            
            test_logger.info(f"✅ 自定义调整了 {updated_count} 个孔位项的显示大小")
            
        except Exception as e:
            test_logger.error(f"❌ 自定义半径调整失败: {e}")
            import traceback
            test_logger.error(f"详细错误: {traceback.format_exc()}")
    
    def _override_hole_radius_scaling(self):
        """临时覆盖孔位半径缩放逻辑 - 直接修改孔位数据"""
        try:
            current_scale = NoLODHoleGraphicsItem.CURRENT_RADIUS_SCALE
            test_logger.info(f"🔧 正在应用半径缩放: {current_scale*100:.2f}%")
            
            # 直接修改hole_collection中的半径数据
            if hasattr(self, 'hole_collection') and self.hole_collection:
                modified_count = 0
                for hole in self.hole_collection.holes:
                    # 保存原始半径
                    if not hasattr(hole, '_original_radius'):
                        hole._original_radius = hole.radius
                    
                    # 应用缩放
                    hole.radius = max(0.1, hole._original_radius * current_scale)
                    modified_count += 1
                
                test_logger.info(f"✅ 直接修改了 {modified_count} 个孔位的半径数据")
            
        except Exception as e:
            test_logger.warning(f"⚠️ 覆盖孔位半径缩放失败: {e}")
            import traceback
            test_logger.warning(f"详细错误: {traceback.format_exc()}")


class NoLODHoleItemFactory:
    """无LOD优化的孔位图形项工厂"""
    
    @staticmethod
    def create_hole_item(hole_data: HoleData) -> 'NoLODHoleGraphicsItem':
        """创建无LOD优化的孔位图形项"""
        return NoLODHoleGraphicsItem(hole_data)
    
    @staticmethod
    def create_batch_items(hole_collection) -> list:
        """批量创建无LOD优化的孔位图形项"""
        items = []
        test_logger.info(f"🎨 创建无LOD图形项: {len(hole_collection)} 个孔位")
        
        for hole in hole_collection:
            item = NoLODHoleGraphicsItem(hole)
            items.append(item)
            # 记录前几个孔位的信息以确认工厂被调用
            if len(items) <= 3:
                test_logger.info(f"✅ 无LOD工厂创建孔位: {hole.hole_id}, 半径: {item.hole_data.radius:.3f}")
        
        test_logger.info(f"✅ 无LOD图形项创建完成: {len(items)} 个")
        return items


class NoLODHoleGraphicsItem(HoleGraphicsItem):
    """完全禁用LOD优化的孔位图形项，使用可调节的小半径避免重叠"""
    
    # 类变量：当前半径缩放比例
    CURRENT_RADIUS_SCALE = 0.005  # 默认0.5%，更小的默认值
    
    def __init__(self, hole_data: HoleData, parent=None):
        """使用可调节的小半径初始化避免重叠"""
        # 保存原始半径以便后续调整
        if not hasattr(hole_data, '_original_radius'):
            hole_data._original_radius = hole_data.radius
        
        # 使用类变量的缩放比例
        original_radius = hole_data._original_radius
        scale = self.__class__.CURRENT_RADIUS_SCALE
        hole_data.radius = max(0.1, original_radius * scale)  # 最小0.1像素
        
        # 调用父类构造函数
        super().__init__(hole_data, parent)
        
        # 每100个孔位记录一次日志，避免日志过多
        if hole_data.hole_id.endswith('001') or hole_data.hole_id.endswith('100'):
            test_logger.info(f"🔧 孔位{hole_data.hole_id}半径: {original_radius:.1f} → {hole_data.radius:.1f} (缩放:{scale*100:.2f}%)")
    
    def paint(self, painter: QPainter, option, widget=None):
        """完全禁用LOD优化的绘制方法"""
        # 启用高质量渲染设置
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        
        # 强制调用父类的完整椭圆绘制，完全绕过LOD检查
        from PySide6.QtWidgets import QGraphicsEllipseItem
        QGraphicsEllipseItem.paint(self, painter, option, widget)
        
        # 记录高质量绘制
        test_logger.debug(f"🎨 无LOD绘制孔位: {self.hole_data.hole_id}")


class LegacyQualityDisplayWidget(NoLODPanoramaWidget):
    """使用无LOD优化的高质量显示组件（替代老版本方法）"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        test_logger.info("🏛️ 无LOD优化显示组件初始化完成（替代老版本）")


class OptimizedPanoramaWidget(SectorViewQualityPanoramaWidget):
    """测试界面专用的高质量全景图组件"""
    
    def _enable_high_quality_rendering(self):
        """启用高质量渲染设置"""
        try:
            from PySide6.QtGui import QPainter
            from PySide6.QtWidgets import QGraphicsView
            
            # 强制覆盖性能优化设置，启用高质量渲染
            test_logger.info("🔧 正在覆盖性能优化设置...")
            
            # 启用抗锯齿和平滑变换（强制覆盖）
            self.panorama_view.setRenderHint(QPainter.Antialiasing, True)
            self.panorama_view.setRenderHint(QPainter.SmoothPixmapTransform, True)
            self.panorama_view.setRenderHint(QPainter.TextAntialiasing, True)
            # HighQualityAntialiasing在PySide6中不存在，跳过
            
            # 禁用性能优化标志
            self.panorama_view.setOptimizationFlag(QGraphicsView.DontSavePainterState, False)
            self.panorama_view.setOptimizationFlag(QGraphicsView.DontAdjustForAntialiasing, False)
            
            # 设置为高质量更新模式（测试环境可以接受性能损失）
            self.panorama_view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
            
            # 启用项目缓存
            self.panorama_view.setCacheMode(QGraphicsView.CacheBackground)
            
            # 验证设置是否生效
            aa_enabled = self.panorama_view.renderHints() & QPainter.Antialiasing
            smooth_enabled = self.panorama_view.renderHints() & QPainter.SmoothPixmapTransform
            test_logger.info(f"🔍 抗锯齿状态: {'✅ 启用' if aa_enabled else '❌ 禁用'}")
            test_logger.info(f"🔍 平滑变换状态: {'✅ 启用' if smooth_enabled else '❌ 禁用'}")
            
            test_logger.info("✅ 高质量渲染设置已启用")
        except Exception as e:
            test_logger.warning(f"⚠️ 启用高质量渲染失败: {e}")
            import traceback
            test_logger.warning(f"详细错误: {traceback.format_exc()}")
    
    def load_hole_collection(self, hole_collection):
        """加载孔位集合时应用扇形视图质量配置"""
        test_logger.info("🚀 开始加载孔位集合（扇形视图质量模式）")
        
        # 临时替换工厂方法为高质量版本
        from src.core_business.graphics import hole_item
        original_factory = hole_item.HoleItemFactory
        
        # 替换为高质量工厂
        hole_item.HoleItemFactory = HighQualityHoleItemFactory
        test_logger.info("🎨 已临时替换为高质量图形项工厂")
        
        try:
            # 存储孔位集合用于后续处理
            self.hole_collection = hole_collection
            
            # 优化场景设置（在加载前设置边界）
            self._optimize_scene_for_quality(hole_collection)
            
            # 调用父类方法加载数据
            result = super(SectorViewQualityPanoramaWidget, self).load_hole_collection(hole_collection)
            
            # 应用扇形视图质量配置
            self._apply_sector_view_quality()
            
            # 强制高LOD渲染
            self._force_high_lod_rendering()
            
            # 延迟再次应用缩放（确保场景完全加载后生效）
            from PySide6.QtCore import QTimer
            QTimer.singleShot(500, self._delayed_quality_boost)
            
            test_logger.info("✅ 扇形视图质量配置加载完成")
            return result
            
        except Exception as e:
            test_logger.error(f"❌ 扇形视图质量配置加载失败: {e}")
            import traceback
            test_logger.error(f"详细错误: {traceback.format_exc()}")
            return None
        finally:
            # 恢复原工厂（避免影响其他组件）
            hole_item.HoleItemFactory = original_factory
            test_logger.info("🔄 已恢复原图形项工厂")
    
    def _delayed_quality_boost(self):
        """延迟质量提升 - 确保场景完全加载后再次优化"""
        try:
            test_logger.info("🚀 执行延迟质量提升...")
            
            # 再次应用扇形视图质量配置
            self._apply_sector_view_quality()
            
            # 再次强制高LOD渲染
            self._force_high_lod_rendering()
            
            # 强制更新所有图形项
            scene = self.panorama_view.scene()
            if scene:
                for item in scene.items():
                    if hasattr(item, 'update_appearance'):
                        item.update_appearance()
                    item.update()
                
                # 强制场景更新
                scene.update()
                self.panorama_view.viewport().update()
            
            test_logger.info("✅ 延迟质量提升完成")
        except Exception as e:
            test_logger.warning(f"⚠️ 延迟质量提升失败: {e}")
    
    def set_hole_radius_multiplier(self, multiplier: float):
        """设置孔位半径倍数"""
        self._hole_radius_multiplier = multiplier
        if hasattr(self, 'panorama_view') and hasattr(self.panorama_view, 'hole_items'):
            test_logger.info(f"🔍 调整孔位大小倍数: {multiplier}")
            # 重新调整孔位显示大小
            self._adjust_hole_display_size()
    
    def set_path_visibility(self, visible: bool):
        """设置路径显示开关"""
        self._show_paths = visible
        test_logger.info(f"🛤️  路径显示: {'开启' if visible else '关闭'}")
        # 这里可以添加路径显示/隐藏的逻辑
    
    def set_path_opacity(self, opacity: float):
        """设置路径透明度"""
        self._path_opacity = opacity
        test_logger.info(f"🌫️  路径透明度: {opacity}")


class DataLoader(QThread):
    """异步数据加载器，防止UI阻塞"""
    
    # 信号定义
    loading_progress = Signal(int, str)  # progress, status
    loading_finished = Signal(object)   # hole_collection
    loading_error = Signal(str)         # error_message
    
    def __init__(self, dxf_path: str):
        super().__init__()
        self.dxf_path = dxf_path
        self._is_loading = False
    
    def run(self):
        """异步加载DXF数据"""
        if self._is_loading:
            test_logger.warning("⚠️  数据正在加载中，跳过重复请求")
            return
            
        self._is_loading = True
        
        try:
            test_logger.info(f"📂 使用控制器加载CAP1000产品数据")
            self.loading_progress.emit(10, "初始化控制器...")
            
            # 创建主窗口控制器
            controller = MainWindowController()
            
            self.loading_progress.emit(30, "选择CAP1000产品...")
            
            # 选择CAP1000产品（这会自动加载DXF和孔位数据）
            success = controller.select_product("CAP1000")
            
            if not success:
                raise ValueError("无法选择CAP1000产品")
            
            self.loading_progress.emit(60, "获取孔位数据...")
            
            # 获取孔位集合 - 从business service获取
            hole_collection = controller.business_service.get_hole_collection()
            
            if not hole_collection or len(hole_collection.holes) == 0:
                raise ValueError("CAP1000产品中没有找到孔位数据")
            
            self.loading_progress.emit(90, f"加载完成: {len(hole_collection.holes)} 个孔位")
            
            # 短暂延迟确保UI更新
            self.msleep(300)
            
            self.loading_progress.emit(100, "数据加载完成")
            self.loading_finished.emit(hole_collection)
            
            test_logger.info(f"✅ DXF数据加载成功: {len(hole_collection.holes)} 个孔位")
            
        except Exception as e:
            error_msg = f"DXF加载失败: {str(e)}"
            test_logger.error(f"❌ {error_msg}")
            self.loading_error.emit(error_msg)
        finally:
            self._is_loading = False


class CAP1000RenderTest(QMainWindow):
    """CAP1000渲染测试主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CAP1000.dxf 渲染测试界面")
        self.setGeometry(100, 100, 1600, 1000)
        
        # 数据
        self.hole_collection: Optional[HoleCollection] = None
        self.panorama_widget: Optional[OptimizedPanoramaWidget] = None
        self.simulation_controller: Optional[SimulationController] = None
        self.data_loader: Optional[DataLoader] = None
        
        # DXF文件路径
        self.dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-LFS/Data/Products/CAP1000/dxf/CAP1000.dxf"
        
        # 设置UI
        self._setup_ui()
        
        # 应用样式
        self._apply_theme()
        
        test_logger.info("🚀 CAP1000渲染测试界面初始化完成")
    
    def _setup_ui(self):
        """设置用户界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局 - 水平分割
        main_layout = QHBoxLayout(central_widget)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧控制面板
        control_panel = self._create_control_panel()
        splitter.addWidget(control_panel)
        
        # 右侧显示区域
        display_area = self._create_display_area()
        splitter.addWidget(display_area)
        
        # 设置分割比例：控制面板30%，显示区域70%
        splitter.setSizes([400, 1200])
    
    def _create_control_panel(self) -> QWidget:
        """创建控制面板"""
        panel = QWidget()
        panel.setMaximumWidth(400)
        layout = QVBoxLayout(panel)
        
        # 标题
        title = QLabel("🎯 CAP1000 渲染测试")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 文件信息组
        file_group = QGroupBox("📂 文件信息")
        file_layout = QVBoxLayout(file_group)
        
        self.file_path_label = QLabel("文件路径:")
        self.file_path_label.setWordWrap(True)
        file_layout.addWidget(self.file_path_label)
        
        self.file_status_label = QLabel("状态: 未加载")
        file_layout.addWidget(self.file_status_label)
        
        layout.addWidget(file_group)
        
        # 加载控制组
        load_group = QGroupBox("🔄 加载控制")
        load_layout = QVBoxLayout(load_group)
        
        self.load_button = QPushButton("加载CAP1000.dxf")
        self.load_button.clicked.connect(self._load_dxf_data)
        load_layout.addWidget(self.load_button)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        load_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("")
        load_layout.addWidget(self.progress_label)
        
        layout.addWidget(load_group)
        
        # 渲染方法选择组
        render_group = QGroupBox("🎨 渲染方法")
        render_layout = QVBoxLayout(render_group)
        
        self.render_method_combo = QComboBox()
        self.render_method_combo.addItems([
            "优化全景图 (有LOD优化)",
            "无LOD优化渲染 (推荐)"
        ])
        self.render_method_combo.setCurrentIndex(1)  # 默认选择无LOD方法
        render_layout.addWidget(self.render_method_combo)
        
        render_info = QLabel("💡 无LOD方法完全禁用细节层次优化，确保高质量椭圆渲染")
        render_info.setWordWrap(True)
        render_info.setStyleSheet("color: #87CEEB; font-size: 11px;")
        render_layout.addWidget(render_info)
        
        layout.addWidget(render_group)
        
        # 显示控制组
        display_group = QGroupBox("🎨 显示控制")
        display_layout = QVBoxLayout(display_group)
        
        # 孔位大小控制
        display_layout.addWidget(QLabel("孔位大小:"))
        self.hole_size_slider = QSlider(Qt.Horizontal)
        self.hole_size_slider.setRange(1, 50)  # 0.1% to 5.0% of original radius
        self.hole_size_slider.setValue(5)  # 0.5% (default, smaller)
        self.hole_size_slider.valueChanged.connect(self._on_hole_size_changed)
        display_layout.addWidget(self.hole_size_slider)
        
        self.hole_size_label = QLabel("0.5%")
        display_layout.addWidget(self.hole_size_label)
        
        hole_size_info = QLabel("💡 调整孔位圆点大小，数值越小越不重叠")
        hole_size_info.setWordWrap(True)
        hole_size_info.setStyleSheet("color: #90EE90; font-size: 11px;")
        display_layout.addWidget(hole_size_info)
        
        # 路径显示开关 - 默认关闭，专注孔位圆点
        self.show_paths_checkbox = QCheckBox("显示检测路径连线")
        self.show_paths_checkbox.setChecked(False)  # 默认关闭路径显示
        self.show_paths_checkbox.toggled.connect(self._on_path_visibility_changed)
        display_layout.addWidget(self.show_paths_checkbox)
        
        # 路径透明度控制
        display_layout.addWidget(QLabel("路径透明度:"))
        self.path_opacity_slider = QSlider(Qt.Horizontal)
        self.path_opacity_slider.setRange(1, 30)  # 1%-30%，非常低的透明度
        self.path_opacity_slider.setValue(5)     # 默认5%透明度
        self.path_opacity_slider.valueChanged.connect(self._on_path_opacity_changed)
        display_layout.addWidget(self.path_opacity_slider)
        
        self.opacity_label = QLabel("5%")
        display_layout.addWidget(self.opacity_label)
        
        # 路径说明
        path_info = QLabel("💡 可显示间隔4列S形路径，透明度很低不干扰孔位观察")
        path_info.setWordWrap(True)
        path_info.setStyleSheet("color: #FFA500; font-size: 12px;")
        display_layout.addWidget(path_info)
        
        # 视图缩放控制
        display_layout.addWidget(QLabel("视图缩放:"))
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(10, 500)  # 0.1x to 5.0x
        self.zoom_slider.setValue(100)  # 1.0x
        self.zoom_slider.valueChanged.connect(self._on_zoom_changed)
        display_layout.addWidget(self.zoom_slider)
        
        self.zoom_label = QLabel("1.0x")
        display_layout.addWidget(self.zoom_label)
        
        zoom_info = QLabel("💡 调整缩放比例来查看孔位细节")
        zoom_info.setWordWrap(True)
        zoom_info.setStyleSheet("color: #87CEEB; font-size: 11px;")
        display_layout.addWidget(zoom_info)
        
        layout.addWidget(display_group)
        
        # 测试控制组
        test_group = QGroupBox("🧪 测试控制")
        test_layout = QVBoxLayout(test_group)
        
        self.test_blue_button = QPushButton("测试蓝色状态")
        self.test_blue_button.clicked.connect(self._test_blue_status)
        self.test_blue_button.setEnabled(False)
        test_layout.addWidget(self.test_blue_button)
        
        self.start_simulation_button = QPushButton("开始间隔4列检测")
        self.start_simulation_button.clicked.connect(self._start_simulation)
        self.start_simulation_button.setEnabled(False)
        test_layout.addWidget(self.start_simulation_button)
        
        self.stop_simulation_button = QPushButton("停止检测")
        self.stop_simulation_button.clicked.connect(self._stop_simulation)
        self.stop_simulation_button.setEnabled(False)
        test_layout.addWidget(self.stop_simulation_button)
        
        layout.addWidget(test_group)
        
        # 状态日志
        log_group = QGroupBox("📋 状态日志")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)
        
        # 弹性空间
        layout.addStretch()
        
        return panel
    
    def _create_display_area(self) -> QWidget:
        """创建显示区域"""
        display_widget = QWidget()
        layout = QVBoxLayout(display_widget)
        
        # 显示标题
        title = QLabel("🖼️  孔位渲染显示区域")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 全景图组件占位符
        self.panorama_placeholder = QLabel("请点击\"加载CAP1000.dxf\"开始")
        self.panorama_placeholder.setAlignment(Qt.AlignCenter)
        self.panorama_placeholder.setStyleSheet("""
            QLabel {
                border: 2px dashed #666;
                color: #999;
                font-size: 16px;
                padding: 50px;
            }
        """)
        layout.addWidget(self.panorama_placeholder)
        
        return display_widget
    
    def _apply_theme(self):
        """应用主题样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #666;
                color: #999;
            }
            QSlider::groove:horizontal {
                border: 1px solid #999;
                height: 8px;
                background: #555;
                margin: 2px 0;
            }
            QSlider::handle:horizontal {
                background: #4CAF50;
                border: 1px solid #4CAF50;
                width: 18px;
                margin: -2px 0;
                border-radius: 3px;
            }
        """)
    
    def _load_dxf_data(self):
        """加载DXF数据"""
        test_logger.info("🔍 [DEBUG] 开始DXF加载流程...")
        test_logger.info(f"🔍 [DEBUG] 检查文件路径: {self.dxf_path}")
        
        if not os.path.exists(self.dxf_path):
            test_logger.error(f"❌ [ERROR] DXF文件不存在: {self.dxf_path}")
            self._log_message(f"❌ DXF文件不存在: {self.dxf_path}")
            return
        
        file_size = os.path.getsize(self.dxf_path)
        test_logger.info(f"✅ [DEBUG] 文件存在，大小: {file_size / 1024 / 1024:.2f} MB")
        
        self._log_message("🚀 开始加载CAP1000.dxf...")
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.load_button.setEnabled(False)
        
        # 更新文件路径显示
        self.file_path_label.setText(f"文件路径: {self.dxf_path}")
        self.file_status_label.setText("状态: 加载中...")
        
        test_logger.info("🔍 [DEBUG] 创建数据加载线程...")
        
        # 创建并启动数据加载器
        self.data_loader = DataLoader(self.dxf_path)
        self.data_loader.loading_progress.connect(self._on_loading_progress)
        self.data_loader.loading_finished.connect(self._on_loading_finished)
        self.data_loader.loading_error.connect(self._on_loading_error)
        self.data_loader.start()
        
        test_logger.info("🔍 [DEBUG] 数据加载线程已启动")
    
    @pyqtSlot(int, str)
    def _on_loading_progress(self, progress: int, status: str):
        """加载进度更新"""
        self.progress_bar.setValue(progress)
        self.progress_label.setText(status)
        self._log_message(f"📊 {status} ({progress}%)")
    
    @pyqtSlot(object)
    def _on_loading_finished(self, hole_collection: HoleCollection):
        """加载完成"""
        test_logger.info("🔍 [DEBUG] DXF加载完成回调触发")
        
        self.hole_collection = hole_collection
        
        # 隐藏进度条
        self.progress_bar.setVisible(False)
        self.progress_label.setText("")
        self.load_button.setEnabled(True)
        
        # 更新状态
        hole_count = len(hole_collection.holes)
        test_logger.info(f"🔍 [DEBUG] 解析得到孔位数量: {hole_count}")
        
        # 分析孔位分布
        if hole_count > 0:
            first_hole = next(iter(hole_collection.holes.values()))
            test_logger.info(f"🔍 [DEBUG] 第一个孔位示例: {first_hole.hole_id}, 坐标({first_hole.center_x}, {first_hole.center_y})")
            
            # 分析坐标范围
            x_coords = [hole.center_x for hole in hole_collection.holes.values()]
            y_coords = [hole.center_y for hole in hole_collection.holes.values()]
            test_logger.info(f"🔍 [DEBUG] X坐标范围: {min(x_coords):.1f} ~ {max(x_coords):.1f}")
            test_logger.info(f"🔍 [DEBUG] Y坐标范围: {min(y_coords):.1f} ~ {max(y_coords):.1f}")
        
        self.file_status_label.setText(f"状态: 已加载 ({hole_count} 个孔位)")
        
        # 创建全景图组件
        test_logger.info("🔍 [DEBUG] 开始创建全景图组件...")
        self._create_panorama_widget()
        
        # 启用测试按钮
        self.test_blue_button.setEnabled(True)
        self.start_simulation_button.setEnabled(True)
        
        test_logger.info("✅ [SUCCESS] DXF加载和组件创建完成")
        self._log_message(f"✅ 加载完成！共 {hole_count} 个孔位")
    
    @pyqtSlot(str)
    def _on_loading_error(self, error_message: str):
        """加载错误"""
        self.progress_bar.setVisible(False)
        self.progress_label.setText("")
        self.load_button.setEnabled(True)
        self.file_status_label.setText("状态: 加载失败")
        self._log_message(f"❌ {error_message}")
    
    def _create_panorama_widget(self):
        """创建全景图组件"""
        test_logger.info("🔍 [DEBUG] 进入_create_panorama_widget方法")
        
        if self.panorama_widget is None:
            test_logger.info("🔍 [DEBUG] panorama_widget为空，开始创建...")
            
            # 根据选择的渲染方法创建组件
            render_method = self.render_method_combo.currentIndex()
            
            try:
                if render_method == 1:
                    # 无LOD优化渲染方法（推荐）
                    self.panorama_widget = LegacyQualityDisplayWidget()
                    test_logger.info("✅ [DEBUG] NoLODPanoramaWidget创建成功（无LOD优化方法）")
                else:
                    # 优化全景图方法（有LOD优化）
                    self.panorama_widget = OptimizedPanoramaWidget()
                    test_logger.info("✅ [DEBUG] OptimizedPanoramaWidget创建成功（有LOD优化方法）")
            except Exception as e:
                test_logger.error(f"❌ [ERROR] 全景图组件创建失败: {e}")
                import traceback
                test_logger.error(f"❌ [ERROR] 详细错误: {traceback.format_exc()}")
                return
            
            # 替换占位符
            test_logger.info("🔍 [DEBUG] 开始替换UI占位符...")
            display_area = self.panorama_placeholder.parent()
            layout = display_area.layout()
            
            # 移除占位符
            layout.removeWidget(self.panorama_placeholder)
            self.panorama_placeholder.deleteLater()
            test_logger.info("🔍 [DEBUG] 占位符已移除")
            
            # 添加全景图组件
            layout.addWidget(self.panorama_widget)
            test_logger.info("🔍 [DEBUG] 全景图组件已添加到布局")
        else:
            test_logger.info("🔍 [DEBUG] panorama_widget已存在，跳过创建")
        
        # 加载孔位数据
        if self.hole_collection:
            hole_count = len(self.hole_collection.holes)
            test_logger.info(f"🔍 [DEBUG] 开始加载 {hole_count} 个孔位数据到全景图...")
            
            try:
                self.panorama_widget.load_hole_collection(self.hole_collection)
                test_logger.info("✅ [DEBUG] 孔位数据加载到全景图成功")
                self._log_message("🖼️  全景图渲染完成")
            except Exception as e:
                test_logger.error(f"❌ [ERROR] 孔位数据加载失败: {e}")
                import traceback
                test_logger.error(f"❌ [ERROR] 详细错误: {traceback.format_exc()}")
        else:
            test_logger.warning("⚠️ [WARNING] hole_collection为空，无法加载数据")
    
    def _on_hole_size_changed(self, value: int):
        """孔位大小改变 - 实时更新"""
        percentage = value / 10.0  # 转换为百分比 (1-50 -> 0.1%-5.0%)
        self.hole_size_label.setText(f"{percentage:.1f}%")
        
        # 更新类变量
        scale = percentage / 100.0
        NoLODHoleGraphicsItem.CURRENT_RADIUS_SCALE = scale
        
        self._log_message(f"🔧 孔位大小: {percentage:.1f}% (实时更新中...)")
        
        # 实时更新已存在的孔位图形项
        self._update_existing_hole_sizes(scale)
    
    def _update_existing_hole_sizes(self, scale: float):
        """实时更新已存在的孔位图形项的大小 - 使用新的API"""
        try:
            if not hasattr(self, 'panorama_widget') or not self.panorama_widget:
                self._log_message("⚠️ 全景图组件不存在")
                return
            
            # 使用新的API直接设置缩放因子
            if hasattr(self.panorama_widget, 'set_user_hole_scale_factor'):
                self.panorama_widget.set_user_hole_scale_factor(scale)
                test_logger.info(f"✅ 使用新API设置孔位缩放因子: {scale*100:.1f}%")
                self._log_message(f"✅ 孔位缩放已设置: {scale*100:.1f}%")
            else:
                self._log_message("⚠️ 全景图组件不支持设置用户缩放因子")
                test_logger.warning("全景图组件不支持set_user_hole_scale_factor方法")
            
        except Exception as e:
            test_logger.error(f"❌ 设置孔位缩放因子失败: {e}")
            self._log_message(f"❌ 设置失败: {e}")
            import traceback
            test_logger.error(f"详细错误: {traceback.format_exc()}")
    
    def _on_path_visibility_changed(self, checked: bool):
        """路径显示开关"""
        if self.simulation_controller:
            self.simulation_controller.set_path_visibility(checked)
        
        self._log_message(f"🛤️  路径显示: {'开启' if checked else '关闭'}")
    
    def _on_path_opacity_changed(self, value: int):
        """路径透明度改变"""
        opacity = value / 100.0
        self.opacity_label.setText(f"{value}%")
        
        if self.simulation_controller:
            self.simulation_controller.set_path_opacity(opacity)
        
        self._log_message(f"🌫️  路径透明度: {value}%")
    
    def _on_zoom_changed(self, value: int):
        """缩放倍数改变"""
        zoom = value / 100.0  # 转换为倍数
        self.zoom_label.setText(f"{zoom:.1f}x")
        
        # 如果有全景图组件，应用缩放
        if self.panorama_widget and hasattr(self.panorama_widget, 'panorama_view'):
            try:
                # 重置变换然后应用新的缩放
                self.panorama_widget.panorama_view.resetTransform()
                self.panorama_widget.panorama_view.scale(zoom, zoom)
                test_logger.info(f"🔍 视图缩放已更新: {zoom:.1f}x")
                self._log_message(f"🔍 视图缩放: {zoom:.1f}x")
            except Exception as e:
                test_logger.warning(f"⚠️ 缩放更新失败: {e}")
                self._log_message(f"❌ 缩放更新失败: {e}")
    
    def _test_blue_status(self):
        """测试蓝色状态显示"""
        test_logger.info("🔍 [DEBUG] 开始蓝色状态测试...")
        
        if not self.hole_collection or not self.panorama_widget:
            test_logger.warning("⚠️ [WARNING] 缺少必要组件，无法测试")
            self._log_message("❌ 请先加载DXF数据")
            return
        
        test_logger.info(f"🔍 [DEBUG] 可用孔位数量: {len(self.hole_collection.holes)}")
        self._log_message("🔵 开始测试蓝色状态...")
        
        # 选择几个测试孔位
        test_holes = list(self.hole_collection.holes.keys())[:5]
        blue_color = QColor(33, 150, 243)  # 蓝色
        
        test_logger.info(f"🔍 [DEBUG] 测试孔位: {test_holes}")
        test_logger.info(f"🔍 [DEBUG] 蓝色颜色: RGB({blue_color.red()}, {blue_color.green()}, {blue_color.blue()})")
        
        for i, hole_id in enumerate(test_holes):
            # 延迟显示蓝色状态
            QTimer.singleShot(i * 500, lambda hid=hole_id: self._set_hole_blue_status(hid, blue_color))
        
        # 3秒后恢复原状态
        QTimer.singleShot(3000, self._reset_test_holes_status)
    
    def _set_hole_blue_status(self, hole_id: str, blue_color: QColor):
        """设置孔位蓝色状态"""
        test_logger.info(f"🔍 [DEBUG] 设置孔位 {hole_id} 为蓝色状态")
        
        if self.panorama_widget:
            try:
                self.panorama_widget.update_hole_status(hole_id, HoleStatus.PENDING, blue_color)
                test_logger.info(f"✅ [DEBUG] 孔位 {hole_id} 蓝色状态设置成功")
                self._log_message(f"🔵 {hole_id} 设置为蓝色状态")
            except Exception as e:
                test_logger.error(f"❌ [ERROR] 孔位 {hole_id} 蓝色状态设置失败: {e}")
        else:
            test_logger.warning("⚠️ [WARNING] panorama_widget不存在")
    
    def _reset_test_holes_status(self):
        """重置测试孔位状态"""
        test_holes = list(self.hole_collection.holes.keys())[:5]
        for hole_id in test_holes:
            if self.panorama_widget:
                self.panorama_widget.update_hole_status(hole_id, HoleStatus.PENDING)
        self._log_message("🔄 测试孔位状态已重置")
    
    def _start_simulation(self):
        """开始间隔4列检测模拟"""
        if not self.hole_collection or not self.panorama_widget:
            self._log_message("❌ 请先加载DXF数据")
            return
        
        self._log_message("🚀 开始间隔4列S形检测模拟...")
        
        # 创建模拟控制器 - 使用混合显示控制器
        if self.simulation_controller is None:
            self.simulation_controller = HybridSimulationController()
            self.simulation_controller.set_panorama_widget(self.panorama_widget)
            # 同步当前的显示设置
            self.simulation_controller.set_path_visibility(self.show_paths_checkbox.isChecked())
            self.simulation_controller.set_path_opacity(self.path_opacity_slider.value() / 100.0)
            
            self.simulation_controller.simulation_started.connect(lambda: self._log_message("✅ 模拟检测已启动"))
            self.simulation_controller.simulation_stopped.connect(lambda: self._log_message("⏹️  模拟检测已停止"))
            self.simulation_controller.simulation_progress.connect(self._on_simulation_progress)
        
        # 加载孔位数据并开始模拟
        self.simulation_controller.load_hole_collection(self.hole_collection)
        self.simulation_controller.start_simulation()
        
        # 更新按钮状态
        self.start_simulation_button.setEnabled(False)
        self.stop_simulation_button.setEnabled(True)
    
    def _stop_simulation(self):
        """停止检测模拟"""
        if self.simulation_controller:
            self.simulation_controller.stop_simulation()
        
        # 更新按钮状态
        self.start_simulation_button.setEnabled(True)
        self.stop_simulation_button.setEnabled(False)
        
        self._log_message("⏹️  检测模拟已停止")
    
    @pyqtSlot(int, int)
    def _on_simulation_progress(self, current: int, total: int):
        """模拟进度更新"""
        percentage = (current / total * 100) if total > 0 else 0
        self._log_message(f"📈 检测进度: {current}/{total} ({percentage:.1f}%)")
    
    def _log_message(self, message: str):
        """添加日志消息"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        # 添加到日志区域
        self.log_text.append(formatted_message)
        
        # 自动滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)
        
        # 同时输出到控制台
        test_logger.info(message)


def main():
    """主函数"""
    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("CAP1000 渲染测试")
    app.setApplicationVersion("1.0")
    
    # 设置应用图标和样式
    app.setStyle('Fusion')  # 使用Fusion样式获得更好的外观
    
    # 创建主窗口
    window = CAP1000RenderTest()
    window.show()
    
    test_logger.info("🎬 CAP1000渲染测试界面启动完成")
    
    # 运行应用
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        test_logger.info("👋 用户中断，程序退出")
        sys.exit(0)


if __name__ == "__main__":
    main()