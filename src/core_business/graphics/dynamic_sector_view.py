"""
动态扇形区域图形管理器
根据检测进度动态显示对应扇形区域的DXF图形部分
🚨 EMERGENCY FIX VERSION 2025-07-18-17:30 🚨
"""

import math
from typing import Dict, List, Optional, Tuple
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGraphicsItem, QGraphicsPathItem, QGraphicsEllipseItem, QGraphicsView
from PySide6.QtCore import Qt, QPointF, QRectF, Signal, QTimer, QEvent
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QPainterPath, QTransform

from src.core_business.graphics.graphics_view import OptimizedGraphicsView
from src.core_business.graphics.sector_manager import SectorManager, SectorQuadrant, SectorProgress
from src.core_business.models.hole_data import HoleData, HoleCollection


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
            # 连接回中心点以形成完整的扇形
            path.lineTo(self.center)
            path.closeSubpath()
            
            print(f"🎨 [高亮路径] 扇形 {self.sector.value}: 中心({self.center.x():.1f}, {self.center.y():.1f}), 半径={self.radius:.1f}, 角度={start_angle}°-{start_angle+span_angle}°")
            
            # 验证路径是否正确
            if span_angle <= 0 or span_angle >= 360:
                print(f"⚠️ [高亮路径] 扇形 {self.sector.value} 角度异常: span_angle={span_angle}°")
                print(f"⚠️ [高亮路径] 调试信息:")
                print(f"    self.sector = {self.sector}")
                print(f"    self.sector.value = {getattr(self.sector, 'value', 'N/A')}")
                print(f"    start_angle = {start_angle}")
                print(f"    span_angle = {span_angle}")
                print(f"    角度计算来源: _get_sector_angles() = {self._get_sector_angles()}")
                
                # 🔧 FIX: 强制修正异常角度，防止圆形显示
                print(f"🔧 [高亮路径] 强制修正span_angle从{span_angle}°到90°")
                span_angle = 90
                
                # 重新创建路径
                path = QPainterPath()
                path.moveTo(self.center)
                path.arcTo(rect, start_angle, span_angle)
                path.lineTo(self.center)
                path.closeSubpath()
                print(f"✅ [高亮路径] 路径已重新创建，角度={start_angle}°-{start_angle+span_angle}°")
            
            # 扇形样式：淡黄色半透明，适中透明度以显示孔位
            highlight_color = QColor(255, 255, 0, 80)  # 淡黄色，半透明
            border_color = QColor(255, 193, 7, 180)   # 淡黄色边框
            pen = QPen(border_color, 3, Qt.SolidLine)  # 适中的边框宽度
        
        self.setPath(path)
        # 设置填充颜色
        if self.highlight_mode == "sector":
            # 使用淡黄色半透明填充
            self.setBrush(QBrush(highlight_color))
        else:
            self.setBrush(Qt.NoBrush)  # 不填充，完全透明
        self.setPen(pen)
        
        # 设置图层级别（在孔位上方，确保可见）
        self.setZValue(100)  # 设置较高的Z值确保在顶层
        
        # 确保高亮项不会阻挡鼠标事件
        self.setAcceptedMouseButtons(Qt.NoButton)
        self.setAcceptHoverEvents(False)
        
        # 默认隐藏
        self.setVisible(False)
    
    def _get_sector_angles(self) -> Tuple[float, float]:
        """获取扇形的起始角度和跨度角度"""
        # 🔧 FIX: 增加调试信息和错误检查，防止扇形→圆形显示异常
        print(f"🔍 [角度计算] 扇形 {self.sector} 的角度计算")
        
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
        
        # 🔧 FIX: 检查sector值是否有效，防止使用fallback导致的异常
        if self.sector not in angle_map:
            print(f"⚠️ [角度计算] 无效的扇形值: {self.sector}，使用fallback (0, 90)")
            return (0, 90)
        
        start_angle, span_angle = angle_map[self.sector]
        print(f"✅ [角度计算] 扇形 {self.sector.value}: start_angle={start_angle}°, span_angle={span_angle}°")
        
        return (start_angle, span_angle)
    
    def show_highlight(self):
        """显示高亮"""
        self.setVisible(True)
        self.update()
        print(f"🔆 [高亮] 显示扇形 {self.sector.value} 高亮, 可见性: {self.isVisible()}, Z值: {self.zValue()}")
    
    def hide_highlight(self):
        """隐藏高亮"""
        self.setVisible(False)
        self.update()
    
    def set_sector_manager(self, sector_manager):
        """设置扇形管理器以支持自适应角度"""
        self.sector_manager = sector_manager
        
        # 如果是增强型扇形管理器，获取角度配置
        if hasattr(sector_manager, 'sector_angles'):
            self.adaptive_angles = sector_manager.sector_angles
        
        # 重新设置高亮以应用新的角度配置
        self.setup_highlight()
    
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
        
        # 调试：同时计算平均中心点
        sum_x = sum(hole.center_x for hole in self.hole_collection.holes.values())
        sum_y = sum(hole.center_y for hole in self.hole_collection.holes.values())
        count = len(self.hole_collection.holes)
        avg_center_x = sum_x / count if count > 0 else 0
        avg_center_y = sum_y / count if count > 0 else 0
        
        print(f"\n[DEBUG] 中心点计算:")
        print(f"  - 边界框中心（使用中）: ({center_x:.2f}, {center_y:.2f})")
        print(f"  - 平均中心: ({avg_center_x:.2f}, {avg_center_y:.2f})")
        print(f"  - 差异: ({abs(center_x - avg_center_x):.2f}, {abs(center_y - avg_center_y):.2f})")
        print(f"  - 边界: ({bounds[0]:.2f}, {bounds[1]:.2f}) - ({bounds[2]:.2f}, {bounds[3]:.2f})")
        
        return QPointF(center_x, center_y)
    
    def _create_sector_collections(self) -> Dict[SectorQuadrant, HoleCollection]:
        """为每个扇形区域创建独立的孔位集合"""
        print("\n=== [DEBUG] 开始创建扇形集合 ===")
        print(f"总孔位数: {len(self.hole_collection.holes)}")
        print(f"中心点: ({self.center_point.x():.2f}, {self.center_point.y():.2f})")
        
        # 打印前5个孔位的ID格式作为示例
        sample_ids = list(self.hole_collection.holes.keys())[:5]
        print(f"原始孔位ID格式示例: {sample_ids}")
        
        sector_collections = {}
        holes_by_angle = {}  # 用于调试：记录每个孔位的角度
        
        for sector in SectorQuadrant:
            sector_holes = {}
            
            for hole_id, hole in self.hole_collection.holes.items():
                # 计算角度用于调试
                dx = hole.center_x - self.center_point.x()
                dy = hole.center_y - self.center_point.y()
                angle_rad = math.atan2(dy, dx)
                angle_deg = math.degrees(angle_rad)
                if angle_deg < 0:
                    angle_deg += 360
                
                holes_by_angle[hole_id] = angle_deg
                
                if self._is_hole_in_sector(hole, sector):
                    sector_holes[hole_id] = hole
            
            print(f"\n扇形 {sector.value}:")
            print(f"  - 分配了 {len(sector_holes)} 个孔位")
            if sector_holes:
                # 打印该扇形的前3个孔位ID
                sample_sector_ids = list(sector_holes.keys())[:3]
                print(f"  - 孔位ID示例: {sample_sector_ids}")
                # 打印角度范围
                angles = [holes_by_angle[hid] for hid in sector_holes.keys()]
                if angles:
                    print(f"  - 角度范围: {min(angles):.1f}° - {max(angles):.1f}°")
            
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
        
        # 统计未分配的孔位
        all_assigned = sum(len(col.holes) for col in sector_collections.values())
        print(f"\n总计分配: {all_assigned} / {len(self.hole_collection.holes)} 个孔位")
        if all_assigned != len(self.hole_collection.holes):
            print(f"⚠️ 警告: 有 {len(self.hole_collection.holes) - all_assigned} 个孔位未被分配到任何扇形！")
        
        # 现在计算每个扇形的边界并更新metadata
        for sector, collection in sector_collections.items():
            if collection and len(collection) > 0:
                bounds = collection.get_bounds()
                collection.metadata['sector_bounds'] = bounds
        
        print("=== [DEBUG] 扇形集合创建完成 ===\n")
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
        
        # 添加调试信息（只在第一次处理时打印）
        if not hasattr(self, '_debug_printed_angles'):
            self._debug_printed_angles = set()
        
        debug_key = f"{hole.hole_id}_{sector.value}"
        if debug_key not in self._debug_printed_angles and len(self._debug_printed_angles) < 10:
            print(f"[DEBUG] 孔位 {hole.hole_id}: 位置({hole.center_x:.1f}, {hole.center_y:.1f}), 角度={angle_deg:.1f}°, 扇形={sector.value}")
            self._debug_printed_angles.add(debug_key)
        
        # 判断属于哪个扇形
        # 角度范围定义（数学坐标系，逆时针）：
        # SECTOR_1: 0°-90° (右上)
        # SECTOR_2: 90°-180° (左上)
        # SECTOR_3: 180°-270° (左下)
        # SECTOR_4: 270°-360° (右下)
        
        if sector == SectorQuadrant.SECTOR_1:
            # 0°-90°
            return 0 <= angle_deg < 90
        elif sector == SectorQuadrant.SECTOR_2:
            # 90°-180°
            return 90 <= angle_deg < 180
        elif sector == SectorQuadrant.SECTOR_3:
            # 180°-270°
            return 180 <= angle_deg < 270
        elif sector == SectorQuadrant.SECTOR_4:
            # 270°-360°
            return 270 <= angle_deg < 360
        else:
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
    
    def set_sector_manager(self, sector_manager):
        """设置扇形管理器以支持自适应角度"""
        self.sector_manager = sector_manager
        
        # 如果是增强型扇形管理器，获取角度配置
        if hasattr(sector_manager, 'sector_angles'):
            self.adaptive_angles = sector_manager.sector_angles
        
        # 重新创建扇形集合以应用新的角度配置
        self.sector_collections = self._create_sector_collections()
    
    def get_sector_collection(self, sector: SectorQuadrant) -> Optional[HoleCollection]:
        """获取指定扇形区域的孔位集合"""
        return self.sector_collections.get(sector)
    
    def get_all_sector_collections(self) -> Dict[SectorQuadrant, HoleCollection]:
        """获取所有扇形区域的孔位集合"""
        return self.sector_collections.copy()


