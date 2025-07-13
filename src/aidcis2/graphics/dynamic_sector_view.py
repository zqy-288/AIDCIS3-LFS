"""
动态扇形区域图形管理器
根据检测进度动态显示对应扇形区域的DXF图形部分
"""

import math
from typing import Dict, List, Optional, Tuple
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGraphicsItem, QGraphicsPathItem
from PySide6.QtCore import Qt, QPointF, QRectF, Signal, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QPainterPath

from aidcis2.graphics.graphics_view import OptimizedGraphicsView
from aidcis2.graphics.sector_manager import SectorManager, SectorQuadrant, SectorProgress
from aidcis2.models.hole_data import HoleData, HoleCollection


class SectorHighlightItem(QGraphicsPathItem):
    """扇形区域高亮显示图形项"""
    
    def __init__(self, sector: SectorQuadrant, center: QPointF, radius: float, sector_bounds: Optional[Tuple[float, float, float, float]] = None, parent=None):
        super().__init__(parent)
        self.sector = sector
        self.center = center
        self.radius = radius
        self.sector_bounds = sector_bounds  # (min_x, min_y, max_x, max_y)
        self.highlight_mode = "sector"  # "sector" 或 "bounds"
        self.setup_highlight()
    
    def setup_highlight(self):
        """设置高亮显示样式"""
        path = QPainterPath()
        
        if self.highlight_mode == "bounds" and self.sector_bounds:
            # 边界框模式：绘制矩形边界
            min_x, min_y, max_x, max_y = self.sector_bounds
            rect = QRectF(min_x, min_y, max_x - min_x, max_y - min_y)
            path.addRect(rect)
            
            # 边界框样式：更淡的颜色，虚线边框
            highlight_color = QColor(76, 175, 80, 60)  # 淡绿色，更透明
            border_color = QColor(76, 175, 80, 120)    # 绿色边框
            pen = QPen(border_color, 2, Qt.DashLine)
            
        else:
            # 扇形模式：绘制扇形区域
            start_angle, span_angle = self._get_sector_angles()
            
            # 移动到中心点
            path.moveTo(self.center)
            
            # 绘制扇形
            rect = QRectF(
                self.center.x() - self.radius, 
                self.center.y() - self.radius,
                self.radius * 2, 
                self.radius * 2
            )
            path.arcTo(rect, start_angle, span_angle)
            path.closeSubpath()
            
            # 扇形样式：黄色半透明
            highlight_color = QColor(255, 193, 7, 80)  # 淡黄色，半透明
            border_color = QColor(255, 193, 7, 150)   # 边框稍深
            pen = QPen(border_color, 2, Qt.SolidLine)
        
        self.setPath(path)
        self.setBrush(QBrush(highlight_color))
        self.setPen(pen)
        
        # 设置图层级别（在孔位上方但不遮挡）
        self.setZValue(10)  # 高于孔位图形项
        
        # 默认隐藏
        self.setVisible(False)
    
    def _get_sector_angles(self) -> Tuple[float, float]:
        """获取扇形的起始角度和跨度角度"""
        # Qt的角度系统：0度在3点钟方向，顺时针为正
        # 但是数据使用数学坐标系：0度在右边，逆时针为正
        # 需要转换：Qt角度 = -数学角度
        # 数学坐标系：
        #   扇形1: 0°-90° (右上)
        #   扇形2: 90°-180° (左上)
        #   扇形3: 180°-270° (左下)
        #   扇形4: 270°-360° (右下)
        # Qt坐标系（顺时针）：
        #   扇形1: 0°到-90° => 270°到360°
        #   扇形2: -90°到-180° => 180°到270°
        #   扇形3: -180°到-270° => 90°到180°
        #   扇形4: -270°到-360° => 0°到90°
        angle_map = {
            SectorQuadrant.SECTOR_1: (270, 90),    # 右上：270°-360°
            SectorQuadrant.SECTOR_2: (180, 90),    # 左上：180°-270°
            SectorQuadrant.SECTOR_3: (90, 90),     # 左下：90°-180°
            SectorQuadrant.SECTOR_4: (0, 90),      # 右下：0°-90°
        }
        return angle_map.get(self.sector, (0, 90))
    
    def show_highlight(self):
        """显示高亮"""
        self.setVisible(True)
        self.update()
    
    def hide_highlight(self):
        """隐藏高亮"""
        self.setVisible(False)
        self.update()
    
    def set_highlight_mode(self, mode: str):
        """设置高亮模式
        
        Args:
            mode: "sector" 用于扇形高亮，"bounds" 用于边界框高亮
        """
        if mode in ["sector", "bounds"]:
            self.highlight_mode = mode
            self.setup_highlight()
            print(f"🎨 [高亮] 扇形 {self.sector.value} 切换到 {mode} 模式")


class SectorGraphicsManager:
    """扇形图形管理器 - 负责将DXF图形划分为4个扇形区域"""
    
    def __init__(self, hole_collection: HoleCollection, center_point: Optional[QPointF] = None):
        self.hole_collection = hole_collection
        self.center_point = center_point if center_point else self._calculate_center()
        self.sector_collections = self._create_sector_collections()
    
    def _calculate_center(self) -> QPointF:
        """计算DXF图形的中心点"""
        if not self.hole_collection:
            return QPointF(0, 0)
        
        bounds = self.hole_collection.get_bounds()
        center_x = (bounds[0] + bounds[2]) / 2
        center_y = (bounds[1] + bounds[3]) / 2
        return QPointF(center_x, center_y)
    
    def _create_sector_collections(self) -> Dict[SectorQuadrant, HoleCollection]:
        """为每个扇形区域创建独立的孔位集合"""
        sector_collections = {}
        
        for sector in SectorQuadrant:
            sector_holes = {}
            
            for hole_id, hole in self.hole_collection.holes.items():
                if self._is_hole_in_sector(hole, sector):
                    sector_holes[hole_id] = hole
            
            # 创建扇形专用的孔位集合
            sector_collection = HoleCollection(
                holes=sector_holes,
                metadata={
                    'sector': sector,
                    'source_file': self.hole_collection.metadata.get('source_file', ''),
                    'total_holes': len(sector_holes),
                    'sector_bounds': None  # 先设置为None，后续计算
                }
            )
            
            sector_collections[sector] = sector_collection
        
        # 现在计算每个扇形的边界并更新metadata
        for sector, collection in sector_collections.items():
            if collection and len(collection) > 0:
                bounds = collection.get_bounds()
                collection.metadata['sector_bounds'] = bounds
        
        return sector_collections
    
    def _is_hole_in_sector(self, hole: HoleData, sector: SectorQuadrant) -> bool:
        """判断孔位是否属于指定扇形区域"""
        dx = hole.center_x - self.center_point.x()
        dy = hole.center_y - self.center_point.y()
        
        # 计算角度
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        
        # 转换为0-360度范围
        if angle_deg < 0:
            angle_deg += 360
        
        # 判断属于哪个扇形
        # 将数学坐标系角度转换为Qt坐标系角度（顺时针）
        # 使用与主视图SectorManager相同的数学坐标系（不转换）
        # 直接使用数学角度系统，与主视图保持一致
        
        # 数学坐标系中的扇形定义（与SectorManager保持一致）：
        # 区域1：0°-90°（右上）
        # 区域2：90°-180°（左上）
        # 区域3：180°-270°（左下）
        # 区域4：270°-360°（右下）
        if sector == SectorQuadrant.SECTOR_1:
            return 0 <= angle_deg < 90      # 右上
        elif sector == SectorQuadrant.SECTOR_2:
            return 90 <= angle_deg < 180    # 左上
        elif sector == SectorQuadrant.SECTOR_3:
            return 180 <= angle_deg < 270   # 左下
        elif sector == SectorQuadrant.SECTOR_4:
            return 270 <= angle_deg < 360   # 右下
        
        return False
    
    def _get_sector_bounds(self, sector: SectorQuadrant) -> Tuple[float, float, float, float]:
        """获取扇形区域的边界范围"""
        # 从已创建的扇形集合中获取边界，避免递归调用
        if sector in self.sector_collections:
            sector_collection = self.sector_collections[sector]
            if sector_collection and len(sector_collection) > 0:
                return sector_collection.get_bounds()
        
        # 如果扇形集合还未创建，直接计算该扇形的孔位边界
        sector_holes = []
        for hole_id, hole in self.hole_collection.holes.items():
            if self._is_hole_in_sector(hole, sector):
                sector_holes.append(hole)
        
        if not sector_holes:
            return (0, 0, 0, 0)
        
        min_x = min(hole.center_x for hole in sector_holes)
        max_x = max(hole.center_x for hole in sector_holes)
        min_y = min(hole.center_y for hole in sector_holes)
        max_y = max(hole.center_y for hole in sector_holes)
        
        return (min_x, min_y, max_x, max_y)
    
    def get_sector_collection(self, sector: SectorQuadrant) -> Optional[HoleCollection]:
        """获取指定扇形区域的孔位集合"""
        return self.sector_collections.get(sector)
    
    def get_all_sector_collections(self) -> Dict[SectorQuadrant, HoleCollection]:
        """获取所有扇形区域的孔位集合"""
        return self.sector_collections.copy()


