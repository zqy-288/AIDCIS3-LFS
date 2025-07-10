"""
独立的增强报告生成器（无GUI依赖）
专门用于集成包络图和内窥镜展开图的报告生成
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .standalone_report_generator import ReportGenerator, ReportData


class EnhancedReportGenerator(ReportGenerator):
    """增强的报告生成器，集成包络图和内窥镜展开图"""
    
    def __init__(self, db_manager=None):
        super().__init__(db_manager)
        self.chart_temp_dir = Path(tempfile.mkdtemp())
        self.chart_temp_dir.mkdir(exist_ok=True)
        
    def generate_comprehensive_pdf_report(self, hole_data: Dict, 
                                        workpiece_info: Dict,
                                        measurement_data: List[Dict] = None,
                                        endoscope_images: List[str] = None) -> str:
        """
        生成包含包络图和内窥镜展开图的综合PDF报告
        """
        # 准备报告数据
        report_data = self._prepare_enhanced_report_data(
            hole_data, workpiece_info, measurement_data, endoscope_images
        )
        
        # 生成图表和图像
        self._generate_report_charts(report_data, measurement_data)
        self._process_endoscope_images(report_data, endoscope_images)
        
        # 模拟PDF生成（实际环境中会调用父类方法）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_filename = f"comprehensive_report_{workpiece_info.get('model', 'TEST')}_{timestamp}.pdf"
        pdf_path = self.output_dir / pdf_filename
        
        # 创建模拟PDF文件
        with open(pdf_path, 'w') as f:
            f.write("Mock PDF Report Content")
            
        return str(pdf_path)
        
    def generate_envelope_chart_with_annotations(self, measurement_data: List[Dict], 
                                               target_diameter: float,
                                               upper_tolerance: float, 
                                               lower_tolerance: float,
                                               hole_id: str = "") -> str:
        """
        生成带详细标注的包络图
        """
        if not measurement_data:
            # 生成模拟数据用于演示
            measurement_data = self._generate_demo_measurement_data()
            
        # 准备数据
        depths = [d.get('depth', i * 0.1) for i, d in enumerate(measurement_data)]
        diameters = [d.get('diameter', target_diameter + np.random.normal(0, 0.01)) 
                    for d in measurement_data]
        
        # 创建图形
        fig, ax = plt.subplots(figsize=(14, 10))
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 绘制测量数据
        ax.plot(depths, diameters, 'b-', linewidth=2.5, label='实测直径', alpha=0.8)
        ax.scatter(depths[::10], diameters[::10], color='blue', s=20, alpha=0.6, zorder=5)
        
        # 计算公差带
        upper_limit = target_diameter + upper_tolerance
        lower_limit = target_diameter - lower_tolerance
        
        # 绘制公差带
        ax.axhline(y=upper_limit, color='red', linestyle='--', linewidth=2, 
                  label=f'上限 {upper_limit:.3f}mm (+{upper_tolerance:.3f})', alpha=0.8)
        ax.axhline(y=lower_limit, color='red', linestyle='--', linewidth=2, 
                  label=f'下限 {lower_limit:.3f}mm (-{lower_tolerance:.3f})', alpha=0.8)
        ax.axhline(y=target_diameter, color='green', linestyle='-', linewidth=2, 
                  label=f'目标直径 {target_diameter:.3f}mm', alpha=0.8)
        
        # 填充合格区域
        ax.fill_between(depths, upper_limit, lower_limit, alpha=0.15, color='green', 
                       label='合格区域')
        
        # 标记超差点
        out_of_spec_points = []
        for i, (depth, diameter) in enumerate(zip(depths, diameters)):
            if diameter > upper_limit or diameter < lower_limit:
                out_of_spec_points.append((depth, diameter, i))
                ax.scatter(depth, diameter, color='red', s=80, zorder=10, 
                          marker='X', linewidths=2, edgecolors='darkred')
                
                # 添加标注
                deviation = max(diameter - upper_limit, lower_limit - diameter)
                ax.annotate(f'{diameter:.3f}mm\n(超差{deviation:.3f})', 
                           (depth, diameter), 
                           xytext=(10, 10), textcoords='offset points',
                           bbox=dict(boxstyle='round,pad=0.5', 
                                   facecolor='red', alpha=0.8, edgecolor='darkred'),
                           color='white', fontweight='bold', fontsize=9,
                           arrowprops=dict(arrowstyle='->', color='red', lw=1.5))
        
        # 添加统计信息文本框
        stats_text = self._generate_statistics_text(diameters, target_diameter, 
                                                   upper_tolerance, lower_tolerance)
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
               verticalalignment='top', horizontalalignment='left',
               bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.8),
               fontsize=10, fontweight='bold')
        
        # 设置图形属性
        ax.set_xlabel('探头深度 (mm)', fontsize=14, fontweight='bold')
        ax.set_ylabel('孔径直径 (mm)', fontsize=14, fontweight='bold')
        
        title = f'孔径包络图 - 公差带分析'
        if hole_id:
            title += f' (孔位: {hole_id})'
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        
        ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        ax.legend(loc='upper right', fontsize=11, framealpha=0.9)
        
        # 设置Y轴范围（适当扩展以显示完整信息）
        y_margin = max(upper_tolerance, lower_tolerance) * 2
        ax.set_ylim(target_diameter - y_margin, target_diameter + y_margin)
        
        # 设置坐标轴刻度
        ax.tick_params(axis='both', which='major', labelsize=12)
        
        # 保存图片
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        chart_filename = f"envelope_chart_{hole_id}_{timestamp}.png"
        chart_path = self.chart_temp_dir / chart_filename
        
        plt.tight_layout()
        plt.savefig(chart_path, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close()
        
        return str(chart_path)
        
    def generate_endoscope_panorama(self, endoscope_images: List[str], 
                                  hole_id: str = "") -> str:
        """
        生成内窥镜全景展开图
        """
        if not endoscope_images:
            # 生成占位符图像
            return self._generate_placeholder_endoscope_image(hole_id)
            
        try:
            # 加载图像
            images = []
            for img_path in endoscope_images:
                if os.path.exists(img_path):
                    img = Image.open(img_path)
                    images.append(img)
                    
            if not images:
                return self._generate_placeholder_endoscope_image(hole_id)
            
            # 计算全景图尺寸
            max_width = max(img.width for img in images)
            total_height = sum(img.height for img in images)
            
            # 创建全景图画布
            panorama = Image.new('RGB', (max_width, total_height), 'white')
            
            # 拼接图像
            y_offset = 0
            for i, img in enumerate(images):
                # 调整图像大小到统一宽度
                if img.width != max_width:
                    aspect_ratio = img.height / img.width
                    new_height = int(max_width * aspect_ratio)
                    img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                
                panorama.paste(img, (0, y_offset))
                y_offset += img.height
                
            # 添加深度标记
            self._add_depth_markers(panorama, len(images))
            
            # 保存全景图
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            panorama_filename = f"endoscope_panorama_{hole_id}_{timestamp}.png"
            panorama_path = self.chart_temp_dir / panorama_filename
            
            panorama.save(panorama_path, 'PNG', quality=95)
            
            return str(panorama_path)
            
        except Exception as e:
            print(f"⚠️ 生成内窥镜全景图失败: {e}")
            return self._generate_placeholder_endoscope_image(hole_id)
            
    def generate_defect_annotation_overlay(self, base_image_path: str, 
                                         defect_annotations: List[Dict],
                                         hole_id: str = "") -> str:
        """
        生成带缺陷标注的内窥镜图像
        """
        try:
            if not os.path.exists(base_image_path):
                return self._generate_placeholder_endoscope_image(hole_id)
                
            # 打开基础图像
            base_img = Image.open(base_image_path)
            draw = ImageDraw.Draw(base_img)
            
            # 尝试设置字体
            try:
                font = ImageFont.truetype("arial.ttf", 16)
                small_font = ImageFont.truetype("arial.ttf", 12)
            except:
                font = ImageFont.load_default()
                small_font = font
            
            # 绘制缺陷标注
            for i, annotation in enumerate(defect_annotations):
                # 获取边界框坐标
                bbox = annotation.get('bbox', [])
                if len(bbox) >= 4:
                    x1, y1, x2, y2 = bbox[:4]
                    
                    # 绘制边界框
                    draw.rectangle([(x1, y1), (x2, y2)], 
                                 outline='red', width=3)
                    
                    # 添加标签
                    label = annotation.get('label', f'缺陷{i+1}')
                    confidence = annotation.get('confidence', 0)
                    
                    label_text = f'{label}'
                    if confidence > 0:
                        label_text += f' {confidence:.1%}'
                        
                    # 绘制标签背景
                    text_bbox = draw.textbbox((0, 0), label_text, font=font)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_height = text_bbox[3] - text_bbox[1]
                    
                    label_bg = (x1, y1 - text_height - 5, 
                               x1 + text_width + 10, y1)
                    draw.rectangle(label_bg, fill='red', outline='red')
                    
                    # 绘制标签文字
                    draw.text((x1 + 5, y1 - text_height - 2), 
                             label_text, fill='white', font=font)
            
            # 添加图例
            self._add_defect_legend(draw, base_img.size, font, small_font)
            
            # 保存标注图像
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            annotated_filename = f"endoscope_annotated_{hole_id}_{timestamp}.png"
            annotated_path = self.chart_temp_dir / annotated_filename
            
            base_img.save(annotated_path, 'PNG', quality=95)
            
            return str(annotated_path)
            
        except Exception as e:
            print(f"⚠️ 生成缺陷标注图像失败: {e}")
            return self._generate_placeholder_endoscope_image(hole_id)
            
    def _prepare_enhanced_report_data(self, hole_data: Dict, workpiece_info: Dict,
                                    measurement_data: List[Dict] = None,
                                    endoscope_images: List[str] = None) -> ReportData:
        """准备增强的报告数据"""
        report_data = super()._prepare_report_data(hole_data, workpiece_info)
        
        # 添加图表和图像路径
        if measurement_data:
            envelope_chart = self.generate_envelope_chart_with_annotations(
                measurement_data, 17.6, 0.05, 0.07, 
                hole_data.get('current_hole_id', 'H001')
            )
            report_data.charts['envelope'] = envelope_chart
            
        if endoscope_images:
            panorama = self.generate_endoscope_panorama(
                endoscope_images, hole_data.get('current_hole_id', 'H001')
            )
            report_data.images['endoscope_panorama'] = panorama
            
        return report_data
        
    def _generate_report_charts(self, report_data: ReportData, 
                              measurement_data: List[Dict] = None):
        """生成报告所需的图表"""
        if measurement_data:
            # 生成包络图
            envelope_chart = self.generate_envelope_chart_with_annotations(
                measurement_data, 17.6, 0.05, 0.07
            )
            report_data.charts['envelope'] = envelope_chart
            
            # 生成统计图表
            stats_chart = self._generate_statistics_chart(measurement_data)
            report_data.charts['statistics'] = stats_chart
            
    def _process_endoscope_images(self, report_data: ReportData, 
                                endoscope_images: List[str] = None):
        """处理内窥镜图像"""
        if endoscope_images:
            # 生成全景图
            panorama = self.generate_endoscope_panorama(endoscope_images)
            report_data.images['endoscope_panorama'] = panorama
            
    def _generate_demo_measurement_data(self) -> List[Dict]:
        """生成演示用的测量数据"""
        data = []
        target = 17.6
        for i in range(1000):
            depth = i * 0.5  # 每0.5mm一个测量点
            # 添加一些变化和少量超差点
            noise = np.random.normal(0, 0.005)
            if i > 800 and i < 820:  # 在某个区域添加超差
                noise += 0.08
            diameter = target + noise
            data.append({'depth': depth, 'diameter': diameter})
        return data
        
    def _generate_statistics_text(self, diameters: List[float], 
                                target: float, upper_tol: float, 
                                lower_tol: float) -> str:
        """生成统计信息文本"""
        diameters = np.array(diameters)
        mean_diameter = np.mean(diameters)
        std_diameter = np.std(diameters)
        min_diameter = np.min(diameters)
        max_diameter = np.max(diameters)
        
        # 计算超差点
        upper_limit = target + upper_tol
        lower_limit = target - lower_tol
        out_of_spec = np.sum((diameters > upper_limit) | (diameters < lower_limit))
        out_of_spec_rate = (out_of_spec / len(diameters)) * 100
        
        stats_text = f"""统计信息:
