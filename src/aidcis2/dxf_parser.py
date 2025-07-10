"""
DXF文件解析器
负责解析DXF文件并提取管孔信息
"""

import ezdxf
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import math

# 修改导入路径以适应主项目结构
from aidcis2.models.hole_data import HoleData, HoleCollection, HoleStatus


class DXFParser:
    """DXF文件解析器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.hole_radius_tolerance = 0.1  # 半径容差
        self.position_tolerance = 0.01    # 位置容差
        self.expected_hole_radius = 8.865  # 预期孔半径
        
    def parse_file(self, file_path: str) -> HoleCollection:
        """
        解析DXF文件

        Args:
            file_path: DXF文件路径

        Returns:
            HoleCollection: 解析得到的孔集合
        """
        try:
            self.logger.info(f"开始解析DXF文件: {file_path}")

            # 检查文件是否存在
            if not Path(file_path).exists():
                raise FileNotFoundError(f"DXF文件不存在: {file_path}")

            # 检查文件大小
            file_size = Path(file_path).stat().st_size
            self.logger.info(f"文件大小: {file_size} 字节")

            if file_size == 0:
                raise ValueError("DXF文件为空")

            # 读取DXF文件
            try:
                doc = ezdxf.readfile(file_path)
                self.logger.info(f"DXF版本: {doc.dxfversion}")
            except ezdxf.DXFStructureError as e:
                raise ValueError(f"DXF文件结构错误: {e}")
            except ezdxf.DXFVersionError as e:
                raise ValueError(f"不支持的DXF版本: {e}")

            # 获取模型空间
            modelspace = doc.modelspace()
            entities = list(modelspace)
            self.logger.info(f"实体总数: {len(entities)}")

            if len(entities) == 0:
                self.logger.warning("DXF文件中没有找到任何实体")

            # 解析弧形实体
            arcs = self._extract_arcs(entities)
            self.logger.info(f"弧形实体数量: {len(arcs)}")

            if len(arcs) == 0:
                self.logger.warning("DXF文件中没有找到弧形实体")

            # 识别管孔
            holes = self._identify_holes(arcs)
            self.logger.info(f"识别到管孔数量: {len(holes)}")

            if len(holes) == 0:
                self.logger.warning(f"未识别到管孔。预期半径: {self.expected_hole_radius}mm")
                # 输出调试信息
                if len(arcs) > 0:
                    radii = [arc.dxf.radius for arc in arcs]
                    unique_radii = sorted(set(radii))
                    self.logger.info(f"发现的弧形半径: {unique_radii}")

            # 分配网格位置
            self._assign_grid_positions(holes)

            # 创建孔集合
            hole_collection = HoleCollection(
                holes={hole.hole_id: hole for hole in holes},
                metadata={
                    'source_file': file_path,
                    'dxf_version': doc.dxfversion,
                    'total_entities': len(entities),
                    'total_arcs': len(arcs),
                    'file_size': file_size
                }
            )

            self.logger.info(f"DXF解析完成，共解析出 {len(hole_collection)} 个管孔")
            return hole_collection

        except (FileNotFoundError, ValueError) as e:
            # 重新抛出已知错误
            raise
        except Exception as e:
            self.logger.error(f"解析DXF文件时出现未知错误: {e}")
            raise ValueError(f"DXF文件解析失败: {e}")
    
    def _extract_arcs(self, entities) -> List:
        """提取所有弧形实体"""
        arcs = []
        for entity in entities:
            if entity.dxftype() == 'ARC':
                arcs.append(entity)
        return arcs
    
    def _identify_holes(self, arcs: List) -> List[HoleData]:
        """
        从弧形实体中识别管孔

        管孔由两个半圆弧组成，具有相同的中心和半径
        """
        # 按中心位置和半径分组弧形
        arc_groups = defaultdict(list)
        filtered_count = 0
        boundary_count = 0

        self.logger.info(f"开始识别管孔，总弧形数: {len(arcs)}")

        for arc in arcs:
            center = arc.dxf.center
            radius = arc.dxf.radius

            # 过滤掉外边界大圆（半径2300）
            if radius > 100:  # 大于100的半径认为是边界
                boundary_count += 1
                self.logger.debug(f"过滤边界弧形: 半径={radius:.3f}")
                continue

            # 只处理预期半径的弧形
            if abs(radius - self.expected_hole_radius) > self.hole_radius_tolerance:
                filtered_count += 1
                self.logger.debug(f"过滤非标准半径弧形: 半径={radius:.3f}, 预期={self.expected_hole_radius}")
                continue

            # 使用中心坐标和半径作为分组键
            key = (
                round(center.x, 2),  # 保留2位小数精度
                round(center.y, 2),
                round(radius, 3)
            )
            arc_groups[key].append(arc)

        self.logger.info(f"弧形过滤结果: 边界弧形={boundary_count}, 非标准半径={filtered_count}, 有效弧形组={len(arc_groups)}")

        # 识别完整的孔（由两个半圆弧组成）
        holes = []
        hole_id_counter = 1
        incomplete_groups = 0

        for (center_x, center_y, radius), group_arcs in arc_groups.items():
            self.logger.debug(f"检查孔位组: 中心({center_x}, {center_y}), 半径={radius}, 弧形数={len(group_arcs)}")

            if len(group_arcs) >= 2:  # 至少有两个弧形才能组成一个孔
                # 检查是否有互补的半圆弧
                if self._is_complete_circle(group_arcs):
                    # 创建孔数据
                    hole = HoleData(
                        hole_id=f"H{hole_id_counter:05d}",
                        center_x=center_x,
                        center_y=center_y,
                        radius=radius,
                        status=HoleStatus.PENDING,
                        layer=group_arcs[0].dxf.layer,
                        metadata={
                            'arc_count': len(group_arcs),
                            'source_arcs': [i for i, arc in enumerate(group_arcs)]
                        }
                    )
                    holes.append(hole)
                    self.logger.debug(f"识别到完整孔位: {hole.hole_id}")
                    hole_id_counter += 1
                else:
                    incomplete_groups += 1
                    self.logger.debug(f"不完整孔位组: 中心({center_x}, {center_y}), 弧形数={len(group_arcs)}")
            else:
                incomplete_groups += 1
                self.logger.debug(f"弧形数不足: 中心({center_x}, {center_y}), 弧形数={len(group_arcs)}")

        self.logger.info(f"孔位识别完成: 完整孔位={len(holes)}, 不完整组={incomplete_groups}")
        return holes
    
    def _is_complete_circle(self, arcs: List) -> bool:
        """
        检查弧形列表是否组成完整的圆

        Args:
            arcs: 弧形实体列表

        Returns:
            bool: 是否组成完整圆
        """
        if len(arcs) < 2:
            return False

        # 计算总角度覆盖
        total_angle = 0
        angle_ranges = []

        for arc in arcs:
            start_angle = arc.dxf.start_angle
            end_angle = arc.dxf.end_angle

            # 标准化角度到0-360范围
            start_angle = start_angle % 360
            end_angle = end_angle % 360

            # 计算角度差
            if end_angle == 0 and start_angle == 180:
                # 特殊情况：180°-0° 实际上是 180°-360°
                angle_diff = 180
            elif end_angle < start_angle:
                # 跨越0度的情况
                angle_diff = (360 - start_angle) + end_angle
            else:
                # 正常情况
                angle_diff = end_angle - start_angle

            total_angle += angle_diff
            angle_ranges.append((start_angle, end_angle, angle_diff))

            self.logger.debug(f"弧形角度: {start_angle:.1f}° -> {end_angle:.1f}°, 角度差: {angle_diff:.1f}°")

        self.logger.debug(f"总角度覆盖: {total_angle:.1f}°")

        # 检查总角度是否接近360度
        is_complete = abs(total_angle - 360) < 10  # 允许10度误差

        if not is_complete:
            self.logger.debug(f"不完整圆形，总角度: {total_angle:.1f}°")

        return is_complete
    
    def _assign_grid_positions(self, holes: List[HoleData]) -> None:
        """
        为孔分配网格位置（行列号）
        
        Args:
            holes: 孔数据列表
        """
        if not holes:
            return
        
        # 按Y坐标排序确定行
        holes_by_y = sorted(holes, key=lambda h: h.center_y, reverse=True)
        
        # 识别行
        current_row = 1
        current_y = holes_by_y[0].center_y
        row_tolerance = 5.0  # Y坐标容差
        
        for hole in holes_by_y:
            if abs(hole.center_y - current_y) > row_tolerance:
                current_row += 1
                current_y = hole.center_y
            hole.row = current_row
        
        # 为每行按X坐标排序确定列
        rows = defaultdict(list)
        for hole in holes:
            rows[hole.row].append(hole)
        
        for row_num, row_holes in rows.items():
            row_holes.sort(key=lambda h: h.center_x)
            for col_num, hole in enumerate(row_holes, 1):
                hole.column = col_num
    
    def get_parsing_stats(self, hole_collection: HoleCollection) -> Dict:
        """
        获取解析统计信息
        
        Args:
            hole_collection: 孔集合
            
        Returns:
            Dict: 统计信息
        """
        if not hole_collection.holes:
            return {}
        
        holes = list(hole_collection.holes.values())
        
        # 计算边界
        min_x = min(hole.center_x for hole in holes)
        max_x = max(hole.center_x for hole in holes)
        min_y = min(hole.center_y for hole in holes)
        max_y = max(hole.center_y for hole in holes)
        
        # 统计半径分布
        radii = [hole.radius for hole in holes]
        unique_radii = list(set(radii))
        
        # 统计图层分布
        layers = [hole.layer for hole in holes]
        layer_counts = {}
        for layer in layers:
            layer_counts[layer] = layer_counts.get(layer, 0) + 1
        
        return {
            'total_holes': len(holes),
            'bounds': {
                'min_x': min_x,
                'max_x': max_x,
                'min_y': min_y,
                'max_y': max_y,
                'width': max_x - min_x,
                'height': max_y - min_y
            },
            'radius_distribution': {
                'unique_count': len(unique_radii),
                'radii': sorted(unique_radii),
                'most_common': max(set(radii), key=radii.count) if radii else None
            },
            'layer_distribution': layer_counts,
            'status_counts': hole_collection.get_status_counts()
        }
