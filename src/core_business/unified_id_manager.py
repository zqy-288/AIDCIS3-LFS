"""
统一ID管理器
负责管理和转换所有孔位ID格式，确保系统各模块间的ID一致性
解决DXF解析、扇形分配、图形显示等模块间的ID格式不匹配问题
"""

import re
import time
from typing import Dict, List, Tuple, Optional, Set, Any
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict, Counter
from PySide6.QtCore import QObject, Signal

from src.core_business.models.hole_data import HoleData, HoleCollection


class IDFormat(Enum):
    """孔位ID格式类型"""
    DXF_ORIGINAL = "dxf_original"          # DXF原始格式（可能各种格式）
    STANDARD_CRR = "CxxxRyyy"              # 旧标准格式：C001R002
    STANDARD_ACBC = "ACxxxRyyy"            # 新标准格式：AC001R001, BC001R001
    GRID_POSITION = "row_col"              # 网格位置：(行,列)
    SEQUENTIAL = "sequential"              # 连续编号：H001, H002
    CUSTOM = "custom"                      # 自定义格式


@dataclass
class IDPattern:
    """ID模式定义"""
    format_type: IDFormat
    pattern: str                           # 正则表达式模式
    template: str                          # 格式化模板
    description: str                       # 描述
    priority: int = 0                      # 优先级（数字越大优先级越高）


@dataclass
class IDMappingRule:
    """ID映射规则"""
    source_format: IDFormat
    target_format: IDFormat
    converter_func: callable
    description: str


@dataclass 
class IDAnalysisResult:
    """ID分析结果"""
    total_count: int
    detected_formats: Dict[IDFormat, int]  # 格式 -> 数量
    primary_format: IDFormat
    confidence: float                      # 识别置信度 0-1
    sample_ids: List[str]                  # 样本ID
    format_details: Dict[IDFormat, Dict]   # 详细分析结果


