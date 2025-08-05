"""
缺陷标注数据模型
提供缺陷数据的基本结构和管理功能
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from enum import Enum
from PySide6.QtGui import QColor


class DefectSeverity(Enum):
    """缺陷严重程度枚举"""
    MINOR = "轻微"
    MODERATE = "中等"
    SEVERE = "严重"


class DefectType(Enum):
    """缺陷类型枚举"""
    OVERSIZED = "孔径偏大"
    UNDERSIZED = "孔径偏小"
    MISALIGNED = "孔位偏移"
    ROUGH_SURFACE = "表面粗糙"
    BURR = "毛刺"
    OTHER = "其他"


@dataclass
class DefectCategory:
    """缺陷分类"""
    id: str
    name: str
    description: str = ""
    color: QColor = QColor(255, 0, 0)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color.name()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DefectCategory':
        """从字典创建实例"""
        return cls(
            id=data['id'],
            name=data['name'],
            description=data.get('description', ''),
            color=QColor(data.get('color', '#FF0000'))
        )


@dataclass
class DefectAnnotation:
    """缺陷标注数据"""
    id: str
    hole_id: str
    defect_type: str
    severity: str
    position_x: float = 0.0
    position_y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    description: str = ""
    color: QColor = QColor(255, 0, 0)
    confidence: float = 1.0
    timestamp: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'hole_id': self.hole_id,
            'defect_type': self.defect_type,
            'severity': self.severity,
            'position_x': self.position_x,
            'position_y': self.position_y,
            'width': self.width,
            'height': self.height,
            'description': self.description,
            'color': self.color.name(),
            'confidence': self.confidence,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DefectAnnotation':
        """从字典创建实例"""
        return cls(
            id=data['id'],
            hole_id=data['hole_id'],
            defect_type=data['defect_type'],
            severity=data['severity'],
            position_x=data.get('position_x', 0.0),
            position_y=data.get('position_y', 0.0),
            width=data.get('width', 0.0),
            height=data.get('height', 0.0),
            description=data.get('description', ''),
            color=QColor(data.get('color', '#FF0000')),
            confidence=data.get('confidence', 1.0),
            timestamp=data.get('timestamp')
        )
    
    def get_bounding_box(self) -> tuple:
        """获取边界框坐标"""
        return (self.position_x, self.position_y, self.width, self.height)
    
    def set_bounding_box(self, x: float, y: float, width: float, height: float):
        """设置边界框坐标"""
        self.position_x = x
        self.position_y = y
        self.width = width
        self.height = height


class DefectAnnotationModel:
    """缺陷标注管理模型"""
    
    def __init__(self):
        self.annotations: Dict[str, DefectAnnotation] = {}
        self.categories: Dict[str, DefectCategory] = {}
        self._init_default_categories()
    
    def _init_default_categories(self):
        """初始化默认缺陷分类"""
        default_categories = [
            DefectCategory("oversized", "孔径偏大", "孔径超出上限公差", QColor(255, 165, 0)),
            DefectCategory("undersized", "孔径偏小", "孔径低于下限公差", QColor(255, 0, 0)),
            DefectCategory("misaligned", "孔位偏移", "孔位置偏离设计位置", QColor(255, 255, 0)),
            DefectCategory("rough", "表面粗糙", "孔壁表面粗糙度超标", QColor(128, 0, 128)),
            DefectCategory("burr", "毛刺", "孔边缘存在毛刺", QColor(0, 255, 255)),
            DefectCategory("other", "其他", "其他类型缺陷", QColor(128, 128, 128))
        ]
        
        for category in default_categories:
            self.categories[category.id] = category
    
    def add_annotation(self, annotation: DefectAnnotation) -> bool:
        """添加缺陷标注"""
        if annotation.id in self.annotations:
            return False
        
        self.annotations[annotation.id] = annotation
        return True
    
    def remove_annotation(self, annotation_id: str) -> bool:
        """删除缺陷标注"""
        if annotation_id in self.annotations:
            del self.annotations[annotation_id]
            return True
        return False
    
    def get_annotation(self, annotation_id: str) -> Optional[DefectAnnotation]:
        """获取缺陷标注"""
        return self.annotations.get(annotation_id)
    
    def get_annotations_for_hole(self, hole_id: str) -> List[DefectAnnotation]:
        """获取指定孔位的所有缺陷标注"""
        return [annotation for annotation in self.annotations.values() 
                if annotation.hole_id == hole_id]
    
    def get_all_annotations(self) -> List[DefectAnnotation]:
        """获取所有缺陷标注"""
        return list(self.annotations.values())
    
    def add_category(self, category: DefectCategory) -> bool:
        """添加缺陷分类"""
        if category.id in self.categories:
            return False
        
        self.categories[category.id] = category
        return True
    
    def get_category(self, category_id: str) -> Optional[DefectCategory]:
        """获取缺陷分类"""
        return self.categories.get(category_id)
    
    def get_all_categories(self) -> List[DefectCategory]:
        """获取所有缺陷分类"""
        return list(self.categories.values())
    
    def clear_annotations(self):
        """清空所有标注"""
        self.annotations.clear()
    
    def clear_hole_annotations(self, hole_id: str):
        """清空指定孔位的标注"""
        to_remove = [ann_id for ann_id, annotation in self.annotations.items() 
                     if annotation.hole_id == hole_id]
        
        for ann_id in to_remove:
            del self.annotations[ann_id]
    
    def export_annotations(self) -> Dict[str, Any]:
        """导出所有标注数据"""
        return {
            'annotations': [ann.to_dict() for ann in self.annotations.values()],
            'categories': [cat.to_dict() for cat in self.categories.values()]
        }
    
    def import_annotations(self, data: Dict[str, Any]):
        """导入标注数据"""
        # 导入分类
        if 'categories' in data:
            for cat_data in data['categories']:
                category = DefectCategory.from_dict(cat_data)
                self.categories[category.id] = category
        
        # 导入标注
        if 'annotations' in data:
            for ann_data in data['annotations']:
                annotation = DefectAnnotation.from_dict(ann_data)
                self.annotations[annotation.id] = annotation