平均直径: {mean_diameter:.3f} mm
标准偏差: {std_diameter:.3f} mm
最小直径: {min_diameter:.3f} mm
最大直径: {max_diameter:.3f} mm
测量点数: {len(diameters)}
超差点数: {out_of_spec}
超差率: {out_of_spec_rate:.1f}%"""
        
        return stats_text
        
    def _generate_statistics_chart(self, measurement_data: List[Dict]) -> str:
        """生成统计分析图表"""
        diameters = [d.get('diameter', 17.6) for d in measurement_data]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # 直径分布直方图
        ax1.hist(diameters, bins=50, alpha=0.7, color='skyblue', edgecolor='black')
        ax1.axvline(np.mean(diameters), color='red', linestyle='--', 
                   label=f'平均值: {np.mean(diameters):.3f}mm')
        ax1.set_xlabel('直径 (mm)')
        ax1.set_ylabel('频次')
        ax1.set_title('直径分布直方图')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 控制图
        indices = list(range(len(diameters)))
        ax2.plot(indices[::10], diameters[::10], 'b-', alpha=0.6)
        ax2.axhline(np.mean(diameters), color='green', linestyle='-', label='均值')
        ax2.axhline(np.mean(diameters) + 3*np.std(diameters), color='red', 
                   linestyle='--', label='+3σ')
        ax2.axhline(np.mean(diameters) - 3*np.std(diameters), color='red', 
                   linestyle='--', label='-3σ')
        ax2.set_xlabel('测量序号')
        ax2.set_ylabel('直径 (mm)')
        ax2.set_title('过程控制图')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        chart_filename = f"statistics_chart_{timestamp}.png"
        chart_path = self.chart_temp_dir / chart_filename
        
        plt.tight_layout()
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(chart_path)
        
    def _generate_placeholder_endoscope_image(self, hole_id: str = "") -> str:
        """生成占位符内窥镜图像"""
        # 创建占位符图像
        width, height = 800, 600
        img = Image.new('RGB', (width, height), 'lightgray')
        draw = ImageDraw.Draw(img)
        
        # 绘制占位符内容
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()
            
        text = f"内窥镜图像\\n孔位: {hole_id}" if hole_id else "内窥镜图像"
        text += "\\n(图像不可用)"
        
        # 计算文本位置
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        draw.text((x, y), text, fill='black', font=font)
        
        # 绘制边框
        draw.rectangle([(10, 10), (width-10, height-10)], outline='black', width=2)
        
        # 保存图像
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        placeholder_filename = f"endoscope_placeholder_{hole_id}_{timestamp}.png"
        placeholder_path = self.chart_temp_dir / placeholder_filename
        
        img.save(placeholder_path, 'PNG', quality=95)
        
        return str(placeholder_path)
        
    def _add_depth_markers(self, panorama: Image.Image, num_images: int):
        """在全景图上添加深度标记"""
        draw = ImageDraw.Draw(panorama)
        
        try:
            font = ImageFont.truetype("arial.ttf", 14)
        except:
            font = ImageFont.load_default()
            
        segment_height = panorama.height // num_images
        
        for i in range(num_images + 1):
            y = i * segment_height
            if y < panorama.height:
                # 绘制标记线
                draw.line([(0, y), (50, y)], fill='red', width=2)
                
                # 添加深度标签
                depth_text = f"{i * 50}mm"  # 假设每50mm一个图像
                draw.text((55, y - 7), depth_text, fill='red', font=font)
                
    def _add_defect_legend(self, draw: ImageDraw.Draw, image_size: Tuple[int, int],
                          font, small_font):
        """添加缺陷图例"""
        width, height = image_size
        
        # 图例位置（右下角）
        legend_x = width - 200
        legend_y = height - 100
        
        # 绘制图例背景
        draw.rectangle([(legend_x, legend_y), (width - 10, height - 10)], 
                      fill='white', outline='black', width=2)
        
        # 添加图例标题
        draw.text((legend_x + 10, legend_y + 10), "缺陷标注", 
                 fill='black', font=font)
        
        # 添加图例项
        draw.rectangle([(legend_x + 10, legend_y + 35), (legend_x + 25, legend_y + 50)], 
                      outline='red', width=2)
        draw.text((legend_x + 35, legend_y + 37), "检测到的缺陷", 
                 fill='black', font=small_font)
        
    def cleanup_temp_files(self):
        """清理临时文件"""
        try:
            for file_path in self.chart_temp_dir.glob("*"):
                if file_path.is_file():
                    file_path.unlink()
        except Exception as e:
            print(f"⚠️ 清理临时文件失败: {e}")


if __name__ == "__main__":
    """测试增强报告生成器"""
    generator = EnhancedReportGenerator()
    
    # 测试包络图生成
    test_data = generator._generate_demo_measurement_data()
    envelope_chart = generator.generate_envelope_chart_with_annotations(
        test_data, 17.6, 0.05, 0.07, "H001"
    )
    print(f"包络图已生成: {envelope_chart}")
    
    # 测试占位符内窥镜图像
    placeholder = generator._generate_placeholder_endoscope_image("H001")
    print(f"占位符图像已生成: {placeholder}")
    
    print("✅ 增强报告生成器测试完成")