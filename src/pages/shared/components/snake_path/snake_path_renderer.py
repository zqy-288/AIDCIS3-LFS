"""
蛇形路径渲染器 - 适配A/B侧编号系统
在图形界面中可视化显示检测路径的连接线，支持列式蛇形扫描

核心功能：
1. 按A/B侧分组（y>0为A侧，y<0为B侧）
2. 在每侧内按列进行蛇形扫描
3. 奇数列（C001,C003...）：从R001→R164（升序）
4. 偶数列（C002,C004...）：从R164→R001（降序）
5. 渲染检测路径的连接线和移动轨迹

📝 注意：此模块仍在使用中，但建议逐步迁移到 
    src.modules.panorama_view.snake_path_renderer 新架构
"""

import re
import math
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal, QPointF, QRectF, Qt
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QPainterPath, QFont
from PySide6.QtWidgets import QGraphicsItem, QGraphicsPathItem, QGraphicsTextItem

from src.core_business.models.hole_data import HoleData, HoleCollection
from src.core_business.graphics.sector_controllers import UnifiedLogger


class PathStrategy(Enum):
    """蛇形路径策略"""
    LABEL_BASED = "label_based"      # 先处理A侧，再处理B侧
    SPATIAL_SNAKE = "spatial_snake"  # 纯空间位置蛇形扫描
    HYBRID = "hybrid"                # 混合策略（A/B分组+空间优化）
    INTERVAL_FOUR_S_SHAPE = "interval_four_s_shape"  # 间隔4列S形扫描策略


class PathRenderStyle(Enum):
    """路径渲染样式"""
    SIMPLE_LINE = "simple_line"           # 简单直线连接
    CURVED_ARROW = "curved_arrow"         # 曲线箭头
    SNAKE_FLOW = "snake_flow"             # 蛇形流动线
    AB_GROUPED = "ab_grouped"             # A/B侧分组显示
    NUMBERED_SEQUENCE = "numbered_sequence"  # 编号序列显示


class PathSegmentType(Enum):
    """路径段类型"""
    A_SIDE_NORMAL = "a_side_normal"       # A侧正常段
    B_SIDE_NORMAL = "b_side_normal"       # B侧正常段
    COLUMN_RETURN = "column_return"       # 列内返回段
    CROSS_COLUMN = "cross_column"         # 跨列段
    CROSS_SIDE = "cross_side"             # 跨A/B侧段
    COMPLETED = "completed"               # 已完成段
    CURRENT = "current"                   # 当前段


@dataclass
class HolePosition:
    """孔位位置信息"""
    hole_id: str
    center_x: float
    center_y: float
    column_num: int  # 列号 (C001 -> 1)
    row_num: int     # 行号 (R001 -> 1)
    side: str        # 'A' 或 'B'


@dataclass
class HolePair:
    """孔位对数据结构 - 用于间隔4列检测"""
    holes: List[HoleData]  # 1-2个孔位
    is_pair: bool = True   # 是否是配对（False表示单个孔位）
    
    @property
    def primary_hole(self) -> HoleData:
        """主要孔位（用于扇形判断）"""
        return self.holes[0]
    
    @property
    def hole_count(self) -> int:
        """孔位数量"""
        return len(self.holes)
    
    def get_hole_ids(self) -> List[str]:
        """获取所有孔位ID"""
        return [hole.hole_id for hole in self.holes]


@dataclass
class PathSegment:
    """路径段数据"""
    start_hole: HolePosition
    end_hole: HolePosition
    segment_type: PathSegmentType
    sequence_number: int
    distance: float = 0.0
    is_snake_direction: bool = True  # 是否为蛇形方向
    metadata: Dict[str, Any] = None


@dataclass
class PathStyleConfig:
    """路径样式配置"""
    # 基础样式
    line_width: float = 2.0
    line_color: QColor = QColor(50, 150, 250)
    arrow_size: float = 8.0
    
    # 不同类型的颜色
    normal_color: QColor = QColor(50, 150, 250)     # 蓝色
    return_color: QColor = QColor(255, 165, 0)      # 橙色
    jump_color: QColor = QColor(255, 50, 50)        # 红色
    completed_color: QColor = QColor(100, 200, 100) # 绿色
    current_color: QColor = QColor(255, 255, 0)     # 黄色
    
    # 文字样式
    show_sequence_numbers: bool = True
    number_font_size: int = 10
    number_color: QColor = QColor(0, 0, 0)
    
    # 动画样式
    enable_animation: bool = False
    animation_speed: float = 1.0


