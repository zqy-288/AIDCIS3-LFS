"""
蛇形路径协调器
负责协调和同步多个视图之间的蛇形路径状态和更新
"""

from typing import Optional, List, Dict, Any
from PySide6.QtCore import QObject, Signal

from src.core_business.graphics.snake_path_renderer import PathStrategy, PathRenderStyle
from src.core_business.graphics.sector_controllers import UnifiedLogger
from src.core_business.models.hole_data import HoleCollection


class SnakePathCoordinator(QObject):
    """
    蛇形路径协调器
    
    职责：
    1. 管理全局蛇形路径状态
    2. 协调多个视图的路径更新
    3. 提供统一的路径控制接口
    4. 处理路径同步逻辑
    """
    
    # 信号
    path_enabled_changed = Signal(bool)  # 路径启用状态改变
    path_strategy_changed = Signal(PathStrategy)  # 路径策略改变
    path_style_changed = Signal(PathRenderStyle)  # 路径样式改变
    path_progress_updated = Signal(int)  # 路径进度更新
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = UnifiedLogger("SnakePathCoordinator")
        
        # 全局状态
        self.enabled = False
        self.strategy = PathStrategy.INTERVAL_FOUR_S_SHAPE  # 默认使用间隔4列S形策略
        self.style = PathRenderStyle.SIMPLE_LINE
        self.debug_mode = False
        self.current_progress = 0
        
        # 注册的视图组件
        self.registered_views = []
        self.main_view = None  # 主视图（用于生成全局路径）
        self.sector_view = None  # 扇形视图
        self.panorama_widget = None  # 全景组件
        
        # 全局路径数据
        self.global_snake_path: List[str] = []
        self.hole_collection: Optional[HoleCollection] = None
        
    def register_main_view(self, view):
        """注册主视图（GraphicsView）"""
        self.main_view = view
        self.registered_views.append(view)
        self.logger.info("注册主视图", "📝")
        
    def register_sector_view(self, view):
        """注册扇形视图（DynamicSectorView）"""
        self.sector_view = view
        self.registered_views.append(view)
        self.logger.info("注册扇形视图", "📝")
        
    def register_panorama_widget(self, widget):
        """注册全景组件（CompletePanoramaWidget）"""
        self.panorama_widget = widget
        self.registered_views.append(widget)
        self.logger.info("注册全景组件", "📝")
        
    def set_hole_collection(self, collection: HoleCollection):
        """设置孔位集合"""
        self.hole_collection = collection
        self.logger.info(f"设置孔位集合: {len(collection) if collection else 0}个孔位", "📦")
        
        # 如果路径已启用，重新生成
        if self.enabled:
            self._regenerate_global_path()
            
    def enable_snake_path(self, enabled: bool, debug: bool = False):
        """
        启用/禁用蛇形路径
        同步更新所有注册的视图
        """
        self.enabled = enabled
        self.debug_mode = debug
        
        if debug:
            self.logger.info(f"🐍 [调试] 全局蛇形路径: {'启用' if enabled else '禁用'}", "🔧")
        
        # 生成或清除全局路径
        if enabled and self.hole_collection:
            self._regenerate_global_path()
        else:
            self.global_snake_path.clear()
        
        # 同步更新所有视图
        self._sync_enable_state(enabled, debug)
        
        # 发出信号
        self.path_enabled_changed.emit(enabled)
        
    def set_path_strategy(self, strategy: PathStrategy):
        """
        设置路径策略
        同步更新所有注册的视图
        """
        self.strategy = strategy
        
        if self.debug_mode:
            self.logger.info(f"🐍 [调试] 全局路径策略: {strategy.value}", "🔧")
        
        # 如果路径已启用，重新生成
        if self.enabled and self.hole_collection:
            self._regenerate_global_path()
        
        # 同步更新所有视图
        self._sync_strategy(strategy)
        
        # 发出信号
        self.path_strategy_changed.emit(strategy)
        
    def set_path_style(self, style: PathRenderStyle):
        """
        设置路径样式
        同步更新所有注册的视图
        """
        self.style = style
        
        if self.debug_mode:
            self.logger.info(f"🐍 [调试] 全局路径样式: {style.value}", "🔧")
        
        # 同步更新所有视图
        self._sync_style(style)
        
        # 发出信号
        self.path_style_changed.emit(style)
        
    def update_progress(self, current_sequence: int):
        """
        更新路径进度
        同步更新所有注册的视图
        """
        self.current_progress = current_sequence
        
        # 同步更新所有视图
        self._sync_progress(current_sequence)
        
        # 发出信号
        self.path_progress_updated.emit(current_sequence)
        
    def _regenerate_global_path(self):
        """重新生成全局路径"""
        if not self.main_view or not self.hole_collection:
            self.logger.warning("无法生成全局路径：缺少主视图或孔位数据", "⚠️")
            return
        
        try:
            # 确保主视图有孔位数据
            if not self.main_view.hole_collection:
                self.main_view.set_hole_collection(self.hole_collection)
            
            # 生成全局路径
            self.global_snake_path = self.main_view.snake_path_renderer.generate_snake_path(self.strategy)
            
            if self.debug_mode:
                self.logger.info(f"🐍 [调试] 生成全局路径: {len(self.global_snake_path)}个孔位", "🔧")
                if self.global_snake_path:
                    self.logger.info(f"    前5个: {self.global_snake_path[:5]}", "📍")
                    
        except Exception as e:
            self.logger.error(f"生成全局路径失败: {e}", "❌")
            
    def _sync_enable_state(self, enabled: bool, debug: bool):
        """同步启用状态到所有视图"""
        if self.main_view and hasattr(self.main_view, 'set_snake_path_visible'):
            self.main_view.set_snake_path_visible(enabled)
            
        if self.sector_view and hasattr(self.sector_view, 'enable_snake_path'):
            self.sector_view.enable_snake_path(enabled, debug)
            
        if self.panorama_widget and hasattr(self.panorama_widget, 'enable_snake_path'):
            self.panorama_widget.enable_snake_path(enabled, debug)
            
    def _sync_strategy(self, strategy: PathStrategy):
        """同步路径策略到所有视图"""
        if self.main_view and hasattr(self.main_view, 'set_snake_path_strategy'):
            self.main_view.set_snake_path_strategy(strategy)
            
        if self.sector_view and hasattr(self.sector_view, 'set_snake_path_strategy'):
            self.sector_view.set_snake_path_strategy(strategy)
            
        if self.panorama_widget and hasattr(self.panorama_widget, 'set_snake_path_strategy'):
            self.panorama_widget.set_snake_path_strategy(strategy)
            
    def _sync_style(self, style: PathRenderStyle):
        """同步路径样式到所有视图"""
        if self.main_view and hasattr(self.main_view, 'set_snake_path_style'):
            self.main_view.set_snake_path_style(style)
            
        if self.sector_view and hasattr(self.sector_view, 'set_snake_path_style'):
            self.sector_view.set_snake_path_style(style)
            
        if self.panorama_widget and hasattr(self.panorama_widget, 'set_snake_path_style'):
            self.panorama_widget.set_snake_path_style(style)
            
    def _sync_progress(self, current_sequence: int):
        """同步路径进度到所有视图"""
        if self.main_view and hasattr(self.main_view, 'update_snake_path_progress'):
            self.main_view.update_snake_path_progress(current_sequence)
            
        if self.panorama_widget and hasattr(self.panorama_widget, 'update_snake_path_progress'):
            self.panorama_widget.update_snake_path_progress(current_sequence)
            
    def get_global_path(self) -> List[str]:
        """获取全局路径"""
        return self.global_snake_path
    
    def get_snake_path_order(self, holes: List[Any]) -> List[Any]:
        """获取蛇形路径顺序的孔位列表"""
        if not holes:
            return []
            
        try:
            # 使用SnakePathRenderer生成路径
            from src.core_business.graphics.snake_path_renderer import SnakePathRenderer
            renderer = SnakePathRenderer()
            
            # 创建临时的hole_collection
            from src.core_business.models.hole_data import HoleCollection
            holes_dict = {hole.hole_id: hole for hole in holes}
            temp_collection = HoleCollection(holes_dict)
            
            # 设置hole_collection到renderer
            renderer.set_hole_collection(temp_collection)
            
            # 生成路径（返回hole_id列表）
            path_ids = renderer.generate_snake_path(self.strategy)
            
            # 根据ID顺序返回hole对象列表
            ordered_holes = []
            for hole_id in path_ids:
                if hole_id in holes_dict:
                    ordered_holes.append(holes_dict[hole_id])
                    
            return ordered_holes
            
        except Exception as e:
            self.logger.error(f"生成蛇形路径顺序失败: {e}")
            # 如果失败，返回原始顺序
            return holes.copy()
        
    def get_statistics(self) -> Dict[str, Any]:
        """获取综合统计信息"""
        stats = {
            'coordinator': {
                'enabled': self.enabled,
                'strategy': self.strategy.value,
                'style': self.style.value,
                'debug_mode': self.debug_mode,
                'current_progress': self.current_progress,
                'global_path_length': len(self.global_snake_path),
                'registered_views': len(self.registered_views)
            },
            'views': {}
        }
        
        # 收集各视图的统计信息
        if self.main_view and hasattr(self.main_view, 'get_snake_path_statistics'):
            stats['views']['main_view'] = self.main_view.get_snake_path_statistics()
            
        if self.sector_view and hasattr(self.sector_view, 'get_snake_path_debug_info'):
            stats['views']['sector_view'] = self.sector_view.get_snake_path_debug_info()
            
        if self.panorama_widget and hasattr(self.panorama_widget, 'get_snake_path_statistics'):
            stats['views']['panorama_widget'] = self.panorama_widget.get_snake_path_statistics()
            
        return stats
        
    def test_synchronization(self):
        """测试同步功能"""
        self.logger.info("=== 测试蛇形路径同步 ===", "🧪")
        
        # 测试启用/禁用
        self.logger.info("测试1: 启用路径", "1️⃣")
        self.enable_snake_path(True, debug=True)
        
        # 测试策略切换
        self.logger.info("测试2: 切换策略", "2️⃣")
        self.set_path_strategy(PathStrategy.SPATIAL_SNAKE)
        
        # 测试样式切换
        self.logger.info("测试3: 切换样式", "3️⃣")
        self.set_path_style(PathRenderStyle.CURVED_ARROW)
        
        # 测试进度更新
        self.logger.info("测试4: 更新进度", "4️⃣")
        self.update_progress(10)
        
        # 打印统计信息
        stats = self.get_statistics()
        self.logger.info(f"统计信息: {stats}", "📊")
        
        self.logger.info("=== 同步测试完成 ===", "✅")