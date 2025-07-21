"""
报告生成器核心模块
实现报告数据收集、处理和生成功能
"""

import os
import csv
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
import numpy as np

from .report_models import (
    ReportData, ReportConfiguration, ReportType, ReportFormat,
    WorkpieceInfo, HoleQualityData, DefectData, ManualReviewRecord,
    QualitySummary, ReportInstance, ReportDataCollector
)
from .hole_id_mapper import HoleIdMapper


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self, data_root_path: str = "Data"):
        self.data_root_path = Path(data_root_path)
        self.data_collector = ReportDataCollector()
        
        # 标准参数
        self.standard_diameter = 17.6  # mm
        self.upper_tolerance = 0.05    # mm
        self.lower_tolerance = 0.07    # mm
        
    def collect_workpiece_data(self, workpiece_id: str) -> ReportData:
        """收集指定工件的完整报告数据"""
        print(f"📊 开始收集工件 {workpiece_id} 的报告数据...")
        
        # 收集工件基本信息
        workpiece_info = self._collect_workpiece_info(workpiece_id)
        
        # 收集孔位质量数据
        all_hole_data = self._collect_all_hole_quality_data(workpiece_id)
        
        # 分离合格和不合格孔位
        qualified_holes = [hole for hole in all_hole_data if hole.is_qualified]
        unqualified_holes = [hole for hole in all_hole_data if not hole.is_qualified]
        
        # 收集缺陷数据
        defect_data = self._collect_defect_data(workpiece_id)
        
        # 收集人工复检记录
        manual_reviews = self._collect_manual_reviews(workpiece_id)
        
        # 生成质量汇总
        quality_summary = self._generate_quality_summary(
            all_hole_data, defect_data, manual_reviews
        )
        
        # 收集图表数据
        charts_data = self._generate_charts_data(all_hole_data)
        
        # 收集图像数据
        images_data = self._collect_images_data(workpiece_id)
        
        report_data = ReportData(
            workpiece_info=workpiece_info,
            quality_summary=quality_summary,
            qualified_holes=qualified_holes,
            unqualified_holes=unqualified_holes,
            defect_data=defect_data,
            manual_reviews=manual_reviews,
            charts_data=charts_data,
            images_data=images_data
        )
        
        print(f"✅ 工件 {workpiece_id} 数据收集完成")
        print(f"   总孔位: {len(all_hole_data)}")
        print(f"   合格孔位: {len(qualified_holes)}")
        print(f"   不合格孔位: {len(unqualified_holes)}")
        print(f"   缺陷记录: {len(defect_data)}")
        print(f"   人工复检: {len(manual_reviews)}")
        
        return report_data
    
    def _collect_workpiece_info(self, workpiece_id: str) -> WorkpieceInfo:
        """收集工件基本信息"""
        # 根据工件ID返回相应的工件信息
        if workpiece_id == "CAP1000":
            return WorkpieceInfo(
                workpiece_id=workpiece_id,
                name="工件-CAP1000",
                type="管板工件",
                material="母材材质：SA508.Gr3. C1.2；堆焊层材质：镍基堆焊层",
                total_holes=20050,  # 该工件包含20000个孔
                description="管孔检测系统工件，包含20050个孔位，目前已有R001C001~R001C003孔位的检测数据",
                created_at=datetime.now()
            )
        elif workpiece_id.startswith('H'):
            # 单个孔位的情况
            return WorkpieceInfo(
                workpiece_id=workpiece_id,
                name=f"孔位-{workpiece_id}",
                type="单孔检测",
                material="母材材质：SA508.Gr3. C1.2；堆焊层材质：镍基堆焊层",
                total_holes=1,
                description=f"单个孔位 {workpiece_id} 的检测数据",
                created_at=datetime.now()
            )
        else:
            # 其他工件的默认信息
            return WorkpieceInfo(
                workpiece_id=workpiece_id,
                name=f"工件-{workpiece_id}",
                type="管板工件",
                material="母材材质：SA508.Gr3. C1.2；堆焊层材质：镍基堆焊层",
                total_holes=48,  # 默认值
                description="管孔检测系统测试工件",
                created_at=datetime.now()
            )
    
    def _collect_all_hole_quality_data(self, workpiece_id: str) -> List[HoleQualityData]:
        """收集所有孔位的质量数据"""
        hole_data_list = []

        # 对于单个孔位ID（如R001C001），直接处理该孔位
        if workpiece_id.startswith('R') and 'C' in workpiece_id:
            hole_id = workpiece_id
            hole_dir = self.data_root_path / hole_id
            if hole_dir.exists():
                hole_quality_data = self._collect_hole_quality_data(hole_id, hole_dir)
                if hole_quality_data:
                    hole_data_list.append(hole_quality_data)
            else:
                print(f"⚠️ 孔位数据目录不存在: {hole_dir}")
        else:
            # 对于工件ID（如CAP1000），扫描Data目录下所有新格式的孔位目录
            print(f"📊 扫描工件 {workpiece_id} 的所有孔位数据...")

            # 直接扫描Data目录下的所有新格式孔位目录（R开头且包含C）
            for hole_dir in self.data_root_path.iterdir():
                if hole_dir.is_dir() and hole_dir.name.startswith('R') and 'C' in hole_dir.name:
                    hole_id = hole_dir.name
                    print(f"   处理孔位: {hole_id}")
                    hole_quality_data = self._collect_hole_quality_data(hole_id, hole_dir)
                    if hole_quality_data:
                        hole_data_list.append(hole_quality_data)
                        print(f"   ✅ 孔位 {hole_id} 数据收集成功")
                    else:
                        print(f"   ⚠️ 孔位 {hole_id} 数据收集失败")

        return hole_data_list
    
    def _collect_hole_quality_data(self, hole_id: str, hole_dir: Path) -> Optional[HoleQualityData]:
        """收集单个孔位的质量数据"""
        try:
            # 查找CCIDM目录下的CSV文件
            ccidm_dir = hole_dir / "CCIDM"
            if not ccidm_dir.exists():
                return None
            
            # 查找最新的测量数据文件
            csv_files = list(ccidm_dir.glob("measurement_data_*.csv"))
            if not csv_files:
                return None
            
            # 使用最新的CSV文件
            latest_csv = max(csv_files, key=lambda f: f.stat().st_mtime)
            
            # 读取CSV数据，尝试多种编码
            measured_diameters = []
            encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']

            for encoding in encodings:
                try:
                    with open(latest_csv, 'r', encoding=encoding) as f:
                        reader = csv.reader(f)
                        header = next(reader)  # 跳过标题行

                        # 查找直径列的索引（通常是最后一列）
                        diameter_col_index = -1  # 默认使用最后一列

                        for row in reader:
                            try:
                                if len(row) > abs(diameter_col_index):
                                    diameter = float(row[diameter_col_index])
                                    if diameter > 0:  # 过滤无效数据
                                        measured_diameters.append(diameter)
                            except (ValueError, TypeError, IndexError):
                                continue
                    break  # 如果成功读取，跳出循环
                except (UnicodeDecodeError, FileNotFoundError):
                    continue  # 尝试下一种编码
            
            if not measured_diameters:
                return None
            
            # 计算质量统计
            qualified_count = sum(
                1 for d in measured_diameters
                if self.standard_diameter - self.lower_tolerance <= d <= self.standard_diameter + self.upper_tolerance
            )
            total_count = len(measured_diameters)
            qualification_rate = (qualified_count / total_count * 100) if total_count > 0 else 0.0
            is_qualified = qualification_rate >= 95.0  # 95%以上认为合格
            
            # 计算偏差统计
            deviations = [d - self.standard_diameter for d in measured_diameters]
            deviation_stats = {
                'min': min(deviations),
                'max': max(deviations),
                'avg': np.mean(deviations),
                'std': np.std(deviations)
            }
            
            # 估算孔位坐标（基于孔位ID）
            position_x, position_y = self._estimate_hole_position(hole_id)
            
            return HoleQualityData(
                hole_id=hole_id,
                position_x=position_x,
                position_y=position_y,
                target_diameter=self.standard_diameter,
                tolerance_upper=self.upper_tolerance,
                tolerance_lower=self.lower_tolerance,
                measured_diameters=measured_diameters,
                qualified_count=qualified_count,
                total_count=total_count,
                qualification_rate=qualification_rate,
                is_qualified=is_qualified,
                deviation_stats=deviation_stats,
                measurement_timestamp=datetime.fromtimestamp(latest_csv.stat().st_mtime)
            )
            
        except Exception as e:
            print(f"❌ 收集孔位 {hole_id} 数据失败: {e}")
            return None
    
    def _estimate_hole_position(self, hole_id: str) -> Tuple[float, float]:
        """根据孔位ID估算坐标位置"""
        try:
            # 使用HoleIdMapper来估算新格式ID的位置
            if HoleIdMapper.is_new_format(hole_id):
                return HoleIdMapper.estimate_position_from_new_id(hole_id)

            # 兼容旧格式ID的处理
            if hole_id.startswith('H'):
                hole_number = int(hole_id[1:])  # 去掉'H'前缀

                # 假设6x8布局，从左上角开始编号
                cols = 8
                row = (hole_number - 1) // cols
                col = (hole_number - 1) % cols

                # 估算坐标（基于标准间距）
                start_x, start_y = -140, -100
                spacing_x, spacing_y = 40, 35

                x = start_x + col * spacing_x
                y = start_y + row * spacing_y

                return x, y

            return 0.0, 0.0

        except (ValueError, IndexError):
            return 0.0, 0.0
    
    def _collect_defect_data(self, workpiece_id: str) -> List[DefectData]:
        """收集缺陷数据"""
        # 这里应该从标注系统收集缺陷数据
        # 暂时返回空列表，后续实现
        return []
    
    def _collect_manual_reviews(self, workpiece_id: str) -> List[ManualReviewRecord]:
        """收集人工复检记录"""
        # 这里应该从数据库收集人工复检记录
        # 暂时返回空列表，后续实现
        return []
    
    def _generate_quality_summary(self, hole_data: List[HoleQualityData], 
                                defect_data: List[DefectData],
                                manual_reviews: List[ManualReviewRecord]) -> QualitySummary:
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
        
        # 统计有缺陷的孔位
        holes_with_defects = len(set(defect.hole_id for defect in defect_data))
        
        # 统计人工复检数量
        manual_review_count = len(manual_reviews)
        
        # 计算直径统计
        all_diameters = []
        for hole in hole_data:
            all_diameters.extend(hole.measured_diameters)
        
        diameter_statistics = {}
        if all_diameters:
            diameter_statistics = {
                'min': min(all_diameters),
                'max': max(all_diameters),
                'avg': np.mean(all_diameters),
                'std': np.std(all_diameters),
                'count': len(all_diameters)
            }
        
        return QualitySummary(
            total_holes=total_holes,
            qualified_holes=qualified_holes,
            unqualified_holes=unqualified_holes,
            qualification_rate=qualification_rate,
            holes_with_defects=holes_with_defects,
            manual_review_count=manual_review_count,
            completion_rate=100.0,  # 假设所有孔位都已检测完成
            diameter_statistics=diameter_statistics
        )
    
    def _generate_charts_data(self, hole_data: List[HoleQualityData]) -> Dict[str, Any]:
        """生成图表数据"""
        charts_data = {}
        
        if hole_data:
            # 合格率分布数据
            qualification_rates = [hole.qualification_rate for hole in hole_data]
            charts_data['qualification_distribution'] = {
                'hole_ids': [hole.hole_id for hole in hole_data],
                'rates': qualification_rates
            }
            
            # 直径分布数据
            all_diameters = []
            for hole in hole_data:
                all_diameters.extend(hole.measured_diameters)
            
            charts_data['diameter_distribution'] = {
                'diameters': all_diameters,
                'standard': self.standard_diameter,
                'upper_limit': self.standard_diameter + self.upper_tolerance,
                'lower_limit': self.standard_diameter - self.lower_tolerance
            }
        
        return charts_data
    
    def _collect_images_data(self, workpiece_id: str) -> Dict[str, str]:
        """收集图像数据路径"""
        images_data = {}

        # 对于单个孔位ID
        if workpiece_id.startswith('H'):
            hole_dir = self.data_root_path / workpiece_id
            if hole_dir.exists():
                endoscope_dir = hole_dir / "endoscope"
                if endoscope_dir.exists():
                    image_files = list(endoscope_dir.glob("*.jpg")) + list(endoscope_dir.glob("*.png"))
                    if image_files:
                        images_data[workpiece_id] = str(image_files[0])
        else:
            # 对于工件ID，扫描Data目录下所有H开头的孔位目录
            for hole_dir in self.data_root_path.iterdir():
                if hole_dir.is_dir() and hole_dir.name.startswith('H'):
                    hole_id = hole_dir.name

                    # 查找内窥镜图像
                    endoscope_dir = hole_dir / "endoscope"
                    if endoscope_dir.exists():
                        image_files = list(endoscope_dir.glob("*.jpg")) + list(endoscope_dir.glob("*.png"))
                        if image_files:
                            # 使用第一张图像
                            images_data[hole_id] = str(image_files[0])

        return images_data
    
    def generate_report_instance(self, workpiece_id: str, 
                                config: ReportConfiguration) -> ReportInstance:
        """生成报告实例"""
        instance_id = str(uuid.uuid4())
        
        # 创建输出目录
        output_dir = Path("reports") / workpiece_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成输出文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{workpiece_id}_{timestamp}.{config.report_format.value}"
        output_path = output_dir / filename
        
        return ReportInstance(
            instance_id=instance_id,
            workpiece_id=workpiece_id,
            template_id="default",
            configuration=config,
            output_path=str(output_path),
            status="pending"
        )
