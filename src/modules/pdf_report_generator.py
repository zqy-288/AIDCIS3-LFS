"""
PDF报告生成器
使用reportlab库生成PDF格式的质量检测报告
"""

import os
import platform
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

try:
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, Image, KeepTogether
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from .report_models import ReportData, ReportConfiguration


class PDFReportGenerator:
    """PDF报告生成器"""

    def __init__(self):
        self.styles = None
        self.story = []
        self.chinese_font_name = None

        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab库未安装，无法生成PDF报告。请运行: pip install reportlab")

        # 注册中文字体
        self._register_chinese_fonts()
    
    def generate_report(self, report_data: ReportData, config: ReportConfiguration, output_path: str):
        """生成PDF报告"""
        # 初始化样式
        self._init_styles()
        
        # 创建文档
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # 构建报告内容
        self.story = []
        
        # 添加标题页
        self._add_title_page(report_data, config)
        
        # 添加工件信息
        if config.include_workpiece_info:
            self._add_workpiece_info(report_data.workpiece_info)
        
        # 添加质量汇总
        if config.include_quality_summary:
            self._add_quality_summary(report_data.quality_summary)
        
        # 添加合格孔位信息
        if config.include_qualified_holes and report_data.qualified_holes:
            self._add_qualified_holes_summary(report_data.qualified_holes)
        
        # 添加不合格孔位详情
        if config.include_unqualified_holes and report_data.unqualified_holes:
            self._add_unqualified_holes_detail(report_data.unqualified_holes)
        
        # 添加人工复检记录
        if config.include_manual_reviews and report_data.manual_reviews:
            self._add_manual_reviews(report_data.manual_reviews)
        
        # 添加缺陷分析
        if config.include_defect_analysis and report_data.defect_data:
            self._add_defect_analysis(report_data.defect_data)
        
        # 添加附录
        self._add_appendix(report_data)
        
        # 生成PDF
        doc.build(self.story)
        
        return output_path

    def _register_chinese_fonts(self):
        """注册中文字体到reportlab"""
        try:
            system = platform.system()
            font_registered = False

            if system == "Windows":
                # Windows系统字体路径
                font_paths = [
                    (r"C:\Windows\Fonts\msyh.ttc", "Microsoft-YaHei"),
                    (r"C:\Windows\Fonts\msyh.ttf", "Microsoft-YaHei"),
                    (r"C:\Windows\Fonts\simhei.ttf", "SimHei"),
                    (r"C:\Windows\Fonts\simsun.ttc", "SimSun"),
                ]
            elif system == "Darwin":  # macOS
                font_paths = [
                    ("/System/Library/Fonts/PingFang.ttc", "PingFang-SC"),
                    ("/System/Library/Fonts/Hiragino Sans GB.ttc", "Hiragino-Sans-GB"),
                ]
            else:  # Linux
                font_paths = [
                    ("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc", "WenQuanYi-Micro-Hei"),
                    ("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc", "Noto-Sans-CJK"),
                ]

            # 尝试注册字体
            for font_path, font_name in font_paths:
                if os.path.exists(font_path):
                    try:
                        # 对于.ttc文件，需要特殊处理
                        if font_path.endswith('.ttc'):
                            # 尝试注册第一个字体
                            pdfmetrics.registerFont(TTFont(font_name, font_path, subfontIndex=0))
                        else:
                            pdfmetrics.registerFont(TTFont(font_name, font_path))

                        self.chinese_font_name = font_name
                        font_registered = True
                        print(f"✅ 成功注册中文字体: {font_name} ({font_path})")
                        break
                    except Exception as e:
                        print(f"⚠️ 注册字体失败 {font_name}: {e}")
                        continue

            if not font_registered:
                print("⚠️ 未找到可用的中文字体，将使用默认字体")
                self.chinese_font_name = "Helvetica"

        except Exception as e:
            print(f"❌ 字体注册过程出错: {e}")
            self.chinese_font_name = "Helvetica"

    def _init_styles(self):
        """初始化样式"""
        self.styles = getSampleStyleSheet()

        # 获取字体名称（中文字体或默认字体）
        font_name = self.chinese_font_name or "Helvetica"

        # 自定义样式 - 支持中文
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontName=font_name,
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))

        self.styles.add(ParagraphStyle(
            name='CustomHeading1',
            parent=self.styles['Heading1'],
            fontName=font_name,
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkblue
        ))

        self.styles.add(ParagraphStyle(
            name='CustomHeading2',
            parent=self.styles['Heading2'],
            fontName=font_name,
            fontSize=14,
            spaceAfter=10,
            spaceBefore=15,
            textColor=colors.darkgreen
        ))

        # 自定义中文正文样式
        self.styles.add(ParagraphStyle(
            name='ChineseNormal',
            parent=self.styles['Normal'],
            fontName=font_name,
            fontSize=12,
            spaceAfter=6,
            leading=16
        ))

        # 自定义中文表格样式
        self.styles.add(ParagraphStyle(
            name='ChineseTable',
            parent=self.styles['Normal'],
            fontName=font_name,
            fontSize=10,
            alignment=TA_CENTER,
            leading=12
        ))
    
    def _add_title_page(self, report_data: ReportData, config: ReportConfiguration):
        """添加标题页"""
        # 主标题
        title = config.custom_title or "管孔检测系统质量检测报告"
        self.story.append(Paragraph(title, self.styles['CustomTitle']))
        self.story.append(Spacer(1, 0.5*inch))
        
        # 工件信息摘要
        workpiece_info = [
            f"工件ID: {report_data.workpiece_info.workpiece_id}",
            f"工件名称: {report_data.workpiece_info.name}",
            f"工件类型: {report_data.workpiece_info.type}",
            f"材料: {report_data.workpiece_info.material}",
        ]
        
        for info in workpiece_info:
            self.story.append(Paragraph(info, self.styles['ChineseNormal']))

        self.story.append(Spacer(1, 0.5*inch))

        # 报告信息
        report_info = [
            f"报告生成时间: {report_data.generated_at.strftime('%Y年%m月%d日 %H:%M:%S')}",
            f"报告生成者: {report_data.generated_by}",
            f"报告版本: {report_data.report_version}",
        ]

        for info in report_info:
            self.story.append(Paragraph(info, self.styles['ChineseNormal']))
        
        self.story.append(PageBreak())
    
    def _add_workpiece_info(self, workpiece_info):
        """添加工件信息"""
        self.story.append(Paragraph("1. 工件信息", self.styles['CustomHeading1']))
        
        data = [
            ['项目', '内容'],
            ['工件ID', workpiece_info.workpiece_id],
            ['工件名称', workpiece_info.name],
            ['工件类型', workpiece_info.type],
            ['材料', workpiece_info.material],
            ['总孔位数', str(workpiece_info.total_holes)],
        ]
        
        if workpiece_info.description:
            data.append(['描述', workpiece_info.description])
        
        table = Table(data, colWidths=[3*cm, 10*cm])

        # 获取字体名称
        font_name = self.chinese_font_name or "Helvetica"
        font_bold = f"{font_name}-Bold" if self.chinese_font_name else "Helvetica-Bold"

        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), font_name),
            ('FONTNAME', (0, 1), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        self.story.append(table)
        self.story.append(Spacer(1, 0.3*inch))
    
    def _add_quality_summary(self, quality_summary):
        """添加质量汇总"""
        self.story.append(Paragraph("2. 质量汇总", self.styles['CustomHeading1']))
        
        # 基本统计
        basic_data = [
            ['统计项目', '数量', '百分比'],
            ['总孔位数', str(quality_summary.total_holes), '100.0%'],
            ['合格孔位', str(quality_summary.qualified_holes), f'{quality_summary.qualification_rate:.1f}%'],
            ['不合格孔位', str(quality_summary.unqualified_holes), f'{100-quality_summary.qualification_rate:.1f}%'],
            ['有缺陷孔位', str(quality_summary.holes_with_defects), '-'],
            ['人工复检数', str(quality_summary.manual_review_count), '-'],
        ]
        
        table = Table(basic_data, colWidths=[5*cm, 3*cm, 3*cm])

        # 获取字体名称
        font_name = self.chinese_font_name or "Helvetica"

        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), font_name),
            ('FONTNAME', (0, 1), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        self.story.append(table)
        self.story.append(Spacer(1, 0.2*inch))
        
        # 直径统计（如果有数据）
        if quality_summary.diameter_statistics:
            self.story.append(Paragraph("2.1 直径测量统计", self.styles['CustomHeading2']))
            
            stats = quality_summary.diameter_statistics
            diameter_data = [
                ['统计项目', '数值 (mm)'],
                ['最小直径', f"{stats.get('min', 0):.4f}"],
                ['最大直径', f"{stats.get('max', 0):.4f}"],
                ['平均直径', f"{stats.get('avg', 0):.4f}"],
                ['标准偏差', f"{stats.get('std', 0):.4f}"],
                ['测量点数', str(stats.get('count', 0))],
            ]
            
            diameter_table = Table(diameter_data, colWidths=[5*cm, 4*cm])

            # 获取字体名称
            font_name = self.chinese_font_name or "Helvetica"

            diameter_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), font_name),
                ('FONTNAME', (0, 1), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            self.story.append(diameter_table)
        
        self.story.append(Spacer(1, 0.3*inch))
    
    def _add_qualified_holes_summary(self, qualified_holes):
        """添加合格孔位汇总"""
        self.story.append(Paragraph("3. 合格孔位汇总", self.styles['CustomHeading1']))
        
        self.story.append(Paragraph(f"共有 {len(qualified_holes)} 个孔位检测合格。", self.styles['ChineseNormal']))
        
        # 合格孔位列表（简化显示）
        if len(qualified_holes) <= 20:  # 如果孔位不多，显示详细列表
            data = [['孔位ID', '位置(X,Y)', '合格率', '测量次数']]
            
            for hole in qualified_holes:
                data.append([
                    hole.hole_id,
                    f"({hole.position_x:.1f}, {hole.position_y:.1f})",
                    f"{hole.qualification_rate:.1f}%",
                    f"{hole.qualified_count}/{hole.total_count}"
                ])
            
            table = Table(data, colWidths=[3*cm, 4*cm, 3*cm, 3*cm])

            # 获取字体名称
            font_name = self.chinese_font_name or "Helvetica"

            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.green),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), font_name),
                ('FONTNAME', (0, 1), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            self.story.append(table)
        else:
            # 如果孔位太多，只显示统计信息
            hole_ids = [hole.hole_id for hole in qualified_holes]
            hole_ids_text = ", ".join(hole_ids[:10])
            if len(qualified_holes) > 10:
                hole_ids_text += f" ... (共{len(qualified_holes)}个)"
            
            self.story.append(Paragraph(f"合格孔位: {hole_ids_text}", self.styles['ChineseNormal']))
        
        self.story.append(Spacer(1, 0.3*inch))
    
    def _add_unqualified_holes_detail(self, unqualified_holes):
        """添加不合格孔位详情"""
        self.story.append(Paragraph("4. 不合格孔位详情", self.styles['CustomHeading1']))
        
        if not unqualified_holes:
            self.story.append(Paragraph("所有孔位均检测合格。", self.styles['ChineseNormal']))
            return
        
        self.story.append(Paragraph(f"共有 {len(unqualified_holes)} 个孔位检测不合格，详情如下：", self.styles['ChineseNormal']))
        self.story.append(Spacer(1, 0.2*inch))
        
        for i, hole in enumerate(unqualified_holes, 1):
            # 孔位标题
            self.story.append(Paragraph(f"4.{i} 孔位 {hole.hole_id}", self.styles['CustomHeading2']))
            
            # 孔位详细信息
            hole_data = [
                ['项目', '数值'],
                ['位置坐标', f"({hole.position_x:.1f}, {hole.position_y:.1f})"],
                ['目标直径', f"{hole.target_diameter:.2f} mm"],
                ['公差范围', f"+{hole.tolerance_upper:.3f}/-{hole.tolerance_lower:.3f} mm"],
                ['合格率', f"{hole.qualification_rate:.1f}%"],
                ['测量次数', f"{hole.total_count}"],
                ['合格次数', f"{hole.qualified_count}"],
                ['平均偏差', f"{hole.deviation_stats.get('avg', 0):.4f} mm"],
                ['最大偏差', f"{hole.deviation_stats.get('max', 0):.4f} mm"],
                ['最小偏差', f"{hole.deviation_stats.get('min', 0):.4f} mm"],
            ]
            
            hole_table = Table(hole_data, colWidths=[4*cm, 6*cm])

            # 获取字体名称
            font_name = self.chinese_font_name or "Helvetica"

            hole_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.red),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), font_name),
                ('FONTNAME', (0, 1), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            self.story.append(hole_table)
            self.story.append(Spacer(1, 0.2*inch))
    
    def _add_manual_reviews(self, manual_reviews):
        """添加人工复检记录"""
        self.story.append(Paragraph("5. 人工复检记录", self.styles['CustomHeading1']))
        
        if not manual_reviews:
            self.story.append(Paragraph("无人工复检记录。", self.styles['ChineseNormal']))
            return
        
        data = [['孔位ID', '复检员', '原始直径(mm)', '复检直径(mm)', '最终判定', '复检时间']]
        
        for review in manual_reviews:
            data.append([
                review.hole_id,
                review.reviewer,
                f"{review.original_diameter:.4f}",
                f"{review.reviewed_diameter:.4f}",
                review.final_judgment,
                review.review_timestamp.strftime('%Y-%m-%d %H:%M')
            ])
        
        table = Table(data, colWidths=[2*cm, 2*cm, 2.5*cm, 2.5*cm, 2*cm, 3*cm])

        # 获取字体名称
        font_name = self.chinese_font_name or "Helvetica"

        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.orange),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), font_name),
            ('FONTNAME', (0, 1), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        self.story.append(table)
        self.story.append(Spacer(1, 0.3*inch))
    
    def _add_defect_analysis(self, defect_data):
        """添加缺陷分析"""
        self.story.append(Paragraph("6. 缺陷分析", self.styles['CustomHeading1']))
        
        if not defect_data:
            self.story.append(Paragraph("未发现缺陷。", self.styles['ChineseNormal']))
            return
        
        # 缺陷统计
        defect_types = {}
        for defect in defect_data:
            defect_types[defect.defect_type] = defect_types.get(defect.defect_type, 0) + defect.defect_count
        
        self.story.append(Paragraph("6.1 缺陷类型统计", self.styles['CustomHeading2']))
        
        stats_data = [['缺陷类型', '数量']]
        for defect_type, count in defect_types.items():
            stats_data.append([defect_type, str(count)])
        
        stats_table = Table(stats_data, colWidths=[5*cm, 3*cm])

        # 获取字体名称
        font_name = self.chinese_font_name or "Helvetica"

        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.purple),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), font_name),
            ('FONTNAME', (0, 1), (-1, -1), font_name),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        self.story.append(stats_table)
        self.story.append(Spacer(1, 0.3*inch))
    
    def _add_appendix(self, report_data):
        """添加附录"""
        self.story.append(Paragraph("附录", self.styles['CustomHeading1']))
        
        appendix_info = [
            "A. 检测标准: 管孔直径标准 17.6mm ±0.05/-0.07mm",
            "B. 检测设备: 光谱共焦测量系统",
            "C. 合格判定标准: 单孔合格率 ≥ 95%",
            f"D. 报告生成时间: {report_data.generated_at.strftime('%Y年%m月%d日 %H:%M:%S')}",
            f"E. 数据版本: {report_data.report_version}",
        ]
        
        for info in appendix_info:
            self.story.append(Paragraph(info, self.styles['ChineseNormal']))
            self.story.append(Spacer(1, 0.1*inch))
