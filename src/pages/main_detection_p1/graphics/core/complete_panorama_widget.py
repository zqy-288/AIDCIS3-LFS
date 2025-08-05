"""
完整全景图显示组件
显示所有孔位的全景视图，支持扇形交互和状态更新

警告：此文件已被重构并迁移到新架构
请使用 src.modules.panorama_view 包中的新组件
此文件将在未来版本中移除
"""

import warnings
warnings.warn(
    "CompletePanoramaWidget 已被弃用，请使用 src.modules.panorama_view 包中的新架构",
    DeprecationWarning,
    stacklevel=2
)

import math
from typing import Dict, Optional, List, Tuple, Any
from collections import defaultdict

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt, QPointF, QRectF, Signal, QTimer, QEvent, QObject
from PySide6.QtGui import QColor, QFont, QPen, QBrush, QTransform
try:
    from PySide6 import shiboken6 as sip
except ImportError:
    try:
        import shiboken6 as sip
    except ImportError:
        # 如果都失败了，创建一个假的sip模块
        class FakeSip:
            @staticmethod
            def isdeleted(obj):
                try:
                    # 尝试访问对象的属性来检查是否有效
                    _ = obj.__class__
                    return False
                except:
                    return True
        sip = FakeSip()

from src.pages.main_detection_p1.graphics.core.graphics_view import OptimizedGraphicsView
from src.pages.main_detection_p1.graphics.core.sector_types import SectorQuadrant
from src.pages.main_detection_p1.graphics.core.sector_highlight_item import SectorHighlightItem
from src.pages.main_detection_p1.graphics.core.sector_controllers import UnifiedLogger
from src.shared.models.hole_data import HoleCollection, HoleStatus
from src.shared.components.theme import ModernThemeManager as ThemeManager
from src.pages.main_detection_p1.graphics.core.snake_path_renderer import PathStrategy, PathRenderStyle


