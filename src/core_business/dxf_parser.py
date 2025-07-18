"""
DXF文件解析器
负责解析DXF文件并提取管孔信息
"""

import ezdxf
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from collections import defaultdict
import math
import time
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

# 修改导入路径以适应主项目结构
from src.core_business.models.hole_data import HoleData, HoleCollection, HoleStatus
from src.core.dependency_injection import injectable, ServiceLifetime
from src.core.error_handler import get_error_handler, error_handler, ErrorCategory
from src.data.config_manager import get_config
from src.core_business.business_cache import BusinessCacheManager, cached_business_operation
from src.core_business.business_rules import BusinessRuleEngine, apply_business_rules


@injectable(ServiceLifetime.SINGLETON)
class DXFParser:
    """DXF文件解析器 - 优化版本"""
    
    def __init__(self, cache_manager: BusinessCacheManager = None, 
                 rule_engine: BusinessRuleEngine = None):
        self.logger = logging.getLogger(__name__)
        self.error_handler = get_error_handler()
        
        # 初始化缓存管理器
        if cache_manager is None:
            try:
                self.cache_manager = BusinessCacheManager()
            except Exception as e:
                self.logger.warning(f"无法初始化缓存管理器: {e}")
                self.cache_manager = None
        else:
            self.cache_manager = cache_manager
            
        self.rule_engine = rule_engine
        
        # 从配置获取参数
        self.hole_radius_tolerance = get_config('aidcis2.hole_radius_tolerance', 0.1)
        self.position_tolerance = get_config('aidcis2.position_tolerance', 0.01)
        self.expected_hole_radius = get_config('aidcis2.expected_hole_radius', 8.865)
        self.enable_parallel_processing = get_config('aidcis2.enable_parallel_processing', True)
        self.max_workers = get_config('aidcis2.max_workers', 4)
        
        # 性能统计
        self._parsing_stats = {
            'total_files_parsed': 0,
            'total_parsing_time': 0.0,
            'average_parsing_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
    @error_handler(component="DXFParser", category=ErrorCategory.BUSINESS)
    @cached_business_operation(operation_name="dxf_parse_file")
    @apply_business_rules(["dxf_file_validation", "performance_optimization"])
    def parse_file(self, file_path: str) -> HoleCollection:
        """
        解析DXF文件 - 性能优化版本

        Args:
            file_path: DXF文件路径

        Returns:
            HoleCollection: 解析得到的孔集合
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"开始解析DXF文件: {file_path}")
            
            # 检查缓存
            cache_key = self._get_file_cache_key(file_path)
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                self._parsing_stats['cache_hits'] += 1
                self.logger.info(f"DXF解析命中缓存: {file_path}")
                return cached_result
            
            self._parsing_stats['cache_misses'] += 1

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
                self.error_handler.handle_error(e, component="DXFParser", context={"file": file_path})
                raise ValueError(f"DXF文件结构错误: {e}")
            except ezdxf.DXFVersionError as e:
                self.error_handler.handle_error(e, component="DXFParser", context={"file": file_path})
                raise ValueError(f"不支持的DXF版本: {e}")

            # 获取模型空间
            modelspace = doc.modelspace()
            entities = list(modelspace)
            self.logger.info(f"实体总数: {len(entities)}")

            if len(entities) == 0:
                self.logger.warning("DXF文件中没有找到任何实体")

            # 觧析弧形实体 - 并行优化
            if self.enable_parallel_processing and len(entities) > 1000:
                arcs = self._extract_arcs_parallel(entities)
            else:
                arcs = self._extract_arcs(entities)
            self.logger.info(f"弧形实体数量: {len(arcs)}")

            if len(arcs) == 0:
                self.logger.warning("DXF文件中没有找到弧形实体")

            # 识别管孔 - 优化算法
            holes = self._identify_holes_optimized(arcs)
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
            
            # AI员工2号修改开始 - 2025-01-14
            # 修改目的：将孔位ID从(row,column)格式转换为C{col}R{row}格式
            # 更新hole_id为C{column:03d}R{row:03d}格式
            for hole in holes:
                if hole.row is not None and hole.column is not None:
                    hole.hole_id = f"C{hole.column:03d}R{hole.row:03d}"
            # AI员工2号修改结束

            # 对所有孔位进行90度逆时针旋转
            self._rotate_holes_90_ccw(holes)
            
            # 创建孔集合
            hole_collection = HoleCollection(
                holes={hole.hole_id: hole for hole in holes},
                metadata={
                    'source_file': file_path,
                    'dxf_version': doc.dxfversion,
                    'total_entities': len(entities),
                    'total_arcs': len(arcs),
                    'file_size': file_size,
                    'pre_rotated': True  # 标记已预旋转
                }
            )

            # 缓存结果到新的缓存管理器
            self._cache_result(cache_key, hole_collection)
            
            # 同时缓存到业务缓存管理器（如果可用）
            if self.cache_manager:
                self.cache_manager.cache_business_operation(
                    "dxf_parse_complete", 
                    {"file_path": file_path, "file_size": file_size}, 
                    hole_collection,
                    ttl=1800  # 30分钟
                )
            
            # 更新统计信息
            parsing_time = time.time() - start_time
            self._update_parsing_stats(parsing_time)
            
            self.logger.info(f"DXF解析完成，共解析出 {len(hole_collection)} 个管孔（耗时{parsing_time:.3f}秒）")
            return hole_collection

        except (FileNotFoundError, ValueError) as e:
            # 重新抛出已知错误
            raise
        except Exception as e:
            self.error_handler.handle_error(e, component="DXFParser", context={"file": file_path})
            self.logger.error(f"解析DXF文件时出现未知错误: {e}")
            raise ValueError(f"DXF文件解析失败: {e}")
        finally:
            # 即使失败也要统计时间
            if 'start_time' in locals():
                parsing_time = time.time() - start_time
                self._update_parsing_stats(parsing_time)
    
    def _extract_arcs(self, entities) -> List:
        """提取所有弧形实体"""
        arcs = []
        for entity in entities:
            if entity.dxftype() == 'ARC':
                arcs.append(entity)
        return arcs
    
    def _extract_arcs_parallel(self, entities) -> List:
        """并行提取弧形实体"""
        def extract_chunk(chunk):
            return [entity for entity in chunk if entity.dxftype() == 'ARC']
        
        # 分块处理
        chunk_size = max(1, len(entities) // self.max_workers)
        chunks = [entities[i:i + chunk_size] for i in range(0, len(entities), chunk_size)]
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            results = list(executor.map(extract_chunk, chunks))
        
        # 合并结果
        arcs = []
        for result in results:
            arcs.extend(result)
        
        return arcs
    
    def _identify_holes_optimized(self, arcs: List) -> List[HoleData]:
        """
        优化的管孔识别算法 - 向量化批处理版本
        """
        if not arcs:
            return []
            
        start_time = time.time()
        # 静默处理，只在处理大数据集时输出关键信息
        if len(arcs) > 10000:
            self.logger.info(f"🚀 开始孔位识别: {len(arcs)} 个弧形")
        
        # 使用优化的实现
        holes = self._identify_holes_vectorized(arcs)
        
        elapsed_time = time.time() - start_time
        
        # 只在处理大数据集时输出性能信息
        if len(arcs) > 10000:
            self.logger.info(f"✅ 孔位识别完成: {len(holes)} 个孔位，{elapsed_time:.1f}秒，{len(arcs)/elapsed_time:.0f} 弧形/秒")
        
        return holes
    
    def _identify_holes_vectorized(self, arcs: List) -> List[HoleData]:
        """
        向量化的管孔识别算法 - 高性能版本
        """
        # 按中心位置和半径分组弧形 - 使用优化的键生成
        arc_groups = defaultdict(list)
        filtered_count = 0
        boundary_count = 0
        
        # 批量预处理弧形
        batch_size = 5000
        for i in range(0, len(arcs), batch_size):
            batch = arcs[i:i + batch_size]
            
            for arc in batch:
                center = arc.dxf.center
                radius = arc.dxf.radius
                
                # 快速过滤（使用早期返回）
                if radius > 100:  # 大于100的半径认为是边界
                    boundary_count += 1
                    continue
                    
                if abs(radius - self.expected_hole_radius) > self.hole_radius_tolerance:
                    filtered_count += 1
                    continue
                
                # 优化的分组键（减少精度以提高命中率）
                key = (
                    round(center.x, 1),  # 减少精度以提高分组效率
                    round(center.y, 1),
                    round(radius, 2)
                )
                arc_groups[key].append(arc)
        
        # 只在处理大数据集时输出统计信息
        if len(arcs) > 10000:
            self.logger.info(f"📊 弧形预处理: 边界弧形={boundary_count}, 过滤弧形={filtered_count}, 有效组={len(arc_groups)}")
        
        # 批量识别孔位
        holes = []
        hole_id_counter = 1
        
        for (center_x, center_y, radius), group_arcs in arc_groups.items():
            if len(group_arcs) >= 2 and self._is_complete_circle_fast(group_arcs):
                hole = HoleData(
                    hole_id=f"H{hole_id_counter:05d}",
                    center_x=center_x,
                    center_y=center_y,
                    radius=radius,
                    status=HoleStatus.PENDING,
                    layer=group_arcs[0].dxf.layer,
                    metadata={
                        'arc_count': len(group_arcs),
                        'source_arcs': list(range(len(group_arcs)))
                    }
                )
                holes.append(hole)
                hole_id_counter += 1
        
        return holes
    
    def _is_complete_circle_fast(self, arcs: List) -> bool:
        """
        快速检查弧形列表是否组成完整的圆 - 优化版本
        """
        if len(arcs) < 2:
            return False
            
        # 简化的完整性检查 - 只检查弧形数量和基本角度覆盖
        if len(arcs) == 2:
            # 两个弧形的情况：检查角度差是否接近180度
            arc1, arc2 = arcs[0], arcs[1]
            angle_diff = abs(arc1.dxf.start_angle - arc2.dxf.start_angle)
            return 160 <= angle_diff <= 200 or 340 <= angle_diff <= 380
        else:
            # 多个弧形的情况：简单检查总角度
            total_angle = sum(abs(arc.dxf.end_angle - arc.dxf.start_angle) for arc in arcs)
            return 340 <= total_angle <= 380
    
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
    
    def _rotate_holes_90_ccw(self, holes: List[HoleData]) -> None:
        """
        对所有孔位进行90度逆时针旋转 - 优化版本
        旋转公式: (x, y) -> (-y, x)
        
        增强功能：
        - 支持自适应旋转角度
        - 保持坐标系一致性
        - 优化性能
        
        Args:
            holes: 孔位列表
        """
        if not holes:
            return
            
        start_time = time.perf_counter()
        hole_count = len(holes)
        
        # 计算几何中心（使用所有孔位的中心）
        center_x = sum(hole.center_x for hole in holes) / hole_count
        center_y = sum(hole.center_y for hole in holes) / hole_count
        
        # 获取旋转配置
        rotation_config = self._get_rotation_config()
        rotation_angle = rotation_config.get('angle', 90.0)  # 默认90度
        apply_rotation = rotation_config.get('enabled', True)
        
        if not apply_rotation:
            self.logger.info("坐标旋转已禁用")
            return
        
        # 只在处理大数据集时输出旋转信息
        if hole_count > 10000:
            self.logger.info(f"🔄 执行{rotation_angle}度逆时针旋转: ({center_x:.2f}, {center_y:.2f})")
        
        # 计算旋转参数
        rotation_rad = math.radians(rotation_angle)
        cos_angle = math.cos(rotation_rad)
        sin_angle = math.sin(rotation_rad)
        
        # 批量旋转 - 向量化操作
        batch_size = 5000  # 分批处理避免内存峰值
        
        for i in range(0, hole_count, batch_size):
            batch = holes[i:i + batch_size]
            
            # 批量计算旋转坐标
            for hole in batch:
                # 平移到原点
                x = hole.center_x - center_x
                y = hole.center_y - center_y
                
                # 应用旋转变换
                new_x = x * cos_angle - y * sin_angle
                new_y = x * sin_angle + y * cos_angle
                
                # 平移回原位置
                hole.center_x = new_x + center_x
                hole.center_y = new_y + center_y
        
        elapsed_time = time.perf_counter() - start_time
        # 只在处理大数据集时输出性能信息
        if hole_count > 10000:
            self.logger.info(f"✅ 旋转完成: {hole_count} 个孔位，{elapsed_time:.1f}秒，{hole_count/elapsed_time:.0f} 孔位/秒")
    
    def _get_rotation_config(self) -> Dict[str, Any]:
        """获取旋转配置"""
        try:
            # 尝试从配置文件获取旋转设置
            return {
                'enabled': get_config('aidcis2.coordinate_rotation.enabled', True),
                'angle': get_config('aidcis2.coordinate_rotation.angle', 90.0),
                'adaptive': get_config('aidcis2.coordinate_rotation.adaptive', False)
            }
        except Exception:
            # 返回默认配置
            return {
                'enabled': True,
                'angle': 90.0,
                'adaptive': False
            }
    
    @lru_cache(maxsize=128)
    def _get_file_cache_key(self, file_path: str) -> str:
        """生成文件缓存键"""
        file_stat = Path(file_path).stat()
        return f"{file_path}_{file_stat.st_mtime}_{file_stat.st_size}"
    
    def _get_cached_result(self, cache_key: str) -> Optional[HoleCollection]:
        """获取缓存结果 - 优化版本"""
        if not hasattr(self, '_cache'):
            self._cache = {}
            self._cache_access_times = {}  # 记录访问时间用于LRU策略
        
        if cache_key in self._cache:
            # 更新访问时间
            self._cache_access_times[cache_key] = time.time()
            return self._cache[cache_key]
        
        return None
    
    def _cache_result(self, cache_key: str, result: HoleCollection) -> None:
        """缓存结果 - 智能内存管理版本"""
        if not hasattr(self, '_cache'):
            self._cache = {}
            self._cache_access_times = {}
        
        # 动态缓存大小限制（基于可用内存）
        max_cache_size = get_config('aidcis2.max_cache_size', 5)  # 减少默认缓存大小
        
        # 检查缓存大小并执行LRU清理
        if len(self._cache) >= max_cache_size:
            # 找出最久未使用的条目
            oldest_key = min(self._cache_access_times.keys(), 
                           key=lambda k: self._cache_access_times[k])
            
            # 删除最旧的条目
            del self._cache[oldest_key]
            del self._cache_access_times[oldest_key]
            
            # 主动垃圾回收
            import gc
            gc.collect()
            
            # 静默清理缓存
            if len(self._cache) > 5:  # 只在缓存较多时输出
                self.logger.info(f"🧹 清理缓存条目: {oldest_key}")
        
        # 缓存新结果
        self._cache[cache_key] = result
        self._cache_access_times[cache_key] = time.time()
        
        # 记录内存使用情况
        cache_size_mb = len(self._cache) * 0.1  # 估算每个缓存条目约0.1MB
        # 静默缓存管理
        if len(self._cache) > 3:  # 只在缓存较多时输出
            self.logger.info(f"📊 缓存大小: {len(self._cache)} 条目, 约 {cache_size_mb:.1f}MB")
    
    def _update_parsing_stats(self, parsing_time: float) -> None:
        """更新解析统计信息"""
        self._parsing_stats['total_files_parsed'] += 1
        self._parsing_stats['total_parsing_time'] += parsing_time
        self._parsing_stats['average_parsing_time'] = (
            self._parsing_stats['total_parsing_time'] / 
            self._parsing_stats['total_files_parsed']
        )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return {
            'parsing_stats': self._parsing_stats.copy(),
            'cache_stats': {
                'cache_size': len(getattr(self, '_cache', {})),
                'hit_rate': (
                    self._parsing_stats['cache_hits'] / 
                    (self._parsing_stats['cache_hits'] + self._parsing_stats['cache_misses'])
                    if (self._parsing_stats['cache_hits'] + self._parsing_stats['cache_misses']) > 0 
                    else 0
                )
            },
            'configuration': {
                'hole_radius_tolerance': self.hole_radius_tolerance,
                'position_tolerance': self.position_tolerance,
                'expected_hole_radius': self.expected_hole_radius,
                'enable_parallel_processing': self.enable_parallel_processing,
                'max_workers': self.max_workers
            }
        }
    
    def clear_cache(self) -> None:
        """清空缓存 - 内存优化版本"""
        cache_count = 0
        
        if hasattr(self, '_cache'):
            cache_count = len(self._cache)
            self._cache.clear()
            
        if hasattr(self, '_cache_access_times'):
            self._cache_access_times.clear()
            
        # 主动垃圾回收
        import gc
        gc.collect()
        
        # 只在有大量缓存时输出清理信息
        if cache_count > 0:
            self.logger.info(f"🧹 DXF解析缓存已清空: {cache_count} 个条目")