class DynamicSectorDisplayWidget(QWidget):
    """动态扇形区域显示组件"""
    
    sector_changed = Signal(SectorQuadrant)  # 扇形切换信号
    
    # 默认配置常量（已移除偏移相关配置）
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sector_graphics_manager: Optional[SectorGraphicsManager] = None
        self.complete_hole_collection: Optional[HoleCollection] = None  # 保存完整孔位集合
        self.current_sector = SectorQuadrant.SECTOR_1
        self.sector_views = {}  # 缓存各扇形的图形视图
        
        # 防止重复创建扇形视图的标志
        self._creating_sector_views = False
        
        # 扇形偏移配置已移除
        
        # 小型全景图相关
        # 不再需要 mini_panorama_items，使用 CompletePanoramaWidget 的内部机制
        
        # 响应式缩放控制
        self.disable_responsive_scaling = False  # 是否禁用响应式缩放
        
        self._init_creation_lock()
        self.setup_ui()
    
    def _init_creation_lock(self):
        """初始化扇形创建锁"""
        if not hasattr(self, '_creation_locks'):
            self._creation_locks = {
                'sector_creation': False,
                'view_switching': False,
                'panorama_setup': False
            }
    
    # 偏移配置功能已移至CompletePanoramaWidget
    
    def setup_ui(self):
        """设置用户界面"""
        # 使用无边距的主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 主图形显示区域（占据全部空间）
        self.graphics_view = OptimizedGraphicsView()
        # 设置大小策略为扩展
        from PySide6.QtWidgets import QSizePolicy
        self.graphics_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # 确保主视图可见
        self.graphics_view.show()
        self.graphics_view.setEnabled(True)
        
        # 配置缩放设置以防止过度缩放
        self.graphics_view.max_auto_scale = 1.5  # 设置最大自动缩放比例为1.5
        
        # 设置背景以便调试
        from PySide6.QtGui import QPalette, QColor
        palette = self.graphics_view.palette()
        palette.setColor(QPalette.Base, QColor(250, 250, 250))  # 浅灰色背景
        self.graphics_view.setPalette(palette)
        self.graphics_view.setFrameStyle(QFrame.StyledPanel)
        # 设置最小尺寸确保有足够空间
        # self.graphics_view.setMinimumSize(600, 600)  # 使用自适应
        
        main_layout.addWidget(self.graphics_view)
        
        # 添加状态标签用于显示提示信息（扩展高度）
        # 状态标签（用于无数据时显示）
        self.status_label = QLabel("请选择产品型号或加载DXF文件", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #D3D8E0;
                font-size: 16px;
                background-color: transparent;
            }
        """)
        self.status_label.setVisible(False)  # 初始隐藏，需要时再显示
        
        # 将状态标签放在底层，不要遮挡主视图
        self.status_label.lower()
        
        main_layout.addWidget(self.status_label)
        
        # 创建状态控制按钮栏（已禁用）
        # self.status_control_widget = self._create_status_control_buttons()
        # main_layout.addWidget(self.status_control_widget)
        
        # 创建浮动的小型全景图 - 暂时注释掉
        # print(f"🔍 [DEBUG] 开始创建浮动全景图")
        # self.floating_panorama = self._create_floating_panorama()
        # print(f"🔍 [DEBUG] 浮动全景图创建完成: {self.floating_panorama}")
        # print(f"🔍 [DEBUG] self.mini_panorama 现在存在: {hasattr(self, 'mini_panorama')}")
        
        # 暂时设置为None
        self.floating_panorama = None
        self.mini_panorama = None
    
    def set_appropriate_scale(self):
        """设置适当的缩放比例"""
        if not hasattr(self, 'graphics_view') or not self.graphics_view:
            return
        
        # 获取视图尺寸
        view_size = self.graphics_view.size()
        
        # 如果视图尺寸无效，跳过
        if view_size.width() <= 0 or view_size.height() <= 0:
            return
        
        # 获取场景边界
        scene_rect = self.graphics_view.scene.sceneRect()
        if scene_rect.isEmpty():
            return
        
        # 计算适合的缩放比例
        view_width = view_size.width() - 40  # 留出边距
        view_height = view_size.height() - 40
        
        width_scale = view_width / scene_rect.width()
        height_scale = view_height / scene_rect.height()
        
        # 使用较小的缩放比例，确保完全适配
        scale = min(width_scale, height_scale) * 0.9
        
        # 限制缩放范围
        scale = max(0.1, min(1.5, scale))
        
        # 应用缩放
        self.graphics_view.resetTransform()
        self.graphics_view.scale(scale, scale)
        self.graphics_view.centerOn(scene_rect.center())
        
        print(f"🔧 [缩放设置] 应用缩放比例: {scale:.3f}")
    
    def _create_status_control_buttons(self):
        """创建状态控制按钮栏"""
        from PySide6.QtWidgets import QHBoxLayout, QPushButton, QFrame
        from PySide6.QtCore import Qt
        
        # 创建状态控制容器
        status_frame = QFrame()
        status_frame.setFixedHeight(50)
        status_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(240, 240, 240, 0.9);
                border: 1px solid #404552;
                border-radius: 5px;
                margin: 5px;
            }
        """)
        
        layout = QHBoxLayout(status_frame)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(15)
        
        # 状态按钮定义
        status_buttons = [
            ("待检", "pending", "#999", "灰色"),
            ("合格", "qualified", "#4CAF50", "绿色"),
            ("异常", "defective", "#F44336", "红色"),
            ("盲孔", "blind", "#FF9800", "橙色"),
            ("拉杆孔", "tie_rod", "#8BC34A", "浅绿色"),
            ("检测中", "processing", "#2196F3", "蓝色")
        ]
        
        self.status_buttons = {}
        
        for text, status_key, color, description in status_buttons:
            btn = QPushButton(text)
            btn.setFixedSize(80, 35)
            btn.setCheckable(True)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border: none;
                    border-radius: 5px;
                    font-size: 12px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {color}DD;
                }}
                QPushButton:checked {{
                    background-color: {color};
                    border: 2px solid #333;
                }}
                QPushButton:pressed {{
                    background-color: {color}BB;
                }}
            """)
            
            # 连接点击事件
            btn.clicked.connect(lambda checked, key=status_key: self._on_status_button_clicked(key, checked))
            
            self.status_buttons[status_key] = btn
            layout.addWidget(btn)
        
        # 添加弹簧以右对齐
        layout.addStretch()
        
        # 初始状态：隐藏，直到有数据时才显示
        status_frame.hide()
        
        return status_frame
    
    def _on_status_button_clicked(self, status_key, checked):
        """状态按钮点击事件"""
        try:
            if checked:
                # 取消其他按钮的选中状态
                for key, btn in self.status_buttons.items():
                    if key != status_key:
                        btn.setChecked(False)
                
                # 根据状态过滤显示孔位
                self._filter_holes_by_status(status_key)
                print(f"筛选显示状态为 {status_key} 的孔位")
            else:
                # 如果取消选中，显示所有孔位
                self._show_all_holes()
                print("显示所有孔位")
                
        except Exception as e:
            print(f"状态按钮点击处理失败: {e}")
    
    def _filter_holes_by_status(self, status_key):
        """根据状态过滤显示孔位"""
        # 这里可以添加过滤逻辑
        # 例如：只显示特定状态的孔位，隐藏其他孔位
        pass
    
    def _show_all_holes(self):
        """显示所有孔位"""
        # 这里可以添加显示所有孔位的逻辑
        pass
    
    def _create_floating_panorama(self):
        """创建浮动的全景图窗口"""
        # 创建浮动容器
        floating_container = QWidget(self)
        floating_container.setFixedSize(220, 240)  # 增加高度以容纳标题
        floating_container.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.85);
                border: none;
                border-radius: 8px;
            }
        """)
        
        # 设置浮动窗口的层级和透明度
        floating_container.setWindowFlags(Qt.Widget)
        floating_container.setAttribute(Qt.WA_TranslucentBackground, False)
        floating_container.raise_()
        
        # 在浮动容器中添加标题和全景图
        layout = QVBoxLayout(floating_container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(5)
        
        # 添加标题
        title_label = QLabel("全局预览视图")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #D3D8E0;
                font-size: 12px;
                font-weight: bold;
                background: transparent;
                border: none;
                padding: 3px;
            }
        """)
        layout.addWidget(title_label)
        
        # 创建小型全景图组件
        self.mini_panorama = self._create_mini_panorama()
        print(f"🔍 [DEBUG] mini_panorama 创建后: {self.mini_panorama}")
        print(f"🔍 [DEBUG] mini_panorama 类型: {type(self.mini_panorama)}")
        print(f"🔍 [DEBUG] mini_panorama.panorama_view 存在: {hasattr(self.mini_panorama, 'panorama_view') if self.mini_panorama else False}")
        layout.addWidget(self.mini_panorama)
        
        # 初始定位到左上角
        floating_container.move(10, 10)
        floating_container.show()
        
        return floating_container
    
    def connect_data_signals(self, main_window):
        """连接主窗口的数据更新信号"""
        print(f"🔗 [信号连接] 尝试连接主窗口信号...")
        
        if hasattr(main_window, 'status_updated'):
            main_window.status_updated.connect(self.update_floating_panorama_hole_status)
            print(f"✅ [信号连接] 已连接 status_updated 信号到浮动全景图更新")
        else:
            print(f"⚠️ [信号连接] 主窗口没有 status_updated 信号")
        
        # 也尝试连接其他可能的信号
        if hasattr(main_window, 'hole_status_changed'):
            main_window.hole_status_changed.connect(self.update_floating_panorama_hole_status)
            print(f"✅ [信号连接] 已连接 hole_status_changed 信号")
        
        print(f"🔗 [信号连接] 信号连接完成")
    
    def update_floating_panorama_hole_status(self, hole_id: str, status):
        """更新浮动全景图中的孔位状态（复用左边栏逻辑）"""
        print(f"🎨 [浮动全景图] 接收到状态更新信号: {hole_id} -> {status}")
        
        if hasattr(self, 'mini_panorama') and self.mini_panorama:
            self.update_mini_panorama_hole_status(hole_id, status)
        else:
            # 如果mini_panorama不存在，创建它
            self._create_mini_panorama()
            if hasattr(self, 'mini_panorama') and self.mini_panorama:
                self.update_mini_panorama_hole_status(hole_id, status)
    
    def resizeEvent(self, event):
        """处理窗口大小变化事件，实现响应式设计"""
        super().resizeEvent(event)
        
        # 更新浮动窗口位置
        if hasattr(self, 'floating_panorama') and self.floating_panorama:
            # 保持浮动窗口在左上角
            self.floating_panorama.move(10, 10)
            self.floating_panorama.raise_()
        
        # 实现响应式设计：根据窗口大小调整图表
        if hasattr(self, 'graphics_view') and self.graphics_view and hasattr(self, 'current_sector'):
            self._update_responsive_chart_size()
    
    def _update_responsive_chart_size(self):
        """更新响应式图表大小"""
        try:
            # 如果禁用了响应式缩放，则跳过
            if getattr(self, 'disable_responsive_scaling', False):
                return
                
            # 获取可用的视图尺寸
            view_size = self.graphics_view.size()
            available_width = view_size.width() - 40  # 留出边距
            available_height = view_size.height() - 40
            
            if available_width <= 0 or available_height <= 0:
                return
            
            # 如果有场景边界，基于场景大小计算缩放比例
            if hasattr(self.graphics_view, 'scene') and self.graphics_view.scene:
                scene_rect = self.graphics_view.scene.sceneRect()
                if not scene_rect.isEmpty():
                    # 计算适合的缩放比例
                    width_scale = available_width / scene_rect.width()
                    height_scale = available_height / scene_rect.height()
                    
                    # 使用较小的缩放比例，确保完全适配
                    optimal_scale = min(width_scale, height_scale) * 0.9  # 留10%边距
                    
                    # 限制缩放范围，防止过度缩放
                    optimal_scale = max(0.1, min(2.0, optimal_scale))  # 更严格的限制
                    
                    # 应用新的缩放
                    if hasattr(self, 'current_sector') and self.current_sector:
                        print(f"🔄 [响应式设计] 窗口大小: {available_width}x{available_height}, 最优缩放: {optimal_scale:.2f}")
                        self._apply_responsive_scaling(optimal_scale)
                        
        except Exception as e:
            print(f"❌ [响应式设计] 更新图表大小失败: {e}")
    
    def _apply_responsive_scaling(self, scale: float):
        """应用响应式缩放"""
        try:
            # 更新视图变换，保持居中
            if hasattr(self, 'graphics_view') and self.graphics_view:
                # 获取当前视图中心
                view_center = self.graphics_view.mapToScene(self.graphics_view.viewport().rect().center())
                
                # 重置变换并应用新的缩放
                self.graphics_view.resetTransform()
                self.graphics_view.scale(scale, scale)
                
                # 重新居中视图
                self.graphics_view.centerOn(view_center)
                
                print(f"✅ [响应式设计] 应用缩放: {scale:.2f}")
                
        except Exception as e:
            print(f"❌ [响应式设计] 应用缩放失败: {e}")
    
    def _verify_transform_applied(self, expected_center_x: float, expected_center_y: float):
        """验证变换是否成功应用"""
        try:
            # 获取当前视图中心
            view_center = self.graphics_view.mapToScene(self.graphics_view.viewport().rect().center())
            print(f"🔍 [变换验证] 期望中心: ({expected_center_x}, {expected_center_y})")
            print(f"🔍 [变换验证] 实际中心: ({view_center.x()}, {view_center.y()})")
            
            # 计算偏差
            diff_x = abs(view_center.x() - expected_center_x)
            diff_y = abs(view_center.y() - expected_center_y)
            
            # 偏移验证已移除
            
            # 允许一定的误差范围
            tolerance = 5.0
            
            if diff_x > tolerance or diff_y > tolerance:
                print(f"⚠️ [变换验证] 偏差较大: X偏差={diff_x:.1f}, Y偏差={diff_y:.1f}")
                # 偏移相关验证已移除
                return False
            else:
                print(f"✅ [变换验证] 变换成功应用")
                return True
        except Exception as e:
            print(f"❌ [变换验证] 验证失败: {e}")
            return False
    
    def _reapply_transform_if_needed(self, expected_center_x: float, expected_center_y: float):
        """如果变换被覆盖，重新应用"""
        if not self._verify_transform_applied(expected_center_x, expected_center_y):
            print(f"🔄 [变换修复] 检测到变换被覆盖，重新应用")
            # 重新应用视图设置
            if hasattr(self, '_sector_view_settings'):
                settings = self._sector_view_settings
                self.graphics_view.resetTransform()
                self.graphics_view.scale(settings['scale'], settings['scale'])
                self.graphics_view.centerOn(settings['visual_center'])
            self.graphics_view.viewport().update()
    
    def _create_mini_panorama(self):
        """创建小型全景预览图 - 使用 CompletePanoramaWidget"""
        # 创建一个小尺寸的 CompletePanoramaWidget
        mini_panorama = CompletePanoramaWidget()
        
        # 调整大小以适应浮动窗口
        mini_panorama.setFixedSize(300, 200)
        
        # 调整内部全景视图的大小
        if hasattr(mini_panorama, 'panorama_view'):
            mini_panorama.panorama_view.setFixedSize(280, 150)  # 留出一些边距给标签
        
        # 更新信息标签样式以适应小尺寸
        if hasattr(mini_panorama, 'info_label'):
            mini_panorama.info_label.setStyleSheet("""
                QLabel {
                    padding: 4px;
                    font-size: 11px;
                    font-weight: bold;
                    color: #D3D8E0;
                    background-color: rgba(248, 249, 250, 200);
                    border: 1px solid #404552;
                    border-radius: 4px;
                    margin: 2px;
                }
            """)
        
        # 连接小型全景图的扇形点击信号到当前组件的扇形切换
        mini_panorama.sector_clicked.connect(self.sector_changed.emit)
        print(f"✅ [信号连接] 小型全景图的 sector_clicked 信号已连接到 sector_changed")
        
        # DEBUG: 小型全景图特定调试
        print(f"🔍 [DEBUG] 小型全景图创建完成")
        print(f"🔍 [DEBUG] mini_panorama类型: {type(mini_panorama)}")
        print(f"🔍 [DEBUG] mini_panorama.panorama_view类型: {type(mini_panorama.panorama_view)}")
        print(f"🔍 [DEBUG] panorama_view是否有load_holes: {hasattr(mini_panorama.panorama_view, 'load_holes')}")
        print(f"🔍 [DEBUG] panorama_view是否有scene: {hasattr(mini_panorama.panorama_view, 'scene')}")
        
        return mini_panorama
    
    def _mini_panorama_mouse_press(self, event):
        """小型全景图鼠标点击事件"""
        # 将点击事件委托给主全景图的点击处理逻辑
        if hasattr(self, 'sector_graphics_manager') and self.sector_graphics_manager:
            view_pos = event.position().toPoint() if hasattr(event.position(), 'toPoint') else event.pos()
            scene_pos = self.mini_panorama.mapToScene(view_pos)
            
            # 检测点击的扇形区域
            clicked_sector = self._detect_clicked_sector_mini(scene_pos)
            if clicked_sector:
                print(f"🖱️ [小型全景图] 点击扇形: {clicked_sector.value}")
                self.sector_changed.emit(clicked_sector)
    
    def _detect_clicked_sector_mini(self, scene_pos: QPointF) -> Optional[SectorQuadrant]:
        """检测小型全景图中点击的扇形区域"""
        if not hasattr(self, 'center_point') or not self.center_point:
            return None
        # 计算相对于中心点的位置
        dx = scene_pos.x() - self.center_point.x()
        dy = scene_pos.y() - self.center_point.y()
        
        # 计算距离，用于验证点击是否在圆形区域内
        import math
        distance = math.sqrt(dx * dx + dy * dy)
        
        # 设置有效点击距离范围
        if hasattr(self, 'panorama_radius') and self.panorama_radius > 0:
            max_valid_distance = self.panorama_radius * 1.2
        else:
            max_valid_distance = 200  # 默认值
        
        if distance > max_valid_distance:
            return None
        # 计算角度
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        
        # 转换为0-360度范围
        if angle_deg < 0:
            angle_deg += 360
        
        # 根据角度确定扇形
        if 315 <= angle_deg or angle_deg < 45:
            return SectorQuadrant.SECTOR_1
        elif 45 <= angle_deg < 135:
            return SectorQuadrant.SECTOR_2
        elif 135 <= angle_deg < 225:
            return SectorQuadrant.SECTOR_3
        elif 225 <= angle_deg < 315:
            return SectorQuadrant.SECTOR_4
            return None
    def set_hole_collection(self, hole_collection: HoleCollection, sector_manager=None):
        """设置孔位集合并创建扇形图形管理器"""
        print(f"🚀 [DynamicSectorDisplayWidget] set_hole_collection 被调用")
        print(f"  - 数据量: {len(hole_collection) if hole_collection else 0}")
        print(f"  - 外部扇形管理器: {sector_manager is not None}")
        
        
        try:
            if hole_collection and len(hole_collection) > 0:
                # 保存完整的孔位集合以供扇形切换使用
                self.complete_hole_collection = hole_collection
                
                # 确保小型全景图使用完整数据
                self.mini_panorama_complete_data = hole_collection  # 专门为小型全景图保存的完整数据
                
                # 使用外部扇形管理器或创建内部管理器
                if sector_manager:
                    print(f"🔗 [DynamicSectorDisplayWidget] 使用外部扇形管理器")
                    
                    # 检查扇形管理器是否有数据，如果没有则先加载
                    if hasattr(sector_manager, '_manager') and sector_manager._manager:
                        if not hasattr(sector_manager._manager, 'hole_collection') or not sector_manager._manager.hole_collection:
                            sector_manager.load_hole_collection(hole_collection)
                        elif len(getattr(sector_manager._manager, 'sector_assignments', {})) == 0:
                            sector_manager.load_hole_collection(hole_collection)
                    
                    self.external_sector_manager = sector_manager
                    self.sector_graphics_manager = None  # 不创建内部管理器
                else:
                    print(f"🔧 [DynamicSectorDisplayWidget] 创建内部扇形管理器")
                    self.external_sector_manager = None
                    self.sector_graphics_manager = SectorGraphicsManager(hole_collection)
                    
                    # 如果有增强型扇形管理器，传递给数据管理器以支持自适应角度
                    if hasattr(sector_manager, 'get_enhanced_manager'):
                        enhanced_manager = sector_manager.get_enhanced_manager()
                        if enhanced_manager:
                            self.sector_graphics_manager.set_sector_manager(enhanced_manager)
                            print(f"  - 已连接增强型扇形管理器以支持自适应角度")
                
                # 创建扇形视图缓存
                print(f"📋 [DEBUG] 准备创建扇形视图...")
                self._create_sector_views()
                print(f"📋 [DEBUG] 扇形视图创建完成，sector_views 数量: {len(self.sector_views)}")
                
                # 设置小型全景图数据
                print(f"🔍 [DEBUG] 准备调用 _setup_mini_panorama")
                print(f"🔍 [DEBUG] self.mini_panorama 存在: {hasattr(self, 'mini_panorama')}")
                print(f"🔍 [DEBUG] self.mini_panorama 值: {getattr(self, 'mini_panorama', 'None')}")
                self._setup_mini_panorama(hole_collection)
                print(f"🔍 [DEBUG] _setup_mini_panorama 调用完成")
                
                # 隐藏状态标签
                if hasattr(self, 'status_label'):
                    self.status_label.hide()
                # if hasattr(self, 'status_control_widget'):
                #     self.status_control_widget.show()
                
                # 显示初始扇形
                if hasattr(self, 'graphics_view'):
                    # 设置禁用自动适应，避免显示完整圆形
                    self.graphics_view.disable_auto_fit = True
                    
                    # 改为加载完整集合，然后通过切换扇形来显示
                    print(f"🔧 [初始化] 加载完整孔位集合到视图（禁用自动适应）")
                    self.graphics_view.load_holes(self.complete_hole_collection)
                    
                    # 立即切换到初始扇形
                    print(f"🔧 [初始化] 切换到初始扇形: {self.current_sector.value}")
                    self.switch_to_sector(self.current_sector)
                    
                    # 强制刷新视图
                    try:
                        scene = self.graphics_view.scene() if callable(self.graphics_view.scene) else self.graphics_view.scene
                        if scene:
                            scene.update()
                    except Exception as e:
                        print(f"⚠️ 场景更新失败: {e}")
                    self.graphics_view.viewport().update()
                    
                    # 跳过自动适应，避免显示完整圆形
                    print("🚫 [扇形视图] 跳过自动适应，避免完整圆形显示")
                    
                if hasattr(self, 'graphics_view') and self.graphics_view:
                    self.graphics_view.show()
                    self.graphics_view.update()
                    
                if hasattr(self, 'mini_panorama') and self.mini_panorama:
                    self.mini_panorama.show()
                    self.mini_panorama.update()
                
                if hasattr(self, 'floating_panorama') and self.floating_panorama:
                    self.floating_panorama.show()
                    self.floating_panorama.raise_()
            else:
                # 清空数据
                self.complete_hole_collection = None
                self.mini_panorama_complete_data = None
                self.sector_graphics_manager = None
                
                # 清空视图
                if hasattr(self, 'graphics_view'):
                    self.graphics_view.clear()
                
                # 清空小型全景图
                if hasattr(self, 'mini_panorama') and self.mini_panorama and hasattr(self.mini_panorama, 'scene'):
                    self.mini_panorama.scene.clear()
        except Exception as e:
            print(f"❌ [DynamicSectorDisplayWidget] set_hole_collection 出错: {e}")
            import traceback
            traceback.print_exc()
    
    def _setup_mini_panorama(self, hole_collection: HoleCollection):
        """设置小型全景图数据 - 使用 load_complete_view"""
        # DEBUG: 浮动全景图数据加载调试
        print(f"🚀 [小型全景图] 开始设置，数据量: {len(hole_collection)}")
        
        print(f"🔍 [小型全景图] hasattr(self, 'mini_panorama'): {hasattr(self, 'mini_panorama')}")
        print(f"🔍 [小型全景图] self.mini_panorama: {getattr(self, 'mini_panorama', None)}")
        
        if not hasattr(self, 'mini_panorama') or not self.mini_panorama:
            print(f"❌ [小型全景图] mini_panorama 不存在")
            return
        
        # 检查mini_panorama的属性
        print(f"🔍 [小型全景图] mini_panorama类型: {type(self.mini_panorama)}")
        print(f"🔍 [小型全景图] mini_panorama.info_label: {hasattr(self.mini_panorama, 'info_label')}")
        print(f"🔍 [小型全景图] mini_panorama.panorama_view: {hasattr(self.mini_panorama, 'panorama_view')}")
        
        # 直接使用 CompletePanoramaWidget 的 load_complete_view 方法
        try:
            print(f"🔍 [小型全景图] 调用 load_complete_view 前的信息标签文本: {self.mini_panorama.info_label.text() if hasattr(self.mini_panorama, 'info_label') else 'N/A'}")
            
            self.mini_panorama.load_complete_view(hole_collection)
            print(f"✅ [小型全景图] 已调用 load_complete_view 加载 {len(hole_collection)} 个孔位")
            
            # 检查调用后的状态
            print(f"🔍 [小型全景图] 调用 load_complete_view 后的信息标签文本: {self.mini_panorama.info_label.text() if hasattr(self.mini_panorama, 'info_label') else 'N/A'}")
            print(f"🔍 [小型全景图] 调用后的 hole_collection: {hasattr(self.mini_panorama, 'hole_collection') and self.mini_panorama.hole_collection is not None}")
            
            # 为小型全景图添加点击事件处理
            if hasattr(self.mini_panorama, 'panorama_view'):
                self.mini_panorama.panorama_view.viewport().installEventFilter(self)
                print(f"✅ [小型全景图] 事件过滤器已安装")
                
        except Exception as e:
            print(f"❌ [小型全景图] 加载失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _load_hole_data_from_json(self):
        """从JSON文件加载孔数据"""
        import json
        import os
        
        # 定义可能的JSON文件路径
        json_paths = [
            "/Users/vsiyo/Desktop/AIDCIS/AIDCIS3-LFS/assets/dxf/DXF Graph/dongzhong_hole_grid.json",
            "/Users/vsiyo/Desktop/AIDCIS/AIDCIS3-LFS/src/data/batch_0001_1752418706.json",  # 批处理数据示例
        ]
        
        for json_path in json_paths:
            try:
                if os.path.exists(json_path):
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    print(f"✅ [小型全景图] 成功加载JSON文件: {json_path}")
                    return data
            except Exception as e:
                print(f"⚠️ [小型全景图] 加载JSON文件失败 {json_path}: {e}")
        
        print(f"❌ [小型全景图] 未找到可用的JSON孔数据文件")
        return None
    
    def _setup_mini_panorama_from_json(self, json_data):
        """从JSON数据设置小型全景图"""
        from PySide6.QtWidgets import QGraphicsScene, QGraphicsEllipseItem
        from PySide6.QtGui import QBrush, QColor, QPen
        from PySide6.QtCore import QPointF
        
        # 清空现有的字典
        self.mini_panorama_items.clear()
        
        # 创建场景
        scene = QGraphicsScene()
        self.mini_panorama.setScene(scene)
        
        # 设置背景刷
        self.mini_panorama.setBackgroundBrush(QBrush(QColor(45, 45, 48)))  # 深色背景
        
        # 解析JSON数据格式
        holes_data = []
        if 'holes' in json_data:  # DXF格式
            holes_data = json_data['holes']
            total_holes = json_data.get('total_holes', len(holes_data))
            print(f"📊 [小型全景图] 从DXF JSON加载 {total_holes} 个孔")
        elif isinstance(json_data, dict) and 'holes' in json_data:  # 批处理格式
            holes_data = json_data['holes']
            print(f"📊 [小型全景图] 从批处理JSON加载 {len(holes_data)} 个孔")
        
        if not holes_data:
            print(f"❌ [小型全景图] JSON数据中没有找到孔信息")
            return
        
        # 计算边界
        x_coords = []
        y_coords = []
        
        for hole in holes_data:
            if 'coordinates' in hole:  # DXF格式
                x_coords.append(hole['coordinates']['x_mm'])
                y_coords.append(hole['coordinates']['y_mm'])
            elif 'center_x' in hole:  # 批处理格式
                x_coords.append(hole['center_x'])
                y_coords.append(hole['center_y'])
        
        if not x_coords or not y_coords:
            print(f"❌ [小型全景图] 无法提取坐标信息")
            return
        
        # 计算中心点和边界
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        self.center_point = QPointF(center_x, center_y)
        print(f"🎯 [小型全景图] JSON数据中心: ({center_x:.1f}, {center_y:.1f})")
        
        # 计算缩放比例以适应mini panorama视图
        width = max_x - min_x
        height = max_y - min_y
        view_width = 280  # mini panorama 宽度 - 边距
        view_height = 180  # mini panorama 高度 - 边距
        
        scale_x = view_width / width if width > 0 else 1
        scale_y = view_height / height if height > 0 else 1
        scale = min(scale_x, scale_y) * 0.8  # 留出边距
        
        print(f"📏 [小型全景图] 缩放比例: {scale:.6f}")
        
        # 添加孔到场景
        hole_count = 0
        for hole in holes_data:
            # 提取坐标
            if 'coordinates' in hole:  # DXF格式
                x = hole['coordinates']['x_mm']
                y = hole['coordinates']['y_mm']
                radius = hole.get('radius_mm', 8.865) / 2  # 默认直径转半径
            elif 'center_x' in hole:  # 批处理格式
                x = hole['center_x']
                y = hole['center_y']
                radius = hole.get('radius', 8.865)
            else:
                continue
            
            # 转换到视图坐标系（以中心为原点）
            view_x = (x - center_x) * scale
            view_y = (y - center_y) * scale
            view_radius = max(radius * scale, 1.5)  # 最小显示半径
            
            # 创建孔的图形项
            hole_item = QGraphicsEllipseItem(
                view_x - view_radius,
                view_y - view_radius,
                view_radius * 2,
                view_radius * 2
            )
            
            # 根据孔状态设置颜色
            hole_status = hole.get('status', 'unknown')
            if hole_status == 'qualified':
                color = QColor(85, 170, 85)  # 绿色
            elif hole_status == 'unqualified':
                color = QColor(255, 85, 85)  # 红色
            else:
                color = QColor(170, 170, 170)  # 灰色
            
            hole_item.setBrush(QBrush(color))
            hole_item.setPen(QPen(QColor(255, 255, 255), 0.3))
            hole_item.setVisible(True)
            hole_item.setZValue(1)
            
            # 启用悬停事件和工具提示
            hole_item.setAcceptHoverEvents(True)
            
            # 创建工具提示文本
            tooltip_text = (
                f"孔位置: {hole.get('hole_id', f'hole_{hole_count}')}\n"
                f"坐标: ({hole.get('center_x', 0):.3f}, {hole.get('center_y', 0):.3f})\n"
                f"半径: {hole.get('radius', 0):.3f}\n"
                f"状态: {hole.get('status', 'unknown')}"
            )
            hole_item.setToolTip(tooltip_text)
            
            # 添加到场景
            scene.addItem(hole_item)
            
            # 存储到字典中，使用hole_id作为键
            hole_id = hole.get('hole_id', f"hole_{hole_count}")
            self.mini_panorama_items[hole_id] = hole_item
            
            hole_count += 1
        
        print(f"✅ [小型全景图] 成功渲染 {hole_count} 个孔")
        
        # 设置场景矩形以确保所有内容可见
        scene.setSceneRect(-view_width/2, -view_height/2, view_width, view_height)
        
        # 调整视图以显示所有内容
        from PySide6.QtCore import Qt
        self.mini_panorama.fitInView(scene.sceneRect(), Qt.KeepAspectRatio)
        self.mini_panorama.viewport().update()
    
    def _setup_mini_panorama_from_collection(self, hole_collection: HoleCollection):
        """从HoleCollection设置小型全景图（回退方案）"""
        # 清空现有的字典
        self.mini_panorama_items.clear()
        
        # 创建场景
        from PySide6.QtWidgets import QGraphicsScene
        from PySide6.QtGui import QBrush, QColor, QPen
        from PySide6.QtWidgets import QGraphicsEllipseItem
        
        scene = QGraphicsScene()
        self.mini_panorama.setScene(scene)
        
        # 设置背景刷以确保视图可见
        from PySide6.QtGui import QBrush, QColor
        self.mini_panorama.setBackgroundBrush(QBrush(QColor(245, 245, 245)))
        
        # 计算中心点和边界，向右下偏移
        bounds = hole_collection.get_bounds()
        original_center_x = (bounds[0] + bounds[2]) / 2
        original_center_y = (bounds[1] + bounds[3] ) / 2
        
        # 小型全景图使用真正的中心点（不偏移）以准确显示数据结构
        self.center_point = QPointF(original_center_x, original_center_y)
        
        print(f"🎯 [小型全景图] 使用数据几何中心: ({self.center_point.x():.1f}, {self.center_point.y():.1f})")
        
        # 计算全景图半径，调整尺寸让高亮区域适中
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        self.panorama_radius = max(width, height) / 2 * 1.3  # 调整到1.3，让扇形初始大小更大
        
        # 添加所有孔位到小型全景图
        hole_count = 0
        # 确保正确遍历hole_collection
        if hasattr(hole_collection, 'holes') and isinstance(hole_collection.holes, dict):
            holes_to_add = hole_collection.holes.values()
        else:
            # 如果是可迭代对象，直接使用
            holes_to_add = hole_collection
            
        for hole in holes_to_add:
            # 创建简单的圆形表示
            hole_item = QGraphicsEllipseItem(
                hole.center_x - hole.radius,
                hole.center_y - hole.radius,
                hole.radius * 2,
                hole.radius * 2
            )
            
            # 设置初始颜色（灰色）
            hole_item.setBrush(QBrush(QColor(200, 200, 200)))
            hole_item.setPen(QPen(QColor(150, 150, 150), 0.5))
            
            # 确保项是可见的
            hole_item.setVisible(True)
            
            # 设置 Z 值确保在上层
            hole_item.setZValue(1)
            
            # 确保大小合适（如果孔太小，放大显示）
            min_display_radius = 2.0  # 最小显示半径
            if hole.radius < min_display_radius:
                scale_factor = min_display_radius / hole.radius
                hole_item.setScale(scale_factor)
                print(f"  🔍 [小型全景图] 孔位 {hole.hole_id} 太小，放大 {scale_factor:.1f} 倍")
            
            # 启用悬停事件和工具提示
            hole_item.setAcceptHoverEvents(True)
            
            # 创建工具提示文本
            tooltip_text = (
                f"孔位置: {hole.hole_id}\n"
                f"坐标: ({hole.center_x:.3f}, {hole.center_y:.3f})\n"
                f"半径: {hole.radius:.3f}\n"
                f"状态: {hole.status.value if hasattr(hole.status, 'value') else str(hole.status)}"
            )
            hole_item.setToolTip(tooltip_text)
            
            # 设置hole_id作为data以便更新时查找
            hole_item.setData(0, hole.hole_id)
            
            # 保存到字典中便于快速查找
            self.mini_panorama_items[hole.hole_id] = hole_item
            
            scene.addItem(hole_item)
            hole_count += 1
        
        print(f"🎨 [小型全景图] 已创建 {hole_count} 个孔位图形项")
        print(f"📦 [小型全景图] 保存了 {len(self.mini_panorama_items)} 个项到查找字典")
        
        # 设置场景边界
        from PySide6.QtCore import QRectF
        margin = 50
        scene_rect = QRectF(
            bounds[0] - margin, bounds[1] - margin,
            bounds[2] - bounds[0] + 2 * margin,
            bounds[3] - bounds[1] + 2 * margin
        )
        scene.setSceneRect(scene_rect)
        
        # 适应视图
        # 计算适合的缩放
        view_rect = self.mini_panorama.viewport().rect()
        scale_x = view_rect.width() / scene_rect.width()
        scale_y = view_rect.height() / scene_rect.height()
        scale = min(scale_x, scale_y) * 0.9  # 留10%边距
        
        # 重置变换并应用缩放
        self.mini_panorama.resetTransform()
        self.mini_panorama.scale(scale, scale)
        
        # 居中显示
        self.mini_panorama.centerOn(scene_rect.center())
        
        # 强制刷新场景
        scene.update()
        self.mini_panorama.viewport().update()
        self.mini_panorama.repaint()
        
        # 验证孔位数量
        item_count = len(scene.items())
        print(f"🔢 [小型全景图] 场景中的图形项数: {item_count}")
        
        print(f"✅ [小型全景图] 回退方案渲染完成")
        self.mini_panorama.show()
        
        print(f"📐 [小型全景图] 场景矩形: ({scene_rect.x():.1f}, {scene_rect.y():.1f}, {scene_rect.width():.1f}, {scene_rect.height():.1f})")
        print(f"📐 [小型全景图] 视图已适配")
    
    def _initialize_mini_panorama_data(self, hole_collection):
        """初始化小型全景图的数据"""
        print(f"🔄 [小型全景图] 初始化数据，共 {len(hole_collection)} 个孔位")
        
        if not self.mini_panorama:
            print(f"❌ [小型全景图] mini_panorama 不存在")
            return
            
        # 确保有场景
        if not hasattr(self.mini_panorama, 'scene') or not self.mini_panorama.scene:
            from PySide6.QtWidgets import QGraphicsScene
            scene = QGraphicsScene()
            self.mini_panorama.setScene(scene)
        
        # 设置背景刷以确保视图可见
        from PySide6.QtGui import QBrush, QColor
        self.mini_panorama.setBackgroundBrush(QBrush(QColor(245, 245, 245)))
        print(f"✅ [小型全景图] 创建新场景")
        
        scene = self.mini_panorama.scene
        
        # 清空现有内容
        scene.clear()
        
        # 创建字典存储所有孔位项，便于后续快速查找
        self.mini_panorama_items = {}
        
        # 创建所有孔位的图形项
        from PySide6.QtWidgets import QGraphicsEllipseItem
        from PySide6.QtGui import QBrush, QPen, QColor
        
        hole_count = 0
        # 确保正确遍历hole_collection
        if hasattr(hole_collection, 'holes') and isinstance(hole_collection.holes, dict):
            holes_to_add = hole_collection.holes.values()
        else:
            holes_to_add = hole_collection
            
        for hole in holes_to_add:
            # 创建简单的圆形表示
            hole_item = QGraphicsEllipseItem(
                hole.center_x - hole.radius,
                hole.center_y - hole.radius,
                hole.radius * 2,
                hole.radius * 2
            )
            
            # 设置初始颜色（灰色）
            hole_item.setBrush(QBrush(QColor(200, 200, 200)))
            hole_item.setPen(QPen(QColor(150, 150, 150), 0.5))
            
            # 确保项是可见的
            hole_item.setVisible(True)
            
            # 设置 Z 值确保在上层
            hole_item.setZValue(1)
            
            # 确保大小合适（如果孔太小，放大显示）
            min_display_radius = 2.0  # 最小显示半径
            if hole.radius < min_display_radius:
                scale_factor = min_display_radius / hole.radius
                hole_item.setScale(scale_factor)
                print(f"  🔍 [小型全景图] 孔位 {hole.hole_id} 太小，放大 {scale_factor:.1f} 倍")
            
            # 启用悬停事件和工具提示
            hole_item.setAcceptHoverEvents(True)
            
            # 创建工具提示文本
            tooltip_text = (
                f"孔位置: {hole.hole_id}\n"
                f"坐标: ({hole.center_x:.3f}, {hole.center_y:.3f})\n"
                f"半径: {hole.radius:.3f}\n"
                f"状态: {hole.status.value if hasattr(hole.status, 'value') else str(hole.status)}"
            )
            hole_item.setToolTip(tooltip_text)
            
            # 设置hole_id作为data以便更新时查找
            hole_item.setData(0, hole.hole_id)
            
            # 保存到字典中便于快速查找
            self.mini_panorama_items[hole.hole_id] = hole_item
            
            scene.addItem(hole_item)
            hole_count += 1
        
        print(f"🎨 [小型全景图] 已创建 {hole_count} 个孔位图形项")
        print(f"📦 [小型全景图] 保存了 {len(self.mini_panorama_items)} 个项到查找字典")
        
        # 设置场景边界
        bounds = hole_collection.get_bounds()
        margin = 50
        scene_rect = QRectF(
            bounds[0] - margin, bounds[1] - margin,
            bounds[2] - bounds[0] + 2 * margin,
            bounds[3] - bounds[1] + 2 * margin
        )
        scene.setSceneRect(scene_rect)
        
        
        # 适应视图
        # 计算适合的缩放
        view_rect = self.mini_panorama.viewport().rect()
        scale_x = view_rect.width() / scene_rect.width()
        scale_y = view_rect.height() / scene_rect.height()
        scale = min(scale_x, scale_y) * 0.9  # 留10%边距
        
        # 重置变换并应用缩放
        self.mini_panorama.resetTransform()
        self.mini_panorama.scale(scale, scale)
        
        # 居中显示
        self.mini_panorama.centerOn(scene_rect.center())
        
        # 强制刷新场景
        scene.update()
        self.mini_panorama.viewport().update()
        self.mini_panorama.repaint()
        
        # 验证孔位数量
        item_count = len(scene.items())
        print(f"🔢 [小型全景图] 场景中的图形项数: {item_count}")
        
        # 确保场景内容可见
        self.mini_panorama.show()
        
        print(f"📐 [小型全景图] 场景矩形: ({scene_rect.x():.1f}, {scene_rect.y():.1f}, {scene_rect.width():.1f}, {scene_rect.height():.1f})")
        print(f"📐 [小型全景图] 视图已适配")
    
    # 强制偏移方法已移除
    # 偏移测试方法已移除
    # 滚动条偏移方法已移除
    def debug_mini_panorama_state(self):
        """调试小型全景图状态"""
        if not hasattr(self, 'mini_panorama'):
            print("❌ [调试] 没有 mini_panorama 属性")
            return
            
        print("=" * 60)
        print("🔍 小型全景图状态调试:")
        print(f"  类型: {type(self.mini_panorama)}")
        print(f"  是否可见: {self.mini_panorama.isVisible()}")
        
        if hasattr(self.mini_panorama, 'scene'):
            scene = self.mini_panorama.scene
            if scene:
                items = scene.items()
                print(f"  场景项数量: {len(items)}")
                
                # 统计不同颜色的项
                color_stats = {}
                for item in items[:100]:  # 只检查前100个避免太慢
                    if hasattr(item, 'brush'):
                        brush = item.brush()
                        color = brush.color()
                        color_key = f"({color.red()}, {color.green()}, {color.blue()})"
                        color_stats[color_key] = color_stats.get(color_key, 0) + 1
                
                print(f"  颜色统计 (前100项):")
                for color, count in color_stats.items():
                    print(f"    {color}: {count} 个")
                    
                # 检查视口设置
                if hasattr(self.mini_panorama, 'viewport'):
                    viewport = self.mini_panorama.viewport()
                    print(f"  视口大小: {viewport.width()}x{viewport.height()}")
                    print(f"  视口更新模式: {self.mini_panorama.viewportUpdateMode()}")
                    
        print("=" * 60)
    def force_mini_panorama_refresh(self):
        """强制刷新小型全景图"""
        if hasattr(self, 'mini_panorama') and self.mini_panorama:
            # 方法1：重置视口
            if hasattr(self.mini_panorama, 'viewport'):
                self.mini_panorama.viewport().update()
                
            # 方法2：触发重绘事件
            from PySide6.QtCore import QEvent
            from PySide6.QtGui import QPaintEvent
            event = QPaintEvent(self.mini_panorama.rect())
            self.mini_panorama.event(event)
            
            # 方法3：重置变换
            transform = self.mini_panorama.transform()
            self.mini_panorama.resetTransform()
            self.mini_panorama.setTransform(transform)
            
            print("🔄 [小型全景图] 已执行强制刷新")
    def test_mini_panorama_update(self):
        """测试小型全景图更新（手动调用）"""
        if not hasattr(self, 'mini_panorama') or not self.mini_panorama:
            print("❌ [测试] 小型全景图不存在")
            return
            
        print("🧪 [测试] 开始测试小型全景图更新...")
        
        # 获取场景
        scene = self.mini_panorama.scene
        if not scene:
            print("❌ [测试] 场景不存在")
            return
            
        items = scene.items()
        print(f"📊 [测试] 场景中有 {len(items)} 个项")
        
        # 测试更新前10个项为绿色
        from PySide6.QtGui import QBrush, QPen, QColor
        green_color = QColor(76, 175, 80)
        
        updated_count = 0
        for i, item in enumerate(items[:10]):
            if hasattr(item, 'setBrush'):
                item.setBrush(QBrush(green_color))
                item.setPen(QPen(green_color.darker(120), 0.5))
                item.update()
                updated_count += 1
                
                # 获取位置信息
                pos = item.pos()
                print(f"  ✅ [测试] 更新了项 {i}: 位置 ({pos.x():.1f}, {pos.y():.1f})")
        
        # 强制刷新
        scene.update()
        self.mini_panorama.update()
        self.mini_panorama.viewport().update()
        self.mini_panorama.viewport().repaint()
        
        print(f"🎨 [测试] 已将 {updated_count} 个项设置为绿色")
        print("🔄 [测试] 已执行所有刷新命令")
        print("👀 [测试] 请检查小型全景图是否显示绿色点")
    def test_mini_panorama_update(self):
        """测试小型全景图更新（手动调用）"""
        if not hasattr(self, 'mini_panorama') or not self.mini_panorama:
            print("❌ [测试] 小型全景图不存在")
            return
            
        print("🧪 [测试] 开始测试小型全景图更新...")
        
        # 获取场景
        scene = self.mini_panorama.scene
        if not scene:
            print("❌ [测试] 场景不存在")
            return
            
        items = scene.items()
        print(f"📊 [测试] 场景中有 {len(items)} 个项")
        
        # 测试更新前10个项为绿色
        from PySide6.QtGui import QBrush, QPen, QColor
        green_color = QColor(76, 175, 80)
        
        updated_count = 0
        for i, item in enumerate(items[:10]):
            if hasattr(item, 'setBrush'):
                item.setBrush(QBrush(green_color))
                item.setPen(QPen(green_color.darker(120), 0.5))
                item.update()
                updated_count += 1
                
                # 获取位置信息
                pos = item.pos()
                print(f"  ✅ [测试] 更新了项 {i}: 位置 ({pos.x():.1f}, {pos.y():.1f})")
        
        # 强制刷新
        scene.update()
        self.mini_panorama.update()
        self.mini_panorama.viewport().update()
        self.mini_panorama.viewport().repaint()
        
        print(f"🎨 [测试] 已将 {updated_count} 个项设置为绿色")
        print("🔄 [测试] 已执行所有刷新命令")
        print("👀 [测试] 请检查小型全景图是否显示绿色点")
    def debug_mini_panorama_state(self):
        """调试小型全景图状态"""
        if not hasattr(self, 'mini_panorama'):
            print("❌ [调试] 没有 mini_panorama 属性")
            return
            
        print("=" * 60)
        print("🔍 小型全景图状态调试:")
        print(f"  类型: {type(self.mini_panorama)}")
        print(f"  是否可见: {self.mini_panorama.isVisible()}")
        
        if hasattr(self.mini_panorama, 'scene'):
            scene = self.mini_panorama.scene
            if scene:
                items = scene.items()
                print(f"  场景项数量: {len(items)}")
                
                # 统计不同颜色的项
                color_stats = {}
                for item in items[:100]:  # 只检查前100个避免太慢
                    if hasattr(item, 'brush'):
                        brush = item.brush()
                        color = brush.color()
                        color_key = f"({color.red()}, {color.green()}, {color.blue()})"
                        color_stats[color_key] = color_stats.get(color_key, 0) + 1
                
                print(f"  颜色统计 (前100项):")
                for color, count in color_stats.items():
                    print(f"    {color}: {count} 个")
                    
                # 检查视口设置
                if hasattr(self.mini_panorama, 'viewport'):
                    viewport = self.mini_panorama.viewport()
                    print(f"  视口大小: {viewport.width()}x{viewport.height()}")
                    print(f"  视口更新模式: {self.mini_panorama.viewportUpdateMode()}")
                    
        print("=" * 60)
    def force_mini_panorama_refresh(self):
        """强制刷新小型全景图"""
        if hasattr(self, 'mini_panorama') and self.mini_panorama:
            # 方法1：重置视口
            if hasattr(self.mini_panorama, 'viewport'):
                self.mini_panorama.viewport().update()
                
            # 方法2：触发重绘事件
            from PySide6.QtCore import QEvent
            from PySide6.QtGui import QPaintEvent
            event = QPaintEvent(self.mini_panorama.rect())
            self.mini_panorama.event(event)
            
            # 方法3：重置变换
            transform = self.mini_panorama.transform()
            self.mini_panorama.resetTransform()
            self.mini_panorama.setTransform(transform)
            
            print("🔄 [小型全景图] 已执行强制刷新")
    def verify_mini_panorama_items_visibility(self):
        """验证小型全景图中项的可见性"""
        if not hasattr(self, 'mini_panorama') or not self.mini_panorama:
            print("❌ [验证] 小型全景图不存在")
            return
            
        scene = self.mini_panorama.scene
        if not scene:
            print("❌ [验证] 场景不存在")
            return
            
        items = scene.items()
        print(f"🔍 [验证] 检查 {len(items)} 个项的可见性...")
        
        visible_count = 0
        invisible_count = 0
        out_of_bounds_count = 0
        
        scene_rect = scene.sceneRect()
        
        for item in items[:100]:  # 检查前100个
            if hasattr(item, 'isVisible'):
                if item.isVisible():
                    visible_count += 1
                    
                    # 检查是否在场景范围内
                    item_rect = item.sceneBoundingRect()
                    if not scene_rect.contains(item_rect):
                        out_of_bounds_count += 1
                        print(f"  ⚠️ 项在场景范围外: {item_rect}")
                else:
                    invisible_count += 1
        
        print(f"  ✅ 可见项: {visible_count}")
        print(f"  ❌ 不可见项: {invisible_count}")
        print(f"  ⚠️ 超出范围项: {out_of_bounds_count}")
        
        # 检查视口变换
        transform = self.mini_panorama.transform()
        print(f"  🔄 视口变换: 缩放({transform.m11():.2f}, {transform.m22():.2f})")
        
        # 检查视口大小
        viewport_rect = self.mini_panorama.viewport().rect()
        print(f"  📐 视口大小: {viewport_rect.width()}x{viewport_rect.height()}")
    
    def trigger_mini_panorama_paint(self):
        """触发小型全景图的绘制事件"""
        if not hasattr(self, 'mini_panorama') or not self.mini_panorama:
            return
            
        try:
            # 方法1：使用 QApplication 处理事件
            from PySide6.QtWidgets import QApplication
            QApplication.processEvents()
            
            # 方法2：触发 paintEvent
            self.mini_panorama.update()
            self.mini_panorama.repaint()
            
            # 方法3：如果有场景，更新场景
            if hasattr(self.mini_panorama, 'scene') and self.mini_panorama.scene:
                self.mini_panorama.scene.update()
                
                # 获取所有项并强制更新
                items = self.mini_panorama.scene.items()
                update_count = 0
                for item in items[:50]:  # 更新前50个作为测试
                    if hasattr(item, 'update'):
                        item.update()
                        update_count += 1
                
                print(f"🎨 [小型全景图] 触发了 {update_count} 个项的更新")
            
            print("🔄 [小型全景图] 已触发绘制事件")
            
        except Exception as e:
            print(f"❌ [小型全景图] 触发绘制事件失败: {e}")

    def _create_sector_views(self):
        """预创建所有扇形区域的图形视图"""
        # 防止重复创建
        if self._creating_sector_views:
            print("⚠️ [防重复] 扇形视图创建已在进行中，跳过重复调用")
            return
        
        self._creating_sector_views = True
        print("\n=== [DEBUG] 开始创建扇形视图 ===")
        
        # 选择使用的扇形管理器
        active_manager = None
        if self.external_sector_manager:
            active_manager = self.external_sector_manager
            print("🔗 使用外部扇形管理器 (SectorManagerAdapter)")
    
    
            
            # 验证外部扇形管理器是否有数据
            
            if hasattr(active_manager, '_manager') and active_manager._manager:
                
                has_hole_collection = hasattr(active_manager._manager, 'hole_collection') and active_manager._manager.hole_collection
                
                if has_hole_collection:
                    sector_assignments_count = len(getattr(active_manager._manager, 'sector_assignments', {}))
                
                
                # 检查是否需要重新加载数据
                needs_reload = False
                if not has_hole_collection:
                    print("⚠️ [紧急修复] 外部扇形管理器没有hole_collection，立即重新加载...")
                    needs_reload = True
                elif sector_assignments_count == 0:
                    print("⚠️ [紧急修复] 外部扇形管理器sector_assignments为空，立即重新加载...")
                    needs_reload = True
                
                if needs_reload:
                    # 首先尝试使用 complete_hole_collection
                    recovery_data = None
                    if hasattr(self, 'complete_hole_collection') and self.complete_hole_collection:
                        recovery_data = self.complete_hole_collection
                        print(f"🔧 [紧急修复] 使用 complete_hole_collection，孔位数: {len(recovery_data.holes)}")
                    
                    # 如果 complete_hole_collection 不可用，尝试从其他地方获取数据
                    elif hasattr(self, 'mini_panorama_complete_data') and self.mini_panorama_complete_data:
                        recovery_data = self.mini_panorama_complete_data
                        print(f"🔧 [紧急修复] 使用 mini_panorama_complete_data，孔位数: {len(recovery_data.holes)}")
                    
                    # 最后尝试从主窗口获取数据（通过parent链）
                    elif hasattr(self, 'parent') and self.parent():
                        try:
                            parent_window = self.parent()
                            while parent_window and not hasattr(parent_window, 'hole_collection'):
                                parent_window = parent_window.parent()
                            
                            if parent_window and hasattr(parent_window, 'hole_collection') and parent_window.hole_collection:
                                recovery_data = parent_window.hole_collection
                                print(f"🔧 [紧急修复] 从主窗口获取数据，孔位数: {len(recovery_data.holes)}")
                                # 同时更新本地缓存
                                self.complete_hole_collection = recovery_data
                        except Exception as e:
                            print(f"⚠️ [紧急修复] 从主窗口获取数据失败: {e}")
                    
                    # 执行数据恢复
                    if recovery_data:
                        print(f"🔧 [紧急修复] 执行数据重新加载...")
                        active_manager.load_hole_collection(recovery_data)
                        print(f"🔧 [紧急修复] 重新加载完成，验证结果...")
                        # 验证重新加载结果
                        new_assignments_count = len(getattr(active_manager._manager, 'sector_assignments', {}))
                        print(f"✅ [紧急修复] 重新加载后 sector_assignments 数量: {new_assignments_count}")
                        
                        # 如果修复仍然失败，这是一个致命错误
                        if new_assignments_count == 0:
                            print(f"🚨 [致命错误] 数据修复失败！这是一个严重的安全问题！")
                            print(f"🚨 [致命错误] 请立即停止操作并检查系统状态！")
                            return  # 立即停止，防止错误的检测结果
                    else:
                        print(f"🚨 [致命错误] 所有数据源都不可用，无法修复!")
                        print(f"🚨 [致命错误] complete_hole_collection: {getattr(self, 'complete_hole_collection', 'MISSING')}")
                        print(f"🚨 [致命错误] mini_panorama_complete_data: {getattr(self, 'mini_panorama_complete_data', 'MISSING')}")
                        print(f"🚨 [致命错误] 无法继续创建扇形视图，这可能导致安全问题！")
                        return  # 立即停止，防止创建无效的视图
            else:
                print(f"❌ [关键诊断] active_manager没有_manager属性或_manager为空")
                print(f"❌ [关键诊断] hasattr(_manager): {hasattr(active_manager, '_manager')}")
                if hasattr(active_manager, '_manager'):
                    print(f"❌ [关键诊断] _manager值: {active_manager._manager}")
                        
        elif self.sector_graphics_manager:
            active_manager = self.sector_graphics_manager
            print("🔧 使用内部扇形管理器 (SectorGraphicsManager)")
        else:
            print("❌ 没有可用的扇形管理器!")
            return
        
        print("扇形管理器中的扇形集合：")
        try:
            print(f"🔍 active_manager 类型: {type(active_manager)}")
            
            # 根据管理器类型使用不同的方法获取扇形数据
            if hasattr(active_manager, 'get_all_sector_collections'):
                # SectorGraphicsManager
                print(f"🔍 sector_collections 存在: {hasattr(active_manager, 'sector_collections')}")
                if hasattr(active_manager, 'sector_collections'):
                    print(f"🔍 sector_collections 内容: {list(active_manager.sector_collections.keys())}")
                
                all_collections = active_manager.get_all_sector_collections()
                print(f"🔍 get_all_sector_collections 返回: {type(all_collections)}, 长度: {len(all_collections)}")
                
                for sector, collection in all_collections.items():
                    print(f"  - {sector.value}: {len(collection.holes) if collection and hasattr(collection, 'holes') else 'N/A'} 个孔位")
                    if collection and hasattr(collection, 'holes') and len(collection.holes) > 0:
                        # 显示前3个孔位ID
                        sample_ids = list(collection.holes.keys())[:3]
                        print(f"    样本孔位ID: {sample_ids}")
            
            elif hasattr(active_manager, 'get_sector_holes'):
                # SectorManagerAdapter
                print("🔗 使用SectorManagerAdapter接口")
                
                sectors = [SectorQuadrant.SECTOR_1, SectorQuadrant.SECTOR_2, SectorQuadrant.SECTOR_3, SectorQuadrant.SECTOR_4]
                all_collections = {}
                
                for sector in sectors:
                    sector_holes = active_manager.get_sector_holes(sector)
                    print(f"  - {sector.value}: {len(sector_holes)} 个孔位")
                    
                    if sector_holes:
                        # 显示前3个孔位ID
                        sample_ids = [hole.hole_id for hole in sector_holes[:3]]
                        print(f"    样本孔位ID: {sample_ids}")
                        
                        # 创建HoleCollection用于后续处理
                        from src.core_business.models.hole_data import HoleCollection
                        sector_hole_dict = {hole.hole_id: hole for hole in sector_holes}
                        sector_collection = HoleCollection(
                            holes=sector_hole_dict,
                            metadata={'sector': sector, 'total_holes': len(sector_holes)}
                        )
                        all_collections[sector] = sector_collection
                    else:
                        all_collections[sector] = None
            else:
                print("❌ 扇形管理器接口不兼容")
                return
                
        except Exception as e:
            print(f"❌ 获取扇形集合时出错: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # 清空现有的sector_views，避免重复创建
        self.sector_views.clear()
        
        for sector in SectorQuadrant:
            try:
                sector_collection = all_collections.get(sector)
                print(f"\n检查 {sector.value}:")
                print(f"  - sector_collection 存在: {sector_collection is not None}")
                if sector_collection:
                    print(f"  - 孔位数量: {len(sector_collection.holes) if hasattr(sector_collection, 'holes') else 'N/A'}")
                
                if sector_collection and hasattr(sector_collection, 'holes') and len(sector_collection.holes) > 0:
                    print(f"\n创建 {sector.value} 的视图:")
                    print(f"  - 孔位数量: {len(sector_collection.holes)}")
                    
                    # 打印前3个孔位ID
                    sample_ids = list(sector_collection.holes.keys())[:3]
                    print(f"  - 孔位ID示例: {sample_ids}")
                    
                    # 为该扇形创建独立的图形视图（优化版本）
                    print(f"🚀 [性能优化] 创建扇形 {sector.value} 的图形视图...")
                    import time
                    view_start_time = time.perf_counter()
                    
                    view = OptimizedGraphicsView(self)  # 设置父组件，避免成为独立窗口
                    
                    # 延迟加载：仅在需要时加载图形
                    view.load_holes(sector_collection)
                    view.switch_to_macro_view()
                    view.hide()  # 确保不显示
                    
                    view_elapsed = time.perf_counter() - view_start_time
                    print(f"✅ [性能优化] 扇形 {sector.value} 图形视图创建完成，耗时: {view_elapsed:.3f}秒")
                    
                    self.sector_views[sector] = {
                        'view': view,
                        'collection': sector_collection,
                        'hole_count': len(sector_collection)
                    }
                    print(f"  ✅ {sector.value} 视图创建完成")
                else:
                    print(f"\n⚠️ {sector.value} 没有有效的孔位数据:")
                    if not sector_collection:
                        print(f"  - 扇形集合为空")
                    elif not hasattr(sector_collection, 'holes'):
                        print(f"  - 扇形集合没有holes属性")
                    elif len(sector_collection.holes) == 0:
                        print(f"  - 扇形集合的holes为空")
                    print(f"  - 跳过创建")
            except Exception as e:
                print(f"❌ 创建 {sector.value} 视图时出错: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\n扇形视图创建总结:")
        print(f"  - 创建了 {len(self.sector_views)} 个扇形视图")
        print(f"  - 扇形列表: {list(self.sector_views.keys())}")
        
        # 如果没有创建任何扇形视图，尝试诊断问题
        if len(self.sector_views) == 0:
            print("\n🔍 诊断：没有创建任何扇形视图")
            print(f"  - sector_graphics_manager: {self.sector_graphics_manager}")
            if hasattr(self, 'complete_hole_collection'):
                print(f"  - complete_hole_collection 存在: {self.complete_hole_collection is not None}")
                if self.complete_hole_collection:
                    print(f"  - 完整孔位数量: {len(self.complete_hole_collection.holes)}")
            else:
                print(f"  - complete_hole_collection 不存在")
        
        print("=== [DEBUG] 扇形视图创建完成 ===\n")
    
    # 扇形偏移配置方法已移除
    
    def _debug_verify_sector_visibility(self):
        """调试方法：验证当前扇形的可见性设置"""
        if not hasattr(self, 'current_sector') or not self.current_sector:
            print("[DEBUG] 当前没有选中的扇形")
            return
            
        print(f"\n=== [DEBUG] 验证扇形 {self.current_sector.value} 的可见性 ===")
        
        visible_count = 0
        hidden_count = 0
        visible_ids = []
        
        for hole_id, hole_item in self.graphics_view.hole_items.items():
            if hole_item.isVisible():
                visible_count += 1
                if len(visible_ids) < 5:  # 只记录前5个
                    visible_ids.append(hole_id)
            else:
                hidden_count += 1
        
        print(f"可见孔位: {visible_count}")
        print(f"隐藏孔位: {hidden_count}")
        print(f"可见孔位ID示例: {visible_ids}")
        
        # 检查可见孔位是否都属于当前扇形
        if hasattr(self, 'sector_views') and self.current_sector in self.sector_views:
            sector_info = self.sector_views[self.current_sector]
            sector_collection = sector_info['collection']
            sector_hole_ids = set(hole.hole_id for hole in sector_collection.holes.values())
            
            misplaced_visible = []
            for hole_id, hole_item in self.graphics_view.hole_items.items():
                if hole_item.isVisible() and hole_id not in sector_hole_ids:
                    misplaced_visible.append(hole_id)
                    if len(misplaced_visible) >= 5:
                        break
            
            if misplaced_visible:
                print(f"⚠️ 发现不属于当前扇形但可见的孔位: {misplaced_visible}")
            else:
                print("=== [DEBUG] 验证完成 ===\n")
    
    def switch_to_sector(self, sector: SectorQuadrant):
        """切换到指定扇形区域显示"""
        import time
        start_time = time.perf_counter()
        
        print(f"🔄 [扇形切换] 切换到: {sector.value}")
        
        # 检查是否有可用的扇形管理器（内部或外部）
        has_manager = (hasattr(self, 'sector_graphics_manager') and self.sector_graphics_manager) or \
                     (hasattr(self, 'external_sector_manager') and self.external_sector_manager)
        
        if not has_manager:
            print(f"❌ [扇形切换] 没有可用的扇形管理器")
            return
        
        self.current_sector = sector
        
        # 🔧 FIX: 增强视图变换状态管理，防止扇形→圆形→扇形的显示异常
        # 设置视图变换锁，确保操作的原子性
        self.graphics_view._sector_transform_lock = True
        
        # 设置标志，防止自动适配和强制居中干扰扇形偏移
        self.graphics_view.disable_auto_fit = True
        self.graphics_view.disable_auto_center = True
        
        # 获取扇形数据
        sector_info = self.sector_views.get(sector)
        print(f"📋 [扇形切换] sector_views 包含的扇形: {list(self.sector_views.keys())}")
        print(f"📋 [扇形切换] 请求的扇形 {sector} 数据存在: {sector_info is not None}")
        
        # 如果扇形数据不存在，尝试重新创建
        if not sector_info:
            print(f"⚠️ [扇形切换] 扇形 {sector.value} 在 sector_views 中不存在，尝试重新初始化...")
            
            # 检查是否有完整的孔位数据可以重新创建扇形视图
            if hasattr(self, 'complete_hole_collection') and self.complete_hole_collection:
                try:
                    # 只在不是创建过程中时重新创建扇形视图
                    if not self._creating_sector_views:
                        self._create_sector_views()
                    else:
                        print("⚠️ [防重复] 扇形视图创建中，跳过重复调用")
                        return
                    
                    # 再次尝试获取扇形数据
                    sector_info = self.sector_views.get(sector)
                    if sector_info:
                        print(f"✅ [扇形切换] 扇形 {sector.value} 重新创建成功")
                    else:
                        print(f"❌ [扇形切换] 扇形 {sector.value} 重新创建失败，可能该扇形无孔位数据")
                        if hasattr(self, 'status_label'):
                            self.status_label.setText(f"扇形 {sector.value} 暂无孔位数据")
                        return
                except Exception as e:
                    print(f"❌ [扇形切换] 重新创建扇形视图失败: {e}")
                    if hasattr(self, 'status_label'):
                        self.status_label.setText(f"扇形 {sector.value} 初始化失败")
                    return
            else:
                print(f"❌ [扇形切换] 无完整孔位数据，无法重新创建扇形视图")
                if hasattr(self, 'status_label'):
                    self.status_label.setText(f"扇形 {sector.value} 数据未加载")
                return
        
        # 如果graphics_view还没有加载完整的孔位集合，先加载完整数据
        if not hasattr(self.graphics_view, 'hole_items') or not self.graphics_view.hole_items:
            if hasattr(self, 'complete_hole_collection') and self.complete_hole_collection:
                print(f"🔧 首次加载完整孔位集合 ({len(self.complete_hole_collection)} 个孔位)")
                # 确保在加载之前设置标志
                self.graphics_view.disable_auto_fit = True
                self.graphics_view.load_holes(self.complete_hole_collection)
                
                # 同时初始化小型全景图的数据（如果还没有初始化）
                if hasattr(self, 'mini_panorama') and self.mini_panorama:
                    self._initialize_mini_panorama_data(self.complete_hole_collection)
        
        # 显示/隐藏孔位以实现扇形专注显示
        sector_collection = sector_info['collection']
        print(f"📊 [扇形切换] 扇形 {sector.value} 包含 {len(sector_collection)} 个孔位")
        
        sector_hole_ids = set(hole.hole_id for hole in sector_collection.holes.values())
        print(f"📊 [扇形切换] 扇形孔位ID数量: {len(sector_hole_ids)}")
        
        # 打印前几个孔位ID作为示例
        sample_ids = list(sector_hole_ids)[:5]
        print(f"📊 [扇形切换] 示例孔位ID: {sample_ids}")
        
        # 调试：打印graphics_view中的孔位ID格式
        view_hole_ids = list(self.graphics_view.hole_items.keys())[:5]
        
        
        # 检查ID格式是否匹配
        if sample_ids and view_hole_ids:
            print(f"📊 [扇形切换] ID格式匹配检查: 扇形ID={sample_ids[0]}, 视图ID={view_hole_ids[0]}, 匹配={sample_ids[0] == view_hole_ids[0]}")
        
        # 调试：检查ID匹配问题
        print("\n=== [DEBUG] ID匹配检查 ===")
        graphics_view_ids = list(self.graphics_view.hole_items.keys())[:5]
        print(f"GraphicsView中的孔位ID格式: {graphics_view_ids}")
        print(f"扇形集合中的孔位ID格式: {list(sector_hole_ids)[:5]}")
        
        # 尝试不同的ID格式匹配
        normalized_sector_ids = set()
        for sid in sector_hole_ids:
            normalized_id = self._normalize_hole_id(sid)
            normalized_sector_ids.add(normalized_id)
            if normalized_id != sid:
                pass  # Debug message silenced
        
        # 隐藏所有孔位，只显示当前扇形的孔位
        total_hidden = 0
        total_shown = 0
        not_found = 0
        match_by_normalized = 0
        
        for hole_id, hole_item in self.graphics_view.hole_items.items():
            normalized_view_id = self._normalize_hole_id(hole_id)
            
            # 尝试直接匹配和规范化匹配
            if hole_id in sector_hole_ids:
                hole_item.setVisible(True)
                total_shown += 1
            elif normalized_view_id in normalized_sector_ids:
                hole_item.setVisible(True)
                total_shown += 1
                match_by_normalized += 1
                if match_by_normalized <= 3:  # 只打印前3个
                    print(f"[DEBUG] 通过规范化匹配: {hole_id} -> {normalized_view_id}")
            else:
                hole_item.setVisible(False)
                total_hidden += 1
        
        # 检查是否有扇形孔位在视图中找不到
        for sector_hole_id in sector_hole_ids:
            normalized_sector_id = self._normalize_hole_id(sector_hole_id)
            found = False
            
            # 检查直接匹配
            if sector_hole_id in self.graphics_view.hole_items:
                found = True
            else:
                # 检查规范化匹配
                for view_id in self.graphics_view.hole_items:
                    if self._normalize_hole_id(view_id) == normalized_sector_id:
                        found = True
                        break
            
            if not found:
                not_found += 1
                if not_found <= 5:  # 只打印前5个
                    print(f"⚠️ [扇形切换] 扇形孔位 {sector_hole_id} (规范化: {normalized_sector_id}) 在视图中未找到")
        
        print(f"📊 [扇形切换] 切换到 {sector.value}: 显示 {total_shown} 个孔位 (规范化匹配: {match_by_normalized}), 隐藏 {total_hidden} 个孔位, 未找到 {not_found} 个")
        print("=== [DEBUG] ID匹配检查完成 ===\n")
        
        # 适应视图到当前可见的孔位 - 使用填满策略
        self._apply_fill_view_strategy()
        
        # 🔧 FIX: 释放视图变换锁，确保后续操作正常进行
        self.graphics_view._sector_transform_lock = False
        
        # 更新小型全景图的当前扇形高亮
        if hasattr(self, 'mini_panorama') and self.mini_panorama:
            self.mini_panorama.highlight_sector(sector)
            
        elapsed_time = (time.perf_counter() - start_time) * 1000
        print(f"✅ [扇形切换] 完成切换到 {sector.value}, 显示: {total_shown}, 隐藏: {total_hidden}, 耗时: {elapsed_time:.1f}ms")
        
        # 验证可见性
        self._verify_sector_visibility(sector)
        
        # 调试：验证扇形可见性
        self._debug_verify_sector_visibility()
    
    def _verify_sector_visibility(self, current_sector: SectorQuadrant):
        """验证扇形可见性设置是否正确"""
        print(f"\n🔍 [可见性验证] 验证扇形 {current_sector.value} 的可见性...")
        
        # 获取当前扇形应该显示的孔位ID
        sector_info = self.sector_views.get(current_sector)
        if not sector_info:
            print(f"❌ [可见性验证] 扇形信息不存在")
            return
            
        expected_visible_ids = set(hole.hole_id for hole in sector_info['collection'].holes.values())
        
        # 检查实际可见性
        actual_visible = 0
        should_be_visible = 0
        should_be_hidden = 0
        incorrectly_visible = 0
        
        for hole_id, hole_item in self.graphics_view.hole_items.items():
            is_visible = hole_item.isVisible()
            should_visible = hole_id in expected_visible_ids
            
            if is_visible:
                actual_visible += 1
                if not should_visible:
                    incorrectly_visible += 1
                    if incorrectly_visible <= 5:  # 只打印前5个错误
                        print(f"  ❌ 孔位 {hole_id} 不应该可见但是可见的")
            
            if should_visible:
                should_be_visible += 1
            else:
                should_be_hidden += 1
        
        print(f"🔍 [可见性验证] 结果:")
        print(f"  - 应该可见: {should_be_visible}")
        print(f"  - 应该隐藏: {should_be_hidden}")
        print(f"  - 实际可见: {actual_visible}")
        print(f"  - 错误可见: {incorrectly_visible}")
        
        if incorrectly_visible > 0:
            print(f"  ⚠️ 有 {incorrectly_visible} 个孔位错误地显示了!")
            
            # 强制更新场景
            print(f"  🔧 强制更新场景...")
            self.graphics_view.scene.update()
            self.graphics_view.viewport().update()
    
    def _apply_fill_view_strategy(self):
        """应用填满视图策略 - 让扇形的视觉中心与视图中心对齐"""
        if not self.sector_graphics_manager or not self.sector_graphics_manager.center_point:
            # 如果没有扇形管理器或中心点，直接返回
            print("⚠️ [动态扇形] 缺少扇形管理器或中心点，跳过视图策略")
            return
            
        # 获取当前扇形的实际边界，而不是完整数据边界
        # 使用可见孔位的边界来计算正确的中心点
        visible_items = [item for item in self.graphics_view.hole_items.values() if item.isVisible()]
        
        if not visible_items:
            # 如果没有可见项，使用完整数据的边界
            bounds = self.complete_hole_collection.get_bounds()
            original_center_x = (bounds[0] + bounds[2]) / 2
            original_center_y = (bounds[1] + bounds[3]) / 2
            min_x, min_y, max_x, max_y = bounds
        else:
            # 使用可见项的边界计算中心点
            min_x = min_y = float('inf')
            max_x = max_y = float('-inf')
            
            for item in visible_items:
                pos = item.pos()
                rect = item.boundingRect()
                min_x = min(min_x, pos.x() + rect.left())
                min_y = min(min_y, pos.y() + rect.top())
                max_x = max(max_x, pos.x() + rect.right())
                max_y = max(max_y, pos.y() + rect.bottom())
            
            original_center_x = (min_x + max_x) / 2
            original_center_y = (min_y + max_y) / 2
        
        # 使用扇形的实际几何中心，确保扇形内容正确居中显示
        data_center_x = original_center_x
        data_center_y = original_center_y
        print(f"🎯 [动态扇形] 使用扇形几何中心: ({data_center_x:.1f}, {data_center_y:.1f})")
        
        data_center = QPointF(data_center_x, data_center_y)
        print(f"📊 [动态扇形] 最终数据中心: ({data_center_x:.1f}, {data_center_y:.1f})")
        
        # 如果没有可见项，提前返回
        if not visible_items:
            return
        
        # 使用实际的扇形几何中心作为视觉中心
        # 这样可以确保扇形内容正确居中显示
        visual_center_x = original_center_x  # 使用已计算的扇形中心
        visual_center_y = original_center_y
        visual_center = QPointF(visual_center_x, visual_center_y)
        
        print(f"🎯 [动态扇形] 实际扇形边界: ({min_x:.1f}, {min_y:.1f}) - ({max_x:.1f}, {max_y:.1f})")
        print(f"🎯 [动态扇形] 扇形几何中心: ({visual_center_x:.1f}, {visual_center_y:.1f})")
        
        
        # 计算扇形内容的尺寸（使用已计算的边界）
        content_width = max_x - min_x
        content_height = max_y - min_y
        
        print(f"📏 [动态扇形] 扇形内容尺寸: {content_width:.1f} x {content_height:.1f}")
        
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
        
        # 根据视图大小动态调整缩放 - 更好地利用可用空间
        # 计算视图面积比例来确定缩放因子
        view_area = view_width * view_height
        
        if view_area >= 700000:  # 大视图 (1000x700+)
            # 大视图：充分利用空间
            scale_factor = 0.85
        elif view_area >= 480000:  # 中等视图 (800x600+)
            # 中等视图：平衡缩放
            scale_factor = 0.82
        else:
            # 小视图：最大化利用空间
            scale_factor = 0.88
        
        # 应用缩放系数
        final_scale = base_scale * scale_factor
        
        # 🔧 优化视觉跳动问题：使用单一变换矩阵操作
        # 保存当前的变换状态
        current_transform = self.graphics_view.transform()
        current_center = self.graphics_view.mapToScene(self.graphics_view.viewport().rect().center())
        
        # 检查是否需要变换（避免不必要的更新）
        new_transform = QTransform()
        new_transform.scale(final_scale, final_scale)
        
        # 检查是否需要更新变换（但不跳过初始设置）
        transform_changed = abs(current_transform.m11() - new_transform.m11()) > 0.01 or \
                           abs(current_transform.m22() - new_transform.m22()) > 0.01
        
        center_changed = (current_center - data_center).manhattanLength() > 1.0
        
        # 如果当前缩放接近1.0（未初始化状态），强制更新
        is_uninitialized = abs(current_transform.m11() - 1.0) < 0.01 and abs(current_transform.m22() - 1.0) < 0.01
        
        # 🔧 FIX: 检查视图变换锁状态，防止在扇形切换过程中的并发变换
        is_transform_locked = getattr(self.graphics_view, '_sector_transform_lock', False)
        
        if not transform_changed and not center_changed and not is_uninitialized and not is_transform_locked:
            print(f"🔄 [动态扇形] 变换未发生显著变化，跳过更新")
            return
        
        # 偏移功能已移除
        
        print(f"🔄 [动态扇形] 更新变换: transform_changed={transform_changed}, center_changed={center_changed}, is_uninitialized={is_uninitialized}")
            
        # 使用视图状态管理器临时禁用更新
        self.graphics_view.setUpdatesEnabled(False)
        
        try:
            # 🔧 首先设置正确的场景矩形，确保所有内容都在场景范围内
            margin = 100  # 添加边距
            scene_rect = QRectF(
                min_x - margin, min_y - margin,
                content_width + 2 * margin, content_height + 2 * margin
            )
            
            if self.graphics_view.scene:
                self.graphics_view.scene.setSceneRect(scene_rect)
                print(f"🏗️ [动态扇形] 设置场景矩形: ({scene_rect.x():.1f}, {scene_rect.y():.1f}) {scene_rect.width():.1f}x{scene_rect.height():.1f}")
            
            # 创建复合变换：缩放 + 居中
            transform = QTransform()
            transform.scale(final_scale, final_scale)
            
            # 一次性应用变换和居中，减少视觉跳动
            if not getattr(self.graphics_view, 'disable_auto_center', False):
                # 设置变换
                self.graphics_view.setTransform(transform)
                # 使用数据中心进行居中，如果启用了偏移就会使用偏移后的数据中心
                self.graphics_view.centerOn(data_center)
                print(f"🎯 [动态扇形] 已将数据中心对齐到视图中心: ({data_center.x():.1f}, {data_center.y():.1f})")
            else:
                # 只设置变换，不居中
                self.graphics_view.setTransform(transform)
                print(f"🛡️ [动态扇形] 跳过 centerOn（disable_auto_center=True）")
                
        finally:
            # 重新启用视图更新并强制刷新
            self.graphics_view.setUpdatesEnabled(True)
            self.graphics_view.viewport().update()
        
        # 计算视觉中心与数据中心的偏移
        offset_from_data_center = visual_center - data_center
        
        # 偏移已通过修改数据中心实现，无需额外的滚动条操作
        
        print(f"📊 [动态扇形] 最终边界: ({min_x:.1f}, {min_y:.1f}) - ({max_x:.1f}, {max_y:.1f})")
        print(f"📏 [动态扇形] 内容尺寸: {content_width:.1f} x {content_height:.1f}")
        print(f"🎯 [动态扇形] 视觉中心: ({visual_center_x:.1f}, {visual_center_y:.1f})")
        print(f"📐 [动态扇形] 视觉中心与数据中心偏移: ({offset_from_data_center.x():.1f}, {offset_from_data_center.y():.1f})")
        print(f"🔍 [动态扇形] 最终缩放: {final_scale:.3f} (基础: {base_scale:.3f}, 系数: {scale_factor:.2f})")
        print(f"✅ [动态扇形] 视图策略应用完成 - 修复扇形移动和定位问题")
    
    # 滚动偏移方法已移除
    
    def _normalize_hole_id(self, hole_id: str) -> str:
        """规范化孔位ID以支持新旧格式匹配
        
        支持的格式转换：
        - H001, H00001 -> 001
        - C001R001 -> 001_001  
        - (1,1) -> 1_1
        - hole_1 -> 1
        
        Args:
            hole_id: 原始孔位ID
            
        Returns:
            str: 规范化后的ID
        """
        import re
        if not hole_id:
            return ""
        
        # 新格式 C{col:03d}R{row:03d} -> col_row
        match = re.match(r'^C(\d{3})R(\d{3})$', hole_id)
        if match:
            col, row = match.groups()
            return f"{int(col)}_{int(row)}"
        
        # H格式 H001, H00001 -> 001
        match = re.match(r'^H(\d+)$', hole_id)
        if match:
            return match.group(1).lstrip('0') or '0'
        
        # 坐标格式 (row,col) -> row_col
        match = re.match(r'^\((\d+),(\d+)\)$', hole_id)
        if match:
            row, col = match.groups()
            return f"{row}_{col}"
        
        # hole_格式 hole_1 -> 1
        match = re.match(r'^hole_(\d+)$', hole_id)
        if match:
            return match.group(1)
        
        # 清理其他字符，保留数字和下划线
        normalized = re.sub(r'[^\d_]', '', hole_id)
        return normalized if normalized else hole_id
    
    def update_mini_panorama_hole_status(self, hole_id: str, status, color=None):
        """更新小型全景图中孔位的状态显示
        
        Args:
            hole_id: 孔位ID
            status: 状态值 (字符串或HoleStatus枚举)
            color: 可选的自定义颜色
        """
        try:
            # 使用 CompletePanoramaWidget 的更新机制
            if hasattr(self, 'mini_panorama') and self.mini_panorama:
                if hasattr(self.mini_panorama, 'update_hole_status'):
                    # 直接使用 CompletePanoramaWidget 的 update_hole_status 方法
                    self.mini_panorama.update_hole_status(hole_id, status)
                    print(f"✅ [小型全景图] 已调用 update_hole_status 更新孔位 {hole_id} 的状态为 {status}")
                else:
                    print(f"⚠️ [小型全景图] mini_panorama 没有 update_hole_status 方法")
            else:
                print(f"⚠️ [小型全景图] mini_panorama 不存在")
                
        except Exception as e:
            print(f"❌ [动态扇形-小型全景图] 更新孔位状态失败: {e}")
            import traceback
            traceback.print_exc()


class CompletePanoramaWidget(QWidget):
    """完整全景图显示组件"""
    
    # 添加信号用于扇形区域点击
    sector_clicked = Signal(SectorQuadrant)
    
    # 添加偏移控制信号
    # 偏移信号已移除
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hole_collection: Optional[HoleCollection] = None
        self.center_point: Optional[QPointF] = None
        self.panorama_radius: float = 0.0
        self.sector_highlights: Dict[SectorQuadrant, SectorHighlightItem] = {}
        self.current_highlighted_sector: Optional[SectorQuadrant] = None
        
        # 延迟批量更新机制
        self.pending_status_updates: Dict[str, any] = {}  # hole_id -> status
        self.batch_update_timer = QTimer()
        self.batch_update_timer.timeout.connect(self._apply_batch_updates)
        self.batch_update_timer.setSingleShot(True)
        self.batch_update_interval = 200   # 【修复】减少到200毫秒，提高响应速度
        
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 移除标题，直接显示全景图形视图
        # title_label = QLabel("完整孔位全景图")
        # title_label.setAlignment(Qt.AlignCenter)
        # title_label.setFont(QFont("Arial", 12, QFont.Bold))
        # title_label.setStyleSheet("padding: 5px; background-color: #313642; border-radius: 3px;")
        # layout.addWidget(title_label)
        
        # 全景图形视图 - 固定尺寸确保布局一致性
        self.panorama_view = OptimizedGraphicsView()
        self.panorama_view.setFrameStyle(QFrame.NoFrame)  # 移除边框避免黑框
        self.panorama_view.setFixedSize(350, 350)    # 调整显示面板尺寸适配380px宽度
        
        # 统一渲染设置，使其与OptimizedGraphicsView一致
        from PySide6.QtWidgets import QGraphicsView
        from PySide6.QtGui import QPainter
        
        # 使用与OptimizedGraphicsView相同的性能优化设置
        self.panorama_view.setRenderHint(QPainter.Antialiasing, False)
        self.panorama_view.setRenderHint(QPainter.SmoothPixmapTransform, False)
        self.panorama_view.setViewportUpdateMode(QGraphicsView.MinimalViewportUpdate)
        self.panorama_view.setOptimizationFlag(QGraphicsView.DontSavePainterState, True)
        self.panorama_view.setOptimizationFlag(QGraphicsView.DontAdjustForAntialiasing, True)
        self.panorama_view.setCacheMode(QGraphicsView.CacheNone)
        
        # 隐藏滚动条
        self.panorama_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.panorama_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 移除硬编码样式，使用主题管理器
        self.panorama_view.setObjectName("PanoramaGraphicsView")
        
        # 启用鼠标跟踪以支持点击扇形区域
        self.panorama_view.setMouseTracking(True)
        
        # 安装事件过滤器来拦截鼠标点击事件
        self.panorama_view.viewport().installEventFilter(self)
        
        
        # 创建全景图容器以实现完美居中（水平+垂直）
        panorama_container = QWidget()
        panorama_container.setFixedSize(360, 380)  # 固定容器大小
        panorama_layout = QVBoxLayout(panorama_container)
        panorama_layout.setContentsMargins(0, 0, 0, 0)
        panorama_layout.setAlignment(Qt.AlignCenter)
        
        # 创建带浮动控制面板的全景图区域
        panorama_widget = QWidget()
        panorama_widget.setFixedSize(350, 350)
        
        # 使用绝对定位来管理全景图和控制面板
        self.panorama_view.setParent(panorama_widget)
        self.panorama_view.move(0, 0)
        
        # 偏移控制面板已移除
        
        panorama_layout.addWidget(panorama_widget)
        layout.addWidget(panorama_container)
        
        # 信息标签 - 放在全景图下方，增大字体
        self.info_label = QLabel("等待数据加载...")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("""
            QLabel {
                padding: 8px;
                font-size: 14px;
                font-weight: bold;
                color: #D3D8E0;
                background-color: rgba(248, 249, 250, 200);
                border: 1px solid #404552;
                border-radius: 6px;
                margin: 5px;
            }
        """)
        layout.addWidget(self.info_label)
    
    
    
    def load_complete_view(self, hole_collection: HoleCollection):
        """加载完整的全景图 - 使用统一缩放管理"""
        print(f"🎯 [全景图] load_complete_view 被调用, hole_collection={hole_collection is not None}, 数量={len(hole_collection) if hole_collection else 0}")
        if hole_collection and len(hole_collection) > 0:
            try:
                print(f"🔄 [全景图] 开始加载 {len(hole_collection)} 个孔位")
                
                # 使用统一缩放管理系统（支持超大数据集优化）
                from src.core_business.graphics.scale_manager import apply_panorama_overview_scale
                
                # 一步完成数据加载和智能缩放（自动检测数据规模）
                success = apply_panorama_overview_scale(self.panorama_view, hole_collection)
                
                if success:
                    print(f"✅ [全景图] 数据加载和缩放完成")
                    
                    # 保存数据引用
                    self.hole_collection = hole_collection
                    
                    # 立即创建扇形高亮（避免用户看到空白状态）
                    print(f"📌 [全景图] 准备计算几何信息...")
                    self._calculate_panorama_geometry()
                    print(f"📌 [全景图] 准备创建扇形高亮...")
                    self._create_sector_highlights()
                    print(f"📌 [全景图] 扇形高亮创建流程完成")
                    
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
                        
                        # 检查高亮项
                        highlight_count = len(self.sector_highlights)
                        print(f"🎨 [全景图] 扇形高亮数量: {highlight_count}")
                        for sector, highlight in self.sector_highlights.items():
                            print(f"   - {sector.value}: 可见={highlight.isVisible()}, Z值={highlight.zValue()}")
                        
                        if items_count == 0:
                            print("⚠️ [全景图] 警告: 场景中没有图形项!")
                else:
                    print("❌ [全景图] 缩放失败，尝试诊断问题...")
                    # 使用诊断功能
                    from src.core_business.graphics.scale_manager import diagnose_scale_issues, fix_over_scaled_view
                    
                    diagnosis = diagnose_scale_issues(self.panorama_view, hole_collection)
                    print(f"🔍 [全景图] 诊断结果: {len(diagnosis['issues'])} 个问题")
                    for issue in diagnosis['issues']:
                        print(f"   - {issue}")
                    
                    # 尝试修复
                    print("🔧 [全景图] 尝试自动修复...")
                    if fix_over_scaled_view(self.panorama_view, hole_collection):
                        print("✅ [全景图] 自动修复成功")
                        self.hole_collection = hole_collection
                        actual_hole_count = len(hole_collection.holes) if hasattr(hole_collection, 'holes') else len(hole_collection)
                        self.info_label.setText(f"全景: {actual_hole_count} 个孔位")
                    else:
                        print("❌ [全景图] 自动修复失败")
                        self.info_label.setText("全景图加载失败")
                    
            except Exception as e:
                print(f"❌ [全景图] 加载失败: {e}")
                import traceback
                traceback.print_exc()
                self.info_label.setText("全景图加载错误")
        else:
            print("⚠️ [全景图] 没有提供有效的孔位数据")
            self.info_label.setText("等待数据加载...")
    
    # 注意：原_fit_panorama_view方法已被统一缩放管理系统替代
    # 新的缩放逻辑在scale_manager.py中实现，无需多重缩放操作
    
    def _ensure_perfect_centering(self):
        """确保全景图完美居中"""
        try:
            scene = self.panorama_view.scene
            if scene and len(scene.items()) > 0:
                # 获取场景内容边界
                scene_rect = scene.itemsBoundingRect()
                if scene_rect.isEmpty() or scene_rect.width() <= 0:
                    scene_rect = scene.sceneRect()
                
                # 获取内容中心
                content_center = scene_rect.center()
                
                # 强制居中到内容中心
                self.panorama_view.centerOn(content_center)
                
                # 强制重绘
                self.panorama_view.viewport().update()
                
                print(f"✨ [全景图] 执行完美居中调整: ({content_center.x():.1f}, {content_center.y():.1f})")
                
        except Exception as e:
            print(f"⚠️ [全景图] 完美居中调整失败: {e}")
    
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
        # DEBUG: 扇形交互调试
        print(f"🔍 [DEBUG] _calculate_panorama_geometry 被调用")
        print(f"🔍 [DEBUG] hole_collection 存在: {self.hole_collection is not None}")
        if self.hole_collection:
            print(f"🔍 [DEBUG] hole_collection 大小: {len(self.hole_collection)}")
        
        if not self.hole_collection:
            print(f"⚠️ [DEBUG] hole_collection 为空，无法计算几何信息")
            return
        
        try:
            # 直接使用数据的几何中心作为扇形中心点
            # 这样可以确保扇形与孔位数据完美对齐
            bounds = self.hole_collection.get_bounds()
            original_center_x = (bounds[0] + bounds[2]) / 2
            original_center_y = (bounds[1] + bounds[3]) / 2
            
            # 使用真正的数据几何中心，不做任何偏移
            data_center_x = original_center_x
            data_center_y = original_center_y
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
            
            # 添加一些边距，让高亮区域适中
            self.panorama_radius = max_distance * 1.3  # 调整到1.3，让扇形初始大小更大
            
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

        if not self.hole_collection:
            print("⚠️ [全景图] 无法创建扇形高亮：孔位数据不存在")
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
            
            # 扇形高亮使用更小的半径，以更好地适应圆形区域
            sector_highlight_radius = self.panorama_radius * 0.75
            
            # 计算真正的数据中心点用于扇形高亮（不偏移）
            bounds = self.hole_collection.get_bounds()
            true_center_x = (bounds[0] + bounds[2]) / 2
            true_center_y = (bounds[1] + bounds[3]) / 2
            true_center_point = QPointF(true_center_x, true_center_y)
            
            print(f"🎯 [扇形高亮] 使用真正的数据中心: ({true_center_point.x():.1f}, {true_center_point.y():.1f})")
            print(f"🎯 [扇形高亮] 偏移后的显示中心: ({self.center_point.x():.1f}, {self.center_point.y():.1f})")
            
            # 为每个扇形创建高亮项，使用真正的数据中心
            for sector in SectorQuadrant:
                highlight = SectorHighlightItem(
                    sector=sector,
                    center=true_center_point,  # 使用真正的中心点
                    radius=sector_highlight_radius,  # 使用更小的扇形高亮半径
                    sector_bounds=None  # 不使用边界框模式
                )
                
                # 使用扇形模式
                highlight.set_highlight_mode("sector")
                
                # 添加到场景
                scene.addItem(highlight)
                self.sector_highlights[sector] = highlight
                
                # 确保高亮项在正确的层级
                highlight.setZValue(100)  # 设置较高的Z值确保在顶层
                
                print(f"🎨 [全景图] 创建扇形高亮: {sector.value}, 中心=({true_center_point.x():.1f}, {true_center_point.y():.1f}), 半径={display_radius:.1f}")
                
                # 验证高亮是否正确添加到场景
                if highlight.scene() == scene:
                    print(f"✅ [全景图] 扇形 {sector.value} 高亮已添加到场景")
                    # 检查场景中其他项的Z值
                    z_values = []
                    for item in scene.items():
                        z_values.append(item.zValue())
                    if z_values:
                        print(f"📊 [全景图] 场景Z值范围: 最小={min(z_values)}, 最大={max(z_values)}, 高亮Z值={highlight.zValue()}")
                else:
                    print(f"❌ [全景图] 扇形 {sector.value} 高亮未能添加到场景")
            
            # 创建扇形分隔线，使扇形边界更清晰
            self._create_sector_dividers()
            
            print(f"✅ [全景图] 扇形高亮创建完成，共 {len(self.sector_highlights)} 个扇形")

        except Exception as e:
            print(f"❌ [全景图] 扇形高亮创建失败: {e}")
            import traceback
            traceback.print_exc()

    def _recreate_all_highlights(self):
        """强制重新创建所有扇形高亮（恢复机制）"""
        try:
            print("🔄 [全景图] 强制重新创建扇形高亮系统...")
            # 清理现有高亮
            scene = self.panorama_view.scene
            if scene:
                for highlight in list(self.sector_highlights.values()):
                    try:
                        if highlight.scene():
                            scene.removeItem(highlight)
                    except RuntimeError:
                        pass
            self.sector_highlights.clear()
            
            # 重新创建
            self._create_sector_highlights()
            print("✅ [全景图] 扇形高亮系统重新创建完成")
        except Exception as e:
            print(f"❌ [全景图] 重新创建扇形高亮失败: {e}")

    def _ensure_sector_highlight_exists(self, sector: SectorQuadrant) -> bool:
        """确保指定扇形的高亮项存在，如果不存在则创建"""
        if sector in self.sector_highlights:
            # 检查现有高亮项是否有效
            highlight = self.sector_highlights[sector]
            if highlight and highlight.scene():
                return True
            else:
                # 如果现有高亮项无效，移除它
                print(f"🔄 [高亮] 移除无效的扇形 {sector.value} 高亮项")
                del self.sector_highlights[sector]

        if not self.hole_collection or not self.center_point:
            print(f"⚠️ [全景图] 无法创建扇形 {sector.value} 高亮：缺少必要数据")
            return False

        try:
            scene = self.panorama_view.scene
            if not scene:
                print(f"⚠️ [全景图] 无法创建扇形 {sector.value} 高亮：场景不存在")
                return False

            # 计算真正的数据中心点用于扇形高亮（不偏移）
            bounds = self.hole_collection.get_bounds()
            true_center_x = (bounds[0] + bounds[2]) / 2
            true_center_y = (bounds[1] + bounds[3]) / 2
            true_center_point = QPointF(true_center_x, true_center_y)

            # 使用当前的半径，如果没有则使用默认值
            radius = getattr(self, 'panorama_radius', 100.0)
            # 扇形高亮使用更小的半径，以更好地适应圆形区域
            sector_highlight_radius = radius * 0.75

            highlight = SectorHighlightItem(
                sector=sector,
                center=true_center_point,
                radius=sector_highlight_radius,
                sector_bounds=None
            )
            highlight.set_highlight_mode("sector")

            # 添加到场景
            scene.addItem(highlight)
            self.sector_highlights[sector] = highlight
            
            # 确保高亮项在正确的层级
            highlight.setZValue(100)  # 设置较高的Z值确保在顶层

            print(f"✅ [全景图] 即时创建扇形 {sector.value} 高亮项")
            return True

        except Exception as e:
            print(f"❌ [全景图] 即时创建扇形 {sector.value} 高亮失败: {e}")
            return False
    
    def _create_sector_dividers(self):
        """创建扇形分隔线，使扇形边界更清晰"""
        try:
            scene = self.panorama_view.scene
            if not scene or not self.center_point:
                return
            
            # 创建十字分隔线 - 进一步增强可见性
            pen = QPen(QColor(50, 50, 50), 3, Qt.SolidLine)
            
            # 水平线（分隔上下）
            h_line = scene.addLine(
                self.center_point.x() - self.panorama_radius,
                self.center_point.y(),
                self.center_point.x() + self.panorama_radius,
                self.center_point.y(),
                pen
            )
            h_line.setZValue(15)  # 在高亮层之上
            h_line.setAcceptedMouseButtons(Qt.NoButton)
            
            # 垂直线（分隔左右）
            v_line = scene.addLine(
                self.center_point.x(),
                self.center_point.y() - self.panorama_radius,
                self.center_point.x(),
                self.center_point.y() + self.panorama_radius,
                pen
            )
            v_line.setZValue(15)  # 在高亮层之上
            v_line.setAcceptedMouseButtons(Qt.NoButton)
            
            # 创建中心点标记 - 增强可见性
            center_pen = QPen(QColor(255, 0, 0, 180), 3)
            center_brush = QBrush(QColor(255, 0, 0, 120))
            center_mark = scene.addEllipse(
                self.center_point.x() - 4,
                self.center_point.y() - 4,
                8,
                8,
                center_pen,
                center_brush
            )
            center_mark.setZValue(20)  # 最上层
            center_mark.setAcceptedMouseButtons(Qt.NoButton)
            
            print(f"✅ [全景图] 扇形分隔线创建完成")
            
        except Exception as e:
            print(f"❌ [全景图] 扇形分隔线创建失败: {e}")
    
    
    def test_highlight_all_sectors(self):
        """测试方法：高亮显示所有扇形"""
        print("🧪 [测试] 开始测试所有扇形高亮...")
        for sector in SectorQuadrant:
            if sector in self.sector_highlights:
                highlight = self.sector_highlights[sector]
                highlight.show_highlight()
                print(f"🧪 [测试] 显示扇形 {sector.value} 高亮")
        
        # 强制刷新视图
        if self.panorama_view.scene:
            self.panorama_view.scene.update()
        self.panorama_view.viewport().update()
        self.panorama_view.repaint()
        print("🧪 [测试] 所有扇形高亮已显示")
    
    def update_sector_progress(self, sector: SectorQuadrant, progress):
        """
        更新扇形进度显示
        """
        # 如果有扇形高亮，可以在此处更新高亮状态
        if hasattr(self, 'sector_highlights') and sector in self.sector_highlights:
            highlight = self.sector_highlights[sector]
            if progress and hasattr(progress, 'completed_holes') and progress.completed_holes > 0:
                highlight.show_highlight()
            else:
                highlight.hide_highlight()
        
        # 如果有扇形视图，也可以在此处更新
        if hasattr(self, 'sector_views') and sector in self.sector_views:
            sector_view = self.sector_views[sector]
            if hasattr(sector_view, 'update_sector_progress'):
                sector_view.update_sector_progress(sector, progress)
    
    def highlight_sector(self, sector: SectorQuadrant):
        """高亮显示指定的扇形区域"""
        try:
            # 清除所有高亮
            for s, highlight in list(self.sector_highlights.items()):
                try:
                    highlight.hide_highlight()
                except (RuntimeError, AttributeError):
                    # 高亮项可能已被删除，从字典中移除
                    self.sector_highlights.pop(s, None)

            # 确保高亮项存在 - 多次尝试确保成功
            max_attempts = 3
            for attempt in range(max_attempts):
                if self._ensure_sector_highlight_exists(sector):
                    break
                if attempt < max_attempts - 1:
                    print(f"⚠️ [全景图] 第{attempt+1}次创建扇形 {sector.value} 高亮失败，重试...")
                    # 强制重新创建高亮系统
                    QTimer.singleShot(10, self._recreate_all_highlights)
                else:
                    print(f"❌ [全景图] 无法为扇形 {sector.value} 创建高亮项，已重试{max_attempts}次")
                    return

            # 验证高亮项确实存在且有效
            if sector not in self.sector_highlights:
                print(f"❌ [全景图] 扇形 {sector.value} 高亮项创建后仍不存在")
                return

            highlight_item = self.sector_highlights[sector]
            if not highlight_item or not hasattr(highlight_item, 'show_highlight'):
                print(f"❌ [全景图] 扇形 {sector.value} 高亮项无效")
                return

            # 高亮指定扇形
            highlight_item.show_highlight()
            self.current_highlighted_sector = sector
            print(f"🎯 [全景图] 高亮扇形: {sector.value}")
            
        except Exception as e:
            print(f"❌ [全景图] 扇形高亮失败: {e}")
            import traceback
            traceback.print_exc()
            # 强制重新创建高亮系统作为恢复机制
            QTimer.singleShot(100, self._recreate_all_highlights)
    
    # CompletePanoramaWidget中的强制偏移方法已移除


        except Exception as e:
            print(f"❌ [全景图] 扇形高亮失败: {e}")
            import traceback
            traceback.print_exc()
            # 强制重新创建高亮系统作为恢复机制
            QTimer.singleShot(100, self._recreate_all_highlights)
    
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
    
    def eventFilter(self, obj, event):
        """事件过滤器，处理全景视图的鼠标事件"""
        if obj == self.panorama_view.viewport() and event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                # 将视口坐标转换为场景坐标
                scene_pos = self.panorama_view.mapToScene(event.pos())
                
                # DEBUG: 扇形交互调试
                print(f"🖱️ [全景图] 鼠标点击: 视口坐标={event.pos()}, 场景坐标=({scene_pos.x():.1f}, {scene_pos.y():.1f})")
                print(f"🔍 [DEBUG] center_point: {self.center_point}")
                print(f"🔍 [DEBUG] panorama_radius: {self.panorama_radius}")
                
                
                # 检测点击的扇形
                clicked_sector = self._detect_clicked_sector(scene_pos)
                if clicked_sector:
                    print(f"🎯 [全景图] 检测到扇形点击: {clicked_sector.value}")
                    self.sector_clicked.emit(clicked_sector)
                    # 高亮被点击的扇形
                    self.highlight_sector(clicked_sector)
                    return True  # 事件已处理
                else:
                    print(f"❌ [全景图] 未检测到扇形点击")
        
        return super().eventFilter(obj, event)
    
    def _detect_clicked_sector(self, scene_pos: QPointF) -> Optional[SectorQuadrant]:
        """检测点击位置属于哪个扇形区域"""
        print(f"🖱️ [全景图] 检测点击位置: ({scene_pos.x():.1f}, {scene_pos.y():.1f})")
        if not self.center_point:
            print(f"⚠️ [全景图] 中心点未设置")
            return None
        if not self.hole_collection:
            print(f"⚠️ [全景图] 孔位集合未设置")
            return None
        try:
            # 计算点击位置相对于中心的向量
            dx = scene_pos.x() - self.center_point.x()
            dy = scene_pos.y() - self.center_point.y()
            
            # 计算距离，判断是否在有效范围内
            distance = math.sqrt(dx * dx + dy * dy)
            print(f"📏 [全景图] 点击距离中心: {distance:.1f}, 半径: {self.panorama_radius:.1f}")
            
            # 放宽距离检查，只要不是太远的点击都认为有效
            max_valid_distance = self.panorama_radius * 1.5 if self.panorama_radius > 0 else 1000
            if distance > max_valid_distance:
                print(f"❌ [全景图] 点击距离过远: {distance:.1f} > {max_valid_distance:.1f}")
                return None
            # 计算角度
            angle_rad = math.atan2(dy, dx)
            angle_deg = math.degrees(angle_rad)
            
            # 转换为0-360度范围
            if angle_deg < 0:
                angle_deg += 360
            
            print(f"📐 [全景图] 点击角度: {angle_deg:.1f}°, 中心点: ({self.center_point.x():.1f}, {self.center_point.y():.1f})")
            
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
            import traceback
            traceback.print_exc()
            return None
    
    def update_hole_status(self, hole_id: str, status):
        """更新孔位状态（智能批量/实时更新版本）"""
        print(f"📦 [全景图] 接收到状态更新: {hole_id} -> {status.value if hasattr(status, 'value') else status}")
        print(f"🔍 [调试] 当前时间: {__import__('datetime').datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
        
        # 检查是否在模拟期间
        print(f"🔍 [调试] 开始检查模拟状态...")
        is_simulation_running = self._check_simulation_status()
        print(f"🔍 [调试] 模拟状态检查结果: {is_simulation_running}")
        
        if is_simulation_running:
            # 模拟期间：直接实时更新
            print(f"🔥 [全景图] 模拟期间，使用实时更新")
            self._apply_single_update(hole_id, status)
        else:
            # 【修复】增加备用强制实时更新机制
            print(f"📦 [全景图] 模拟状态检测为False，检查是否需要强制实时更新...")
            
            # 检查是否是重要状态变化（pending -> 其他状态）
            force_immediate = self._should_force_immediate_update(hole_id, status)
            
            if force_immediate:
                print(f"🚀 [修复] 检测到重要状态变化，强制实时更新: {hole_id}")
                self._apply_single_update(hole_id, status)
            else:
                # 正常期间：使用批量更新（但延迟大大减少）
                print(f"📦 [全景图] 使用优化的批量更新（{self.batch_update_interval}ms延迟）")
                
                # 将状态更新加入缓存
                self.pending_status_updates[hole_id] = status
                
                # 重启批量更新定时器
                if self.batch_update_timer.isActive():
                    print(f"⏹️ [全景图] 停止现有定时器")
                    self.batch_update_timer.stop()
                
                print(f"⏰ [全景图] 启动批量更新定时器: {self.batch_update_interval}ms，当前队列: {len(self.pending_status_updates)}个")
                self.batch_update_timer.start(self.batch_update_interval)
                
                # 验证定时器是否真的启动了
                if self.batch_update_timer.isActive():
                    print(f"✅ [全景图] 定时器已激活，{self.batch_update_timer.remainingTime()}ms 后执行")
                else:
                    print(f"❌ [全景图] 定时器启动失败!")
                
                print(f"🔄 [全景图] 缓存中现有 {len(self.pending_status_updates)} 个待更新")
    
    def _should_force_immediate_update(self, hole_id: str, new_status) -> bool:
        """判断是否应该强制立即更新（备用机制）"""
        try:
            from src.core_business.models.hole_data import HoleStatus
            
            # 如果是从pending到其他状态的变化，强制立即更新
            if hasattr(new_status, 'value'):
                status_value = new_status.value
            else:
                status_value = str(new_status)
            
            # 重要状态变化：pending -> qualified/defective/等
            important_statuses = ['qualified', 'defective', 'blind', 'tie_rod']
            is_important_change = status_value.lower() in important_statuses
            
            if is_important_change:
                print(f"🎯 [修复] 检测到重要状态变化: {hole_id} -> {status_value}")
                return True
            
            # 检查队列长度，如果队列太长也强制立即更新
            queue_length = len(self.pending_status_updates)
            if queue_length > 20:  # 队列超过20个项目
                print(f"🚨 [修复] 队列过长({queue_length})，强制立即更新: {hole_id}")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ [修复] 强制更新检查失败: {e}")
            return True  # 出错时强制立即更新，保证可靠性
    
    def _check_simulation_status(self) -> bool:
        """检查当前是否在模拟期间（修复版本）"""
        print(f"🔍 [修复] 开始检查模拟状态...")
        
        try:
            # 【修复1】更全面的父级搜索：检查所有可能的模拟状态属性
            main_window = self.parent()
            parent_chain = []
            
            while main_window:
                parent_chain.append(type(main_window).__name__)
                
                # 【修复2】检查所有模拟相关属性，而不仅仅是 simulation_running
                has_sim_v1 = hasattr(main_window, 'simulation_running')
                has_sim_v2 = hasattr(main_window, 'simulation_running_v2')
                
                if has_sim_v1 or has_sim_v2:
                    print(f"🔍 [修复] 找到模拟窗口: {type(main_window).__name__}")
                    print(f"🔍 [修复] 具有属性: V1={has_sim_v1}, V2={has_sim_v2}")
                    break
                    
                main_window = main_window.parent()
            
            print(f"🔍 [修复] 父级链路: {' -> '.join(parent_chain)}")
            
            if main_window:
                # 【修复3】更安全的属性获取，同时检查V1和V2
                simulation_v1 = getattr(main_window, 'simulation_running', False)
                simulation_v2 = getattr(main_window, 'simulation_running_v2', False)
                is_running = simulation_v1 or simulation_v2
                
                print(f"🔍 [修复] 主窗口类型: {type(main_window).__name__}")
                print(f"🔍 [修复] simulation_running (V1): {simulation_v1}")
                print(f"🔍 [修复] simulation_running_v2 (V2): {simulation_v2}")
                print(f"🔍 [修复] 最终模拟状态: {is_running}")
                
                if is_running:
                    print(f"🎯 [修复] ✅ 确认模拟运行中: V1={simulation_v1}, V2={simulation_v2}")
                else:
                    print(f"⏸️ [修复] ❌ 模拟未运行: V1={simulation_v1}, V2={simulation_v2}")
                    
                return is_running
            else:
                # 【修复4】如果找不到主窗口，尝试全局搜索
                print(f"⚠️ [修复] 无法通过parent找到主窗口，尝试全局搜索...")
                print(f"🔍 [修复] 完整父级链路: {' -> '.join(parent_chain) if parent_chain else '无父级'}")
                
                # 尝试通过QApplication查找主窗口
                try:
                    from PySide6.QtWidgets import QApplication
                    app = QApplication.instance()
                    if app:
                        for widget in app.allWidgets():
                            if hasattr(widget, 'simulation_running_v2') or hasattr(widget, 'simulation_running'):
                                simulation_v1 = getattr(widget, 'simulation_running', False)
                                simulation_v2 = getattr(widget, 'simulation_running_v2', False)
                                is_running = simulation_v1 or simulation_v2
                                
                                print(f"🔍 [修复] 全局搜索找到: {type(widget).__name__}")
                                print(f"🔍 [修复] V1={simulation_v1}, V2={simulation_v2}, 运行中={is_running}")
                                
                                if is_running:
                                    print(f"🎯 [修复] ✅ 全局搜索确认模拟运行中")
                                    return True
                except Exception as global_e:
                    print(f"❌ [修复] 全局搜索失败: {global_e}")
                
                print(f"⚠️ [修复] 所有搜索方法均失败，假设非模拟期间")
                return False
                
        except Exception as e:
            print(f"❌ [修复] 模拟状态检查失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _apply_single_update(self, hole_id: str, status):
        """立即应用单个孔位状态更新"""
        print(f"⚡ [全景图] 立即更新孔位: {hole_id} -> {status.value if hasattr(status, 'value') else status}")
        
        try:
            # 获取状态颜色
            from src.core_business.models.hole_data import HoleStatus
            from PySide6.QtGui import QColor, QBrush, QPen
            
            color_map = {
                HoleStatus.PENDING: QColor(200, 200, 200),      # 灰色
                HoleStatus.QUALIFIED: QColor(76, 175, 80),      # 绿色
                HoleStatus.DEFECTIVE: QColor(244, 67, 54),      # 红色
                HoleStatus.PROCESSING: QColor(33, 150, 243),    # 蓝色
                HoleStatus.BLIND: QColor(255, 193, 7),          # 黄色
                HoleStatus.TIE_ROD: QColor(156, 39, 176)        # 紫色
            }
            
            # 转换状态
            if isinstance(status, str):
                try:
                    status = HoleStatus(status)
                except ValueError:
                    status = HoleStatus.PENDING
            
            color = color_map.get(status, QColor(200, 200, 200))
            
            # 立即更新图形项
            if hasattr(self.panorama_view, 'hole_items') and hole_id in self.panorama_view.hole_items:
                hole_item = self.panorama_view.hole_items[hole_id]
                hole_item.setBrush(QBrush(color))
                hole_item.setPen(QPen(color.darker(120), 1))
                
                # 强制立即重绘
                hole_item.update()
                self.panorama_view.update()
                print(f"✅ [全景图] 立即更新完成: {hole_id}")
            else:
                print(f"❌ [全景图] 未找到孔位图形项: {hole_id}")
                
        except Exception as e:
            print(f"❌ [全景图] 立即更新失败: {e}")
    
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
                from src.core_business.models.hole_data import HoleStatus
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
            # 清空缓存
            self.pending_status_updates.clear()
    
    def batch_update_hole_status(self, status_updates: Dict[str, any]):
        """直接批量更新多个孔位状态"""
        print(f"🚀 [全景图] 直接批量更新 {len(status_updates)} 个孔位")
        
        # 合并到待更新缓存
        self.pending_status_updates.update(status_updates)
        
        # 立即应用更新
        self._apply_batch_updates()
    
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
    
    def _verify_rendering(self):
        """验证渲染结果"""
        print("🔍 [验证] 开始验证渲染结果...")
        
        # 检查主视图
        if hasattr(self, 'graphics_view') and self.graphics_view:
            scene_items = len(self.graphics_view.scene.items())
            hole_items = len(self.graphics_view.hole_items)
            print(f"🔍 [主视图] 场景项: {scene_items}, 孔位项: {hole_items}")
            
            if hole_items == 0:
                print("❌ [主视图] 没有孔位被渲染!")
            else:
                print(f"✅ [主视图] {hole_items} 个孔位已渲染")
        
        # 检查小型全景图
        if hasattr(self, 'mini_panorama') and self.mini_panorama:
            if hasattr(self.mini_panorama, 'scene'):
                mini_items = len(self.mini_panorama.scene.items())
                print(f"🔍 [小型全景图] 场景项: {mini_items}")
                
                if mini_items == 0:
                    print("❌ [小型全景图] 没有内容被渲染!")
                else:
                    print(f"✅ [小型全景图] {mini_items} 个项已渲染")
        
        # 检查状态标签
        if hasattr(self, 'status_label') and self.status_label:
            is_visible = self.status_label.isVisible()
            print(f"🔍 [状态标签] 可见: {is_visible}")
            
            if is_visible:
                print("⚠️ [状态标签] 仍然可见，尝试再次隐藏")
                self.status_label.hide()
                self.status_label.setVisible(False)
    
    

    def _init_creation_lock(self):
        """初始化扇形创建锁"""
        if not hasattr(self, '_creation_locks'):
            self._creation_locks = {
                'sector_creation': False,
                'view_switching': False,
                'panorama_setup': False
            }
    
    def _acquire_lock(self, lock_type: str) -> bool:
        """获取锁"""
        if not hasattr(self, '_creation_locks'):
            self._init_creation_lock()
        
        if self._creation_locks.get(lock_type, False):
            return False
        
        self._creation_locks[lock_type] = True
        return True
    
    def _release_lock(self, lock_type: str):
        """释放锁"""
        if hasattr(self, '_creation_locks'):
            self._creation_locks[lock_type] = False


class DynamicSectorView(QGraphicsView):
    """动态扇形视图类 - 修复缺失的类定义"""
    
    sector_clicked = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_sector = None
        self.sector_items = {}
    
    def set_sector(self, sector_id: int):
        """设置当前扇形"""
        self.current_sector = sector_id
    
    def add_sector_item(self, sector_id: int, item: QGraphicsItem):
        """添加扇形项"""
        self.sector_items[sector_id] = item
        if self.scene():
            self.scene().addItem(item)
    
    def clear_sectors(self):
        """清理所有扇形"""
        if self.scene():
            for item in self.sector_items.values():
                self.scene().removeItem(item)
        self.sector_items.clear()