class CompletePanoramaWidget(QWidget):
    """完整全景图显示组件"""
    
    # 信号
    sector_clicked = Signal(SectorQuadrant)  # 扇形点击信号
    status_update_completed = Signal(int)    # 状态更新完成信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = UnifiedLogger("CompletePanorama")
        self.setWindowTitle("完整孔位全景")
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        # 初始化属性
        self.hole_collection: Optional[HoleCollection] = None
        self.center_point: Optional[QPointF] = None
        self.panorama_radius: float = 0.0
        self.sector_highlights: Dict[SectorQuadrant, SectorHighlightItem] = {}
        self.current_highlighted_sector: Optional[SectorQuadrant] = None
        
        # 蛇形路径相关
        self.snake_path_enabled = False
        self.snake_path_strategy = PathStrategy.HYBRID
        self.snake_path_style = PathRenderStyle.SIMPLE_LINE
        self.complete_snake_path = []  # 完整蛇形路径
        self.debug_mode = False
        
        # 批量更新相关
        self.batch_update_timer = QTimer()
        self.batch_update_timer.timeout.connect(self._execute_batch_update)
        self.batch_update_timer.setSingleShot(True)
        self.batch_update_interval = 200  # 批量更新间隔（毫秒）
        self.pending_status_updates: Dict[str, HoleStatus] = {}
        self._update_lock = False
        
        # 统一高亮管理定时器 - 替代所有高亮相关定时器
        self.unified_highlight_timer = QTimer()
        self.unified_highlight_timer.timeout.connect(self._execute_unified_highlight)
        self.unified_highlight_timer.setSingleShot(True)
        self.highlight_delay = 50  # 统一延迟时间
        
        # 高亮操作队列
        self.pending_highlight_operations = []  # [(operation_type, sector), ...]
        self.current_highlight_state: Optional[SectorQuadrant] = None
        
        # 设置UI
        self._setup_ui()
        
        # 应用主题
        self._apply_theme()
    
    def _get_scene(self):
        """安全获取scene对象"""
        if hasattr(self.panorama_view, 'scene'):
            # scene是属性
            return self.panorama_view.scene
        else:
            # scene是方法
            return self.panorama_view.scene()
        
    def _setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)  # 减小边距
        layout.setSpacing(5)  # 减小间距
        
        # 全景图形视图
        self.panorama_view = OptimizedGraphicsView()
        # 调整为更小的尺寸以适应侧边栏
        self.panorama_view.setMinimumSize(300, 300)
        self.panorama_view.setSizePolicy(
            self.panorama_view.sizePolicy().horizontalPolicy(),
            self.panorama_view.sizePolicy().verticalPolicy()
        )
        
        # 安装事件过滤器以捕获鼠标点击
        self.panorama_view.viewport().installEventFilter(self)
        
        # 注意：不再创建单独的scene属性，直接使用panorama_view内部的scene
        
        # 创建全景图容器以实现完美居中
        panorama_container = QWidget()
        panorama_layout = QVBoxLayout(panorama_container)
        panorama_layout.setContentsMargins(0, 0, 0, 0)
        panorama_layout.addWidget(self.panorama_view)
        
        layout.addWidget(panorama_container, 1)
        
        # 信息标签（可选，为了节省空间可以隐藏）
        self.info_label = QLabel("全景图准备就绪")
        self.info_label.setAlignment(Qt.AlignCenter)
        font = self.info_label.font()
        font.setPointSize(10)  # 减小字体
        self.info_label.setFont(font)
        self.info_label.setStyleSheet("""
            QLabel {
                padding: 4px;
                background-color: rgba(240, 240, 240, 180);
                border-radius: 4px;
                max-height: 30px;
            }
        """)
        self.info_label.setMaximumHeight(30)
        layout.addWidget(self.info_label)
        
    def _apply_theme(self):
        """应用主题样式"""
        try:
            theme_manager = ThemeManager()
            if hasattr(theme_manager, 'apply_theme'):
                theme_manager.apply_theme(self)
        except Exception as e:
            self.logger.warning(f"应用主题失败: {e}", "⚠️")
            
    def load_complete_view(self, hole_collection: HoleCollection, scale_manager=None):
        """
        加载完整的全景图
        
        Args:
            hole_collection: 孔位集合
            scale_manager: 缩放管理器（可选）
        """
        self.logger.info(f"开始加载全景图，孔位数量: {len(hole_collection) if hole_collection else 0}", "🎯")
        
        if hole_collection and len(hole_collection) > 0:
            try:
                # 保存数据引用
                self.hole_collection = hole_collection
                
                # 调试信息
                self.logger.info(f"全景图视图类型: {type(self.panorama_view)}")
                self.logger.info(f"全景图视图大小: {self.panorama_view.size()}")
                
                # 加载孔位到视图
                self.panorama_view.load_holes(hole_collection)
                
                # 调试：检查加载后的状态
                if hasattr(self.panorama_view, 'hole_items'):
                    self.logger.info(f"加载后hole_items数量: {len(self.panorama_view.hole_items)}")
                    
                # 获取场景
                try:
                    scene = self._get_scene()
                except TypeError:
                    scene = self.panorama_view.scene
                    
                if scene:
                    self.logger.info(f"场景项数量: {len(scene.items())}")
                    self.logger.info(f"场景边界: {scene.sceneRect()}")
                    
                    # 强制更新场景
                    scene.update()
                    self.panorama_view.update()
                    
                # 计算几何信息
                self._calculate_geometry()
                
                # 自适应调整孔位显示大小（针对大数据集）
                self._adjust_hole_display_size()
                
                # 创建扇形高亮项
                self._create_sector_highlights()
                
                # 应用智能缩放
                self._apply_smart_zoom()
                
                # 如果启用了蛇形路径，生成并渲染
                if self.snake_path_enabled:
                    self._generate_complete_snake_path()
                    self._render_snake_path()
                    
                    if self.debug_mode:
                        self.logger.info("🐍 [调试] 全景图加载后自动生成蛇形路径", "✅")
                
                # 更新信息
                actual_hole_count = len(self.panorama_view.hole_items) if hasattr(self.panorama_view, 'hole_items') else 0
                self.info_label.setText(f"全景图已加载: {actual_hole_count} 个孔位")
                
                # 最终调试信息
                self.logger.info(f"全景图最终状态 - 孔位: {actual_hole_count}, 可见: {self.isVisible()}")
                
                self.logger.info("全景图加载完成", "✅")
                
            except Exception as e:
                self.logger.error(f"全景图加载失败: {e}", "❌")
                self.info_label.setText("全景图加载错误")
        else:
            self.logger.warning("没有提供有效的孔位数据", "⚠️")
            self.info_label.setText("暂无数据")
    
    def load_hole_collection(self, hole_collection: HoleCollection):
        """
        加载孔位集合（load_complete_view的别名）
        为了兼容性而提供
        """
        self.load_complete_view(hole_collection)
            
    def _calculate_geometry(self):
        """计算全景图的几何信息"""
        try:
            if not self.hole_collection:
                return
                
            # 获取数据边界
            bounds = self.hole_collection.get_bounds()
            if not bounds:
                return
                
            # 计算中心点
            min_x, min_y, max_x, max_y = bounds
            self.center_point = QPointF((min_x + max_x) / 2, (min_y + max_y) / 2)
            
            # 计算半径（最远点到中心的距离）
            max_distance = 0
            for hole in self.hole_collection.holes.values():
                distance = math.sqrt(
                    (hole.center_x - self.center_point.x()) ** 2 +
                    (hole.center_y - self.center_point.y()) ** 2
                )
                max_distance = max(max_distance, distance)
            
            self.panorama_radius = max_distance * 1.2  # 添加20%边距，确保所有孔位可见
            
            self.logger.debug(f"几何计算完成 - 中心: ({self.center_point.x():.1f}, {self.center_point.y():.1f}), 半径: {self.panorama_radius:.1f}", "📐")
            
        except Exception as e:
            self.logger.error(f"几何计算失败: {e}", "❌")
            
    def _adjust_hole_display_size(self):
        """自适应调整孔位显示大小（与全局缩放管理器协调的连续函数算法）"""
        try:
            if not hasattr(self.panorama_view, 'hole_items') or not self.panorama_view.hole_items:
                return
                
            hole_count = len(self.panorama_view.hole_items)
            
            # 获取全局缩放管理器的数据规模分类
            from src.pages.main_detection_p1.graphics.core.scale_manager import _detect_data_scale
            data_scale = _detect_data_scale(self.panorama_view, debug=False)
            
            # 计算数据密度（孔位数量 / 显示面积）
            if self.panorama_radius > 0:
                area = 3.14159 * (self.panorama_radius ** 2)
                density = hole_count / area
            else:
                density = hole_count / 1000000  # 备用密度
            
            # 连续函数计算最优孔位显示半径
            display_radius = self._calculate_optimal_hole_radius(hole_count, density, data_scale)
            
            # 与全局缩放配置协调
            global_scale_factor = self._get_global_scale_factor(data_scale)
            adjusted_radius = display_radius * global_scale_factor
            
            self.logger.info(f"数据规模:{data_scale}, 孔位:{hole_count}, 密度:{density:.6f}, "
                           f"基础半径:{display_radius:.2f}px, 全局系数:{global_scale_factor:.2f}, "
                           f"最终半径:{adjusted_radius:.2f}px", "🔍")
            
            # 调整所有孔位项的显示大小
            updated_count = 0
            for hole_item in self.panorama_view.hole_items.values():
                if hasattr(hole_item, 'setRect'):
                    # 创建以原点为中心的新矩形
                    new_rect = QRectF(-adjusted_radius, -adjusted_radius, 
                                    adjusted_radius * 2, adjusted_radius * 2)
                    hole_item.setRect(new_rect)
                    updated_count += 1
            
            self.logger.info(f"已调整 {updated_count} 个孔位项的显示大小", "✅")
            
        except Exception as e:
            self.logger.warning(f"调整孔位显示大小失败: {e}", "⚠️")
    
    def _calculate_optimal_hole_radius(self, hole_count: int, density: float, data_scale: str) -> float:
        """
        使用连续函数计算最优孔位显示半径
        
        Args:
            hole_count: 孔位数量
            density: 数据密度
            data_scale: 数据规模分类 ("small", "medium", "large", "massive")
        
        Returns:
            最优显示半径（像素）
        """
        import math
        
        # 基础半径范围 - 专门为全景图优化，确保清晰可见
        # 针对大型数据集显示问题，大幅提高半径确保可见性
        min_radius = 40.0  # 显著提高最小半径，确保在小缩放比例下仍可见
        max_radius = 80.0  # 显著提高最大半径，改善所有数据集的显示效果
        
        # 连续函数：基于对数缩放的密度响应
        # 使用 log(x + 1) 函数提供平滑的连续变化
        if hole_count <= 50:
            # 微小数据集：保持较大的显示半径以确保可见性
            base_radius = max_radius
        else:
            # 优化的连续对数函数：更温和的缩放曲线
            normalized_count = (hole_count - 50) / 30000  # 扩大归一化范围，使缩放更温和
            log_factor = math.log(normalized_count * 5 + 1) / math.log(6)  # 更温和的对数因子
            
            # 基于密度的微调（降低密度影响）
            density_factor = min(0.5, density * 0.0005)  # 减少密度影响因子
            
            # 连续计算半径（更保守的缩减）
            radius_reduction = (max_radius - min_radius) * (log_factor * 0.7 + density_factor * 0.2)
            base_radius = max_radius - radius_reduction
        
        # 确保半径在合理范围内
        base_radius = max(min_radius, min(max_radius, base_radius))
        
        return base_radius
    
    def _get_global_scale_factor(self, data_scale: str) -> float:
        """
        获取与全局缩放管理器协调的缩放因子
        
        Args:
            data_scale: 数据规模分类
        
        Returns:
            全局缩放因子
        """
        # 从scale_manager配置中获取对应的缩放因子（针对全景图优化）
        # 针对显示问题，提高所有缩放因子确保可见性
        scale_factors = {
            "small": 1.5,     # 小数据集：更大放大，充分利用空间
            "medium": 1.3,    # 中等数据集：适度放大
            "large": 1.2,     # 大数据集：保持放大，确保可见性
            "massive": 1.1    # 超大数据集：仍然放大，确保最低可见性
        }
        
        return scale_factors.get(data_scale, 1.0)
            
    def _create_sector_highlights(self):
        """创建扇形高亮项"""
        if not self.center_point or self.panorama_radius <= 0:
            return
            
        # 清除旧的高亮项
        for sector, highlight in list(self.sector_highlights.items()):
            try:
                # 检查对象是否还有效
                if highlight:
                    try:
                        # 使用sip.isdeleted，如果不存在则使用替代方法
                        is_deleted = False
                        if hasattr(sip, 'isdeleted'):
                            is_deleted = sip.isdeleted(highlight)
                        else:
                            # 尝试访问对象属性来检查是否有效
                            try:
                                _ = highlight.scene
                            except (RuntimeError, AttributeError):
                                is_deleted = True
                                
                        if not is_deleted and highlight.scene():
                            scene = self._get_scene()
                            if scene:
                                scene.removeItem(highlight)
                    except (RuntimeError, AttributeError):
                        # 对象已被删除
                        pass
            except RuntimeError:
                # 对象已被删除，忽略错误
                pass
        self.sector_highlights.clear()
        
        # 创建新的高亮项
        for sector in SectorQuadrant:
            self._create_sector_highlight_item(sector)
            
        # 创建扇形分隔线
        self._create_sector_dividers()
        
    def _create_sector_highlight_item(self, sector: SectorQuadrant) -> bool:
        """创建单个扇形高亮项"""
        try:
            if not self.center_point or self.panorama_radius <= 0:
                self.logger.warning(f"无法创建扇形 {sector.value} 高亮：缺少必要数据", "⚠️")
                return False
                
            # 创建高亮项
            highlight = SectorHighlightItem(
                sector=sector,
                center=self.center_point,
                radius=self.panorama_radius
            )
            
            # 添加到场景
            try:
                scene = self._get_scene()
            except TypeError:
                scene = self.panorama_view.scene
                
            if scene:
                scene.addItem(highlight)
                self.sector_highlights[sector] = highlight
            else:
                self.logger.error(f"无法添加扇形高亮：场景为空")
            
            self.logger.debug(f"创建扇形 {sector.value} 高亮项", "✅")
            return True
            
        except Exception as e:
            self.logger.error(f"创建扇形 {sector.value} 高亮失败: {e}", "❌")
            return False
            
    def _create_sector_dividers(self):
        """创建扇形分隔线"""
        try:
            if not self.center_point or self.panorama_radius <= 0:
                return
                
            # 创建十字分隔线
            pen = QPen(QColor(200, 200, 200, 100))
            pen.setWidth(2)
            pen.setStyle(Qt.DashLine)
            
            # 水平线
            scene = self._get_scene()
            if not scene:
                return
            h_line = scene.addLine(
                self.center_point.x() - self.panorama_radius,
                self.center_point.y(),
                self.center_point.x() + self.panorama_radius,
                self.center_point.y(),
                pen
            )
            h_line.setZValue(50)
            
            # 垂直线
            v_line = scene.addLine(
                self.center_point.x(),
                self.center_point.y() - self.panorama_radius,
                self.center_point.x(),
                self.center_point.y() + self.panorama_radius,
                pen
            )
            v_line.setZValue(50)
            
            self.logger.debug("扇形分隔线创建完成", "✅")
            
        except Exception as e:
            self.logger.error(f"扇形分隔线创建失败: {e}", "❌")
            
    def _apply_smart_zoom(self):
        """应用与全局缩放管理器协调的智能缩放"""
        try:
            if not self.hole_collection or len(self.hole_collection) == 0:
                return
            
            # 获取数据规模分类
            from src.pages.main_detection_p1.graphics.core.scale_manager import _detect_data_scale, calculate_scale_config
            data_scale = _detect_data_scale(self.panorama_view, debug=False)
            
            # 首先获取scene
            try:
                scene = self._get_scene()
            except:
                scene = None
                
            if not scene:
                self.logger.warning("无法获取场景，跳过智能缩放")
                return
            
            # 使用计算的几何信息来设置场景边界
            if self.center_point and self.panorama_radius > 0:
                # 基于中心点和半径创建内容矩形
                content_rect = QRectF(
                    self.center_point.x() - self.panorama_radius,
                    self.center_point.y() - self.panorama_radius,
                    self.panorama_radius * 2,
                    self.panorama_radius * 2
                )
            else:
                # 备用方案：获取场景边界
                content_rect = scene.itemsBoundingRect()
                if content_rect.isEmpty():
                    self.logger.warning("场景边界为空，跳过智能缩放")
                    return
            
            # 获取视图矩形
            view_rect = QRectF(self.panorama_view.viewport().rect())
            
            # 根据数据规模选择适当的缩放模式
            scale_mode = self._get_panorama_scale_mode(data_scale)
            
            try:
                # 使用全局缩放管理器计算缩放配置
                scale_config = calculate_scale_config(scale_mode, content_rect, view_rect)
                
                # 获取计算的场景矩形和缩放参数
                scene_rect = scale_config.get('scene_rect', content_rect)
                margin_ratio = scale_config.get('margin_ratio', 0.05)
                
                self.logger.info(f"使用缩放模式: {scale_mode}, 边距比例: {margin_ratio:.3f}", "🔍")
                
            except Exception as scale_error:
                # 备用方案：使用简单的固定边距
                self.logger.warning(f"缩放配置计算失败，使用备用方案: {scale_error}", "⚠️")
                margin = self._get_adaptive_margin(data_scale)
                scene_rect = content_rect.adjusted(-margin, -margin, margin, margin)
            
            # 设置场景矩形
            if scene:
                scene.setSceneRect(scene_rect)
            else:
                self.logger.error("无法设置场景矩形：场景为空")
            
            # 适配到视图
            self.panorama_view.fitInView(scene_rect, Qt.KeepAspectRatio)
            
            # 进行完美居中调整
            self._ensure_perfect_centering()
            
            self.logger.info(f"智能缩放完成 - 数据规模: {data_scale}", "✅")
            
        except Exception as e:
            self.logger.warning(f"智能缩放失败: {e}", "⚠️")
    
    def _get_panorama_scale_mode(self, data_scale: str) -> str:
        """
        根据数据规模获取全景图缩放模式
        
        Args:
            data_scale: 数据规模分类
        
        Returns:
            对应的缩放模式
        """
        scale_mode_map = {
            "small": "sidebar_panorama_overview",      # 小数据集：标准侧边栏模式
            "medium": "sidebar_panorama_overview",     # 中等数据集：标准侧边栏模式
            "large": "panorama_overview",              # 大数据集：概览模式
            "massive": "massive_dataset_panorama"      # 超大数据集：专用模式
        }
        
        return scale_mode_map.get(data_scale, "panorama_overview")
    
    def _get_adaptive_margin(self, data_scale: str) -> float:
        """
        获取基于数据规模的自适应边距
        
        Args:
            data_scale: 数据规模分类
        
        Returns:
            边距值（像素）
        """
        margin_map = {
            "small": 50.0,     # 小数据集：较大边距
            "medium": 75.0,    # 中等数据集：中等边距
            "large": 100.0,    # 大数据集：标准边距
            "massive": 50.0    # 超大数据集：紧凑边距以最大化显示区域
        }
        
        return margin_map.get(data_scale, 75.0)
            
    def _ensure_perfect_centering(self):
        """确保全景图完美居中"""
        try:
            if not self.center_point:
                return
                
            # 获取视图中心
            view_center = self.panorama_view.viewport().rect().center()
            scene_center = self.panorama_view.mapToScene(view_center)
            
            # 计算偏移
            offset = self.center_point - scene_center
            
            # 如果偏移较大，进行调整
            if abs(offset.x()) > 1 or abs(offset.y()) > 1:
                current_center = self.panorama_view.mapToScene(self.panorama_view.viewport().rect().center())
                new_center = current_center + offset
                self.panorama_view.centerOn(new_center)
                
                self.logger.debug(f"执行完美居中调整: ({new_center.x():.1f}, {new_center.y():.1f})", "✨")
                
        except Exception as e:
            self.logger.warning(f"完美居中调整失败: {e}", "⚠️")
            
    def highlight_sector(self, sector: SectorQuadrant):
        """高亮显示指定扇形（使用统一定时器）"""
        self._schedule_highlight_operation("highlight", sector)
    
    def clear_highlight(self):
        """清除所有扇形高亮（使用统一定时器）"""
        self._schedule_highlight_operation("clear", None)
    
    def _schedule_highlight_operation(self, operation_type: str, sector: Optional[SectorQuadrant]):
        """
        调度高亮操作到统一定时器
        
        Args:
            operation_type: 操作类型 ("highlight" 或 "clear")
            sector: 扇形（清除操作时为None）
        """
        # 添加操作到队列，但保持队列简洁
        new_operation = (operation_type, sector)
        
        # 如果是相同的操作，则跳过
        if self.pending_highlight_operations and self.pending_highlight_operations[-1] == new_operation:
            return
        
        # 清空队列并添加新操作（最新的操作优先）
        self.pending_highlight_operations = [new_operation]
        
        # 重启统一定时器
        if self.unified_highlight_timer.isActive():
            self.unified_highlight_timer.stop()
        
        self.unified_highlight_timer.start(self.highlight_delay)
    
    def _execute_unified_highlight(self):
        """执行统一的高亮操作"""
        try:
            if not self.pending_highlight_operations:
                return
            
            # 处理队列中的最后一个操作（最新的）
            operation_type, sector = self.pending_highlight_operations[-1]
            
            if operation_type == "highlight" and sector:
                self._do_highlight_sector(sector)
            elif operation_type == "clear":
                self._do_clear_highlight()
            
        except Exception as e:
            self.logger.error(f"执行统一高亮操作失败: {e}", "❌")
        finally:
            # 清空操作队列
            self.pending_highlight_operations.clear()
    
    def _do_highlight_sector(self, sector: SectorQuadrant):
        """实际执行高亮扇形"""
        # 如果已经高亮了相同扇形，跳过
        if self.current_highlight_state == sector:
            return
        
        # 先清除当前高亮
        self._do_clear_highlight()
        
        # 高亮新扇形
        if sector in self.sector_highlights:
            self.sector_highlights[sector].highlight(True)
            self.current_highlight_state = sector
            self.current_highlighted_sector = sector
            self.logger.debug(f"高亮扇形: {sector.value}", "🎯")
        else:
            # 如果高亮项不存在，尝试创建
            if self._create_sector_highlight_item(sector):
                self.sector_highlights[sector].highlight(True)
                self.current_highlight_state = sector
                self.current_highlighted_sector = sector
                self.logger.debug(f"创建并高亮扇形: {sector.value}", "🎯")
            else:
                self.logger.warning(f"无法创建扇形高亮项: {sector.value}", "⚠️")
        
        # 单次场景更新
        self.panorama_view.scene.update()
    
    def _do_clear_highlight(self):
        """实际执行清除高亮"""
        if not self.current_highlight_state:
            return
        
        # 清除所有高亮
        for highlight_item in self.sector_highlights.values():
            highlight_item.highlight(False)
        
        self.current_highlight_state = None
        self.current_highlighted_sector = None
        self.logger.debug("清除所有扇形高亮", "🧹")
        
        # 单次场景更新
        self.panorama_view.scene.update()
            
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """事件过滤器，处理鼠标点击"""
        if obj == self.panorama_view.viewport() and event.type() == QEvent.MouseButtonPress:
            mouse_event = event
            if mouse_event.button() == Qt.LeftButton:
                # 转换坐标
                scene_pos = self.panorama_view.mapToScene(mouse_event.pos())
                
                # 检测点击的扇形
                clicked_sector = self._detect_sector_at_position(scene_pos)
                
                if clicked_sector:
                    self.logger.info(f"检测到扇形点击: {clicked_sector.value}", "🎯")
                    self.sector_clicked.emit(clicked_sector)
                    self.highlight_sector(clicked_sector)
                    return True
                    
        return super().eventFilter(obj, event)
        
    def _detect_sector_at_position(self, scene_pos: QPointF) -> Optional[SectorQuadrant]:
        """检测指定位置的扇形"""
        try:
            if not self.center_point or not self.hole_collection:
                return None
                
            # 计算相对于中心的角度
            dx = scene_pos.x() - self.center_point.x()
            dy = scene_pos.y() - self.center_point.y()
            
            # 检查是否在有效半径内
            distance = math.sqrt(dx * dx + dy * dy)
            max_valid_distance = self.panorama_radius * 1.2
            
            if distance > max_valid_distance:
                return None
                
            # 计算角度（转换为0-360度）
            # 使用数学坐标系：Y轴向上，角度从正X轴开始逆时针增加
            angle_rad = math.atan2(dy, dx)  # 数学坐标系
            angle_deg = math.degrees(angle_rad)
            
            # 归一化到0-360
            if angle_deg < 0:
                angle_deg += 360
                
            # 根据角度确定扇形
            return SectorQuadrant.from_angle(angle_deg)
            
        except Exception as e:
            self.logger.error(f"扇形检测失败: {e}", "❌")
            return None
            
    def update_hole_status(self, hole_id: str, status: HoleStatus, color_override=None):
        """
        更新孔位状态 - 统一接口实现（支持批量更新）
        
        Args:
            hole_id: 孔位ID
            status: 新状态
            color_override: 颜色覆盖（如蓝色检测中状态）
        """
        self.logger.debug(f"接收到状态更新: {hole_id} -> {status.value if hasattr(status, 'value') else status}", "📦")
        
        # 检查是否需要立即更新
        if self._should_update_immediately():
            self._update_hole_immediately(hole_id, status, color_override)
        else:
            # 添加到批量更新队列
            self.pending_status_updates[hole_id] = (status, color_override)
            
            # 启动或重置批量更新定时器
            if self.batch_update_timer.isActive():
                self.batch_update_timer.stop()
                
            self.batch_update_timer.start(self.batch_update_interval)
            self.logger.debug(f"启动批量更新定时器: {self.batch_update_interval}ms，当前队列: {len(self.pending_status_updates)}个", "⏰")
            
    def _should_update_immediately(self) -> bool:
        """判断是否需要立即更新"""
        # 这里可以根据需要添加条件判断
        # 例如：某些关键状态需要立即更新
        return False
        
    def _update_hole_immediately(self, hole_id: str, status: HoleStatus, color_override=None):
        """立即更新单个孔位状态"""
        try:
            if hasattr(self.panorama_view, 'hole_items') and hole_id in self.panorama_view.hole_items:
                hole_item = self.panorama_view.hole_items[hole_id]
                
                # 更新状态
                if hasattr(hole_item, 'update_status'):
                    hole_item.update_status(status)
                    # 设置颜色覆盖（如果提供）
                    if color_override and hasattr(hole_item, 'set_color_override'):
                        hole_item.set_color_override(color_override)
                    elif not color_override and hasattr(hole_item, 'clear_color_override'):
                        # 清除颜色覆盖
                        hole_item.clear_color_override()
                    hole_item.update()
                    
                self.logger.debug(f"立即更新完成: {hole_id}", "✅")
            else:
                self.logger.warning(f"未找到孔位图形项: {hole_id}", "❌")
                
        except Exception as e:
            self.logger.error(f"立即更新失败: {e}", "❌")
            
    def _execute_batch_update(self):
        """执行批量更新"""
        if not self.pending_status_updates or self._update_lock:
            return
            
        self._update_lock = True
        update_count = len(self.pending_status_updates)
        
        self.logger.info(f"开始批量更新 {update_count} 个孔位状态", "🚀")
        
        try:
            updated_count = 0
            
            if hasattr(self.panorama_view, 'hole_items'):
                for hole_id, status_data in self.pending_status_updates.items():
                    if hole_id in self.panorama_view.hole_items:
                        hole_item = self.panorama_view.hole_items[hole_id]
                        
                        # 解析状态数据（可能是元组或单独的状态）
                        if isinstance(status_data, tuple):
                            status, color_override = status_data
                        else:
                            status, color_override = status_data, None
                        
                        # 更新状态
                        if hasattr(hole_item, 'update_status'):
                            hole_item.update_status(status)
                            # 设置颜色覆盖（如果提供）
                            if color_override and hasattr(hole_item, 'set_color_override'):
                                hole_item.set_color_override(color_override)
                            elif not color_override and hasattr(hole_item, 'clear_color_override'):
                                # 清除颜色覆盖
                                hole_item.clear_color_override()
                            updated_count += 1
                            
                # 只在有实际更新时才刷新场景
                if updated_count > 0:
                    scene = self._get_scene()
                    if scene:
                        scene.update()
                
                self.logger.info(f"批量更新完成: {updated_count}/{update_count} 个孔位", "✅")
                
            # 清空缓存
            self.pending_status_updates.clear()
            
            # 发送完成信号
            self.status_update_completed.emit(updated_count)
            
        except Exception as e:
            self.logger.error(f"批量更新失败: {e}", "❌")
        finally:
            self._update_lock = False
            
    def batch_update_hole_status(self, status_updates: Dict[str, HoleStatus]):
        """直接批量更新多个孔位状态"""
        self.logger.info(f"直接批量更新 {len(status_updates)} 个孔位", "🚀")
        
        # 合并到待更新队列
        self.pending_status_updates.update(status_updates)
        
        # 立即执行批量更新
        self._execute_batch_update()
        
    def set_batch_update_interval(self, interval_ms: int):
        """设置批量更新间隔"""
        self.batch_update_interval = max(50, min(1000, interval_ms))
        self.logger.info(f"批量更新间隔设置为: {self.batch_update_interval}ms", "⚙️")
        
    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        # 重新调整扇形高亮位置
        if self.center_point and self.panorama_radius > 0:
            self._ensure_perfect_centering()
            
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {
            'total_holes': len(self.hole_collection) if self.hole_collection else 0,
            'visible_holes': 0,
            'pending_updates': len(self.pending_status_updates),
            'sectors': {}
        }
        
        if hasattr(self.panorama_view, 'hole_items'):
            stats['visible_holes'] = len([item for item in self.panorama_view.hole_items.values() if item.isVisible()])
            
        # 统计各扇形的孔位数量
        if self.hole_collection:
            for sector in SectorQuadrant:
                sector_holes = [
                    hole for hole in self.hole_collection.holes.values()
                    if SectorQuadrant.from_position(
                        hole.center_x, hole.center_y,
                        self.center_point.x() if self.center_point else 0,
                        self.center_point.y() if self.center_point else 0
                    ) == sector
                ]
                stats['sectors'][sector.value] = len(sector_holes)
                
        return stats
    
    # ==================== 蛇形路径功能 ====================
    
    def enable_snake_path(self, enabled: bool, debug: bool = False):
        """启用/禁用蛇形路径显示"""
        self.snake_path_enabled = enabled
        self.debug_mode = debug
        
        if debug:
            self.logger.info(f"🐍 [调试] 全景图蛇形路径: {'启用' if enabled else '禁用'}", "🔧")
        
        if enabled and self.hole_collection:
            self._generate_complete_snake_path()
            self._render_snake_path()
        else:
            self._clear_snake_path()
    
    def set_snake_path_strategy(self, strategy: PathStrategy):
        """设置蛇形路径策略"""
        self.snake_path_strategy = strategy
        
        if self.debug_mode:
            self.logger.info(f"🐍 [调试] 全景图路径策略: {strategy.value}", "🔧")
        
        if self.snake_path_enabled and self.hole_collection:
            self._generate_complete_snake_path()
            self._render_snake_path()
    
    def set_snake_path_style(self, style: PathRenderStyle):
        """设置蛇形路径样式"""
        self.snake_path_style = style
        
        if self.debug_mode:
            self.logger.info(f"🐍 [调试] 全景图路径样式: {style.value}", "🔧")
        
        # 更新视图的路径样式
        self.panorama_view.set_snake_path_style(style)
    
    def _generate_complete_snake_path(self):
        """生成完整的蛇形路径"""
        if not self.hole_collection:
            return
        
        # 使用全景视图生成完整路径
        self.complete_snake_path = self.panorama_view.snake_path_renderer.generate_snake_path(
            self.snake_path_strategy
        )
        
        if self.debug_mode:
            self.logger.info(f"🐍 [调试] 生成完整路径: {len(self.complete_snake_path)}个孔位", "🔧")
            if len(self.complete_snake_path) > 0:
                self.logger.info(f"    前10个: {self.complete_snake_path[:10]}", "📍")
    
    def _render_snake_path(self):
        """渲染蛇形路径"""
        if not self.complete_snake_path:
            return
        
        if self.debug_mode:
            self.logger.info(f"🐍 [调试] 渲染完整路径: {len(self.complete_snake_path)}个孔位", "🎨")
        
        # 设置路径数据
        self.panorama_view.snake_path_renderer.set_path_data(self.complete_snake_path)
        # 设置样式
        self.panorama_view.snake_path_renderer.set_render_style(self.snake_path_style)
        # 渲染路径
        self.panorama_view.snake_path_renderer.render_paths()
        # 设置可见性
        self.panorama_view.set_snake_path_visible(self.snake_path_enabled)
    
    def _clear_snake_path(self):
        """清除蛇形路径"""
        self.panorama_view.clear_snake_path()
        self.complete_snake_path.clear()
        
        if self.debug_mode:
            self.logger.info("🐍 [调试] 清除全景图路径", "🧹")
    
    def update_snake_path_progress(self, current_sequence: int):
        """更新蛇形路径进度"""
        if self.snake_path_enabled:
            self.panorama_view.update_snake_path_progress(current_sequence)
    
    def get_snake_path_statistics(self) -> Dict[str, Any]:
        """获取蛇形路径统计信息"""
        stats = {
            'enabled': self.snake_path_enabled,
            'strategy': self.snake_path_strategy.value,
            'style': self.snake_path_style.value,
            'total_path_length': len(self.complete_snake_path),
            'path_summary': {}
        }
        
        # 统计各扇形的路径段
        if self.complete_snake_path and self.center_point:
            sector_paths = defaultdict(list)
            
            for hole_id in self.complete_snake_path:
                if hole_id in self.hole_collection.holes:
                    hole = self.hole_collection.holes[hole_id]
                    sector = SectorQuadrant.from_position(
                        hole.center_x, hole.center_y,
                        self.center_point.x(), self.center_point.y()
                    )
                    sector_paths[sector].append(hole_id)
            
            for sector, path in sector_paths.items():
                stats['path_summary'][sector.value] = {
                    'count': len(path),
                    'first_5': path[:5] if path else []
                }
        
        # 获取渲染器的统计信息
        if self.panorama_view.snake_path_renderer:
            stats['renderer_stats'] = self.panorama_view.get_snake_path_statistics()
        
        return stats