class UnifiedIDManager(QObject):
    """统一ID管理器"""
    
    # 信号定义
    id_format_detected = Signal(IDFormat, float)  # 格式, 置信度
    id_mapping_completed = Signal(dict)           # 映射完成
    id_conflict_detected = Signal(list)          # ID冲突检测
    
    def __init__(self):
        super().__init__()
        
        # ID模式定义
        self.patterns = self._initialize_patterns()
        
        # 映射规则
        self.mapping_rules = self._initialize_mapping_rules()
        
        # ID数据存储
        self.original_ids: List[str] = []                    # 原始ID列表
        self.id_mappings: Dict[str, Dict[IDFormat, str]] = {}  # ID映射表
        self.reverse_mappings: Dict[IDFormat, Dict[str, str]] = {}  # 反向映射
        
        # 分析结果
        self.analysis_result: Optional[IDAnalysisResult] = None
        self.primary_format: IDFormat = IDFormat.STANDARD_CRR
        
        # 统计信息
        self.stats = {
            'total_ids_processed': 0,
            'mapping_operations': 0,
            'format_conversions': 0,
            'conflicts_resolved': 0
        }
    
    def _initialize_patterns(self) -> Dict[IDFormat, IDPattern]:
        """初始化ID模式定义"""
        patterns = {
            IDFormat.STANDARD_ACBC: IDPattern(
                format_type=IDFormat.STANDARD_ACBC,
                pattern=r'^([AB])C(\d{3})R(\d{3})$',
                template='{side}C{col:03d}R{row:03d}',
                description='新标准格式：AC001R001, BC001R001',
                priority=150
            ),
            
            IDFormat.STANDARD_CRR: IDPattern(
                format_type=IDFormat.STANDARD_CRR,
                pattern=r'^C(\d{3})R(\d{3})$',
                template='C{col:03d}R{row:03d}',
                description='旧标准格式：C001R002',
                priority=100
            ),
            
            IDFormat.DXF_ORIGINAL: IDPattern(
                format_type=IDFormat.DXF_ORIGINAL,
                pattern=r'^[A-Za-z0-9_\-\.]+$',
                template='{original}',
                description='DXF原始格式（多样化）',
                priority=10
            ),
            
            IDFormat.SEQUENTIAL: IDPattern(
                format_type=IDFormat.SEQUENTIAL,
                pattern=r'^H(\d+)$',
                template='H{seq:03d}',
                description='连续编号：H001, H002',
                priority=50
            ),
            
            IDFormat.GRID_POSITION: IDPattern(
                format_type=IDFormat.GRID_POSITION,
                pattern=r'^(\d+),(\d+)$',
                template='{row},{col}',
                description='网格位置：行,列',
                priority=30
            ),
        }
        
        return patterns
    
    def _initialize_mapping_rules(self) -> List[IDMappingRule]:
        """初始化ID映射规则"""
        rules = [
            # DXF原始 -> 标准格式
            IDMappingRule(
                source_format=IDFormat.DXF_ORIGINAL,
                target_format=IDFormat.STANDARD_CRR,
                converter_func=self._convert_dxf_to_standard,
                description='DXF原始格式转换为标准CxxxRyyy格式'
            ),
            
            # 网格位置 -> 标准格式
            IDMappingRule(
                source_format=IDFormat.GRID_POSITION,
                target_format=IDFormat.STANDARD_CRR,
                converter_func=self._convert_grid_to_standard,
                description='网格位置转换为标准格式'
            ),
            
            # 连续编号 -> 标准格式
            IDMappingRule(
                source_format=IDFormat.SEQUENTIAL,
                target_format=IDFormat.STANDARD_CRR,
                converter_func=self._convert_sequential_to_standard,
                description='连续编号转换为标准格式'
            ),
        ]
        
        return rules
    
    def analyze_hole_collection(self, hole_collection: HoleCollection) -> IDAnalysisResult:
        """
        分析孔位集合的ID格式
        
        Args:
            hole_collection: 孔位集合
            
        Returns:
            IDAnalysisResult: 分析结果
        """
        print(f"🔍 [ID管理器] 开始分析孔位ID格式...")
        
        start_time = time.perf_counter()
        
        self.original_ids = list(hole_collection.holes.keys())
        total_count = len(self.original_ids)
        
        # 检测各种格式
        format_counts = defaultdict(int)
        format_samples = defaultdict(list)
        
        for hole_id in self.original_ids:
            detected_formats = self._detect_id_format(hole_id)
            
            for format_type in detected_formats:
                format_counts[format_type] += 1
                if len(format_samples[format_type]) < 5:
                    format_samples[format_type].append(hole_id)
        
        # 确定主要格式（按优先级和数量）
        primary_format = self._determine_primary_format(format_counts)
        
        # 计算置信度
        primary_count = format_counts.get(primary_format, 0)
        confidence = primary_count / total_count if total_count > 0 else 0.0
        
        # 生成分析结果
        self.analysis_result = IDAnalysisResult(
            total_count=total_count,
            detected_formats=dict(format_counts),
            primary_format=primary_format,
            confidence=confidence,
            sample_ids=format_samples[primary_format][:5],
            format_details={
                fmt: {
                    'count': count,
                    'percentage': (count / total_count * 100) if total_count > 0 else 0,
                    'samples': format_samples[fmt][:3]
                }
                for fmt, count in format_counts.items()
            }
        )
        
        elapsed_time = time.perf_counter() - start_time
        
        print(f"📊 [ID管理器] 分析完成:")
        print(f"   总ID数量: {total_count}")
        print(f"   主要格式: {primary_format.value} (置信度: {confidence:.2%})")
        print(f"   检测到的格式:")
        
        for fmt, details in self.analysis_result.format_details.items():
            print(f"     {fmt.value}: {details['count']} ({details['percentage']:.1f}%) - 样本: {details['samples']}")
        
        print(f"   分析耗时: {elapsed_time:.3f}秒")
        
        # 发射信号
        self.id_format_detected.emit(primary_format, confidence)
        
        return self.analysis_result
    
    def _detect_id_format(self, hole_id: str) -> List[IDFormat]:
        """检测单个ID的可能格式"""
        detected = []
        
        for format_type, pattern in self.patterns.items():
            if re.match(pattern.pattern, hole_id):
                detected.append(format_type)
        
        return detected
    
    def _determine_primary_format(self, format_counts: Dict[IDFormat, int]) -> IDFormat:
        """根据优先级和数量确定主要格式"""
        if not format_counts:
            return IDFormat.STANDARD_CRR
        
        # 按优先级*数量排序
        scored_formats = []
        for format_type, count in format_counts.items():
            priority = self.patterns[format_type].priority
            score = priority * count
            scored_formats.append((score, format_type))
        
        # 返回得分最高的格式
        scored_formats.sort(reverse=True)
        return scored_formats[0][1]
    
    def create_unified_mappings(self, hole_collection: HoleCollection, target_format: IDFormat = IDFormat.STANDARD_CRR) -> Dict[str, str]:
        """
        创建统一的ID映射
        
        Args:
            hole_collection: 孔位集合
            target_format: 目标格式
            
        Returns:
            Dict[str, str]: 原始ID -> 统一ID的映射表
        """
        print(f"🔄 [ID管理器] 创建统一ID映射，目标格式: {target_format.value}")
        
        start_time = time.perf_counter()
        
        # 确保已分析
        if not self.analysis_result:
            self.analyze_hole_collection(hole_collection)
        
        unified_mappings = {}
        self.id_mappings.clear()
        self.reverse_mappings.clear()
        
        # 为每个格式初始化反向映射
        for fmt in IDFormat:
            self.reverse_mappings[fmt] = {}
        
        conflicts = []
        conversion_count = 0
        
        for original_id, hole_data in hole_collection.holes.items():
            try:
                # 检测原始ID格式
                detected_formats = self._detect_id_format(original_id)
                
                if not detected_formats:
                    print(f"⚠️ [ID管理器] 无法识别ID格式: {original_id}")
                    unified_id = original_id  # 保持原样
                else:
                    # 使用第一个检测到的格式进行转换
                    source_format = detected_formats[0]
                    unified_id = self._convert_id(original_id, source_format, target_format, hole_data)
                    conversion_count += 1
                
                # 检查冲突
                if unified_id in self.reverse_mappings[target_format]:
                    existing_original = self.reverse_mappings[target_format][unified_id]
                    conflicts.append({
                        'unified_id': unified_id,
                        'original_ids': [existing_original, original_id],
                        'resolved_id': f"{unified_id}_DUP{len(conflicts)+1}"
                    })
                    unified_id = conflicts[-1]['resolved_id']
                
                # 存储映射
                unified_mappings[original_id] = unified_id
                
                # 创建完整的映射记录
                self.id_mappings[original_id] = {target_format: unified_id}
                self.reverse_mappings[target_format][unified_id] = original_id
                
            except Exception as e:
                print(f"❌ [ID管理器] 转换ID失败 {original_id}: {e}")
                unified_mappings[original_id] = original_id
        
        # 更新统计
        self.stats['total_ids_processed'] = len(unified_mappings)
        self.stats['format_conversions'] = conversion_count
        self.stats['conflicts_resolved'] = len(conflicts)
        self.stats['mapping_operations'] += 1
        
        elapsed_time = time.perf_counter() - start_time
        
        print(f"✅ [ID管理器] 统一映射创建完成:")
        print(f"   处理ID数量: {len(unified_mappings)}")
        print(f"   格式转换数: {conversion_count}")
        print(f"   冲突解决数: {len(conflicts)}")
        print(f"   创建耗时: {elapsed_time:.3f}秒")
        
        if conflicts:
            print(f"🔧 [ID管理器] 解决的ID冲突:")
            for conflict in conflicts[:3]:  # 只显示前3个
                print(f"     {conflict['original_ids']} → {conflict['resolved_id']}")
            if len(conflicts) > 3:
                print(f"     ... 还有{len(conflicts)-3}个冲突")
        
        # 发射信号
        self.id_conflict_detected.emit(conflicts)
        self.id_mapping_completed.emit({
            'total_mapped': len(unified_mappings),
            'conversions': conversion_count,
            'conflicts': len(conflicts),
            'target_format': target_format.value
        })
        
        return unified_mappings
    
    def _convert_id(self, original_id: str, source_format: IDFormat, target_format: IDFormat, hole_data: HoleData) -> str:
        """转换单个ID"""
        if source_format == target_format:
            return original_id
        
        # 查找适用的映射规则
        for rule in self.mapping_rules:
            if rule.source_format == source_format and rule.target_format == target_format:
                return rule.converter_func(original_id, hole_data)
        
        # 如果没有直接规则，尝试通用转换
        return self._generic_id_conversion(original_id, source_format, target_format, hole_data)
    
    def _convert_dxf_to_standard(self, original_id: str, hole_data: HoleData) -> str:
        """DXF原始格式转换为标准格式"""
        # 如果已经是标准格式，直接返回
        if re.match(r'^C(\d{3})R(\d{3})$', original_id):
            return original_id
        
        # 使用孔位的行列信息
        if hole_data.row is not None and hole_data.column is not None:
            return f"C{hole_data.column:03d}R{hole_data.row:03d}"
        
        # 尝试从ID中提取数字
        numbers = re.findall(r'\d+', original_id)
        if len(numbers) >= 2:
            col, row = int(numbers[0]), int(numbers[1])
            return f"C{col:03d}R{row:03d}"
        elif len(numbers) == 1:
            # 单个数字，假设为序号
            seq = int(numbers[0])
            # 简单的序号到行列转换（假设100列）
            row = seq // 100 + 1
            col = seq % 100 + 1
            return f"C{col:03d}R{row:03d}"
        
        # 无法转换，生成唯一ID
        return f"C999R{hash(original_id) % 1000:03d}"
    
    def _convert_grid_to_standard(self, original_id: str, hole_data: HoleData) -> str:
        """网格位置转换为标准格式"""
        match = re.match(r'^(\d+),(\d+)$', original_id)
        if match:
            row, col = int(match.group(1)), int(match.group(2))
            return f"C{col:03d}R{row:03d}"
        return original_id
    
    def _convert_sequential_to_standard(self, original_id: str, hole_data: HoleData) -> str:
        """连续编号转换为标准格式"""
        match = re.match(r'^H(\d+)$', original_id)
        if match:
            seq = int(match.group(1))
            # 简单的序号到行列转换（假设100列）
            row = seq // 100 + 1
            col = seq % 100 + 1
            return f"C{col:03d}R{row:03d}"
        return original_id
    
    def _generic_id_conversion(self, original_id: str, source_format: IDFormat, target_format: IDFormat, hole_data: HoleData) -> str:
        """通用ID转换方法"""
        if target_format == IDFormat.STANDARD_CRR:
            return self._convert_dxf_to_standard(original_id, hole_data)
        elif target_format == IDFormat.SEQUENTIAL:
            # 转换为连续编号
            numbers = re.findall(r'\d+', original_id)
            if numbers:
                return f"H{int(numbers[0]):03d}"
            return f"H{hash(original_id) % 1000:03d}"
        else:
            return original_id
    
    def get_unified_id(self, original_id: str, target_format: IDFormat = IDFormat.STANDARD_CRR) -> Optional[str]:
        """获取统一ID"""
        mapping = self.id_mappings.get(original_id, {})
        return mapping.get(target_format)
    
    def get_original_id(self, unified_id: str, source_format: IDFormat = IDFormat.STANDARD_CRR) -> Optional[str]:
        """根据统一ID获取原始ID"""
        reverse_map = self.reverse_mappings.get(source_format, {})
        return reverse_map.get(unified_id)
    
    def get_format_statistics(self) -> Dict[str, Any]:
        """获取格式统计信息"""
        if not self.analysis_result:
            return {}
        
        return {
            'analysis_result': {
                'total_count': self.analysis_result.total_count,
                'primary_format': self.analysis_result.primary_format.value,
                'confidence': self.analysis_result.confidence,
                'format_distribution': {
                    fmt.value: details for fmt, details in self.analysis_result.format_details.items()
                }
            },
            'mapping_stats': self.stats.copy(),
            'current_mappings': len(self.id_mappings)
        }
    
    def validate_mappings(self) -> Dict[str, Any]:
        """验证映射的完整性和正确性"""
        print(f"🔍 [ID管理器] 验证映射完整性...")
        
        issues = []
        stats = {
            'total_mappings': len(self.id_mappings),
            'missing_mappings': 0,
            'invalid_formats': 0,
            'duplicate_targets': 0
        }
        
        # 检查重复的目标ID
        target_counts = defaultdict(int)
        for original_id, mappings in self.id_mappings.items():
            for target_format, target_id in mappings.items():
                target_counts[(target_format, target_id)] += 1
        
        duplicates = {k: count for k, count in target_counts.items() if count > 1}
        if duplicates:
            stats['duplicate_targets'] = len(duplicates)
            issues.extend([f"重复目标ID: {target_id} ({fmt.value}) - {count}次" 
                          for (fmt, target_id), count in list(duplicates.items())[:5]])
        
        print(f"✅ [ID管理器] 映射验证完成:")
        print(f"   总映射数: {stats['total_mappings']}")
        print(f"   重复目标: {stats['duplicate_targets']}")
        if issues:
            print(f"   发现问题: {len(issues)} 个")
            for issue in issues[:3]:
                print(f"     - {issue}")
        
        return {
            'stats': stats,
            'issues': issues,
            'is_valid': len(issues) == 0
        }
    
    def export_mapping_table(self, target_format: IDFormat = IDFormat.STANDARD_CRR) -> Dict[str, str]:
        """导出映射表"""
        mapping_table = {}
        for original_id, mappings in self.id_mappings.items():
            unified_id = mappings.get(target_format)
            if unified_id:
                mapping_table[original_id] = unified_id
        
        print(f"📤 [ID管理器] 导出映射表: {len(mapping_table)} 条记录")
        return mapping_table
    
    def clear(self):
        """清空所有数据"""
        self.original_ids.clear()
        self.id_mappings.clear()
        self.reverse_mappings.clear()
        self.analysis_result = None
        self.stats = {
            'total_ids_processed': 0,
            'mapping_operations': 0,
            'format_conversions': 0,
            'conflicts_resolved': 0
        }
        print(f"🧹 [ID管理器] 数据清理完成")