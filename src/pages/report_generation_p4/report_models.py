"""
报告数据模型
定义报告生成所需的数据结构和模型
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum
import json


class ReportType(Enum):
    """报告类型枚举"""
    WORKPIECE_SUMMARY = "workpiece_summary"      # 工件汇总报告
    QUALITY_ANALYSIS = "quality_analysis"        # 质量分析报告
    DEFECT_ANALYSIS = "defect_analysis"          # 缺陷分析报告
    COMPREHENSIVE = "comprehensive"              # 综合报告


class ReportFormat(Enum):
    """报告格式枚举"""
    PDF = "pdf"
    HTML = "html"
    EXCEL = "excel"
    WORD = "word"


@dataclass
class WorkpieceInfo:
    """工件信息"""
    workpiece_id: str
    name: str
    type: str
    material: str
    total_holes: int
    dxf_file_path: Optional[str] = None
    project_data_path: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class HoleQualityData:
    """孔位质量数据"""
    hole_id: str
    position_x: float
    position_y: float
    target_diameter: float
    tolerance_upper: float
    tolerance_lower: float
    measured_diameters: List[float]
    qualified_count: int
    total_count: int
    qualification_rate: float
    is_qualified: bool
    deviation_stats: Dict[str, float]  # min, max, avg, std
    measurement_timestamp: Optional[datetime] = None


@dataclass
class DefectData:
    """缺陷数据"""
    hole_id: str
    defect_type: str
    defect_count: int
    confidence: float
    annotator: str
    image_path: str
    coordinates: List[Dict[str, float]]
    created_at: Optional[datetime] = None


@dataclass
class ManualReviewRecord:
    """人工复检记录"""
    hole_id: str
    original_diameter: float
    reviewed_diameter: float
    reviewer: str
    review_reason: str
    review_timestamp: datetime
    final_judgment: str  # "qualified" or "unqualified"
    notes: Optional[str] = None


@dataclass
class QualitySummary:
    """质量汇总数据"""
    total_holes: int
    qualified_holes: int
    unqualified_holes: int
    qualification_rate: float
    holes_with_defects: int
    manual_review_count: int
    completion_rate: float
    
    # 按状态分类的统计
    status_statistics: Dict[str, int] = field(default_factory=dict)
    
    # 质量分布统计
    diameter_statistics: Dict[str, float] = field(default_factory=dict)


@dataclass
class ReportConfiguration:
    """报告配置"""
    report_type: ReportType
    report_format: ReportFormat
    include_workpiece_info: bool = True
    include_quality_summary: bool = True
    include_qualified_holes: bool = True
    include_unqualified_holes: bool = True
    include_defect_analysis: bool = True
    include_manual_reviews: bool = True
    include_charts: bool = True
    include_3d_models: bool = False
    include_endoscope_images: bool = True
    
    # 图表配置
    chart_dpi: int = 300
    chart_format: str = "png"
    
    # 页面配置
    page_size: str = "A4"
    page_orientation: str = "portrait"  # portrait or landscape
    
    # 自定义配置
    custom_title: Optional[str] = None
    custom_logo_path: Optional[str] = None
    company_info: Optional[Dict[str, str]] = None


@dataclass
class ReportData:
    """完整的报告数据"""
    workpiece_info: WorkpieceInfo
    quality_summary: QualitySummary
    qualified_holes: List[HoleQualityData]
    unqualified_holes: List[HoleQualityData]
    defect_data: List[DefectData]
    manual_reviews: List[ManualReviewRecord]
    
    # 报告元数据
    generated_at: datetime = field(default_factory=datetime.now)
    generated_by: str = "系统自动生成"
    report_version: str = "1.0"
    
    # 附加数据
    charts_data: Dict[str, Any] = field(default_factory=dict)
    images_data: Dict[str, str] = field(default_factory=dict)  # hole_id -> image_path


@dataclass
class ReportTemplate:
    """报告模板"""
    template_id: str
    name: str
    description: str
    report_type: ReportType
    default_config: ReportConfiguration
    template_path: str
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'template_id': self.template_id,
            'name': self.name,
            'description': self.description,
            'report_type': self.report_type.value,
            'template_path': self.template_path,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class ReportInstance:
    """报告实例"""
    instance_id: str
    workpiece_id: str
    template_id: str
    configuration: ReportConfiguration
    output_path: str
    status: str  # "generating", "completed", "failed"
    
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    file_size: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'instance_id': self.instance_id,
            'workpiece_id': self.workpiece_id,
            'template_id': self.template_id,
            'output_path': self.output_path,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'file_size': self.file_size
        }


class ReportDataCollector:
    """报告数据收集器"""
    
    def __init__(self):
        self.workpiece_info = None
        self.hole_quality_data = []
        self.defect_data = []
        self.manual_reviews = []
    
    def collect_workpiece_info(self, workpiece_id: str) -> WorkpieceInfo:
        """收集工件信息"""
        # 这里应该从数据库或文件系统收集工件信息
        # 暂时返回示例数据
        return WorkpieceInfo(
            workpiece_id=workpiece_id,
            name="示例工件",
            type="管板",
            material="不锈钢",
            total_holes=48,
            description="示例工件描述"
        )
    
    def collect_hole_quality_data(self, workpiece_id: str) -> List[HoleQualityData]:
        """收集孔位质量数据"""
        # 这里应该从CSV文件和数据库收集实际的质量数据
        # 暂时返回空列表，后续实现
        return []
    
    def collect_defect_data(self, workpiece_id: str) -> List[DefectData]:
        """收集缺陷数据"""
        # 这里应该从标注数据收集缺陷信息
        # 暂时返回空列表，后续实现
        return []
    
    def collect_manual_reviews(self, workpiece_id: str) -> List[ManualReviewRecord]:
        """收集人工复检记录"""
        # 这里应该从数据库收集人工复检记录
        # 暂时返回空列表，后续实现
        return []
    
    def generate_quality_summary(self, hole_data: List[HoleQualityData]) -> QualitySummary:
        """生成质量汇总"""
        if not hole_data:
            return QualitySummary(
                total_holes=0,
                qualified_holes=0,
                unqualified_holes=0,
                qualification_rate=0.0,
                holes_with_defects=0,
                manual_review_count=0,
                completion_rate=0.0
            )
        
        total_holes = len(hole_data)
        qualified_holes = sum(1 for hole in hole_data if hole.is_qualified)
        unqualified_holes = total_holes - qualified_holes
        qualification_rate = (qualified_holes / total_holes * 100) if total_holes > 0 else 0.0
        
        return QualitySummary(
            total_holes=total_holes,
            qualified_holes=qualified_holes,
            unqualified_holes=unqualified_holes,
            qualification_rate=qualification_rate,
            holes_with_defects=0,  # 后续从缺陷数据计算
            manual_review_count=0,  # 后续从复检记录计算
            completion_rate=100.0  # 假设所有孔位都已检测
        )