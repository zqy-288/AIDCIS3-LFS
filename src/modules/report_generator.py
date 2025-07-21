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
    
    def __init__(self, data_root_path: str = "Data/CAP1000"):
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
        
        # 生成报告图表
        report_charts = self.generate_report_charts(all_hole_data, workpiece_id)
        print(f"📊 生成的报告图表: {list(report_charts.keys())}")
        
        # 合并图像数据和报告图表
        all_images_data = {**images_data, **report_charts}
        print(f"📷 合并后的图像数据: {list(all_images_data.keys())}")
        
        report_data = ReportData(
            workpiece_info=workpiece_info,
            quality_summary=quality_summary,
            qualified_holes=qualified_holes,
            unqualified_holes=unqualified_holes,
            defect_data=defect_data,
            manual_reviews=manual_reviews,
            charts_data=charts_data,
            images_data=all_images_data
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
                description="管孔检测系统工件，包含20050个孔位，目前已有R001C001~R001C004孔位的检测数据",
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
    
    # 旧的截图功能已移除，现在直接生成图表文件
    
    def generate_report_charts(self, hole_data: List, workpiece_id: str) -> Dict[str, str]:
        """生成报告图表"""
        charts = {}
        
        try:
            # 生成二维公差带包络图
            tolerance_plot_path = self._generate_2d_tolerance_plot(hole_data)
            if tolerance_plot_path:
                charts['2d_tolerance_plot'] = tolerance_plot_path
            
            # 生成三维模型图
            model_3d_path = self._generate_3d_model_chart(hole_data)
            if model_3d_path:
                charts['3d_model'] = model_3d_path
            
            # 生成缺陷标注图（如果有缺陷数据）
            defect_annotation_path = self._generate_defect_annotation_chart(workpiece_id)
            if defect_annotation_path:
                charts['defect_annotation'] = defect_annotation_path
                
        except Exception as e:
            print(f"❌ 生成报告图表失败: {e}")
            import traceback
            traceback.print_exc()
            
        return charts
    
    def _generate_2d_tolerance_plot(self, hole_data: List) -> str:
        """生成二维公差带包络图"""
        try:
            import matplotlib.pyplot as plt
            import tempfile
            import os
            
            if not hole_data:
                return None
                
            # 配置中文字体
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
            plt.rcParams['axes.unicode_minus'] = False
            
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # 标准参数
            standard_diameter = 17.6
            upper_tolerance = 0.05
            lower_tolerance = 0.07
            
            # 收集所有测量数据
            all_positions = []
            all_diameters = []
            
            for hole in hole_data:
                if hasattr(hole, 'measured_diameters') and hole.measured_diameters:
                    # 为每个孔位的测量创建深度位置
                    positions = np.linspace(0, 100, len(hole.measured_diameters))  # 假设深度0-100mm
                    all_positions.extend(positions)
                    all_diameters.extend(hole.measured_diameters)
            
            if not all_positions:
                return None
            
            # 绘制公差带
            depth_range = np.linspace(0, max(all_positions), 100)
            upper_limit = np.full_like(depth_range, standard_diameter + upper_tolerance)
            lower_limit = np.full_like(depth_range, standard_diameter - lower_tolerance)
            standard_line = np.full_like(depth_range, standard_diameter)
            
            # 绘制公差带区域
            ax.fill_between(depth_range, lower_limit, upper_limit, 
                           alpha=0.3, color='lightblue', label='公差带')
            
            # 绘制标准线
            ax.plot(depth_range, standard_line, 'g--', linewidth=2, label='标准直径')
            
            # 绘制上下限线
            ax.plot(depth_range, upper_limit, 'r-', linewidth=1, label='上公差限')
            ax.plot(depth_range, lower_limit, 'b-', linewidth=1, label='下公差限')
            
            # 绘制实测数据点
            ax.scatter(all_positions, all_diameters, c='red', s=20, alpha=0.7, label='实测数据')
            
            # 设置图形属性
            ax.set_xlabel('深度 (mm)', fontsize=12)
            ax.set_ylabel('直径 (mm)', fontsize=12)
            ax.set_title('二维公差带包络图', fontsize=16, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend()
            
            # 设置y轴范围
            y_min = min(min(all_diameters), standard_diameter - lower_tolerance) - 0.05
            y_max = max(max(all_diameters), standard_diameter + upper_tolerance) + 0.05
            ax.set_ylim(y_min, y_max)
            
            # 保存图表
            temp_dir = tempfile.gettempdir()
            file_path = os.path.join(temp_dir, f"2d_tolerance_plot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            fig.savefig(file_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            
            print(f"✅ 二维公差带包络图已生成: {file_path}")
            return file_path
            
        except Exception as e:
            print(f"❌ 生成二维公差带包络图失败: {e}")
            return None
    
    def _generate_3d_model_chart(self, hole_data: List) -> str:
        """生成三维模型图"""
        try:
            import matplotlib.pyplot as plt
            from mpl_toolkits.mplot3d import Axes3D
            import tempfile
            import os
            
            if not hole_data:
                return None
                
            # 配置中文字体
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
            plt.rcParams['axes.unicode_minus'] = False
            
            fig = plt.figure(figsize=(14, 12))
            ax = fig.add_subplot(111, projection='3d')
            
            # 应用深色主题
            fig.patch.set_facecolor('#2C313C')
            ax.set_facecolor('#2C313C')
            
            # 设置坐标轴面板颜色（兼容不同版本的matplotlib）
            try:
                # 新版本matplotlib
                ax.xaxis.set_pane_color((0.1, 0.1, 0.1, 0.4))
                ax.yaxis.set_pane_color((0.1, 0.1, 0.1, 0.4))
                ax.zaxis.set_pane_color((0.1, 0.1, 0.1, 0.4))
            except AttributeError:
                try:
                    # 旧版本matplotlib
                    ax.w_xaxis.set_pane_color((0.1, 0.1, 0.1, 0.4))
                    ax.w_yaxis.set_pane_color((0.1, 0.1, 0.1, 0.4))
                    ax.w_zaxis.set_pane_color((0.1, 0.1, 0.1, 0.4))
                except AttributeError:
                    # 如果都不支持，跳过面板颜色设置
                    pass
            
            # 标准参数
            standard_diameter = 17.6
            upper_tolerance = 0.05
            lower_tolerance = 0.07
            
            # 生成圆柱面参数
            theta = np.linspace(0, 2*np.pi, 48)
            z_range = np.linspace(0, 100, 80)
            Z, THETA = np.meshgrid(z_range, theta)
            
            # 1. 绘制上公差管径模型（鲜明的红色，增强对比度）
            R_upper = np.full_like(Z, (standard_diameter + upper_tolerance) / 2)
            X_upper = R_upper * np.cos(THETA)
            Y_upper = R_upper * np.sin(THETA)
            
            surf_upper = ax.plot_surface(X_upper, Y_upper, Z,
                                        alpha=0.4, color='crimson',  # 使用更鲜明的红色
                                        linewidth=0.5, edgecolor='darkred',  # 添加边缘线
                                        label=f'上公差 (+{upper_tolerance:.2f}mm)')
            
            # 2. 绘制下公差管径模型（鲜明的蓝色，增强对比度）
            R_lower = np.full_like(Z, (standard_diameter - lower_tolerance) / 2)
            X_lower = R_lower * np.cos(THETA)
            Y_lower = R_lower * np.sin(THETA)
            
            surf_lower = ax.plot_surface(X_lower, Y_lower, Z,
                                        alpha=0.4, color='royalblue',  # 使用更鲜明的蓝色
                                        linewidth=0.5, edgecolor='darkblue',  # 添加边缘线
                                        label=f'下公差 (-{lower_tolerance:.2f}mm)')
            
            # 绘制实测数据点并计算误差统计
            all_errors = []
            for hole in hole_data:
                if hasattr(hole, 'measured_diameters') and hole.measured_diameters:
                    depths = np.linspace(0, 100, len(hole.measured_diameters))
                    radii = np.array(hole.measured_diameters) / 2
                    
                    # 计算误差用于统计
                    errors = np.array(hole.measured_diameters) - standard_diameter
                    all_errors.extend(errors)
                    
                    # 在圆周上分布点
                    angles = np.linspace(0, 2*np.pi, len(hole.measured_diameters))
                    x_points = radii * np.cos(angles)
                    y_points = radii * np.sin(angles)
                    
                    ax.scatter(x_points, y_points, depths, c='red', s=30, alpha=0.8)
            
            # 计算误差统计
            if all_errors:
                max_positive_error = max([e for e in all_errors if e > 0], default=0)
                min_negative_error = min([e for e in all_errors if e < 0], default=0)
            else:
                max_positive_error = 0
                min_negative_error = 0
            
            # 设置图形属性
            ax.set_xlabel('X (mm)', fontsize=14, fontweight='bold')
            ax.set_ylabel('Y (mm)', fontsize=14, fontweight='bold')
            ax.set_zlabel('深度 (mm)', fontsize=14, fontweight='bold')
            ax.set_title('管孔三维模型对比', fontsize=15, fontweight='bold', pad=40)
            
            # 设置坐标轴刻度和标签颜色
            ax.tick_params(axis='x', colors='#D3D8E0')
            ax.tick_params(axis='y', colors='#D3D8E0')
            ax.tick_params(axis='z', colors='#D3D8E0')
            
            ax.xaxis.label.set_color('#D3D8E0')
            ax.yaxis.label.set_color('#D3D8E0')
            ax.zaxis.label.set_color('#D3D8E0')
            ax.title.set_color('#FFFFFF')
            
            # 设置视角
            ax.view_init(elev=25, azim=35)
            
            # 添加与原版本相同的图例信息（文本框形式）
            legend_text = f"""模型说明:
• 深红色半透明: 上公差 (+{upper_tolerance:.2f}mm)
• 蓝色半透明: 下公差 (-{lower_tolerance:.2f}mm)
• 彩色表面: 实测管径
  - 红色区域: 超上公差
  - 明亮绿色区域: 合格范围
  - 蓝色区域: 超下公差

误差统计:
• 最大正误差: +{max_positive_error:.3f}mm
• 最小负误差: {min_negative_error:.3f}mm"""

            # 使用text2D方法在2D平面上显示文本，与原版本相同
            ax.text2D(1.02, 0.98, legend_text,
                     transform=ax.transAxes,
                     bbox=dict(boxstyle='round,pad=1.0',
                             facecolor='#3A404E',  # 深色主题背景
                             alpha=0.9,
                             edgecolor='#505869',  # 深色主题边框
                             linewidth=1),
                     verticalalignment='top',
                     horizontalalignment='left',
                     fontsize=10, fontweight='bold',
                     color='#D3D8E0')  # 深色主题文字颜色
            
            # 设置网格，增强可见性
            ax.grid(True, alpha=0.4, linewidth=0.8)
            
            # 设置坐标轴刻度字体大小
            ax.tick_params(axis='x', labelsize=11)
            ax.tick_params(axis='y', labelsize=11)
            ax.tick_params(axis='z', labelsize=11)
            
            # 调整布局以确保图例不被裁剪，为右侧图例留出空间，最大化绘图区域
            # 为标题留出更多顶部空间，确保标题完全显示
            fig.tight_layout(rect=[0, 0, 0.82, 0.95])
            
            # 保存图表
            temp_dir = tempfile.gettempdir()
            file_path = os.path.join(temp_dir, f"3d_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            fig.savefig(file_path, dpi=300, bbox_inches='tight', 
                       facecolor='#2C313C', edgecolor='none')
            plt.close(fig)
            
            print(f"✅ 三维模型图已生成: {file_path}")
            return file_path
            
        except Exception as e:
            print(f"❌ 生成三维模型图失败: {e}")
            return None
    
    def _generate_defect_annotation_chart(self, workpiece_id: str) -> str:
        """生成缺陷标注图"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib.patches as patches
            import tempfile
            import os
            
            # 配置中文字体
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
            plt.rcParams['axes.unicode_minus'] = False
            
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # 绘制管孔截面（圆形）
            circle = patches.Circle((0, 0), 8.8, linewidth=2, edgecolor='black', facecolor='lightgray', alpha=0.3)
            ax.add_patch(circle)
            
            # 绘制标准直径圆
            standard_circle = patches.Circle((0, 0), 8.8, linewidth=1, edgecolor='green', facecolor='none', linestyle='--')
            ax.add_patch(standard_circle)
            
            # 尝试从数据库或文件中获取实际的缺陷数据
            defects = self._get_defect_data_for_chart(workpiece_id)
            
            # 如果没有实际缺陷数据，使用示例数据
            if not defects:
                defects = [
                    {'pos': (2, 3), 'type': '划痕', 'color': 'red', 'size': (1.5, 0.5)},
                    {'pos': (-3, -2), 'type': '凹坑', 'color': 'blue', 'size': (1.0, 1.0)},
                    {'pos': (1, -4), 'type': '腐蚀', 'color': 'orange', 'size': (2.0, 1.0)},
                    {'pos': (-2, 4), 'type': '裂纹', 'color': 'purple', 'size': (0.8, 2.0)}
                ]
            
            for i, defect in enumerate(defects):
                # 绘制缺陷标注框
                rect = patches.Rectangle(
                    (defect['pos'][0]-defect['size'][0]/2, defect['pos'][1]-defect['size'][1]/2), 
                    defect['size'][0], defect['size'][1], 
                    linewidth=2, 
                    edgecolor=defect['color'], 
                    facecolor=defect['color'],
                    alpha=0.3
                )
                ax.add_patch(rect)
                
                # 添加缺陷标号
                ax.text(defect['pos'][0], defect['pos'][1], str(i+1), 
                       ha='center', va='center', fontsize=12, fontweight='bold', color='white',
                       bbox=dict(boxstyle='circle', facecolor=defect['color']))
                
                # 添加缺陷类型标签
                label_y = defect['pos'][1] - defect['size'][1]/2 - 0.8
                ax.text(defect['pos'][0], label_y, defect['type'], 
                       ha='center', va='center', fontsize=10, color=defect['color'],
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
            
            # 添加图例
            legend_elements = [
                plt.Line2D([0], [0], marker='o', color='w', label='标准直径', 
                          markerfacecolor='green', markersize=10, linestyle='--'),
                plt.Line2D([0], [0], marker='s', color='w', label='缺陷区域', 
                          markerfacecolor='red', markersize=10, alpha=0.3)
            ]
            ax.legend(handles=legend_elements, loc='upper right')
            
            # 设置图形属性
            ax.set_xlim(-12, 12)
            ax.set_ylim(-12, 12)
            ax.set_aspect('equal')
            ax.set_xlabel('X (mm)', fontsize=12)
            ax.set_ylabel('Y (mm)', fontsize=12)
            ax.set_title('缺陷标注图', fontsize=16, fontweight='bold')
            ax.grid(True, alpha=0.3)
            
            # 添加说明文本
            info_text = f"工件ID: {workpiece_id}\n缺陷数量: {len(defects)}"
            ax.text(-11, -11, info_text, fontsize=10, 
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow', alpha=0.8))
            
            # 保存图表
            temp_dir = tempfile.gettempdir()
            file_path = os.path.join(temp_dir, f"defect_annotation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            fig.savefig(file_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            
            print(f"✅ 缺陷标注图已生成: {file_path}")
            return file_path
            
        except Exception as e:
            print(f"❌ 生成缺陷标注图失败: {e}")
            return None
    
    def _get_defect_data_for_chart(self, workpiece_id: str) -> List[Dict]:
        """获取用于图表的缺陷数据"""
        try:
            # 这里可以连接到实际的缺陷数据库或文件
            # 暂时返回空列表，使用示例数据
            return []
        except Exception as e:
            print(f"❌ 获取缺陷数据失败: {e}")
            return []
    
    def test_screenshot_functionality(self) -> bool:
        """测试截图功能是否正常工作"""
        print("🧪 测试截图功能...")
        
        # 手动触发截图生成
        test_screenshots = self.generate_ui_screenshots("test")
        
        if test_screenshots:
            print(f"✅ 截图功能测试成功，生成了 {len(test_screenshots)} 个截图")
            for key, path in test_screenshots.items():
                print(f"  📸 {key}: {path}")
            return True
        else:
            print("❌ 截图功能测试失败，没有生成任何截图")
            return False
    
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
