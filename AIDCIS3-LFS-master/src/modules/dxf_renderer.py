"""
DXF文件渲染和编号模块
提供DXF文件的可视化渲染和孔位编号功能
"""

import os
import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import numpy as np

try:
    import ezdxf
    from ezdxf.document import Drawing
    EZDXF_AVAILABLE = True
    DrawingType = Drawing
except ImportError:
    EZDXF_AVAILABLE = False
    DrawingType = object

try:
    import matplotlib
    # 设置非GUI后端，避免线程安全问题
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from matplotlib.patches import Circle, Arc
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from src.modules.dxf_import import get_dxf_importer, DXFHoleInfo, DXFAnalysisResult

@dataclass
class HoleAnnotation:
    """孔位标注信息"""
    hole: DXFHoleInfo
    number: int
    label: str
    label_position: Tuple[float, float]
    
@dataclass
class DXFRenderResult:
    """DXF渲染结果"""
    holes: List[DXFHoleInfo]
    annotations: List[HoleAnnotation]
    boundary_info: Dict
    rendered_image_path: Optional[str] = None
    hole_table_data: List[Dict] = None

class DXFRenderer:
    """DXF文件渲染器"""
    
    def __init__(self):
        self.dxf_importer = get_dxf_importer()
        self._setup_numbering_strategies()
        
    def check_dependencies(self) -> Dict[str, bool]:
        """检查依赖库"""
        return {
            'ezdxf': EZDXF_AVAILABLE,
            'matplotlib': MATPLOTLIB_AVAILABLE
        }
    
    def render_dxf_with_numbering(self, dxf_file_path: str, 
                                output_path: Optional[str] = None,
                                numbering_strategy: str = "grid") -> DXFRenderResult:
        """渲染DXF文件并添加孔位编号"""
        import time
        start_time = time.time()
        print(f"\n🛠️ [DXF渲染] 开始渲染过程...")
        print(f"   • 输入文件: {dxf_file_path}")
        print(f"   • 编号策略: {numbering_strategy}")
        print(f"   • 输出路径: {output_path}")
        
        if not EZDXF_AVAILABLE:
            print(f"\n❌ [DXF渲染] ezdxf库未安装")
            raise ImportError("ezdxf库未安装。请运行: pip install ezdxf")
        
        if not MATPLOTLIB_AVAILABLE:
            print(f"\n❌ [DXF渲染] matplotlib库未安装")
            raise ImportError("matplotlib库未安装。请运行: pip install matplotlib")
        
        # 1. 解析DXF文件
        parse_start = time.time()
        print(f"\n📄 [DXF渲染] 步面1/4: 解析DXF文件...")
        analysis_result = self.dxf_importer.import_from_dxf(dxf_file_path)
        parse_time = time.time() - parse_start
        
        if not analysis_result:
            print(f"\n❌ [DXF渲染] DXF文件解析失败")
            raise ValueError("DXF文件解析失败")
        
        print(f"   ✓ 解析完成: {len(analysis_result.holes)}个孔位, 耗时 {parse_time:.3f}s")
        
        # 2. 对孔位进行编号
        annotation_start = time.time()
        print(f"\n📝 [DXF渲染] 步面2/4: 创建孔位标注...")
        annotations = self._create_hole_annotations(analysis_result.holes, numbering_strategy)
        annotation_time = time.time() - annotation_start
        print(f"   ✓ 标注完成: {len(annotations)}个标注, 耗时 {annotation_time:.3f}s")
        
        # 3. 渲染图形
        rendered_image_path = None
        if output_path:
            render_start = time.time()
            print(f"\n🎨 [DXF渲染] 步面3/4: 渲染图像...")
            rendered_image_path = self._render_to_image(
                analysis_result, annotations, output_path
            )
            render_time = time.time() - render_start
            print(f"   ✓ 图像渲染完成: {rendered_image_path}, 耗时 {render_time:.3f}s")
        else:
            print(f"\n⏭️ [DXF渲染] 步面3/4: 跳过图像渲染 (无输出路径)")
        
        # 4. 生成孔位表数据
        table_start = time.time()
        print(f"\n📈 [DXF渲染] 步面4/4: 生成孔位表数据...")
        hole_table_data = self._generate_hole_table(annotations)
        table_time = time.time() - table_start
        print(f"   ✓ 表格生成完成: {len(hole_table_data)}行数据, 耗时 {table_time:.3f}s")
        
        total_time = time.time() - start_time
        print(f"\n✨ [DXF渲染] 渲染完成! 总耗时: {total_time:.3f}s")
        print(f"   • 解析时间: {parse_time:.3f}s ({parse_time/total_time*100:.1f}%)")
        print(f"   • 标注时间: {annotation_time:.3f}s ({annotation_time/total_time*100:.1f}%)")
        if output_path:
            print(f"   • 渲染时间: {render_time:.3f}s ({render_time/total_time*100:.1f}%)")
        print(f"   • 表格时间: {table_time:.3f}s ({table_time/total_time*100:.1f}%)")
        print(f"   • 最终结果: {len(analysis_result.holes)}个孔位, {len(annotations)}个标注")
        
        return DXFRenderResult(
            holes=analysis_result.holes,
            annotations=annotations,
            boundary_info=analysis_result.boundary_info,
            rendered_image_path=rendered_image_path,
            hole_table_data=hole_table_data
        )
    
    def _create_hole_annotations(self, holes: List[DXFHoleInfo], numbering_strategy: str) -> List[HoleAnnotation]:
        """创建孔位标注 - 使用独立的编号策略"""
        
        if numbering_strategy not in self.hole_numbering_strategies:
            available = list(self.hole_numbering_strategies.keys())
            raise ValueError(f"不支持的编号策略: {numbering_strategy}，可用策略: {available}")
        
        # 使用指定的编号策略
        strategy_func = self.hole_numbering_strategies[numbering_strategy]
        return strategy_func(holes)
    
    def _setup_numbering_strategies(self):
        """设置编号策略"""
        self.hole_numbering_strategies = {
            'grid': self._grid_numbering,
            'left_to_right': self._left_to_right_numbering,
            'top_to_bottom': self._top_to_bottom_numbering,
            'spiral': self._spiral_numbering,
            'distance': self._distance_based_numbering
        }
    
    def _grid_numbering(self, holes: List[DXFHoleInfo]) -> List[HoleAnnotation]:
        """网格编号策略 - 按行列排序"""
        if not holes:
            return []
        
        print(f"   🔢 使用网格编号策略")
        
        # 按Y坐标分组（行），然后在每行内按X坐标排序
        tolerance = 5.0  # 同一行的Y坐标容差
        
        # 将孔位按Y坐标分组
        rows = {}
        for hole in holes:
            # 找到最接近的已有行，或创建新行
            assigned = False
            for row_y in rows.keys():
                if abs(hole.center_y - row_y) <= tolerance:
                    rows[row_y].append(hole)
                    assigned = True
                    break
            
            if not assigned:
                rows[hole.center_y] = [hole]
        
        # 对每行按X坐标排序，然后按行Y坐标排序
        annotations = []
        number = 1
        
        for row_y in sorted(rows.keys(), reverse=True):  # 从上到下
            row_holes = sorted(rows[row_y], key=lambda h: h.center_x)  # 从左到右
            
            for hole in row_holes:
                label = f"H{number:03d}"
                offset = hole.diameter * 0.6
                label_position = (hole.center_x + offset, hole.center_y + offset)
                
                annotations.append(HoleAnnotation(
                    hole=hole,
                    number=number,
                    label=label,
                    label_position=label_position
                ))
                number += 1
        
        print(f"   ✓ 网格编号完成: {len(annotations)}个孔位")
        return annotations
    
    def _left_to_right_numbering(self, holes: List[DXFHoleInfo]) -> List[HoleAnnotation]:
        """从左到右编号策略"""
        print(f"   🔢 使用从左到右编号策略")
        
        # 按X坐标排序
        sorted_holes = sorted(holes, key=lambda h: h.center_x)
        
        annotations = []
        for i, hole in enumerate(sorted_holes, 1):
            label = f"L{i:03d}"
            offset = hole.diameter * 0.6
            label_position = (hole.center_x + offset, hole.center_y + offset)
            
            annotations.append(HoleAnnotation(
                hole=hole,
                number=i,
                label=label,
                label_position=label_position
            ))
        
        print(f"   ✓ 从左到右编号完成: {len(annotations)}个孔位")
        return annotations
    
    def _top_to_bottom_numbering(self, holes: List[DXFHoleInfo]) -> List[HoleAnnotation]:
        """从上到下编号策略"""
        print(f"   🔢 使用从上到下编号策略")
        
        # 按Y坐标排序（DXF中Y值大的在上方）
        sorted_holes = sorted(holes, key=lambda h: h.center_y, reverse=True)
        
        annotations = []
        for i, hole in enumerate(sorted_holes, 1):
            label = f"T{i:03d}"
            offset = hole.diameter * 0.6
            label_position = (hole.center_x + offset, hole.center_y + offset)
            
            annotations.append(HoleAnnotation(
                hole=hole,
                number=i,
                label=label,
                label_position=label_position
            ))
        
        print(f"   ✓ 从上到下编号完成: {len(annotations)}个孔位")
        return annotations
    
    def _spiral_numbering(self, holes: List[DXFHoleInfo]) -> List[HoleAnnotation]:
        """螺旋编号策略 - 从中心向外螺旋"""
        print(f"   🔢 使用螺旋编号策略")
        
        if not holes:
            return []
        
        # 计算几何中心
        center_x = sum(h.center_x for h in holes) / len(holes)
        center_y = sum(h.center_y for h in holes) / len(holes)
        
        # 按距离中心的距离和角度排序
        def spiral_key(hole):
            dx = hole.center_x - center_x
            dy = hole.center_y - center_y
            distance = math.sqrt(dx*dx + dy*dy)
            angle = math.atan2(dy, dx)
            return (distance, angle)
        
        sorted_holes = sorted(holes, key=spiral_key)
        
        annotations = []
        for i, hole in enumerate(sorted_holes, 1):
            label = f"S{i:03d}"
            offset = hole.diameter * 0.6
            label_position = (hole.center_x + offset, hole.center_y + offset)
            
            annotations.append(HoleAnnotation(
                hole=hole,
                number=i,
                label=label,
                label_position=label_position
            ))
        
        print(f"   ✓ 螺旋编号完成: {len(annotations)}个孔位")
        return annotations
    
    def _distance_based_numbering(self, holes: List[DXFHoleInfo]) -> List[HoleAnnotation]:
        """基于距离的编号策略 - 最短路径遍历"""
        print(f"   🔢 使用距离编号策略")
        
        if not holes:
            return []
        
        # 使用贪心算法找最短路径
        remaining = holes.copy()
        ordered = [remaining.pop(0)]  # 从第一个孔开始
        
        while remaining:
            current = ordered[-1]
            # 找最近的下一个孔
            next_hole = min(remaining, key=lambda h: 
                math.sqrt((h.center_x - current.center_x)**2 + (h.center_y - current.center_y)**2))
            ordered.append(next_hole)
            remaining.remove(next_hole)
        
        annotations = []
        for i, hole in enumerate(ordered, 1):
            label = f"D{i:03d}"
            offset = hole.diameter * 0.6
            label_position = (hole.center_x + offset, hole.center_y + offset)
            
            annotations.append(HoleAnnotation(
                hole=hole,
                number=i,
                label=label,
                label_position=label_position
            ))
        
        print(f"   ✓ 距离编号完成: {len(annotations)}个孔位")
        return annotations
    
    
    
    
    
    
    def _render_to_image(self, analysis_result: DXFAnalysisResult, 
                        annotations: List[HoleAnnotation], 
                        output_path: str) -> str:
        """渲染到图像文件"""
        import time
        render_start = time.time()
        print(f"   🔧 [图像渲染] 初始化matplotlib后端...")
        
        # 确保使用非GUI后端（线程安全）
        import matplotlib
        matplotlib.use('Agg')
        backend_time = time.time() - render_start
        print(f"      ✓ matplotlib后端设置完成: {backend_time:.3f}s")
        
        fig_start = time.time()
        print(f"   📈 [图像渲染] 创建图形对象...")
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        fig_time = time.time() - fig_start
        print(f"      ✓ 图形对象创建完成: {fig_time:.3f}s")
        
        # 设置坐标轴
        axis_start = time.time()
        print(f"   📀 [图像渲染] 计算坐标轴范围...")
        all_x = [h.center_x for h in analysis_result.holes]
        all_y = [h.center_y for h in analysis_result.holes]
        
        if all_x and all_y:
            margin = 50  # 边距
            x_min, x_max = min(all_x) - margin, max(all_x) + margin
            y_min, y_max = min(all_y) - margin, max(all_y) + margin
            
            ax.set_xlim(x_min, x_max)
            ax.set_ylim(y_min, y_max)
            
            axis_time = time.time() - axis_start
            print(f"      ✓ 坐标轴设置: X[{x_min:.1f}, {x_max:.1f}], Y[{y_min:.1f}, {y_max:.1f}], 耗时 {axis_time:.3f}s")
        
        # 绘制边界（如果有）
        boundary_start = time.time()
        if analysis_result.boundary_info.get('has_boundary'):
            print(f"   🔲 [图像渲染] 绘制边界...")
            boundary = analysis_result.boundary_info
            if boundary['boundary_type'] == 'circle':
                dims = boundary['dimensions']
                boundary_circle = Circle(
                    dims['center'], dims['radius'],
                    fill=False, color='gray', linewidth=2, linestyle='--'
                )
                ax.add_patch(boundary_circle)
                boundary_time = time.time() - boundary_start
                print(f"      ✓ 圆形边界绘制完成: 中心{dims['center']}, 半径{dims['radius']}, 耗时 {boundary_time:.3f}s")
        else:
            print(f"   ⏭️ [图像渲染] 跳过边界绘制 (无边界信息)")
        
        # 绘制孔位
        holes_start = time.time()
        print(f"   ⚫ [图像渲染] 绘制{len(annotations)}个孔位...")
        holes_drawn = 0
        for annotation in annotations:
            holes_drawn += 1
            hole = annotation.hole
            
            # 绘制孔位圆圈
            hole_circle = Circle(
                (hole.center_x, hole.center_y), hole.diameter/2,
                fill=False, color='blue', linewidth=2
            )
            ax.add_patch(hole_circle)
            
            # 绘制中心点
            ax.plot(hole.center_x, hole.center_y, 'bo', markersize=3)
            
            # 绘制编号标注
            ax.annotate(
                annotation.label,
                xy=(hole.center_x, hole.center_y),
                xytext=annotation.label_position,
                fontsize=10, fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.3", facecolor='yellow', alpha=0.7),
                arrowprops=dict(arrowstyle='->', color='red', lw=1)
            )
        
        holes_time = time.time() - holes_start
        print(f"      ✓ 孔位绘制完成: {holes_drawn}个孔位, 耗时 {holes_time:.3f}s")
        
        # 设置图形属性
        style_start = time.time()
        print(f"   🎨 [图像渲染] 应用图形样式...")
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('X 坐标 (mm)')
        ax.set_ylabel('Y 坐标 (mm)')
        ax.set_title(f'DXF孔位图 - 共{len(annotations)}个孔')
        style_time = time.time() - style_start
        print(f"      ✓ 图形样式应用完成: {style_time:.3f}s")
        
        # 保存图像
        save_start = time.time()
        print(f"   💾 [图像渲染] 保存图像到: {output_path}")
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        save_time = time.time() - save_start
        print(f"      ✓ 图像保存完成: DPI=300, 耗时 {save_time:.3f}s")
        
        total_render_time = time.time() - render_start
        print(f"   ✨ [图像渲染] 渲染总耗时: {total_render_time:.3f}s")
        
        return output_path
    
    def _generate_hole_table(self, annotations: List[HoleAnnotation]) -> List[Dict]:
        """生成孔位表数据"""
        table_data = []
        
        for annotation in annotations:
            hole = annotation.hole
            row = {
                '编号': annotation.label,
                '序号': annotation.number,
                'X坐标(mm)': round(hole.center_x, 3),
                'Y坐标(mm)': round(hole.center_y, 3),
                '直径(mm)': round(hole.diameter, 3),
                '孔类型': hole.hole_type,
                '位置': f"({hole.center_x:.1f}, {hole.center_y:.1f})"
            }
            table_data.append(row)
        
        return table_data
    
    def export_hole_data(self, render_result: DXFRenderResult, 
                        export_path: str, format: str = 'csv') -> str:
        """导出孔位数据"""
        
        if format.lower() == 'csv':
            return self._export_to_csv(render_result.hole_table_data, export_path)
        elif format.lower() == 'excel':
            return self._export_to_excel(render_result.hole_table_data, export_path)
        else:
            raise ValueError(f"不支持的导出格式: {format}")
    
    def _export_to_csv(self, table_data: List[Dict], export_path: str) -> str:
        """导出到CSV文件"""
        import csv
        
        if not export_path.endswith('.csv'):
            export_path += '.csv'
        
        if table_data:
            with open(export_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = table_data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for row in table_data:
                    writer.writerow(row)
        
        return export_path
    
    def _export_to_excel(self, table_data: List[Dict], export_path: str) -> str:
        """导出到Excel文件"""
        try:
            import pandas as pd
            
            if not export_path.endswith('.xlsx'):
                export_path += '.xlsx'
            
            if table_data:
                df = pd.DataFrame(table_data)
                df.to_excel(export_path, index=False)
            
            return export_path
            
        except ImportError:
            raise ImportError("pandas库未安装。请运行: pip install pandas openpyxl")
    
    def create_numbered_dxf(self, original_dxf_path: str, 
                          output_dxf_path: str) -> str:
        """创建带编号的DXF文件"""
        
        if not EZDXF_AVAILABLE:
            raise ImportError("ezdxf库未安装")
        
        # 读取原DXF文件
        doc = ezdxf.readfile(original_dxf_path)
        
        # 解析和编号
        analysis_result = self.dxf_importer.import_from_dxf(original_dxf_path)
        annotations = self._create_hole_annotations(analysis_result.holes, "grid")
        
        # 在DXF中添加文本标注
        modelspace = doc.modelspace()
        
        for annotation in annotations:
            # 添加文本标注
            modelspace.add_text(
                annotation.label,
                dxfattribs={
                    'insert': annotation.label_position,
                    'height': annotation.hole.diameter * 0.3,  # 文字高度
                    'color': 1,  # 红色
                    'layer': 'HOLE_NUMBERS'
                }
            )
            
            # 添加引线（可选）
            modelspace.add_line(
                (annotation.hole.center_x, annotation.hole.center_y),
                annotation.label_position,
                dxfattribs={'color': 1, 'layer': 'HOLE_NUMBERS'}
            )
        
        # 保存新DXF文件
        doc.saveas(output_dxf_path)
        
        return output_dxf_path

# 单例实例
_dxf_renderer = None

def get_dxf_renderer():
    """获取DXF渲染器单例"""
    global _dxf_renderer
    if _dxf_renderer is None:
        _dxf_renderer = DXFRenderer()
    return _dxf_renderer