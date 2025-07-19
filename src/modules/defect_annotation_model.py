"""
缺陷标注数据模型
支持YOLO格式的缺陷标注数据处理
"""

import os
from datetime import datetime
from typing import List, Optional, Tuple


class DefectAnnotation:
    """缺陷标注数据类 - 支持YOLO格式"""
    
    def __init__(self, defect_class: int, x_center: float, y_center: float, 
                 width: float, height: float, confidence: float = 1.0):
        """
        初始化缺陷标注
        
        Args:
            defect_class: 缺陷类别ID (0, 1, 2, ...)
            x_center: 中心点x坐标 (归一化 0-1)
            y_center: 中心点y坐标 (归一化 0-1)
            width: 宽度 (归一化 0-1)
            height: 高度 (归一化 0-1)
            confidence: 置信度 (0-1)
        """
        self.id = None
        self.defect_class = defect_class
        self.x_center = x_center
        self.y_center = y_center
        self.width = width
        self.height = height
        self.confidence = confidence
        self.created_at = datetime.now()
        
    def to_yolo_format(self) -> str:
        """转换为YOLO格式字符串"""
        return f"{self.defect_class} {self.x_center:.6f} {self.y_center:.6f} {self.width:.6f} {self.height:.6f}"
        
    @classmethod
    def from_yolo_format(cls, yolo_line: str) -> Optional['DefectAnnotation']:
        """从YOLO格式字符串创建标注"""
        try:
            parts = yolo_line.strip().split()
            if len(parts) >= 5:
                defect_class = int(parts[0])
                x_center = float(parts[1])
                y_center = float(parts[2])
                width = float(parts[3])
                height = float(parts[4])
                return cls(defect_class, x_center, y_center, width, height)
        except (ValueError, IndexError):
            pass
        return None
        
    def to_pixel_coords(self, image_width: int, image_height: int) -> Tuple[float, float, float, float]:
        """
        转换为像素坐标
        
        Returns:
            (x1, y1, width_pixel, height_pixel): 左上角坐标和像素尺寸
        """
        x_pixel = self.x_center * image_width
        y_pixel = self.y_center * image_height
        w_pixel = self.width * image_width
        h_pixel = self.height * image_height
        
        # 计算左上角坐标
        x1 = x_pixel - w_pixel / 2
        y1 = y_pixel - h_pixel / 2
        
        return x1, y1, w_pixel, h_pixel
        
    @classmethod
    def from_pixel_coords(cls, defect_class: int, x1: float, y1: float, 
                         width: float, height: float, image_width: int, 
                         image_height: int) -> 'DefectAnnotation':
        """从像素坐标创建标注"""
        # 转换为归一化坐标
        x_center = (x1 + width / 2) / image_width
        y_center = (y1 + height / 2) / image_height
        norm_width = width / image_width
        norm_height = height / image_height
        
        return cls(defect_class, x_center, y_center, norm_width, norm_height)
        
    def is_valid(self) -> bool:
        """验证标注数据是否有效"""
        return (0 <= self.x_center <= 1 and 
                0 <= self.y_center <= 1 and 
                0 < self.width <= 1 and 
                0 < self.height <= 1 and
                self.defect_class >= 0)
                
    def __str__(self) -> str:
        """字符串表示"""
        return f"DefectAnnotation(class={self.defect_class}, center=({self.x_center:.3f}, {self.y_center:.3f}), size=({self.width:.3f}, {self.height:.3f}))"
        
    def __repr__(self) -> str:
        return self.__str__()


class DefectCategory:
    """缺陷类别定义"""
    
    # 预定义的缺陷类别
    CATEGORIES = {
        0: {"name": "crack", "display_name": "裂纹", "color": "#FF0000"},
        1: {"name": "corrosion", "display_name": "腐蚀", "color": "#FF8000"},
        2: {"name": "pit", "display_name": "点蚀", "color": "#FFFF00"},
        3: {"name": "scratch", "display_name": "划痕", "color": "#00FF00"},
        4: {"name": "deposit", "display_name": "沉积物", "color": "#00FFFF"},
        5: {"name": "other", "display_name": "其他", "color": "#8000FF"}
    }
    
    @classmethod
    def get_category_name(cls, class_id: int) -> str:
        """获取类别名称"""
        return cls.CATEGORIES.get(class_id, {}).get("display_name", f"未知类别{class_id}")
        
    @classmethod
    def get_category_color(cls, class_id: int) -> str:
        """获取类别颜色"""
        return cls.CATEGORIES.get(class_id, {}).get("color", "#808080")
        
    @classmethod
    def get_all_categories(cls) -> List[dict]:
        """获取所有类别"""
        return [{"id": k, **v} for k, v in cls.CATEGORIES.items()]


class YOLOFileManager:
    """YOLO格式文件管理器"""
    
    @staticmethod
    def save_annotations(annotations: List[DefectAnnotation], file_path: str) -> bool:
        """保存标注到YOLO格式文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                for annotation in annotations:
                    if annotation.is_valid():
                        f.write(annotation.to_yolo_format() + '\n')
            return True
        except Exception as e:
            print(f"保存标注文件失败: {e}")
            return False
            
    @staticmethod
    def load_annotations(file_path: str) -> List[DefectAnnotation]:
        """从YOLO格式文件加载标注"""
        annotations = []
        
        if not os.path.exists(file_path):
            return annotations
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line and not line.startswith('#'):  # 跳过空行和注释
                        annotation = DefectAnnotation.from_yolo_format(line)
                        if annotation and annotation.is_valid():
                            annotation.id = len(annotations)
                            annotations.append(annotation)
                        else:
                            print(f"警告: 第{line_num}行格式错误: {line}")
        except Exception as e:
            print(f"加载标注文件失败: {e}")
            
        return annotations
        
    @staticmethod
    def get_annotation_file_path(image_path: str) -> str:
        """根据图像路径获取对应的标注文件路径"""
        # 将图像文件扩展名替换为.txt
        base_path = os.path.splitext(image_path)[0]
        return base_path + '.txt'
        
    @staticmethod
    def has_annotations(image_path: str) -> bool:
        """检查图像是否有对应的标注文件"""
        annotation_path = YOLOFileManager.get_annotation_file_path(image_path)
        return os.path.exists(annotation_path)


if __name__ == "__main__":
    # 简单测试
    print("DefectAnnotation 数据模型测试")
    
    # 创建标注
    annotation = DefectAnnotation(0, 0.5, 0.5, 0.2, 0.3)
    print(f"创建标注: {annotation}")
    
    # YOLO格式转换
    yolo_str = annotation.to_yolo_format()
    print(f"YOLO格式: {yolo_str}")
    
    # 从YOLO格式恢复
    restored = DefectAnnotation.from_yolo_format(yolo_str)
    print(f"恢复标注: {restored}")
    
    # 像素坐标转换
    x1, y1, w, h = annotation.to_pixel_coords(800, 600)
    print(f"像素坐标: ({x1}, {y1}, {w}, {h})")
    
    # 类别信息
    print(f"类别名称: {DefectCategory.get_category_name(0)}")
    print(f"类别颜色: {DefectCategory.get_category_color(0)}")