class DynamicSectorDisplayWidget(QWidget):
    """动态扇形区域显示组件"""
    
    sector_changed = Signal(SectorQuadrant)  # 扇形切换信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sector_graphics_manager: Optional[SectorGraphicsManager] = None
        self.complete_hole_collection: Optional[HoleCollection] = None  # 保存完整孔位集合
        self.current_sector = SectorQuadrant.SECTOR_1
        self.sector_views = {}  # 缓存各扇形的图形视图
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 移除标题栏，直接显示图形区域
        # title_frame = QFrame()
        # title_frame.setFrameStyle(QFrame.StyledPanel)
        # title_frame.setMaximumHeight(40)
        # title_layout = QHBoxLayout(title_frame)
        # 
        # self.title_label = QLabel("动态扇形区域显示")
        # self.title_label.setFont(QFont("Arial", 12, QFont.Bold))
        # self.title_label.setAlignment(Qt.AlignCenter)
        # title_layout.addWidget(self.title_label)
        # 
        # layout.addWidget(title_frame)
        
        # 图形显示区域 - 直接填满整个容器
        self.graphics_view = OptimizedGraphicsView()
        self.graphics_view.setFrameStyle(QFrame.StyledPanel)
        # 移除最小尺寸限制，让白色区域可以自由扩展
        # self.graphics_view.setMinimumSize(700, 600)
        
        # 直接添加graphics_view，不使用居中容器，填满整个可用空间
        layout.addWidget(self.graphics_view)
        
        # 添加状态标签用于显示提示信息
        self.status_label = QLabel("请选择产品型号或加载DXF文件")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 14px;
                background-color: rgba(240, 240, 240, 180);
                border: 1px dashed #ccc;
                border-radius: 8px;
                padding: 20px;
                margin: 50px;
            }
        """)
        # 初始时显示状态标签
        layout.addWidget(self.status_label)
        
        # 状态信息 - 移除状态标签以避免不必要的显示
        # self.status_label = QLabel("等待数据加载...")
        # self.status_label.setAlignment(Qt.AlignCenter)
        # self.status_label.setStyleSheet("padding: 5px; background-color: #f0f0f0; border-radius: 3px;")
        # layout.addWidget(self.status_label)
    
    def set_hole_collection(self, hole_collection: HoleCollection):
        """设置孔位集合并创建扇形图形管理器"""
        if hole_collection and len(hole_collection) > 0:
            # 保存完整的孔位集合以供扇形切换使用
            self.complete_hole_collection = hole_collection
            
            self.sector_graphics_manager = SectorGraphicsManager(hole_collection)
            
            # 预创建所有扇形视图
            self._create_sector_views()
            
            # 隐藏状态标签，显示图形内容
            if hasattr(self, 'status_label'):
                self.status_label.hide()
            
            # 延迟显示初始扇形，等待视图完全初始化
            # 这样可以确保视图大小正确，避免前后缩放不一致
            self._wait_for_stable_size_and_switch()
        else:
            # 没有数据时显示状态标签
            if hasattr(self, 'status_label'):
                self.status_label.setText("没有可显示的孔位数据")
                self.status_label.show()
    
    def _create_sector_views(self):
        """预创建所有扇形区域的图形视图"""
        if not self.sector_graphics_manager:
            return
        
        for sector in SectorQuadrant:
            sector_collection = self.sector_graphics_manager.get_sector_collection(sector)
            if sector_collection and len(sector_collection) > 0:
                # 为该扇形创建独立的图形视图（不显示，仅预备）
                view = OptimizedGraphicsView()
                view.load_holes(sector_collection)
                view.switch_to_macro_view()
                
                self.sector_views[sector] = {
                    'view': view,
                    'collection': sector_collection,
                    'hole_count': len(sector_collection)
                }
    
    def _wait_for_stable_size_and_switch(self):
        """等待视图大小稳定后再切换扇形"""
        self._size_check_count = 0
        self._last_size = None
        
        def check_and_switch():
            # 获取当前视图大小
            view_size = self.graphics_view.viewport().size()
            width = view_size.width()
            height = view_size.height()
            current_size = (width, height)
            
            # 增加检查计数
            self._size_check_count += 1
            
            # 如果视图太小（可能还在初始化），继续等待
            # 但是不要等待太久，最多检查10次（0.5秒）
            # 降低阈值，因为我们的缩放算法已经能处理小视图
            if (width < 300 or height < 200) and self._size_check_count < 10:
                print(f"⏳ 视图尺寸过小 ({width}x{height})，继续等待... (检查 {self._size_check_count}/10)")
                QTimer.singleShot(50, check_and_switch)
            else:
                # 如果大小已经稳定（连续两次相同）或超过最大等待次数
                if current_size == self._last_size or self._size_check_count >= 20:
                    print(f"✅ 视图尺寸稳定 ({width}x{height})，切换到初始扇形")
                    self.switch_to_sector(self.current_sector)
                else:
                    # 大小还在变化，再等一次
                    self._last_size = current_size
                    if self._size_check_count < 30:  # 最多等待1.5秒
                        QTimer.singleShot(50, check_and_switch)
                    else:
                        print(f"⚠️ 达到最大等待次数，使用当前尺寸 ({width}x{height})")
                        self.switch_to_sector(self.current_sector)
        
        # 开始检查
        QTimer.singleShot(50, check_and_switch)
    
    def switch_to_sector(self, sector: SectorQuadrant):
        """切换到指定扇形区域显示"""
        if not self.sector_graphics_manager:
            return
        
        self.current_sector = sector
        
        # 设置标志，防止自动适配干扰扇形居中
        self.graphics_view.disable_auto_fit = True
        
        # 获取扇形数据
        sector_info = self.sector_views.get(sector)
        if not sector_info:
            # self.status_label.setText(f"扇形 {sector.value} 暂无数据")
            return
        
        # 如果graphics_view还没有加载完整的孔位集合，先加载完整数据
        if not hasattr(self.graphics_view, 'hole_items') or not self.graphics_view.hole_items:
            if hasattr(self, 'complete_hole_collection') and self.complete_hole_collection:
                print(f"🔧 首次加载完整孔位集合 ({len(self.complete_hole_collection)} 个孔位)")
                # 确保在加载之前设置标志
                self.graphics_view.disable_auto_fit = True
                self.graphics_view.load_holes(self.complete_hole_collection)
        
        # 显示/隐藏孔位以实现扇形专注显示
        sector_collection = sector_info['collection']
        sector_hole_ids = set(hole.hole_id for hole in sector_collection.holes.values())
        
        # 隐藏所有孔位，只显示当前扇形的孔位
        total_hidden = 0
        total_shown = 0
        for hole_id, hole_item in self.graphics_view.hole_items.items():
            if hole_id in sector_hole_ids:
                hole_item.setVisible(True)
                total_shown += 1
            else:
                hole_item.setVisible(False)
                total_hidden += 1
        
        # 适应视图到当前可见的孔位 - 使用填满策略
        # 注释掉 switch_to_macro_view，它会覆盖我们的设置
        # self.graphics_view.switch_to_macro_view()
        
        # 只更新视图模式，不调用任何自动调整方法
        self.graphics_view.current_view_mode = "macro"
        self.graphics_view.view_mode_changed.emit("macro")
        
        # 直接调用填满策略，不使用延迟
        self._apply_fill_view_strategy()
        
        # 添加调试日志
        print(f"🔄 切换到扇形 {sector.value}: 显示 {total_shown} 个孔位，隐藏 {total_hidden} 个孔位")
        if len(sector_collection) > 0:
            bounds = sector_collection.get_bounds()
            print(f"📏 扇形边界: X=[{bounds[0]:.1f}, {bounds[2]:.1f}], Y=[{bounds[1]:.1f}, {bounds[3]:.1f}]")
        
        # 更新标题和状态（移除，因为已删除标题栏）
        # sector_names = {
        #     SectorQuadrant.SECTOR_1: "区域1 (右上)",
        #     SectorQuadrant.SECTOR_2: "区域2 (左上)", 
        #     SectorQuadrant.SECTOR_3: "区域3 (左下)",
        #     SectorQuadrant.SECTOR_4: "区域4 (右下)"
        # }
        
        # self.title_label.setText(f"当前显示: {sector_names[sector]}")
        # self.status_label.setText(f"显示 {sector_info['hole_count']} 个孔位")
        
        # 发射切换信号
        self.sector_changed.emit(sector)
    
    def update_sector_progress(self, sector: SectorQuadrant, progress: SectorProgress):
        """更新扇形进度（禁用自动切换，由模拟系统控制）"""
        # 注释掉自动切换逻辑，改为由扇形顺序模拟系统控制
        # if progress.completed_holes > 0:
        #     self.switch_to_sector(sector)
        
        # 只更新进度数据，不进行视图切换
        # 使用参数避免未使用变量警告
        _ = sector
        _ = progress
    
    def get_current_sector(self) -> SectorQuadrant:
        """获取当前显示的扇形区域"""
        return self.current_sector
    
    def get_sector_info(self, sector: SectorQuadrant) -> Optional[Dict]:
        """获取指定扇形的信息"""
        return self.sector_views.get(sector)
    
    def _apply_fill_view_strategy(self):
        """应用填满视图策略 - 让扇形的视觉中心与视图中心对齐"""
        if not self.sector_graphics_manager or not self.sector_graphics_manager.center_point:
            # 备用方案：使用边界框方法
            self._apply_bbox_strategy()
            return
            
        # 获取完整数据的中心点
        data_center = self.sector_graphics_manager.center_point
        
        # 获取当前扇形的可见孔位
        visible_items = [item for item in self.graphics_view.hole_items.values() if item.isVisible()]
        
        if not visible_items:
            return
        
        # 计算扇形边界
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        for item in visible_items:
            pos = item.pos()
            rect = item.boundingRect()
            min_x = min(min_x, pos.x() + rect.left())
            min_y = min(min_y, pos.y() + rect.top())
            max_x = max(max_x, pos.x() + rect.right())
            max_y = max(max_y, pos.y() + rect.bottom())
        
        # 计算边界框中心作为视觉中心
        # 对于扇形数据，边界框中心就是最合适的视觉中心
        visual_center_x = (min_x + max_x) / 2
        visual_center_y = (min_y + max_y) / 2
        visual_center = QPointF(visual_center_x, visual_center_y)
        
        
        # 计算扇形内容的尺寸
        content_width = max_x - min_x
        content_height = max_y - min_y
        
        # 获取视图尺寸
        view_rect = self.graphics_view.viewport().rect()
        view_width = view_rect.width()
        view_height = view_rect.height()
        
        # 确保视图大小合理，避免初始化时的小尺寸影响计算
        # 总是使用合理的最小值，确保扇形显示足够大
        min_width = 700
        min_height = 500
        
        if view_width < min_width or view_height < min_height:
            print(f"⚠️ 视图尺寸 ({view_width}x{view_height}) 小于最小值，使用默认值 ({min_width}x{min_height})")
            view_width = max(view_width, min_width)
            view_height = max(view_height, min_height)
        
        print(f"📐 使用视图尺寸: {view_width}x{view_height}")
        
        # 计算基础缩放比例
        scale_x = view_width / content_width if content_width > 0 else 1.0
        scale_y = view_height / content_height if content_height > 0 else 1.0
        base_scale = min(scale_x, scale_y)
        
        # 根据视图大小动态调整缩放
        # 使用sigmoid函数实现平滑过渡
        view_size = min(view_width, view_height)
        
        # 归一化视图大小（假设常见范围是300-1000像素）
        normalized_size = (view_size - 300) / 700
        normalized_size = max(0, min(1, normalized_size))  # 限制在0-1范围
        
        # 使用sigmoid函数计算自适应因子
        # 小视图时边距更大（0.65），大视图时边距更小（0.85）
        import math
        adaptive_margin = 0.65 + 0.2 / (1 + math.exp(-6 * (normalized_size - 0.5)))
        
        # 根据内容密度调整
        # 计算内容填充率（内容面积与视图面积的比例）
        content_area = content_width * content_height
        view_area = view_width * view_height
        fill_ratio = content_area / view_area if view_area > 0 else 1.0
        
        # 内容密度越高，需要的边距越小
        density_factor = 1.0 + 0.25 * (1 - math.exp(-2 * fill_ratio))
        
        # 最终缩放
        scale = base_scale * adaptive_margin * density_factor
        
        # 限制缩放范围
        scale = max(0.1, min(5.0, scale))
        
        print(f"📊 自适应缩放: 视图{view_size:.0f}px, 边距系数{adaptive_margin:.2f}, 密度系数{density_factor:.2f}")
        
        # 重置变换
        self.graphics_view.resetTransform()
        
        # 应用缩放
        self.graphics_view.scale(scale, scale)
        
        # 使用更直接的方法：计算视图应该显示的区域
        view_width = self.graphics_view.viewport().width() / scale
        view_height = self.graphics_view.viewport().height() / scale
        
        # 计算以visual_center为中心的视图矩形
        view_rect = QRectF(
            visual_center_x - view_width / 2,
            visual_center_y - view_height / 2,
            view_width,
            view_height
        )
        
        # 设置场景矩形，这会强制视图显示这个区域
        self.graphics_view.setSceneRect(view_rect)
        
        # 确保视图填满整个视口
        self.graphics_view.fitInView(view_rect, Qt.KeepAspectRatio)
        
        print(f"✅ 扇形已居中显示，缩放: {scale:.2f}x")
        
        # 保护我们的设置不被后续操作覆盖
        # 保存当前设置
        self._sector_view_settings = {
            'scale': scale,
            'scene_rect': view_rect,
            'visual_center': visual_center
        }
        
        # 多次延迟保护，确保设置不被覆盖
        for delay in [10, 50, 100, 200, 500]:
            QTimer.singleShot(delay, self._enforce_sector_settings)
    
    def _enforce_sector_settings(self):
        """强制应用扇形视图设置"""
        if not hasattr(self, '_sector_view_settings'):
            return
            
        settings = self._sector_view_settings
        current_scale = self.graphics_view.transform().m11()
        
        # 如果缩放被改变，恢复设置
        if abs(current_scale - settings['scale']) > 0.01:
            print(f"⚠️ 检测到缩放被改变: {current_scale:.3f} -> {settings['scale']:.3f}，强制恢复")
            
            # 重置并应用保存的设置
            self.graphics_view.resetTransform()
            self.graphics_view.scale(settings['scale'], settings['scale'])
            self.graphics_view.setSceneRect(settings['scene_rect'])
            self.graphics_view.fitInView(settings['scene_rect'], Qt.KeepAspectRatio)
    
    def _apply_bbox_strategy(self):
        """备用策略：使用边界框方法"""
        visible_items = [item for item in self.graphics_view.hole_items.values() if item.isVisible()]
        
        if not visible_items:
            return
            
        # 计算可见孔位的边界
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        for item in visible_items:
            pos = item.pos()
            rect = item.boundingRect()
            min_x = min(min_x, pos.x() + rect.left())
            min_y = min(min_y, pos.y() + rect.top())
            max_x = max(max_x, pos.x() + rect.right())
            max_y = max(max_y, pos.y() + rect.bottom())
        
        # 创建可见内容的边界矩形
        visible_rect = QRectF(min_x, min_y, max_x - min_x, max_y - min_y)
        
        # 添加适当边距
        margin = 20
        target_rect = visible_rect.adjusted(-margin, -margin, margin, margin)
        
        # 使用fitInView让扇形内容填满视图
        self.graphics_view.fitInView(target_rect, Qt.KeepAspectRatio)
        
        print(f"🔍 [备用] 边界框视图调整: ({min_x:.1f}, {min_y:.1f}) - ({max_x:.1f}, {max_y:.1f})")


class CompletePanoramaWidget(QWidget):
    """完整全景图显示组件"""
    
    # 添加信号用于扇形区域点击
    sector_clicked = Signal(SectorQuadrant)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hole_collection: Optional[HoleCollection] = None
        self.center_point: Optional[QPointF] = None
        self.panorama_radius: float = 0.0
        self.sector_highlights: Dict[SectorQuadrant, SectorHighlightItem] = {}
        self.current_highlighted_sector: Optional[SectorQuadrant] = None
        
        # 延迟批量更新机制（保留向后兼容）
        self.pending_status_updates: Dict[str, any] = {}  # hole_id -> status
        self.batch_update_timer = QTimer()
        self.batch_update_timer.timeout.connect(self._apply_batch_updates)
        self.batch_update_timer.setSingleShot(True)
        self.batch_update_interval = 100  # 100毫秒间隔，更快响应
        self.max_batch_delay = 1000  # 最大1秒延迟，防止无限推迟
        self.batch_start_time = 0  # 记录批量更新开始时间
        
        # 数据库驱动的同步机制
        self.panorama_sync_manager = None  # 将在主窗口中设置
        self.db_sync_enabled = True        # 是否启用数据库同步
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 移除标题，直接显示全景图形视图
        # title_label = QLabel("完整孔位全景图")
        # title_label.setAlignment(Qt.AlignCenter)
        # title_label.setFont(QFont("Arial", 12, QFont.Bold))
        # title_label.setStyleSheet("padding: 5px; background-color: #e3f2fd; border-radius: 3px;")
        # layout.addWidget(title_label)
        
        # 全景图形视图 - 固定尺寸确保布局一致性
        self.panorama_view = OptimizedGraphicsView()
        self.panorama_view.setFrameStyle(QFrame.NoFrame)  # 移除边框避免黑框
        self.panorama_view.setFixedSize(350, 350)    # 调整显示面板尺寸适配380px宽度
        
        # 为全景图优化渲染设置 - 需要与主视图不同的设置
        from PySide6.QtWidgets import QGraphicsView
        from PySide6.QtGui import QPainter
        
        # 启用抗锯齿和平滑变换以改善全景图显示质量
        self.panorama_view.setRenderHint(QPainter.Antialiasing, True)
        self.panorama_view.setRenderHint(QPainter.SmoothPixmapTransform, True)
        self.panorama_view.setRenderHint(QPainter.TextAntialiasing, True)
        
        # 使用完整视口更新确保正确渲染
        self.panorama_view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        
        # 禁用缓存模式以确保实时更新
        self.panorama_view.setCacheMode(QGraphicsView.CacheNone)
        
        # 设置优化标志以平衡性能和质量
        self.panorama_view.setOptimizationFlag(QGraphicsView.DontSavePainterState, False)
        self.panorama_view.setOptimizationFlag(QGraphicsView.DontAdjustForAntialiasing, False)
        
        # 隐藏滚动条
        self.panorama_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.panorama_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 设置干净的背景，移除边框
        self.panorama_view.setStyleSheet("background-color: white; border: none;")
        
        # 启用鼠标跟踪以支持点击扇形区域
        self.panorama_view.setMouseTracking(True)
        
        
        # 创建全景图容器以实现完全居中（水平+垂直）
        panorama_container = QWidget()
        panorama_layout = QVBoxLayout(panorama_container)
        panorama_layout.setContentsMargins(0, 0, 0, 0)
        panorama_layout.addStretch()  # 上方弹性空间
        
        # 水平居中布局
        h_container = QWidget()
        h_layout = QHBoxLayout(h_container)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.addStretch()  # 左侧弹性空间
        h_layout.addWidget(self.panorama_view)
        h_layout.addStretch()  # 右侧弹性空间
        
        panorama_layout.addWidget(h_container)
        panorama_layout.addStretch()  # 下方弹性空间
        
        layout.addWidget(panorama_container)
        
        # 信息标签 - 放在全景图下方，增大字体
        self.info_label = QLabel("等待数据加载...")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("""
            QLabel {
                padding: 8px;
                font-size: 14px;
                font-weight: bold;
                color: #333;
                background-color: rgba(248, 249, 250, 200);
                border: 1px solid #ddd;
                border-radius: 6px;
                margin: 5px;
            }
        """)
        layout.addWidget(self.info_label)
    
    def load_complete_view(self, hole_collection: HoleCollection):
        """加载完整的全景图"""
        if hole_collection and len(hole_collection) > 0:
            try:
                print(f"🔄 [全景图] 开始加载 {len(hole_collection)} 个孔位")
                
                # 加载孔位数据到全景视图
                self.panorama_view.load_holes(hole_collection)
                print(f"✅ [全景图] 孔位数据已加载到视图")
                
                # 切换到宏观视图
                self.panorama_view.switch_to_macro_view()
                print(f"🔍 [全景图] 已切换到宏观视图")
                
                # 保存数据引用
                self.hole_collection = hole_collection
                
                # 延迟执行适应视图，确保渲染完成
                from PySide6.QtCore import QTimer
                QTimer.singleShot(50, self._setup_panorama_fitting)
                QTimer.singleShot(100, self._calculate_panorama_geometry)  # 先计算几何信息
                QTimer.singleShot(150, self._fit_panorama_view)
                QTimer.singleShot(200, self._create_sector_highlights)  # 创建扇形高亮
                
                # 更新信息 - 从实际数据中读取孔位数量
                actual_hole_count = len(hole_collection.holes) if hasattr(hole_collection, 'holes') else len(hole_collection)
                self.info_label.setText(f"全景: {actual_hole_count} 个孔位")
                print(f"📊 [全景图] 显示信息已更新: {actual_hole_count} 个孔位")
                
                # 验证场景内容
                scene = self.panorama_view.scene
                if scene:
                    items_count = len(scene.items())
                    scene_rect = scene.sceneRect()
                    print(f"📏 [全景图] 场景信息: {items_count} 个图形项, 边界: {scene_rect}")
                    
                    if items_count == 0:
                        print("⚠️ [全景图] 警告: 场景中没有图形项!")
                    
            except Exception as e:
                print(f"❌ [全景图] 加载失败: {e}")
                import traceback
                traceback.print_exc()
                self.info_label.setText(f"加载失败: {str(e)}")
        else:
            self.info_label.setText("暂无数据")
            print("📭 [全景图] 没有数据可加载")
    
    def _setup_panorama_fitting(self):
        """设置全景图适应前的准备工作"""
        try:
            # 确保场景项目可见性设置正确
            scene = self.panorama_view.scene
            if scene:
                for item in scene.items():
                    item.setVisible(True)
                    item.update()
                
                # 更新场景边界
                scene.setSceneRect(scene.itemsBoundingRect())
                
                print(f"🔧 [全景图] 场景设置完成，项目数: {len(scene.items())}")
            
        except Exception as e:
            print(f"⚠️ [全景图] 场景设置失败: {e}")
    
    def _fit_panorama_view(self):
        """延迟适应全景视图 - 确保内容完美居中显示"""
        try:
            scene = self.panorama_view.scene
            if scene and len(scene.items()) > 0:
                # 获取场景内容边界
                scene_rect = scene.itemsBoundingRect()
                
                # 重置变换矩阵
                self.panorama_view.resetTransform()
                
                # 使用Qt的fitInView来确保完美居中和适应
                view_rect = self.panorama_view.viewport().rect()
                
                # 计算适当的边距
                margin_x = scene_rect.width() * 0.05
                margin_y = scene_rect.height() * 0.05
                
                # 创建带边距的目标区域
                target_rect = QRectF(
                    scene_rect.x() - margin_x,
                    scene_rect.y() - margin_y,
                    scene_rect.width() + 2 * margin_x,
                    scene_rect.height() + 2 * margin_y
                )
                
                # 使用fitInView确保内容居中且适应视图
                self.panorama_view.fitInView(target_rect, Qt.KeepAspectRatio)
                
                # 获取内容的实际中心点
                content_center = scene_rect.center()
                
                # 多次强制居中以确保精确对齐
                from PySide6.QtCore import QTimer
                QTimer.singleShot(10, lambda: self.panorama_view.centerOn(content_center))
                QTimer.singleShot(50, lambda: self.panorama_view.centerOn(content_center))
                QTimer.singleShot(100, lambda: self.panorama_view.centerOn(content_center))
                
                print(f"🎯 [全景图] 使用fitInView居中完成")
                print(f"📍 [全景图] 内容中心: ({content_center.x():.1f}, {content_center.y():.1f})")
                print(f"📐 [全景图] 内容边界: ({scene_rect.x():.1f}, {scene_rect.y():.1f}, {scene_rect.width():.1f}, {scene_rect.height():.1f})")
                print(f"📺 [全景图] 视图尺寸: {view_rect.width()}x{view_rect.height()}")
            else:
                # 备用方案：使用原始适应方法
                self.panorama_view.fit_in_view()
                print("🎯 [全景图] 视图适应完成（备用方案）")
            
            # 强制多次刷新以确保渲染
            for _ in range(3):
                self.panorama_view.viewport().update()
                self.panorama_view.update()
                self.panorama_view.scene.update()
            
            # 额外的渲染强制刷新
            from PySide6.QtCore import QTimer
            QTimer.singleShot(50, lambda: self.panorama_view.viewport().repaint())
            QTimer.singleShot(100, lambda: self.panorama_view.update())
            
            print("🔄 [全景图] 强制渲染刷新完成")
            
        except Exception as e:
            print(f"⚠️ [全景图] 适应视图失败: {e}")
    
    def _calculate_adaptive_scale(self, scene_rect):
        """基于内容尺寸动态计算自适应缩放比例"""
        try:
            # 获取视图的可用空间
            view_rect = self.panorama_view.viewport().rect()
            view_width = view_rect.width()
            view_height = view_rect.height()
            
            # 获取场景内容的尺寸
            scene_width = scene_rect.width()
            scene_height = scene_rect.height()
            
            if scene_width <= 0 or scene_height <= 0:
                return 0.5
            
            # 计算内容与视图的尺寸比例
            width_ratio = scene_width / view_width
            height_ratio = scene_height / view_height
            content_size_ratio = max(width_ratio, height_ratio)
            
            # 使用连续函数动态计算边距因子 (0.8-0.95)
            # 内容越小，边距越大；内容越大，边距越小
            import math
            margin_factor = 0.95 - 0.15 * min(1.0, content_size_ratio / 4.0)
            margin_factor = max(0.8, min(0.95, margin_factor))
            
            # 使用连续函数动态计算最小缩放 (0.05-1.0)
            # 内容越大，最小缩放越小
            min_scale = 1.0 * math.exp(-content_size_ratio * 1.2)
            min_scale = max(0.05, min(1.0, min_scale))
            
            # 使用连续函数动态计算最大缩放 (0.5-2.5)
            # 内容越小，允许的最大缩放越大
            max_scale = 0.5 + 2.0 * math.exp(-content_size_ratio * 0.8)
            max_scale = max(0.5, min(2.5, max_scale))
            
            # 计算两个方向的缩放比例
            scale_x = (view_width * margin_factor) / scene_width
            scale_y = (view_height * margin_factor) / scene_height
            
            # 选择较小的缩放比例以确保内容完全可见
            adaptive_scale = min(scale_x, scale_y)
            
            # 应用缩放范围限制
            adaptive_scale = max(min_scale, min(max_scale, adaptive_scale))
            
            print(f"🔧 [全景图] 动态自适应缩放计算:")
            print(f"  📐 视图尺寸: {view_width}x{view_height}")
            print(f"  📦 场景尺寸: {scene_width:.1f}x{scene_height:.1f}")
            print(f"  📊 尺寸比例: {content_size_ratio:.2f} (宽:{width_ratio:.2f}, 高:{height_ratio:.2f})")
            print(f"  🎯 动态参数: 边距={margin_factor:.2f}, 范围=[{min_scale:.2f}, {max_scale:.2f}]")
            print(f"  📏 计算缩放: X={scale_x:.3f}, Y={scale_y:.3f}")
            print(f"  ✅ 最终缩放: {adaptive_scale:.3f}")
            
            return adaptive_scale
            
        except Exception as e:
            print(f"⚠️ [全景图] 动态自适应缩放计算失败: {e}")
            # 发生错误时返回默认缩放
            return 0.25
    
    def _calculate_panorama_geometry(self):
        """计算全景图的几何信息"""
        if not self.hole_collection:
            return
        
        try:
            # 直接使用数据的几何中心作为扇形中心点
            # 这样可以确保扇形与孔位数据完美对齐
            bounds = self.hole_collection.get_bounds()
            data_center_x = (bounds[0] + bounds[2]) / 2
            data_center_y = (bounds[1] + bounds[3]) / 2
            self.center_point = QPointF(data_center_x, data_center_y)
            
            print(f"🎯 [全景图] 使用数据几何中心作为扇形中心: ({self.center_point.x():.1f}, {self.center_point.y():.1f})")
            print(f"📊 [全景图] 数据边界: X=[{bounds[0]:.1f}, {bounds[2]:.1f}], Y=[{bounds[1]:.1f}, {bounds[3]:.1f}]")
            
            # 计算半径（从中心到最远孔位的距离）
            max_distance = 0
            for hole in self.hole_collection.holes.values():
                dx = hole.center_x - data_center_x
                dy = hole.center_y - data_center_y
                distance = math.sqrt(dx * dx + dy * dy)
                max_distance = max(max_distance, distance)
            
            # 添加一些边距
            self.panorama_radius = max_distance * 1.1
            
            print(f"📏 [全景图] 计算半径: {self.panorama_radius:.1f} (最远距离: {max_distance:.1f})")
            
            # 获取视图信息用于调试
            view_rect = self.panorama_view.viewport().rect()
            print(f"📺 [全景图] 视图尺寸: {view_rect.width()}x{view_rect.height()}")
            
        except Exception as e:
            print(f"❌ [全景图] 几何计算失败: {e}")
            # 备用方案
            if self.hole_collection:
                bounds = self.hole_collection.get_bounds()
                self.center_point = QPointF((bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2)
                self.panorama_radius = 100
            else:
                self.center_point = QPointF(0, 0)
                self.panorama_radius = 100
    
    def _create_sector_highlights(self):
        """创建扇形区域高亮显示"""
        if not self.center_point:
            print("⚠️ [全景图] 无法创建扇形高亮：中心点信息不完整")
            return
        
        try:
            scene = self.panorama_view.scene
            if not scene:
                print("⚠️ [全景图] 无法创建扇形高亮：场景不存在")
                return
            
            print(f"🎯 [全景图] 使用数据中心作为扇形中心: ({self.center_point.x():.1f}, {self.center_point.y():.1f})")
            
            # 安全清除现有的高亮项
            for highlight in list(self.sector_highlights.values()):
                try:
                    if highlight.scene():
                        scene.removeItem(highlight)
                except RuntimeError:
                    pass  # 对象已被删除，忽略错误
            self.sector_highlights.clear()
            
            # 使用之前计算的数据半径
            display_radius = self.panorama_radius
            
            # 为每个扇形创建高亮项
            for sector in SectorQuadrant:
                highlight = SectorHighlightItem(
                    sector=sector,
                    center=self.center_point,
                    radius=display_radius,
                    sector_bounds=None  # 不使用边界框模式
                )
                
                # 使用扇形模式
                highlight.set_highlight_mode("sector")
                
                # 添加到场景
                scene.addItem(highlight)
                self.sector_highlights[sector] = highlight
                
                print(f"🎨 [全景图] 创建扇形高亮: {sector.value}, 中心=({self.center_point.x():.1f}, {self.center_point.y():.1f}), 半径={display_radius:.1f}")
            
            print(f"✅ [全景图] 扇形高亮创建完成，共 {len(self.sector_highlights)} 个扇形")
            
        except Exception as e:
            print(f"❌ [全景图] 扇形高亮创建失败: {e}")
            import traceback
            traceback.print_exc()
    
    
    def highlight_sector(self, sector: SectorQuadrant):
        """高亮显示指定的扇形区域"""
        try:
            # 清除所有高亮
            for s, highlight in self.sector_highlights.items():
                highlight.hide_highlight()
            
            # 高亮指定扇形
            if sector in self.sector_highlights:
                self.sector_highlights[sector].show_highlight()
                self.current_highlighted_sector = sector
                print(f"🎯 [全景图] 高亮扇形: {sector.value}")
            else:
                print(f"⚠️ [全景图] 扇形 {sector.value} 的高亮项不存在")
                
        except Exception as e:
            print(f"❌ [全景图] 扇形高亮失败: {e}")
    
    def clear_highlight(self):
        """清除所有扇形高亮"""
        try:
            # 清除所有高亮
            for highlight in self.sector_highlights.values():
                highlight.hide_highlight()
            self.current_highlighted_sector = None
            print("🧹 [全景图] 已清除所有扇形高亮")
        except Exception as e:
            print(f"❌ [全景图] 清除高亮失败: {e}")
    
    def set_highlight_mode(self, mode: str):
        """设置所有扇形的高亮模式"""
        for highlight_item in self.sector_highlights.values():
            highlight_item.set_highlight_mode(mode)
    
    def _on_panorama_mouse_press(self, event):
        """处理全景图上的鼠标点击事件（已由覆盖层处理）"""
        # 覆盖层会处理扇形点击，这里只需要传递事件给原始处理器
        from PySide6.QtWidgets import QGraphicsView
        QGraphicsView.mousePressEvent(self.panorama_view, event)
    
    def _detect_clicked_sector(self, scene_pos: QPointF) -> Optional[SectorQuadrant]:
        """检测点击位置属于哪个扇形区域"""
        if not self.center_point or not self.hole_collection:
            return None
        
        try:
            # 计算点击位置相对于中心的向量
            dx = scene_pos.x() - self.center_point.x()
            dy = scene_pos.y() - self.center_point.y()
            
            # 计算角度
            angle_rad = math.atan2(dy, dx)
            angle_deg = math.degrees(angle_rad)
            
            # 转换为0-360度范围
            if angle_deg < 0:
                angle_deg += 360
            
            # 使用与主视图SectorManager相同的数学坐标系（不转换）
            # 直接使用数学角度系统，与主视图保持一致
            
            # 数学坐标系中的扇形定义（与SectorManager保持一致）：
            # 区域1：0°-90°（右上）
            # 区域2：90°-180°（左上）
            # 区域3：180°-270°（左下）
            # 区域4：270°-360°（右下）
            if 0 <= angle_deg < 90:
                return SectorQuadrant.SECTOR_1  # 右上
            elif 90 <= angle_deg < 180:
                return SectorQuadrant.SECTOR_2  # 左上
            elif 180 <= angle_deg < 270:
                return SectorQuadrant.SECTOR_3  # 左下
            else:  # 270 <= angle_deg < 360
                return SectorQuadrant.SECTOR_4  # 右下
                
        except Exception as e:
            print(f"❌ [全景图] 扇形检测失败: {e}")
            return None
    
    def update_hole_status(self, hole_id: str, status):
        """更新孔位状态（延迟批量更新版本，带最大延迟保护）"""
        print(f"📦 [全景图] 接收到状态更新: {hole_id} -> {status.value if hasattr(status, 'value') else status}")
        
        # 检查并转换ID格式（兼容DXF的(row,column)格式）
        normalized_hole_id = self._normalize_hole_id(hole_id)
        
        # 将状态更新加入缓存
        self.pending_status_updates[normalized_hole_id] = status
        
        import time
        current_time = time.time() * 1000  # 转换为毫秒
        
        # 检查是否需要强制立即更新（防止无限延迟）
        if self.batch_start_time > 0 and (current_time - self.batch_start_time) >= self.max_batch_delay:
            print(f"⚡ [全景图] 达到最大延迟{self.max_batch_delay}ms，强制立即更新")
            self._apply_batch_updates()
            return
        
        # 智能定时器管理：只有在定时器不活跃时才启动
        if not self.batch_update_timer.isActive():
            print(f"⏰ [全景图] 启动新的批量更新定时器: {self.batch_update_interval}ms")
            self.batch_start_time = current_time
            self.batch_update_timer.start(self.batch_update_interval)
            
            # 验证定时器是否真的启动了
            if self.batch_update_timer.isActive():
                print(f"✅ [全景图] 定时器已激活，{self.batch_update_timer.remainingTime()}ms 后执行")
            else:
                print(f"❌ [全景图] 定时器启动失败!")
        else:
            # 定时器已经活跃，只记录剩余时间，不重启
            remaining = self.batch_update_timer.remainingTime()
            print(f"⏳ [全景图] 定时器已运行，还有{remaining}ms执行，累积{len(self.pending_status_updates)}个更新")
        
        print(f"🔄 [全景图] 缓存中现有 {len(self.pending_status_updates)} 个待更新")
    
    def _apply_batch_updates(self):
        """应用批量状态更新"""
        print(f"🚀 [全景图] *** 批量更新定时器被触发! ***")
        
        if not self.pending_status_updates:
            print(f"⚠️ [全景图] 缓存为空，跳过更新")
            return
        
        update_count = len(self.pending_status_updates)
        print(f"🔄 [全景图] 开始批量更新 {update_count} 个孔位状态")
        
        try:
            # 获取全景视图中的孔位图形项
            if hasattr(self.panorama_view, 'hole_items'):
                hole_items_count = len(self.panorama_view.hole_items) if self.panorama_view.hole_items else 0
                print(f"🔍 [全景图] 全景视图中有 {hole_items_count} 个孔位图形项")
                
                if hole_items_count == 0:
                    print(f"❌ [全景图] hole_items 为空! 检查是否有数据加载到全景视图")
                    # 检查全景视图的其他属性
                    if hasattr(self.panorama_view, 'scene') and self.panorama_view.scene:
                        scene_items = self.panorama_view.scene.items()
                        print(f"🔍 [全景图] 场景中有 {len(scene_items)} 个图形项")
                    else:
                        print(f"❌ [全景图] 全景视图没有场景或场景为空")
                    
                if self.panorama_view.hole_items:
                    updated_count = 0
                    print(f"🔍 [全景图] 正在检查 {len(self.pending_status_updates)} 个待更新孔位")
                
                # 状态颜色映射
                from aidcis2.models.hole_data import HoleStatus
                from PySide6.QtGui import QColor, QBrush, QPen
                
                status_colors = {
                    HoleStatus.PENDING: QColor("#CCCCCC"),       # 灰色
                    HoleStatus.QUALIFIED: QColor("#4CAF50"),     # 绿色
                    HoleStatus.DEFECTIVE: QColor("#F44336"),     # 红色
                    HoleStatus.PROCESSING: QColor("#2196F3"),    # 蓝色
                    HoleStatus.BLIND: QColor("#FF9800"),         # 橙色
                    HoleStatus.TIE_ROD: QColor("#9C27B0"),       # 紫色
                }
                
                # 批量更新所有缓存的状态变化
                for hole_id, status in self.pending_status_updates.items():
                    print(f"🔍 [全景图] 检查孔位 {hole_id}, 状态: {status.value if hasattr(status, 'value') else status}")
                    
                    if hole_id in self.panorama_view.hole_items:
                        hole_item = self.panorama_view.hole_items[hole_id]
                        print(f"✅ [全景图] 找到孔位图形项: {hole_id}, 类型: {type(hole_item)}")
                        
                        # 优先使用update_status方法，如果不存在则直接设置颜色
                        if hasattr(hole_item, 'update_status'):
                            hole_item.update_status(status)
                            hole_item.update()
                            updated_count += 1
                            print(f"✅ [全景图] 孔位 {hole_id} 使用update_status更新成功")
                        elif status in status_colors:
                            color = status_colors[status]
                            print(f"🎨 [全景图] 设置颜色: {color.name()}")
                            
                            if hasattr(hole_item, 'setBrush') and hasattr(hole_item, 'setPen'):
                                hole_item.setBrush(QBrush(color))
                                hole_item.setPen(QPen(color.darker(120), 1.0))
                                hole_item.update()
                                updated_count += 1
                                print(f"✅ [全景图] 孔位 {hole_id} 颜色更新成功")
                            else:
                                print(f"❌ [全景图] 孔位图形项缺少 setBrush/setPen 方法")
                        else:
                            print(f"❌ [全景图] 未知状态: {status}")
                    else:
                        print(f"❌ [全景图] 孔位 {hole_id} 不在 hole_items 中")
                        if self.panorama_view.hole_items:
                            available_holes = list(self.panorama_view.hole_items.keys())[:5]  # 显示前5个可用孔位
                            print(f"🔍 [全景图] 可用孔位示例: {available_holes}")
                
                # 强制刷新视图（一次性）
                self.panorama_view.scene.update()
                self.panorama_view.viewport().update()
                
                # 如果有更新，强制重绘以确保显示
                if updated_count > 0:
                    from PySide6.QtCore import QTimer
                    QTimer.singleShot(10, lambda: self.panorama_view.viewport().repaint())
                
                print(f"✅ [全景图] 批量更新完成: {updated_count}/{update_count} 个孔位")
            else:
                print("❌ [全景图] panorama_view 没有 hole_items 属性!")
                print(f"🔍 [全景图] panorama_view 类型: {type(self.panorama_view)}")
                if hasattr(self.panorama_view, '__dict__'):
                    attrs = list(self.panorama_view.__dict__.keys())[:10]  # 显示前10个属性
                    print(f"🔍 [全景图] panorama_view 属性: {attrs}")
            
        except Exception as e:
            print(f"❌ [全景图] 批量更新失败: {e}")
        finally:
            # 清空缓存并重置计时器
            self.pending_status_updates.clear()
            self.batch_start_time = 0  # 重置批量更新开始时间
            print(f"🧹 [全景图] 批量更新完成，缓存已清空，计时器已重置")
    
    def batch_update_hole_status(self, status_updates: Dict[str, any]):
        """直接批量更新多个孔位状态（兼容旧接口）"""
        print(f"🚀 [全景图] 直接批量更新 {len(status_updates)} 个孔位")
        
        # 合并到待更新缓存
        self.pending_status_updates.update(status_updates)
        
        # 立即应用更新
        self._apply_batch_updates()
    
    def batch_update_from_db(self, updates_list: list):
        """从数据库更新列表批量更新孔位状态（新的数据库驱动接口）"""
        print(f"💾 [全景图] 数据库驱动批量更新 {len(updates_list)} 个孔位")
        
        # 转换数据库更新格式为内部格式
        status_updates = {}
        for update in updates_list:
            hole_id = update['hole_id']
            new_status = update['new_status']
            
            # 转换状态字符串为HoleStatus枚举
            from aidcis2.models.hole_data import HoleStatus
            status_mapping = {
                'pending': HoleStatus.PENDING,
                'qualified': HoleStatus.QUALIFIED,
                'defective': HoleStatus.DEFECTIVE,
                'blind': HoleStatus.BLIND,
                'tie_rod': HoleStatus.TIE_ROD,
                'processing': HoleStatus.PROCESSING
            }
            
            if new_status in status_mapping:
                status_updates[hole_id] = status_mapping[new_status]
                print(f"🔄 [全景图] 转换状态: {hole_id} -> {new_status}")
            else:
                print(f"⚠️ [全景图] 未知状态: {hole_id} -> {new_status}")
        
        if status_updates:
            # 直接应用更新，不经过定时器
            self._apply_status_updates_direct(status_updates)
    
    def _apply_status_updates_direct(self, status_updates: Dict[str, any]):
        """直接应用状态更新，不使用定时器机制"""
        print(f"⚡ [全景图] 直接应用 {len(status_updates)} 个状态更新")
        
        try:
            # 获取全景视图中的孔位图形项
            if not hasattr(self.panorama_view, 'hole_items') or not self.panorama_view.hole_items:
                print("❌ [全景图] panorama_view 没有 hole_items 或为空")
                return
            
            from aidcis2.models.hole_data import HoleStatus
            from PySide6.QtGui import QColor, QBrush, QPen
            
            # 状态颜色映射
            status_colors = {
                HoleStatus.PENDING: QColor("#CCCCCC"),       # 灰色
                HoleStatus.QUALIFIED: QColor("#4CAF50"),     # 绿色
                HoleStatus.DEFECTIVE: QColor("#F44336"),     # 红色
                HoleStatus.PROCESSING: QColor("#2196F3"),    # 蓝色
                HoleStatus.BLIND: QColor("#FF9800"),         # 橙色
                HoleStatus.TIE_ROD: QColor("#9C27B0"),       # 紫色
            }
            
            updated_count = 0
            
            # 批量更新所有状态变化
            for hole_id, status in status_updates.items():
                if hole_id in self.panorama_view.hole_items:
                    hole_item = self.panorama_view.hole_items[hole_id]
                    
                    # 优先使用update_status方法
                    if hasattr(hole_item, 'update_status'):
                        hole_item.update_status(status)
                        hole_item.update()
                        updated_count += 1
                        print(f"✅ [全景图] 孔位 {hole_id} 使用update_status更新成功")
                    elif status in status_colors:
                        color = status_colors[status]
                        
                        if hasattr(hole_item, 'setBrush') and hasattr(hole_item, 'setPen'):
                            hole_item.setBrush(QBrush(color))
                            hole_item.setPen(QPen(color.darker(120), 1.0))
                            hole_item.update()
                            updated_count += 1
                            print(f"✅ [全景图] 孔位 {hole_id} 颜色更新成功")
                        else:
                            print(f"❌ [全景图] 孔位图形项缺少 setBrush/setPen 方法")
                    else:
                        print(f"❌ [全景图] 未知状态: {status}")
                else:
                    print(f"❌ [全景图] 孔位 {hole_id} 不在 hole_items 中")
            
            # 强制刷新视图
            self.panorama_view.scene.update()
            self.panorama_view.viewport().update()
            
            # 延迟重绘确保显示
            if updated_count > 0:
                from PySide6.QtCore import QTimer
                QTimer.singleShot(10, lambda: self.panorama_view.viewport().repaint())
            
            print(f"✅ [全景图] 数据库驱动更新完成: {updated_count}/{len(status_updates)} 个孔位")
            
        except Exception as e:
            print(f"❌ [全景图] 数据库驱动更新失败: {e}")
    
    def set_batch_update_interval(self, interval_ms: int):
        """设置批量更新间隔（毫秒）"""
        self.batch_update_interval = interval_ms
        print(f"⚙️ [全景图] 批量更新间隔设置为: {interval_ms}ms")
    
    def force_immediate_update(self):
        """强制立即应用所有待更新的状态变化"""
        if self.batch_update_timer.isActive():
            self.batch_update_timer.stop()
        if self.pending_status_updates:
            self._apply_batch_updates()
    
    def debug_update_coverage(self):
        """调试方法：检查更新覆盖范围"""
        if not hasattr(self.panorama_view, 'hole_items') or not self.panorama_view.hole_items:
            print("❌ [调试] 没有hole_items")
            return
        
        # 统计各区域的孔位和更新情况
        regions = {
            "右上": {"range": (0, 90), "holes": [], "updated": []},
            "左上": {"range": (90, 180), "holes": [], "updated": []},
            "左下": {"range": (180, 270), "holes": [], "updated": []},
            "右下": {"range": (270, 360), "holes": [], "updated": []},
        }
        
        for hole_id, item in self.panorama_view.hole_items.items():
            # 计算孔位角度
            pos = item.pos()
            if self.center_point:
                dx = pos.x() - self.center_point.x()
                dy = pos.y() - self.center_point.y()
                import math
                angle = math.degrees(math.atan2(dy, dx))
                if angle < 0:
                    angle += 360
                
                # 确定所属区域
                for region_name, region_data in regions.items():
                    min_angle, max_angle = region_data["range"]
                    if min_angle <= angle < max_angle:
                        region_data["holes"].append(hole_id)
                        
                        # 检查是否被更新过（通过颜色判断）
                        if hasattr(item, 'brush'):
                            color = item.brush().color().name()
                            if color != "#CCCCCC":  # 非默认灰色
                                region_data["updated"].append(hole_id)
                        break
        
        # 输出统计信息
        print("\n📊 [调试] 全景图更新覆盖范围:")
        for region_name, data in regions.items():
            total = len(data["holes"])
            updated = len(data["updated"])
            percentage = (updated / total * 100) if total > 0 else 0
            print(f"  {region_name}: {updated}/{total} ({percentage:.1f}%)")
            if updated < total and total > 0:
                not_updated = set(data["holes"]) - set(data["updated"])
                print(f"    未更新: {list(not_updated)[:5]}...")  # 显示前5个
    
    def get_update_status(self):
        """获取当前更新状态（用于状态监控）"""
        import time
        current_time = time.time() * 1000
        
        status = {
            "pending_updates": len(self.pending_status_updates),
            "timer_active": self.batch_update_timer.isActive(),
            "timer_remaining": self.batch_update_timer.remainingTime() if self.batch_update_timer.isActive() else 0,
            "batch_delay": int(current_time - self.batch_start_time) if self.batch_start_time > 0 else 0,
            "max_delay": self.max_batch_delay,
            "update_interval": self.batch_update_interval
        }
        
        return status
    
    def print_update_status(self):
        """打印当前更新状态（调试用）"""
        status = self.get_update_status()
        print(f"📊 [全景图状态] 待更新: {status['pending_updates']}, "
              f"定时器: {'活跃' if status['timer_active'] else '非活跃'}, "
              f"剩余: {status['timer_remaining']}ms, "
              f"延迟: {status['batch_delay']}ms/{status['max_delay']}ms")
    
    def set_panorama_sync_manager(self, sync_manager):
        """设置全景图同步管理器"""
        self.panorama_sync_manager = sync_manager
        print(f"🔗 [全景图] 设置同步管理器: {type(sync_manager)}")
        
        # 连接信号
        if hasattr(sync_manager, 'status_updates_available'):
            sync_manager.status_updates_available.connect(self.batch_update_from_db)
        
    def enable_db_sync(self, enabled: bool = True):
        """启用/禁用数据库同步模式"""
        self.db_sync_enabled = enabled
        print(f"⚙️ [全景图] 数据库同步模式: {'启用' if enabled else '禁用'}")
        
        if self.panorama_sync_manager:
            if enabled:
                self.panorama_sync_manager.start_sync()
            else:
                self.panorama_sync_manager.stop_sync()
    
    def _normalize_hole_id(self, hole_id: str) -> str:
        """
        归一化孔位ID格式，兼容不同的ID格式
        
        支持的格式：
        - "(row,column)" 格式（DXF解析器生成）-> 保持原样，因为全景图也是用这种格式
        - "H001" 格式 -> 保持原样
        - 其他格式 -> 保持原样
        
        Args:
            hole_id: 输入的孔位ID
            
        Returns:
            归一化后的孔位ID
        """
        # 直接返回原始ID，因为全景图的hole_items已经使用了相同的ID格式
        # 日志显示全景图成功找到了(26,27)格式的孔位，说明ID格式是匹配的
        return hole_id
    
    def debug_hole_items_format(self, sample_count=10):
        """调试方法：检查hole_items中的ID格式"""
        if not hasattr(self.panorama_view, 'hole_items') or not self.panorama_view.hole_items:
            print("❌ [调试] panorama_view 没有 hole_items")
            return
        
        print(f"\n🔍 [调试] 全景图 hole_items ID格式示例:")
        hole_ids = list(self.panorama_view.hole_items.keys())[:sample_count]
        for hole_id in hole_ids:
            hole_item = self.panorama_view.hole_items[hole_id]
            print(f"   ID: {hole_id}, 类型: {type(hole_id)}, 孔位对象: {type(hole_item)}")
        
        print(f"   总共有 {len(self.panorama_view.hole_items)} 个孔位")
        
        # 检查是否有特定格式的ID
        tuple_format_count = sum(1 for hid in self.panorama_view.hole_items.keys() if hid.startswith('('))
        h_format_count = sum(1 for hid in self.panorama_view.hole_items.keys() if hid.startswith('H'))
        
        print(f"   元组格式 '(x,y)': {tuple_format_count} 个")
        print(f"   H格式 'H001': {h_format_count} 个")
        print(f"   其他格式: {len(self.panorama_view.hole_items) - tuple_format_count - h_format_count} 个")