class SnakePathRenderer(QObject):
    """
    蛇形路径渲染器
    
    功能：
    1. 解析蛇形路径数据
    2. 渲染路径连接线
    3. 支持多种视觉样式
    4. 提供交互功能
    """
    
    # 信号
    path_rendered = Signal(int)  # 路径渲染完成，参数为路径段数量
    segment_clicked = Signal(PathSegment)  # 路径段被点击
    path_hover = Signal(Optional[PathSegment])  # 路径段悬停
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = UnifiedLogger("SnakePathRenderer")
        
        # 路径数据
        self.path_segments: List[PathSegment] = []
        self.hole_positions: Dict[str, QPointF] = {}
        self.hole_collection: Optional[HoleCollection] = None
        
        # 渲染配置
        self.style_config = PathStyleConfig()
        self.render_style = PathRenderStyle.SIMPLE_LINE
        
        # 图形项缓存
        self.path_items: List[QGraphicsItem] = []
        self.graphics_scene = None
        
        # 状态
        self.is_visible = True
        self.current_sequence = 0
        
    def set_graphics_scene(self, scene):
        """设置图形场景"""
        self.graphics_scene = scene
        self.logger.info("设置图形场景", "🎨")
    
    def set_hole_collection(self, hole_collection: HoleCollection):
        """设置孔位集合，解析A/B侧编号信息"""
        self.hole_collection = hole_collection  # 保存引用
        self.hole_positions.clear()
        
        for hole_id, hole in hole_collection.holes.items():
            hole_pos = self._parse_hole_position(hole)
            if hole_pos:
                self.hole_positions[hole_id] = hole_pos
        
        self.logger.info(f"解析孔位位置: {len(self.hole_positions)} 个孔位", "📍")
        
        # 按A/B侧统计
        a_side_count = sum(1 for pos in self.hole_positions.values() if pos.side == 'A')
        b_side_count = sum(1 for pos in self.hole_positions.values() if pos.side == 'B')
        self.logger.info(f"A侧: {a_side_count}个, B侧: {b_side_count}个", "🔢")
    
    def _parse_hole_position(self, hole: HoleData) -> Optional[HolePosition]:
        """解析孔位位置信息，支持A/B侧编号格式"""
        try:
            # 解析编号格式：AC097R001 或 BC097R001
            if hasattr(hole, 'hole_id') and hole.hole_id:
                # 匹配格式：[AB]C(\d{3})R(\d{3})
                match = re.match(r'([AB])C(\d{3})R(\d{3})', hole.hole_id)
                if match:
                    side = match.group(1)
                    column_num = int(match.group(2))
                    row_num = int(match.group(3))
                    
                    return HolePosition(
                        hole_id=hole.hole_id,
                        center_x=hole.center_x,
                        center_y=hole.center_y,
                        column_num=column_num,
                        row_num=row_num,
                        side=side
                    )
            
            # 如果没有标准编号，根据位置推断A/B侧
            side = 'A' if hole.center_y > 0 else 'B'
            
            # 尝试从位置推断列号和行号（简化逻辑）
            estimated_col = max(1, int(hole.center_x / 10) + 1)  # 假设10mm列间距
            estimated_row = max(1, int(abs(hole.center_y) / 10) + 1)  # 假设10mm行间距
            
            return HolePosition(
                hole_id=hole.hole_id or f"hole_{hole.center_x}_{hole.center_y}",
                center_x=hole.center_x,
                center_y=hole.center_y,
                column_num=estimated_col,
                row_num=estimated_row,
                side=side
            )
            
        except Exception as e:
            self.logger.warning(f"解析孔位{hole.hole_id}失败: {e}", "⚠️")
            return None
    
    def generate_snake_path(self, strategy: PathStrategy = PathStrategy.HYBRID):
        """
        生成蛇形路径
        
        Args:
            strategy: 路径策略
            
        Returns:
            对于INTERVAL_FOUR_S_SHAPE策略: List[HolePair] - 检测单元列表
            对于其他策略: List[str] - 按检测顺序排列的孔位ID列表
        """
        if not self.hole_positions:
            self.logger.warning("没有孔位数据，无法生成路径", "⚠️")
            return []
        
        if strategy == PathStrategy.HYBRID:
            return self._generate_hybrid_path()
        elif strategy == PathStrategy.LABEL_BASED:
            return self._generate_label_based_path()
        elif strategy == PathStrategy.SPATIAL_SNAKE:
            return self._generate_spatial_snake_path()
        elif strategy == PathStrategy.INTERVAL_FOUR_S_SHAPE:
            return self._generate_interval_four_path()
        else:
            return self._generate_hybrid_path()
    
    def _generate_hybrid_path(self) -> List[str]:
        """生成混合策略路径：A/B侧分组 + 列式蛇形扫描"""
        path = []
        
        # 按A/B侧分组
        a_side_holes = [pos for pos in self.hole_positions.values() if pos.side == 'A']
        b_side_holes = [pos for pos in self.hole_positions.values() if pos.side == 'B']
        
        self.logger.info(f"HYBRID策略：A侧{len(a_side_holes)}个，B侧{len(b_side_holes)}个", "🐍")
        
        # 先处理A侧
        if a_side_holes:
            a_path = self._generate_side_snake_path(a_side_holes, 'A')
            path.extend(a_path)
            self.logger.info(f"A侧路径生成完成：{len(a_path)}个孔位", "🅰️")
        
        # 再处理B侧
        if b_side_holes:
            b_path = self._generate_side_snake_path(b_side_holes, 'B')
            path.extend(b_path)
            self.logger.info(f"B侧路径生成完成：{len(b_path)}个孔位", "🅱️")
        
        return path
    
    def _generate_side_snake_path(self, holes: List[HolePosition], side: str) -> List[str]:
        """在单侧内生成蛇形路径"""
        if not holes:
            return []
        
        # 按列分组
        columns = {}
        for hole in holes:
            col_num = hole.column_num
            if col_num not in columns:
                columns[col_num] = []
            columns[col_num].append(hole)
        
        # 按列号排序
        sorted_columns = sorted(columns.keys())
        path = []
        
        for i, col_num in enumerate(sorted_columns):
            column_holes = columns[col_num]
            
            # 按行号排序
            if side == 'A':
                # A侧：R001在中心附近（较小的y值）
                column_holes.sort(key=lambda h: h.row_num)
            else:
                # B侧：R001在中心附近（较小的|y|值）  
                column_holes.sort(key=lambda h: h.row_num)
            
            # 蛇形逻辑：奇数列升序，偶数列降序
            is_odd_column = (col_num % 2 == 1)
            
            if is_odd_column:
                # 奇数列：R001→R164（升序）
                ordered_holes = column_holes
                direction = "⬇️"
            else:
                # 偶数列：R164→R001（降序）
                ordered_holes = column_holes[::-1]
                direction = "⬆️"
            
            # 添加到路径
            hole_ids = [hole.hole_id for hole in ordered_holes]
            path.extend(hole_ids)
            
            self.logger.debug(f"{side}侧 C{col_num:03d}: {direction} {len(hole_ids)}个孔位", "📊")
        
        return path
    
    def _generate_label_based_path(self) -> List[str]:
        """生成基于标签的路径：完全按A/B分组"""
        # 简化实现，直接调用混合策略
        return self._generate_hybrid_path()
    
    def _generate_spatial_snake_path(self) -> List[str]:
        """生成基于空间位置的蛇形路径"""
        holes = list(self.hole_positions.values())
        if not holes:
            return []
        
        # 按X坐标分列
        holes.sort(key=lambda h: (h.center_x, h.center_y))
        
        # 简化的空间蛇形算法
        path = []
        columns = {}
        
        # 按X坐标分组（允许一定误差）
        for hole in holes:
            col_key = round(hole.center_x / 10) * 10  # 10mm精度
            if col_key not in columns:
                columns[col_key] = []
            columns[col_key].append(hole)
        
        # 蛇形扫描
        sorted_col_keys = sorted(columns.keys())
        for i, col_key in enumerate(sorted_col_keys):
            column_holes = columns[col_key]
            
            # 按Y坐标排序
            column_holes.sort(key=lambda h: h.center_y)
            
            # 奇偶列交替方向
            if i % 2 == 0:
                ordered_holes = column_holes  # 升序
            else:
                ordered_holes = column_holes[::-1]  # 降序
            
            path.extend([hole.hole_id for hole in ordered_holes])
        
        return path
    
    def _generate_interval_four_path(self) -> List[HolePair]:
        """生成间隔4列S形路径：专用于第一象限间隔4列配对检测"""
        # 首先获取第一象限的孔位
        sector_1_holes = self._get_sector_1_holes()
        if not sector_1_holes:
            self.logger.warning("第一象限没有找到孔位", "⚠️")
            return []
            
        self.logger.info(f"第一象限找到 {len(sector_1_holes)} 个孔位", "🎯")
        
        # 按行分组
        holes_by_row = self._group_holes_by_row(sector_1_holes)
        
        # 生成间隔4列的孔位对
        hole_pairs = self._create_interval_four_pairs(holes_by_row)
        
        # 记录生成结果
        total_holes = sum(len(pair.holes) for pair in hole_pairs)
        self.logger.info(f"生成间隔4列路径: {len(hole_pairs)} 个检测单元，{total_holes} 个孔位", "🐍")
        
        return hole_pairs
    
    def _get_sector_1_holes(self) -> List[HolePosition]:
        """获取第一象限的孔位"""
        sector_1_holes = []
        
        # 遍历所有孔位，筛选第一象限的孔位
        for hole_pos in self.hole_positions.values():
            # 第一象限：右上角，x>=0, y<=0 (Qt坐标系)
            if hole_pos.center_x >= 0 and hole_pos.center_y <= 0:
                sector_1_holes.append(hole_pos)
        
        return sector_1_holes
    
    def _group_holes_by_row(self, holes: List[HolePosition]) -> Dict[int, List[HolePosition]]:
        """按行号分组孔位"""
        holes_by_row = {}
        
        for hole in holes:
            row = hole.row_num
            if row not in holes_by_row:
                holes_by_row[row] = []
            holes_by_row[row].append(hole)
        
        # 每行内按列号排序
        for row in holes_by_row:
            holes_by_row[row].sort(key=lambda h: h.column_num)
            
        return holes_by_row
    
    def _create_interval_four_pairs(self, holes_by_row: Dict[int, List[HolePosition]]) -> List[HolePair]:
        """创建间隔4列的孔位对"""
        hole_pairs = []
        
        # 按行号降序处理（从最上面的行开始，如R164, R163, ...）
        sorted_rows = sorted(holes_by_row.keys(), reverse=True)
        
        for row_index, row_num in enumerate(sorted_rows):
            row_holes = holes_by_row[row_num]
            
            # S形路径：奇数行从左到右，偶数行从右到左
            if row_index % 2 == 1:  # 偶数行（R163, R161, ...）从右到左
                row_holes = list(reversed(row_holes))
            
            # 生成间隔4列的配对
            row_pairs = self._create_row_interval_pairs(row_holes, row_num)
            hole_pairs.extend(row_pairs)
            
        return hole_pairs
    
    def _create_row_interval_pairs(self, row_holes: List[HolePosition], row_num: int) -> List[HolePair]:
        """在单行内创建间隔4列的配对"""
        pairs = []
        processed_indices = set()
        
        # 创建孔位映射（列号到孔位的映射）
        holes_by_col = {hole.column_num: hole for hole in row_holes}
        
        # 按列号排序
        sorted_cols = sorted(holes_by_col.keys())
        
        i = 0
        while i < len(sorted_cols):
            if i in processed_indices:
                i += 1
                continue
                
            current_col = sorted_cols[i]
            current_hole_pos = holes_by_col[current_col]
            
            # 寻找间隔4列的配对孔位
            target_col = current_col + 4
            pair_hole_pos = holes_by_col.get(target_col)
            
            if pair_hole_pos:
                # 找到配对，创建孔位对
                hole1 = self._position_to_hole_data(current_hole_pos)
                hole2 = self._position_to_hole_data(pair_hole_pos)
                
                if hole1 and hole2:
                    pair = HolePair(holes=[hole1, hole2], is_pair=True)
                    pairs.append(pair)
                    processed_indices.add(i)
                    
                    # 找到并标记配对孔位的索引
                    pair_index = None
                    for j, col in enumerate(sorted_cols):
                        if col == target_col:
                            pair_index = j
                            break
                    if pair_index is not None:
                        processed_indices.add(pair_index)
                    
                    self.logger.debug(f"R{row_num}行创建配对: {current_hole_pos.hole_id} + {pair_hole_pos.hole_id}")
                    i += 1
                    continue
            
            # 无法配对，单独处理
            hole = self._position_to_hole_data(current_hole_pos)
            if hole:
                pair = HolePair(holes=[hole], is_pair=False)
                pairs.append(pair)
                self.logger.debug(f"R{row_num}行单独处理: {current_hole_pos.hole_id}")
            
            i += 1
            
        return pairs
    
    def _position_to_hole_data(self, hole_pos: HolePosition) -> Optional[HoleData]:
        """将HolePosition转换为HoleData"""
        if not self.hole_collection:
            return None
            
        # 通过hole_id查找对应的HoleData
        return self.hole_collection.holes.get(hole_pos.hole_id)
    
    def set_path_data(self, snake_path: List[str]):
        """
        设置蛇形路径数据并生成渲染段
        
        Args:
            snake_path: 按检测顺序排列的孔位ID列表
        """
        self.path_segments.clear()
        
        if len(snake_path) < 2:
            self.logger.warning("路径数据不足，至少需要2个孔位", "⚠️")
            return
        
        # 生成路径段
        for i in range(len(snake_path) - 1):
            start_hole_id = snake_path[i]
            end_hole_id = snake_path[i + 1]
            
            # 检查孔位是否存在
            if start_hole_id not in self.hole_positions or end_hole_id not in self.hole_positions:
                continue
            
            start_pos = self.hole_positions[start_hole_id]
            end_pos = self.hole_positions[end_hole_id]
            
            # 分析路径段类型
            segment_type = self._classify_segment_type(start_pos, end_pos)
            distance = self._calculate_distance_between_positions(start_pos, end_pos)
            is_snake_direction = self._is_snake_direction(start_pos, end_pos)
            
            segment = PathSegment(
                start_hole=start_pos,
                end_hole=end_pos,
                segment_type=segment_type,
                sequence_number=i + 1,
                distance=distance,
                is_snake_direction=is_snake_direction,
                metadata={'path_index': i}
            )
            
            self.path_segments.append(segment)
        
        self.logger.info(f"生成路径段: {len(self.path_segments)} 段", "🛤️")
    
    def _classify_segment_type(self, start_pos: HolePosition, end_pos: HolePosition) -> PathSegmentType:
        """分类路径段类型"""
        # 判断是否跨A/B侧
        if start_pos.side != end_pos.side:
            return PathSegmentType.CROSS_SIDE
        
        # 判断是否跨列
        if start_pos.column_num != end_pos.column_num:
            return PathSegmentType.CROSS_COLUMN
        
        # 判断是否为列内返回（反向移动）
        if start_pos.column_num == end_pos.column_num:
            if abs(start_pos.row_num - end_pos.row_num) > 1:
                return PathSegmentType.COLUMN_RETURN
        
        # 根据侧别确定正常段类型
        if start_pos.side == 'A':
            return PathSegmentType.A_SIDE_NORMAL
        else:
            return PathSegmentType.B_SIDE_NORMAL
    
    def _calculate_distance_between_positions(self, start_pos: HolePosition, end_pos: HolePosition) -> float:
        """计算两个孔位之间的距离"""
        dx = end_pos.center_x - start_pos.center_x
        dy = end_pos.center_y - start_pos.center_y
        return (dx * dx + dy * dy) ** 0.5
    
    def _is_snake_direction(self, start_pos: HolePosition, end_pos: HolePosition) -> bool:
        """判断是否为蛇形方向"""
        # 同列内的移动认为是蛇形方向
        if start_pos.column_num == end_pos.column_num:
            return True
        
        # 相邻列的跨列移动也是蛇形方向
        if abs(start_pos.column_num - end_pos.column_num) == 1:
            return True
        
        # 其他情况认为是跳跃
        return False
    
    def render_paths(self):
        """渲染所有路径"""
        if not self.graphics_scene:
            self.logger.warning("未设置图形场景，无法渲染", "⚠️")
            return
        
        # 清除旧的路径项
        self.clear_paths()
        
        # 根据样式渲染路径
        if self.render_style == PathRenderStyle.SIMPLE_LINE:
            self._render_simple_lines()
        elif self.render_style == PathRenderStyle.CURVED_ARROW:
            self._render_curved_arrows()
        elif self.render_style == PathRenderStyle.NUMBERED_SEQUENCE:
            self._render_numbered_sequence()
        else:
            self._render_simple_lines()
        
        self.logger.info(f"渲染路径完成: {len(self.path_items)} 个图形项", "✅")
        self.path_rendered.emit(len(self.path_segments))
    
    def render_path(self, holes: List[HoleData]):
        """便捷方法：设置孔位并渲染路径
        
        Args:
            holes: 按顺序排列的孔位列表
        """
        if not holes:
            self.logger.warning("没有孔位数据，无法渲染路径", "⚠️")
            return
            
        # 创建HoleCollection并设置
        holes_dict = {hole.hole_id: hole for hole in holes}
        hole_collection = HoleCollection(holes=holes_dict)
        self.set_hole_collection(hole_collection)
        
        # 生成路径数据
        path_ids = [hole.hole_id for hole in holes]
        self.set_path_data(path_ids)
        
        # 渲染路径
        self.render_paths()
        
    def render_detection_units(self, detection_units: List):
        """渲染检测单元路径（支持HolePair和HoleData）
        
        Args:
            detection_units: 检测单元列表，包含HolePair和HoleData对象
        """
        if not detection_units:
            self.logger.warning("没有检测单元数据，无法渲染路径", "⚠️")
            return
            
        # 清除现有路径
        self.clear_path()
        
        # 渲染检测单元间的连接路径
        self._render_detection_unit_connections(detection_units)
        
        # 渲染孔位对内部连接
        self._render_hole_pair_internal_connections(detection_units)
        
    def _render_detection_unit_connections(self, detection_units: List):
        """渲染检测单元间的连接路径"""
        if len(detection_units) < 2:
            return
            
        for i in range(len(detection_units) - 1):
            current_unit = detection_units[i]
            next_unit = detection_units[i + 1]
            
            # 获取连接点
            current_pos = self._get_unit_connection_point(current_unit, 'end')
            next_pos = self._get_unit_connection_point(next_unit, 'start')
            
            if current_pos and next_pos:
                # 创建连接线
                connection_item = self._create_unit_connection_line(current_pos, next_pos, i)
                if connection_item:
                    self.graphics_scene.addItem(connection_item)
                    self.path_items.append(connection_item)
                    
    def _render_hole_pair_internal_connections(self, detection_units: List):
        """渲染孔位对内部连接"""
        for i, unit in enumerate(detection_units):
            if isinstance(unit, HolePair) and unit.is_pair and len(unit.holes) == 2:
                # 渲染孔位对内部连接
                hole1, hole2 = unit.holes[0], unit.holes[1]
                internal_connection = self._create_hole_pair_internal_line(hole1, hole2, i)
                if internal_connection:
                    self.graphics_scene.addItem(internal_connection)
                    self.path_items.append(internal_connection)
                    
    def _get_unit_connection_point(self, unit, point_type: str) -> Optional[QPointF]:
        """获取检测单元的连接点
        
        Args:
            unit: 检测单元（HolePair或HoleData）
            point_type: 'start' 或 'end'
        """
        if isinstance(unit, HolePair):
            # 对于孔位对，使用主要孔位的位置
            hole = unit.primary_hole
        else:
            hole = unit
            
        if hole:
            return QPointF(hole.center_x, hole.center_y)
        return None
        
    def _create_unit_connection_line(self, start_pos: QPointF, end_pos: QPointF, sequence: int) -> Optional[QGraphicsPathItem]:
        """创建检测单元间连接线"""
        path = QPainterPath()
        path.moveTo(start_pos)
        path.lineTo(end_pos)
        
        path_item = QGraphicsPathItem(path)
        
        # 设置检测单元连接线样式（蓝色，较粗）
        pen = QPen(QColor(33, 150, 243), 3)  # 蓝色，3像素宽
        pen.setStyle(Qt.SolidLine)
        path_item.setPen(pen)
        path_item.setZValue(-1)
        
        return path_item
        
    def _create_hole_pair_internal_line(self, hole1: HoleData, hole2: HoleData, sequence: int) -> Optional[QGraphicsPathItem]:
        """创建孔位对内部连接线"""
        start_pos = QPointF(hole1.center_x, hole1.center_y)
        end_pos = QPointF(hole2.center_x, hole2.center_y)
        
        path = QPainterPath()
        path.moveTo(start_pos)
        path.lineTo(end_pos)
        
        path_item = QGraphicsPathItem(path)
        
        # 设置孔位对内部连接线样式（绿色，中等粗细，虚线）
        pen = QPen(QColor(76, 175, 80), 2)  # 绿色，2像素宽
        pen.setStyle(Qt.DashLine)
        path_item.setPen(pen)
        path_item.setZValue(-0.5)  #较检测单元连接线更高层
        
        return path_item
        
    def update_detection_unit_progress(self, current_index: int, detection_units: List):
        """更新检测单元进度可视化
        
        Args:
            current_index: 当前检测单元索引
            detection_units: 检测单元列表
        """
        if not self.graphics_scene:
            return
            
        # 高亮当前检测单元
        if 0 <= current_index < len(detection_units):
            current_unit = detection_units[current_index]
            self._highlight_detection_unit(current_unit, is_current=True)
            
        # 将之前的单元标记为已完成
        for i in range(current_index):
            if i < len(detection_units):
                completed_unit = detection_units[i]
                self._highlight_detection_unit(completed_unit, is_current=False)
                
    def _highlight_detection_unit(self, unit, is_current: bool = True):
        """高亮检测单元
        
        Args:
            unit: 检测单元（HolePair或HoleData）
            is_current: 是否为当前单元
        """
        holes_to_highlight = []
        
        if isinstance(unit, HolePair):
            holes_to_highlight = unit.holes
        else:
            holes_to_highlight = [unit]
            
        # 高亮相关孔位
        for hole in holes_to_highlight:
            self._highlight_hole_in_scene(hole, is_current)
            
    def _highlight_hole_in_scene(self, hole: HoleData, is_current: bool):
        """在场景中高亮孔位
        
        Args:
            hole: 要高亮的孔位
            is_current: 是否为当前正在检测的孔位
        """
        if not self.graphics_scene:
            return
            
        # 查找对应的图形项
        for item in self.graphics_scene.items():
            if hasattr(item, 'data') and item.data(0) == hole.hole_id:
                if is_current:
                    # 当前检测：黄色高亮
                    highlight_color = QColor(255, 193, 7)  # 黄色
                    pen_width = 4
                    item.setZValue(10)  # 置于顶层
                else:
                    # 已完成检测：恢复原状态或标记为已处理
                    # 这里可以根据检测状态设置不同颜色
                    highlight_color = QColor(158, 158, 158)  # 灰色
                    pen_width = 2
                    item.setZValue(0)
                    
                # 设置高亮样式
                pen = QPen(highlight_color, pen_width)
                if hasattr(item, 'setPen'):
                    item.setPen(pen)
                break
    
    def _render_simple_lines(self):
        """渲染简单直线路径"""
        for segment in self.path_segments:
            line_item = self._create_line_item(segment)
            if line_item:
                self.graphics_scene.addItem(line_item)
                self.path_items.append(line_item)
                
                # 添加序号标签
                if self.style_config.show_sequence_numbers:
                    number_item = self._create_sequence_number(segment)
                    if number_item:
                        self.graphics_scene.addItem(number_item)
                        self.path_items.append(number_item)
    
    def _render_curved_arrows(self):
        """渲染曲线箭头路径"""
        for segment in self.path_segments:
            arrow_item = self._create_curved_arrow_item(segment)
            if arrow_item:
                self.graphics_scene.addItem(arrow_item)
                self.path_items.append(arrow_item)
    
    def _render_numbered_sequence(self):
        """渲染带编号的序列路径"""
        self._render_simple_lines()  # 基础线条
        
        # 额外的序号显示（更醒目）
        for segment in self.path_segments:
            enhanced_number = self._create_enhanced_sequence_number(segment)
            if enhanced_number:
                self.graphics_scene.addItem(enhanced_number)
                self.path_items.append(enhanced_number)
    
    def _create_line_item(self, segment: PathSegment) -> Optional[QGraphicsPathItem]:
        """创建直线路径项"""
        start_pos = QPointF(segment.start_hole.center_x, segment.start_hole.center_y)
        end_pos = QPointF(segment.end_hole.center_x, segment.end_hole.center_y)
        
        # 创建路径
        path = QPainterPath()
        path.moveTo(start_pos)
        path.lineTo(end_pos)
        
        # 创建图形项
        path_item = QGraphicsPathItem(path)
        
        # 设置虚线样式 - 减少渲染负担
        color = self._get_dashed_line_color()  # 统一使用简单颜色
        line_width = self._get_dashed_line_width()  # 统一使用细线条
        pen = QPen(color, line_width)
        
        # 统一使用虚线样式 - 减少渲染复杂度
        pen.setStyle(Qt.DashLine)  # 统一虚线
        pen.setCapStyle(Qt.RoundCap)  # 圆形端点
        
        path_item.setPen(pen)
        
        # 设置Z值，确保路径在孔位下方
        path_item.setZValue(-1)
        
        return path_item
    
    def _create_curved_arrow_item(self, segment: PathSegment) -> Optional[QGraphicsPathItem]:
        """创建曲线箭头路径项"""
        start_pos = QPointF(segment.start_hole.center_x, segment.start_hole.center_y)
        end_pos = QPointF(segment.end_hole.center_x, segment.end_hole.center_y)
        
        # 创建曲线路径
        path = QPainterPath()
        path.moveTo(start_pos)
        
        # 计算控制点（简单的二次贝塞尔曲线）
        mid_x = (start_pos.x() + end_pos.x()) / 2
        mid_y = (start_pos.y() + end_pos.y()) / 2 - 10  # 向上弯曲
        control_point = QPointF(mid_x, mid_y)
        
        path.quadTo(control_point, end_pos)
        
        # 添加箭头
        self._add_arrow_to_path(path, end_pos, start_pos)
        
        # 创建图形项
        path_item = QGraphicsPathItem(path)
        color = self._get_segment_color(segment.segment_type)
        pen = QPen(color, self.style_config.line_width)
        path_item.setPen(pen)
        path_item.setBrush(QBrush(color))
        path_item.setZValue(-1)
        
        return path_item
    
    def _add_arrow_to_path(self, path: QPainterPath, end_pos: QPointF, start_pos: QPointF):
        """在路径末端添加箭头"""
        # 计算箭头方向
        dx = end_pos.x() - start_pos.x()
        dy = end_pos.y() - start_pos.y()
        length = (dx * dx + dy * dy) ** 0.5
        
        if length == 0:
            return
        
        # 标准化方向向量
        dx /= length
        dy /= length
        
        # 箭头参数
        arrow_length = self.style_config.arrow_size
        arrow_angle = 0.5  # 弧度
        
        # 计算箭头的两个端点
        cos_angle = dx * (-dx) - dy * (-dy)  # cos(180°)
        sin_angle_1 = dx * (-dy) + dy * (-dx) + arrow_angle  # 旋转角度
        sin_angle_2 = dx * (-dy) + dy * (-dx) - arrow_angle  # 旋转角度
        
        # 简化的箭头绘制
        arrow_p1 = QPointF(
            end_pos.x() - arrow_length * dx + arrow_length * 0.3 * dy,
            end_pos.y() - arrow_length * dy - arrow_length * 0.3 * dx
        )
        arrow_p2 = QPointF(
            end_pos.x() - arrow_length * dx - arrow_length * 0.3 * dy,
            end_pos.y() - arrow_length * dy + arrow_length * 0.3 * dx
        )
        
        # 添加箭头到路径
        path.moveTo(arrow_p1)
        path.lineTo(end_pos)
        path.lineTo(arrow_p2)
    
    def _create_sequence_number(self, segment: PathSegment) -> Optional[QGraphicsTextItem]:
        """创建序号标签"""
        # 计算标签位置（路径段中点）
        start_pos = QPointF(segment.start_hole.center_x, segment.start_hole.center_y)
        end_pos = QPointF(segment.end_hole.center_x, segment.end_hole.center_y)
        
        mid_pos = QPointF(
            (start_pos.x() + end_pos.x()) / 2,
            (start_pos.y() + end_pos.y()) / 2 - 5  # 稍微向上偏移
        )
        
        # 创建文本项
        text_item = QGraphicsTextItem(str(segment.sequence_number))
        font = QFont("Arial", self.style_config.number_font_size)
        text_item.setFont(font)
        text_item.setDefaultTextColor(self.style_config.number_color)
        text_item.setPos(mid_pos)
        text_item.setZValue(10)  # 确保在最上层
        
        return text_item
    
    def _create_enhanced_sequence_number(self, segment: PathSegment) -> Optional[QGraphicsTextItem]:
        """创建增强的序号标签（更醒目）"""
        text_item = self._create_sequence_number(segment)
        if text_item:
            # 增大字体和添加背景色
            font = QFont("Arial", self.style_config.number_font_size + 2, QFont.Bold)
            text_item.setFont(font)
            text_item.setDefaultTextColor(QColor(255, 255, 255))  # 白色文字
        
        return text_item
    
    def _get_segment_color(self, segment_type: PathSegmentType) -> QColor:
        """获取路径段颜色"""
        color_map = {
            PathSegmentType.A_SIDE_NORMAL: QColor(50, 150, 250),     # 蓝色 - A侧
            PathSegmentType.B_SIDE_NORMAL: QColor(50, 250, 150),     # 绿色 - B侧
            PathSegmentType.COLUMN_RETURN: QColor(255, 165, 0),      # 橙色 - 列内返回
            PathSegmentType.CROSS_COLUMN: QColor(255, 50, 50),       # 红色 - 跨列
            PathSegmentType.CROSS_SIDE: QColor(255, 0, 255),         # 紫色 - 跨A/B侧
            PathSegmentType.COMPLETED: QColor(100, 200, 100),        # 浅绿 - 已完成
            PathSegmentType.CURRENT: QColor(255, 255, 0),            # 黄色 - 当前
        }
        return color_map.get(segment_type, self.style_config.normal_color)
    
    def _get_dashed_line_color(self) -> QColor:
        """获取虚线颜色 - 统一使用半透明灰色减少渲染负担"""
        return QColor(128, 128, 128, 100)  # 半透明灰色
    
    def _get_dashed_line_width(self) -> float:
        """获取虚线宽度 - 使用细线条"""
        return 1.0  # 1像素细线
    
    def _get_segment_line_width(self, segment_type: PathSegmentType) -> float:
        """获取路径段线宽"""
        width_map = {
            PathSegmentType.A_SIDE_NORMAL: self.style_config.line_width,
            PathSegmentType.B_SIDE_NORMAL: self.style_config.line_width,
            PathSegmentType.COLUMN_RETURN: self.style_config.line_width + 1,  # 返回段稍粗
            PathSegmentType.CROSS_COLUMN: self.style_config.line_width + 2,   # 跨列段更粗
            PathSegmentType.CROSS_SIDE: self.style_config.line_width + 3,     # 跨侧段最粗
            PathSegmentType.COMPLETED: self.style_config.line_width - 0.5,    # 完成段稍细
            PathSegmentType.CURRENT: self.style_config.line_width + 2,        # 当前段较粗
        }
        return max(0.5, width_map.get(segment_type, self.style_config.line_width))
    
    def clear_paths(self):
        """清除所有路径图形项"""
        if self.graphics_scene:
            for item in self.path_items:
                self.graphics_scene.removeItem(item)
        
        self.path_items.clear()
        self.logger.info("清除路径图形项", "🧹")
    
    def set_visibility(self, visible: bool):
        """设置路径可见性"""
        self.is_visible = visible
        for item in self.path_items:
            item.setVisible(visible)
        
        self.logger.info(f"设置路径可见性: {visible}", "👁️")
    
    def set_render_style(self, style: PathRenderStyle):
        """设置渲染样式"""
        self.render_style = style
        self.logger.info(f"设置渲染样式: {style.value}", "🎨")
        
        # 重新渲染
        if self.path_segments:
            self.render_paths()
    
    def update_progress(self, current_sequence: int):
        """更新检测进度"""
        self.current_sequence = current_sequence
        
        # 更新路径段状态
        for segment in self.path_segments:
            if segment.sequence_number < current_sequence:
                segment.segment_type = PathSegmentType.COMPLETED
            elif segment.sequence_number == current_sequence:
                segment.segment_type = PathSegmentType.CURRENT
            else:
                # 恢复到原始段类型，而不是不存在的NORMAL
                segment.segment_type = PathSegmentType.A_SIDE_NORMAL  # 默认为A侧正常段
        
        # 重新渲染
        self.render_paths()
        self.logger.info(f"更新检测进度: {current_sequence}", "📈")
    
    def get_path_statistics(self) -> Dict[str, Any]:
        """获取路径统计信息"""
        if not self.path_segments:
            return {}
        
        total_distance = sum(segment.distance for segment in self.path_segments)
        avg_distance = total_distance / len(self.path_segments)
        max_distance = max(segment.distance for segment in self.path_segments)
        
        return {
            'total_segments': len(self.path_segments),
            'total_distance': total_distance,
            'average_distance': avg_distance,
            'max_distance': max_distance,
            'current_progress': self.current_sequence,
            'completion_rate': self.current_sequence / len(self.path_segments) * 100 if self.path_segments else 0
        }