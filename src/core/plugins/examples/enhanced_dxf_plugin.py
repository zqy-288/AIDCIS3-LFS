"""
增强DXF处理插件示例
演示如何创建一个完整的插件，包括DXF解析、孔位检测、数据验证等功能
"""

import os
import math
import re
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from src.core.plugin_system.interfaces import IAsyncPlugin, PluginContext, PluginMetadata, PluginVersion
from src.plugins.core_extensions import IDXFParserExtension, IDXFProcessorExtension, IBusinessRuleExtension, get_core_extension_manager


class EnhancedDXFPlugin(IAsyncPlugin, IDXFParserExtension, IDXFProcessorExtension, IBusinessRuleExtension):
    """增强DXF处理插件"""
    
    def __init__(self, context: PluginContext):
        super().__init__(context)
        self.metadata = PluginMetadata(
            id="enhanced_dxf_processor",
            name="增强DXF处理器",
            version=PluginVersion(1, 2, 0),
            description="提供高级DXF文件解析和孔位检测功能",
            author="AI-1 架构重构工程师",
            provides=["dxf_parser", "hole_detector", "geometry_validator"],
            requires=["config_manager", "logger"],
            extension_points=["dxf_parser", "dxf_processor", "business_rule"]
        )
        
        # 插件配置
        self._config = {
            "hole_radius_tolerance": 0.1,
            "min_hole_radius": 0.5,
            "max_hole_radius": 50.0,
            "angle_precision": 1.0,
            "enable_advanced_detection": True,
            "cache_parsed_files": True
        }
        
        # 缓存和状态
        self._file_cache: Dict[str, Dict[str, Any]] = {}
        self._statistics = {
            "files_parsed": 0,
            "holes_detected": 0,
            "validation_errors": 0,
            "cache_hits": 0
        }
        
        # 检测参数
        self._detection_params = {
            "min_arc_segments": 3,
            "circle_completion_threshold": 350,  # 度
            "hole_center_tolerance": 0.01
        }
    
    async def initialize(self) -> bool:
        """初始化插件"""
        try:
            # 获取配置
            config = self.context.retrieve_data("config", {})
            self._config.update(config)
            
            # 注册扩展点
            extension_manager = get_core_extension_manager()
            extension_manager.register_extension("dxf_parser", self, self.plugin_id)
            extension_manager.register_extension("dxf_processor", self, self.plugin_id)
            extension_manager.register_extension("business_rule", self, self.plugin_id)
            
            await self.context.log_async("info", f"Enhanced DXF Plugin initialized with config: {self._config}")
            return True
            
        except Exception as e:
            await self.context.log_async("error", f"Failed to initialize Enhanced DXF Plugin: {e}")
            return False
    
    async def start(self) -> bool:
        """启动插件"""
        try:
            self._start_time = self.context.get_plugin_metadata().created_at
            await self.context.log_async("info", "Enhanced DXF Plugin started successfully")
            return True
        except Exception as e:
            await self.context.log_async("error", f"Failed to start Enhanced DXF Plugin: {e}")
            return False
    
    async def stop(self) -> bool:
        """停止插件"""
        try:
            # 清理缓存
            self._file_cache.clear()
            await self.context.log_async("info", "Enhanced DXF Plugin stopped")
            return True
        except Exception as e:
            await self.context.log_async("error", f"Failed to stop Enhanced DXF Plugin: {e}")
            return False
    
    async def cleanup(self) -> bool:
        """清理插件资源"""
        try:
            # 注销扩展点
            extension_manager = get_core_extension_manager()
            extension_manager.unregister_extension("dxf_parser", self)
            extension_manager.unregister_extension("dxf_processor", self)
            extension_manager.unregister_extension("business_rule", self)
            
            # 保存统计信息
            self.context.store_data("statistics", self._statistics, persistent=True)
            
            await self.context.log_async("info", "Enhanced DXF Plugin cleaned up")
            return True
        except Exception as e:
            await self.context.log_async("error", f"Failed to cleanup Enhanced DXF Plugin: {e}")
            return False
    
    # IDXFParserExtension 实现
    def can_parse(self, file_path: str) -> bool:
        """检查是否可以解析指定文件"""
        try:
            path = Path(file_path)
            if not path.exists():
                return False
            
            # 检查文件扩展名
            if path.suffix.lower() not in ['.dxf', '.dwg']:
                return False
            
            # 检查文件头（简化检查）
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                first_line = f.readline().strip()
                return first_line in ['999', 'AutoCAD'] or 'AC10' in first_line
                
        except Exception:
            return False
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """解析DXF文件"""
        try:
            # 检查缓存
            file_key = self._get_file_cache_key(file_path)
            if self._config.get("cache_parsed_files", True) and file_key in self._file_cache:
                self._statistics["cache_hits"] += 1
                return self._file_cache[file_key]
            
            # 解析文件
            result = self._parse_dxf_file(file_path)
            
            # 缓存结果
            if self._config.get("cache_parsed_files", True):
                self._file_cache[file_key] = result
            
            self._statistics["files_parsed"] += 1
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "entities": [],
                "layers": [],
                "metadata": {}
            }
    
    def get_supported_versions(self) -> List[str]:
        """获取支持的DXF版本"""
        return ["R12", "R13", "R14", "R2000", "R2004", "R2007", "R2010", "R2013", "R2016", "R2018"]
    
    # IDXFProcessorExtension 实现
    def process_entities(self, entities: List[Any]) -> List[Any]:
        """处理DXF实体"""
        processed_entities = []
        
        for entity in entities:
            try:
                processed_entity = self._process_single_entity(entity)
                if processed_entity:
                    processed_entities.append(processed_entity)
            except Exception as e:
                # 记录错误但继续处理其他实体
                processed_entities.append({
                    "original": entity,
                    "error": str(e),
                    "processed": False
                })
        
        return processed_entities
    
    def extract_holes(self, entities: List[Any]) -> List[Dict[str, Any]]:
        """从实体中提取孔位信息"""
        holes = []
        
        try:
            # 按类型分组实体
            circles = [e for e in entities if self._is_circle(e)]
            arcs = [e for e in entities if self._is_arc(e)]
            
            # 从圆形实体直接提取孔位
            for circle in circles:
                hole = self._extract_hole_from_circle(circle)
                if hole and self._validate_hole(hole):
                    holes.append(hole)
            
            # 从弧段组合检测孔位
            if self._config.get("enable_advanced_detection", True):
                arc_holes = self._detect_holes_from_arcs(arcs)
                holes.extend(arc_holes)
            
            # 去重和排序
            holes = self._deduplicate_holes(holes)
            holes = sorted(holes, key=lambda h: (h.get("center_x", 0), h.get("center_y", 0)))
            
            self._statistics["holes_detected"] += len(holes)
            
        except Exception as e:
            holes = []
            self._statistics["validation_errors"] += 1
        
        return holes
    
    def validate_geometry(self, geometry: Dict[str, Any]) -> bool:
        """验证几何数据"""
        try:
            # 检查必要字段
            required_fields = ["center_x", "center_y", "radius"]
            for field in required_fields:
                if field not in geometry:
                    return False
            
            # 检查数值范围
            radius = geometry.get("radius", 0)
            if radius < self._config.get("min_hole_radius", 0.5) or radius > self._config.get("max_hole_radius", 50.0):
                return False
            
            # 检查坐标有效性
            center_x = geometry.get("center_x", 0)
            center_y = geometry.get("center_y", 0)
            if not (isinstance(center_x, (int, float)) and isinstance(center_y, (int, float))):
                return False
            
            return True
            
        except Exception:
            return False
    
    # IBusinessRuleExtension 实现
    def validate_hole_data(self, hole_data: Dict[str, Any]) -> List[str]:
        """验证孔位数据，返回错误信息列表"""
        errors = []
        
        try:
            # 基本几何验证
            if not self.validate_geometry(hole_data):
                errors.append("几何数据验证失败")
            
            # 半径公差检查
            expected_radius = self._config.get("expected_hole_radius", 8.865)
            tolerance = self._config.get("hole_radius_tolerance", 0.1)
            actual_radius = hole_data.get("radius", 0)
            
            if abs(actual_radius - expected_radius) > tolerance:
                errors.append(f"孔径偏差超出公差：期望{expected_radius}±{tolerance}，实际{actual_radius}")
            
            # 位置检查
            center_x = hole_data.get("center_x", 0)
            center_y = hole_data.get("center_y", 0)
            
            if abs(center_x) > 1000 or abs(center_y) > 1000:
                errors.append("孔位坐标超出合理范围")
            
            # 完整性检查
            completeness = hole_data.get("completeness", 0)
            if completeness < 0.95:
                errors.append(f"孔位完整性不足：{completeness:.1%}")
        
        except Exception as e:
            errors.append(f"验证过程出错：{str(e)}")
        
        if errors:
            self._statistics["validation_errors"] += 1
        
        return errors
    
    def calculate_metrics(self, holes: List[Dict[str, Any]]) -> Dict[str, float]:
        """计算指标"""
        if not holes:
            return {}
        
        try:
            # 基本统计
            hole_count = len(holes)
            radii = [h.get("radius", 0) for h in holes if "radius" in h]
            
            metrics = {
                "hole_count": float(hole_count),
                "average_radius": sum(radii) / len(radii) if radii else 0.0,
                "min_radius": min(radii) if radii else 0.0,
                "max_radius": max(radii) if radii else 0.0,
                "radius_std_dev": self._calculate_std_dev(radii) if len(radii) > 1 else 0.0
            }
            
            # 位置分布
            x_coords = [h.get("center_x", 0) for h in holes if "center_x" in h]
            y_coords = [h.get("center_y", 0) for h in holes if "center_y" in h]
            
            if x_coords and y_coords:
                metrics.update({
                    "x_range": max(x_coords) - min(x_coords),
                    "y_range": max(y_coords) - min(y_coords),
                    "center_x": sum(x_coords) / len(x_coords),
                    "center_y": sum(y_coords) / len(y_coords)
                })
            
            # 质量指标
            valid_holes = [h for h in holes if not self.validate_hole_data(h)]
            metrics["quality_ratio"] = len(valid_holes) / hole_count if hole_count > 0 else 0.0
            
            return metrics
            
        except Exception as e:
            return {"calculation_error": str(e)}
    
    def apply_business_logic(self, data: Any, context: Dict[str, Any]) -> Any:
        """应用业务逻辑"""
        try:
            # 根据上下文应用不同的业务逻辑
            logic_type = context.get("logic_type", "default")
            
            if logic_type == "hole_detection":
                return self._apply_hole_detection_logic(data, context)
            elif logic_type == "quality_control":
                return self._apply_quality_control_logic(data, context)
            elif logic_type == "measurement":
                return self._apply_measurement_logic(data, context)
            else:
                return data
                
        except Exception as e:
            return {"error": str(e), "original_data": data}
    
    # 私有辅助方法
    def _get_file_cache_key(self, file_path: str) -> str:
        """生成文件缓存键"""
        path = Path(file_path)
        stat = path.stat()
        return f"{file_path}_{stat.st_mtime}_{stat.st_size}"
    
    def _parse_dxf_file(self, file_path: str) -> Dict[str, Any]:
        """解析DXF文件的核心逻辑"""
        result = {
            "success": True,
            "entities": [],
            "layers": [],
            "metadata": {
                "file_path": file_path,
                "file_size": os.path.getsize(file_path),
                "parse_time": None
            }
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # 简化的DXF解析（实际应使用专业DXF库）
            entities = self._extract_entities_from_dxf(content)
            layers = self._extract_layers_from_dxf(content)
            
            result["entities"] = entities
            result["layers"] = layers
            
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
        
        return result
    
    def _extract_entities_from_dxf(self, content: str) -> List[Dict[str, Any]]:
        """从DXF内容中提取实体"""
        entities = []
        
        # 查找CIRCLE实体
        circle_pattern = r'CIRCLE\s*\n.*?(?=\n(?:CIRCLE|ARC|LINE|ENDSEC))'
        circles = re.findall(circle_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for circle_text in circles:
            entity = self._parse_circle_entity(circle_text)
            if entity:
                entities.append(entity)
        
        # 查找ARC实体
        arc_pattern = r'ARC\s*\n.*?(?=\n(?:CIRCLE|ARC|LINE|ENDSEC))'
        arcs = re.findall(arc_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for arc_text in arcs:
            entity = self._parse_arc_entity(arc_text)
            if entity:
                entities.append(entity)
        
        return entities
    
    def _extract_layers_from_dxf(self, content: str) -> List[str]:
        """从DXF内容中提取图层"""
        layers = []
        
        # 简化的图层提取
        layer_pattern = r'2\s*\n([^\n]+)'
        matches = re.findall(layer_pattern, content)
        
        for match in matches:
            layer_name = match.strip()
            if layer_name and layer_name not in layers:
                layers.append(layer_name)
        
        return layers
    
    def _parse_circle_entity(self, circle_text: str) -> Optional[Dict[str, Any]]:
        """解析圆形实体"""
        try:
            # 提取圆心和半径
            x_match = re.search(r'10\s*\n([-\d.]+)', circle_text)
            y_match = re.search(r'20\s*\n([-\d.]+)', circle_text)
            r_match = re.search(r'40\s*\n([-\d.]+)', circle_text)
            
            if x_match and y_match and r_match:
                return {
                    "type": "CIRCLE",
                    "center_x": float(x_match.group(1)),
                    "center_y": float(y_match.group(1)),
                    "radius": float(r_match.group(1))
                }
        except Exception:
            pass
        
        return None
    
    def _parse_arc_entity(self, arc_text: str) -> Optional[Dict[str, Any]]:
        """解析弧形实体"""
        try:
            # 提取弧的参数
            x_match = re.search(r'10\s*\n([-\d.]+)', arc_text)
            y_match = re.search(r'20\s*\n([-\d.]+)', arc_text)
            r_match = re.search(r'40\s*\n([-\d.]+)', arc_text)
            start_match = re.search(r'50\s*\n([-\d.]+)', arc_text)
            end_match = re.search(r'51\s*\n([-\d.]+)', arc_text)
            
            if all([x_match, y_match, r_match, start_match, end_match]):
                return {
                    "type": "ARC",
                    "center_x": float(x_match.group(1)),
                    "center_y": float(y_match.group(1)),
                    "radius": float(r_match.group(1)),
                    "start_angle": float(start_match.group(1)),
                    "end_angle": float(end_match.group(1))
                }
        except Exception:
            pass
        
        return None
    
    def _process_single_entity(self, entity: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理单个实体"""
        if not isinstance(entity, dict):
            return None
        
        entity_type = entity.get("type", "")
        
        if entity_type == "CIRCLE":
            return self._process_circle_entity(entity)
        elif entity_type == "ARC":
            return self._process_arc_entity(entity)
        else:
            return entity
    
    def _process_circle_entity(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """处理圆形实体"""
        processed = entity.copy()
        
        # 计算周长和面积
        radius = entity.get("radius", 0)
        processed["circumference"] = 2 * math.pi * radius
        processed["area"] = math.pi * radius * radius
        
        # 添加完整性信息
        processed["completeness"] = 1.0  # 圆形完整性为100%
        
        return processed
    
    def _process_arc_entity(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """处理弧形实体"""
        processed = entity.copy()
        
        start_angle = entity.get("start_angle", 0)
        end_angle = entity.get("end_angle", 0)
        radius = entity.get("radius", 0)
        
        # 计算弧长
        angle_diff = abs(end_angle - start_angle)
        if angle_diff > 180:
            angle_diff = 360 - angle_diff
        
        arc_length = (angle_diff / 180) * math.pi * radius
        processed["arc_length"] = arc_length
        
        # 计算完整性（相对于完整圆的比例）
        processed["completeness"] = angle_diff / 360
        
        return processed
    
    def _is_circle(self, entity: Dict[str, Any]) -> bool:
        """检查实体是否为圆形"""
        return entity.get("type") == "CIRCLE"
    
    def _is_arc(self, entity: Dict[str, Any]) -> bool:
        """检查实体是否为弧形"""
        return entity.get("type") == "ARC"
    
    def _extract_hole_from_circle(self, circle: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """从圆形实体提取孔位"""
        try:
            return {
                "id": f"hole_{circle.get('center_x', 0):.3f}_{circle.get('center_y', 0):.3f}",
                "center_x": circle.get("center_x", 0),
                "center_y": circle.get("center_y", 0),
                "radius": circle.get("radius", 0),
                "completeness": circle.get("completeness", 1.0),
                "source_type": "circle",
                "area": circle.get("area", 0),
                "circumference": circle.get("circumference", 0)
            }
        except Exception:
            return None
    
    def _detect_holes_from_arcs(self, arcs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从弧段组合检测孔位"""
        holes = []
        
        # 按中心点分组弧段
        arc_groups = self._group_arcs_by_center(arcs)
        
        for center, arc_group in arc_groups.items():
            if len(arc_group) >= self._detection_params["min_arc_segments"]:
                hole = self._construct_hole_from_arcs(arc_group)
                if hole:
                    holes.append(hole)
        
        return holes
    
    def _group_arcs_by_center(self, arcs: List[Dict[str, Any]]) -> Dict[Tuple[float, float], List[Dict[str, Any]]]:
        """按中心点分组弧段"""
        groups = {}
        tolerance = self._detection_params["hole_center_tolerance"]
        
        for arc in arcs:
            center_x = arc.get("center_x", 0)
            center_y = arc.get("center_y", 0)
            
            # 查找匹配的组
            matched_group = None
            for existing_center in groups.keys():
                if (abs(existing_center[0] - center_x) <= tolerance and 
                    abs(existing_center[1] - center_y) <= tolerance):
                    matched_group = existing_center
                    break
            
            if matched_group:
                groups[matched_group].append(arc)
            else:
                groups[(center_x, center_y)] = [arc]
        
        return groups
    
    def _construct_hole_from_arcs(self, arcs: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """从弧段构造孔位"""
        try:
            # 计算平均中心和半径
            center_x = sum(arc.get("center_x", 0) for arc in arcs) / len(arcs)
            center_y = sum(arc.get("center_y", 0) for arc in arcs) / len(arcs)
            radius = sum(arc.get("radius", 0) for arc in arcs) / len(arcs)
            
            # 计算总角度覆盖
            total_coverage = sum(arc.get("completeness", 0) for arc in arcs) * 360
            
            # 检查是否足够形成一个孔
            if total_coverage >= self._detection_params["circle_completion_threshold"]:
                completeness = min(total_coverage / 360, 1.0)
                
                return {
                    "id": f"hole_{center_x:.3f}_{center_y:.3f}",
                    "center_x": center_x,
                    "center_y": center_y,
                    "radius": radius,
                    "completeness": completeness,
                    "source_type": "arc_combination",
                    "arc_count": len(arcs),
                    "area": math.pi * radius * radius,
                    "circumference": 2 * math.pi * radius
                }
        except Exception:
            pass
        
        return None
    
    def _validate_hole(self, hole: Dict[str, Any]) -> bool:
        """验证孔位数据"""
        errors = self.validate_hole_data(hole)
        return len(errors) == 0
    
    def _deduplicate_holes(self, holes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去除重复的孔位"""
        unique_holes = []
        tolerance = self._config.get("hole_radius_tolerance", 0.1)
        
        for hole in holes:
            is_duplicate = False
            center_x = hole.get("center_x", 0)
            center_y = hole.get("center_y", 0)
            
            for existing_hole in unique_holes:
                existing_x = existing_hole.get("center_x", 0)
                existing_y = existing_hole.get("center_y", 0)
                
                distance = math.sqrt((center_x - existing_x)**2 + (center_y - existing_y)**2)
                if distance <= tolerance:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_holes.append(hole)
        
        return unique_holes
    
    def _calculate_std_dev(self, values: List[float]) -> float:
        """计算标准差"""
        if len(values) <= 1:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(variance)
    
    def _apply_hole_detection_logic(self, data: Any, context: Dict[str, Any]) -> Any:
        """应用孔位检测业务逻辑"""
        # 实现具体的孔位检测逻辑
        return data
    
    def _apply_quality_control_logic(self, data: Any, context: Dict[str, Any]) -> Any:
        """应用质量控制业务逻辑"""
        # 实现具体的质量控制逻辑
        return data
    
    def _apply_measurement_logic(self, data: Any, context: Dict[str, Any]) -> Any:
        """应用测量业务逻辑"""
        # 实现具体的测量逻辑
        return data
    
    def get_provided_services(self) -> Dict[str, Any]:
        """获取插件提供的服务"""
        return {
            "dxf_parser": self,
            "hole_detector": self,
            "geometry_validator": self,
            "statistics": lambda: self._statistics,
            "config": lambda: self._config
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """获取插件健康状态"""
        base_status = super().get_health_status()
        base_status.update({
            "statistics": self._statistics,
            "cache_size": len(self._file_cache),
            "config": self._config
        })
        return base_status