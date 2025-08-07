"""
缺陷标注数据库管理器
用于保存和管理缺陷标注结果，支持报告生成的数据需求
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

from .defect_annotation_model import DefectAnnotation


@dataclass
class AnnotationRecord:
    """标注记录数据类"""
    record_id: Optional[int]  # 记录ID（自动生成）
    image_path: str  # 原始图片路径
    image_filename: str  # 图片文件名
    image_size: Tuple[int, int]  # 图片尺寸 (width, height)
    workpiece_id: Optional[str]  # 工件ID
    hole_id: Optional[str]  # 孔位ID
    session_type: str  # 会话类型：'normal' 或 'manual_review'
    annotation_count: int  # 标注数量
    created_at: datetime  # 创建时间
    updated_at: datetime  # 更新时间
    software_version: str  # 软件版本
    operator: Optional[str] = None  # 操作员
    notes: Optional[str] = None  # 备注


@dataclass
class DefectRecord:
    """缺陷记录数据类"""
    defect_id: Optional[int]  # 缺陷ID（自动生成）
    record_id: int  # 关联的标注记录ID
    defect_class: int  # 缺陷类别
    defect_class_name: str  # 缺陷类别名称
    x_center: float  # 中心x坐标（归一化）
    y_center: float  # 中心y坐标（归一化）
    width: float  # 宽度（归一化）
    height: float  # 高度（归一化）
    confidence: float  # 置信度
    x_pixel: int  # 像素坐标x
    y_pixel: int  # 像素坐标y
    width_pixel: int  # 像素宽度
    height_pixel: int  # 像素高度
    area_pixel: int  # 像素面积
    created_at: datetime  # 创建时间


class DefectAnnotationDatabase:
    """缺陷标注数据库管理器"""
    
    def __init__(self, db_path: str = "data/defect_annotations.db"):
        """初始化数据库"""
        self.db_path = db_path
        
        # 确保数据目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # 初始化数据库
        self._init_database()
        
    def _init_database(self):
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 创建标注记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS annotation_records (
                    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_path TEXT NOT NULL,
                    image_filename TEXT NOT NULL,
                    image_width INTEGER NOT NULL,
                    image_height INTEGER NOT NULL,
                    workpiece_id TEXT,
                    hole_id TEXT,
                    session_type TEXT NOT NULL DEFAULT 'normal',
                    annotation_count INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    software_version TEXT NOT NULL,
                    operator TEXT,
                    notes TEXT
                )
            ''')
            
            # 创建缺陷记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS defect_records (
                    defect_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    record_id INTEGER NOT NULL,
                    defect_class INTEGER NOT NULL,
                    defect_class_name TEXT NOT NULL,
                    x_center REAL NOT NULL,
                    y_center REAL NOT NULL,
                    width REAL NOT NULL,
                    height REAL NOT NULL,
                    confidence REAL NOT NULL,
                    x_pixel INTEGER NOT NULL,
                    y_pixel INTEGER NOT NULL,
                    width_pixel INTEGER NOT NULL,
                    height_pixel INTEGER NOT NULL,
                    area_pixel INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (record_id) REFERENCES annotation_records (record_id)
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_image_path ON annotation_records (image_path)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_workpiece_id ON annotation_records (workpiece_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_hole_id ON annotation_records (hole_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_record_id ON defect_records (record_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_defect_class ON defect_records (defect_class)')
            
            conn.commit()
            
    def save_annotation_result(self, 
                             image_path: str,
                             annotations: List[DefectAnnotation],
                             image_size: Tuple[int, int],
                             workpiece_id: Optional[str] = None,
                             hole_id: Optional[str] = None,
                             session_type: str = "normal",
                             operator: Optional[str] = None,
                             notes: Optional[str] = None,
                             category_manager=None) -> int:
        """
        保存标注结果
        
        Args:
            image_path: 图片路径
            annotations: 标注列表
            image_size: 图片尺寸 (width, height)
            workpiece_id: 工件ID
            hole_id: 孔位ID
            session_type: 会话类型
            operator: 操作员
            notes: 备注
            category_manager: 类别管理器
            
        Returns:
            int: 记录ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            image_filename = os.path.basename(image_path)
            
            # 检查是否已存在相同图片的记录
            cursor.execute('''
                SELECT record_id FROM annotation_records 
                WHERE image_path = ? AND session_type = ?
            ''', (image_path, session_type))
            
            existing_record = cursor.fetchone()
            
            if existing_record:
                # 更新现有记录
                record_id = existing_record[0]
                cursor.execute('''
                    UPDATE annotation_records 
                    SET annotation_count = ?, updated_at = ?, operator = ?, notes = ?
                    WHERE record_id = ?
                ''', (len(annotations), now, operator, notes, record_id))
                
                # 删除旧的缺陷记录
                cursor.execute('DELETE FROM defect_records WHERE record_id = ?', (record_id,))
                
            else:
                # 创建新记录
                cursor.execute('''
                    INSERT INTO annotation_records 
                    (image_path, image_filename, image_width, image_height, 
                     workpiece_id, hole_id, session_type, annotation_count, 
                     created_at, updated_at, software_version, operator, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (image_path, image_filename, image_size[0], image_size[1],
                      workpiece_id, hole_id, session_type, len(annotations),
                      now, now, "AIDCIS3-LFS v1.0", operator, notes))
                
                record_id = cursor.lastrowid
            
            # 保存缺陷记录
            for annotation in annotations:
                # 获取缺陷类别名称
                if category_manager:
                    defect_class_name = category_manager.get_category_name(annotation.defect_class)
                else:
                    defect_class_name = f"类别{annotation.defect_class}"
                
                # 计算像素坐标
                x_pixel = int(annotation.x_center * image_size[0])
                y_pixel = int(annotation.y_center * image_size[1])
                width_pixel = int(annotation.width * image_size[0])
                height_pixel = int(annotation.height * image_size[1])
                area_pixel = width_pixel * height_pixel
                
                cursor.execute('''
                    INSERT INTO defect_records 
                    (record_id, defect_class, defect_class_name, 
                     x_center, y_center, width, height, confidence,
                     x_pixel, y_pixel, width_pixel, height_pixel, area_pixel, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (record_id, annotation.defect_class, defect_class_name,
                      annotation.x_center, annotation.y_center, annotation.width, annotation.height,
                      annotation.confidence, x_pixel, y_pixel, width_pixel, height_pixel,
                      area_pixel, now))
            
            conn.commit()
            return record_id
            
    def get_annotation_records(self, 
                              workpiece_id: Optional[str] = None,
                              hole_id: Optional[str] = None,
                              session_type: Optional[str] = None,
                              start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None) -> List[Dict]:
        """
        获取标注记录
        
        Args:
            workpiece_id: 工件ID筛选
            hole_id: 孔位ID筛选
            session_type: 会话类型筛选
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            List[Dict]: 标注记录列表
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = '''
                SELECT * FROM annotation_records 
                WHERE 1=1
            '''
            params = []
            
            if workpiece_id:
                query += ' AND workpiece_id = ?'
                params.append(workpiece_id)
                
            if hole_id:
                query += ' AND hole_id = ?'
                params.append(hole_id)
                
            if session_type:
                query += ' AND session_type = ?'
                params.append(session_type)
                
            if start_date:
                query += ' AND created_at >= ?'
                params.append(start_date.isoformat())
                
            if end_date:
                query += ' AND created_at <= ?'
                params.append(end_date.isoformat())
                
            query += ' ORDER BY created_at DESC'
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
            
    def get_defect_records(self, record_id: int) -> List[Dict]:
        """获取指定记录的缺陷详情"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM defect_records 
                WHERE record_id = ? 
                ORDER BY defect_id
            ''', (record_id,))
            
            return [dict(row) for row in cursor.fetchall()]
            
    def get_defect_statistics(self, 
                            workpiece_id: Optional[str] = None,
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None) -> Dict:
        """获取缺陷统计信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 基础查询条件
            where_conditions = []
            params = []
            
            if workpiece_id:
                where_conditions.append('ar.workpiece_id = ?')
                params.append(workpiece_id)
                
            if start_date:
                where_conditions.append('ar.created_at >= ?')
                params.append(start_date.isoformat())
                
            if end_date:
                where_conditions.append('ar.created_at <= ?')
                params.append(end_date.isoformat())
                
            where_clause = ' AND '.join(where_conditions) if where_conditions else '1=1'
            
            # 总体统计
            cursor.execute(f'''
                SELECT 
                    COUNT(DISTINCT ar.record_id) as total_images,
                    COUNT(dr.defect_id) as total_defects,
                    AVG(ar.annotation_count) as avg_defects_per_image
                FROM annotation_records ar
                LEFT JOIN defect_records dr ON ar.record_id = dr.record_id
                WHERE {where_clause}
            ''', params)
            
            total_stats = cursor.fetchone()
            
            # 按类别统计
            cursor.execute(f'''
                SELECT 
                    dr.defect_class,
                    dr.defect_class_name,
                    COUNT(*) as count,
                    AVG(dr.area_pixel) as avg_area
                FROM annotation_records ar
                JOIN defect_records dr ON ar.record_id = dr.record_id
                WHERE {where_clause}
                GROUP BY dr.defect_class, dr.defect_class_name
                ORDER BY count DESC
            ''', params)
            
            class_stats = cursor.fetchall()
            
            return {
                'total_images': total_stats[0] or 0,
                'total_defects': total_stats[1] or 0,
                'avg_defects_per_image': round(total_stats[2] or 0, 2),
                'defect_classes': [
                    {
                        'class_id': row[0],
                        'class_name': row[1],
                        'count': row[2],
                        'avg_area': round(row[3] or 0, 2)
                    }
                    for row in class_stats
                ]
            }
            
    def export_to_json(self, output_path: str, **filters):
        """导出数据为JSON格式"""
        records = self.get_annotation_records(**filters)
        
        export_data = []
        for record in records:
            defects = self.get_defect_records(record['record_id'])
            record_data = dict(record)
            record_data['defects'] = defects
            export_data.append(record_data)
            
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
            
        return len(export_data)