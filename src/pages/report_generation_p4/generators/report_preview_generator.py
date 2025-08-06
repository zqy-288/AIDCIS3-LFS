"""
报告预览生成器
负责生成真实格式的预览文件，遵循单一职责原则
"""

import tempfile
import os
from pathlib import Path
from typing import Optional, Tuple
from enum import Enum


class PreviewFormat(Enum):
    """预览格式枚举"""
    PDF = "pdf"
    HTML = "html"
    TEXT = "txt"


class ReportPreviewGenerator:
    """报告预览生成器 - 单一职责：生成预览文件"""
    
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "report_previews"
        self.temp_dir.mkdir(exist_ok=True)
    
    def generate_preview_file(self, report_data, template, output_format: str) -> Optional[str]:
        """
        生成预览文件
        
        Args:
            report_data: 报告数据
            template: 报告模板
            output_format: 输出格式 ("PDF", "HTML", "Excel", "Word")
            
        Returns:
            str: 预览文件路径，如果失败返回None
        """
        try:
            # 根据格式选择预览方式
            format_mapping = {
                "PDF": PreviewFormat.PDF,
                "HTML": PreviewFormat.HTML,
                "Excel": PreviewFormat.HTML,  # Excel用HTML预览
                "Word": PreviewFormat.HTML    # Word用HTML预览
            }
            
            preview_format = format_mapping.get(output_format, PreviewFormat.TEXT)
            
            if preview_format == PreviewFormat.PDF:
                return self._generate_pdf_preview(report_data, template)
            elif preview_format == PreviewFormat.HTML:
                return self._generate_html_preview(report_data, template)
            else:
                return self._generate_text_preview(report_data, template)
                
        except Exception as e:
            print(f"❌ 预览文件生成失败: {e}")
            return None
    
    def _generate_pdf_preview(self, report_data, template) -> Optional[str]:
        """生成PDF预览"""
        try:
            # 尝试使用现有的PDF生成器
            from src.pages.report_generation_p4.generators.pdf_report_generator import PDFReportGenerator
            from datetime import datetime
            
            # 创建临时文件
            temp_file = self.temp_dir / f"preview_{id(report_data)}.pdf"
            
            # 确保generated_at是datetime对象
            if hasattr(report_data, 'generated_at') and isinstance(report_data.generated_at, str):
                try:
                    report_data.generated_at = datetime.fromisoformat(report_data.generated_at.replace('Z', '+00:00'))
                except:
                    report_data.generated_at = datetime.now()
            elif not hasattr(report_data, 'generated_at'):
                report_data.generated_at = datetime.now()
            
            # 生成PDF
            pdf_generator = PDFReportGenerator()
            config = template.to_report_configuration()
            pdf_generator.generate_report(report_data, config, str(temp_file))
            
            return str(temp_file) if temp_file.exists() else None
            
        except Exception as e:
            print(f"❌ PDF预览生成失败: {e}")
            # 回退到HTML预览
            return self._generate_html_preview(report_data, template)
    
    def _generate_html_preview(self, report_data, template) -> Optional[str]:
        """生成HTML预览"""
        try:
            temp_file = self.temp_dir / f"preview_{id(report_data)}.html"
            
            html_content = self._create_html_content(report_data, template)
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return str(temp_file)
            
        except Exception as e:
            print(f"❌ HTML预览生成失败: {e}")
            return self._generate_text_preview(report_data, template)
    
    def _generate_text_preview(self, report_data, template) -> Optional[str]:
        """生成文本预览（最后的回退方案）"""
        try:
            temp_file = self.temp_dir / f"preview_{id(report_data)}.txt"
            
            text_content = self._create_text_content(report_data, template)
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            return str(temp_file)
            
        except Exception as e:
            print(f"❌ 文本预览生成失败: {e}")
            return None
    
    def _create_html_content(self, report_data, template) -> str:
        """创建HTML格式的预览内容"""
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>报告预览 - {template.template_name}</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #2E7D32;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .title {{
            color: #2E7D32;
            font-size: 24px;
            font-weight: bold;
            margin: 0;
        }}
        .subtitle {{
            color: #666;
            font-size: 14px;
            margin: 10px 0 0 0;
        }}
        .section {{
            margin: 25px 0;
        }}
        .section-title {{
            color: #1976D2;
            font-size: 18px;
            font-weight: bold;
            border-left: 4px solid #1976D2;
            padding-left: 10px;
            margin-bottom: 15px;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 20px;
        }}
        .info-item {{
            background-color: #f8f9fa;
            padding: 12px;
            border-radius: 4px;
            border-left: 3px solid #4CAF50;
        }}
        .info-label {{
            font-weight: bold;
            color: #333;
        }}
        .info-value {{
            color: #666;
            margin-top: 5px;
        }}
        .summary-stats {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-number {{
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .stat-label {{
            font-size: 14px;
            opacity: 0.9;
        }}
        .qualified {{
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        }}
        .unqualified {{
            background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
        }}
        .rate {{
            background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #666;
            font-size: 12px;
        }}
        .template-info {{
            background-color: #e3f2fd;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
            border: 1px solid #bbdefb;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="title">质量检测报告</h1>
            <p class="subtitle">基于 {template.template_name} 模板生成</p>
        </div>
        
        <div class="template-info">
            <strong>📋 使用模板：</strong>{template.template_name}<br>
            <strong>📝 模板描述：</strong>{template.description}<br>
            <strong>🔒 权限级别：</strong>{template.permission_level.value}
        </div>
"""
        
        # 工件信息
        if hasattr(report_data, 'workpiece_info') and template.include_workpiece_info:
            workpiece = report_data.workpiece_info
            html += f"""
        <div class="section">
            <h2 class="section-title">🔧 工件信息</h2>
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">工件编号</div>
                    <div class="info-value">{getattr(workpiece, 'workpiece_id', '--')}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">工件名称</div>
                    <div class="info-value">{getattr(workpiece, 'name', '--')}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">工件类型</div>
                    <div class="info-value">{getattr(workpiece, 'type', '--')}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">材质信息</div>
                    <div class="info-value">{getattr(workpiece, 'material', '--')}</div>
                </div>
            </div>
        </div>
"""
        
        # 质量汇总
        if hasattr(report_data, 'quality_summary') and template.include_quality_summary:
            summary = report_data.quality_summary
            html += f"""
        <div class="section">
            <h2 class="section-title">📊 质量汇总</h2>
            <div class="summary-stats">
                <div class="stat-card">
                    <div class="stat-number">{getattr(summary, 'total_holes', 0)}</div>
                    <div class="stat-label">总孔位数</div>
                </div>
                <div class="stat-card qualified">
                    <div class="stat-number">{getattr(summary, 'qualified_holes', 0)}</div>
                    <div class="stat-label">合格孔位</div>
                </div>
                <div class="stat-card unqualified">
                    <div class="stat-number">{getattr(summary, 'unqualified_holes', 0)}</div>
                    <div class="stat-label">不合格孔位</div>
                </div>
                <div class="stat-card rate">
                    <div class="stat-number">{getattr(summary, 'qualification_rate', 0):.1f}%</div>
                    <div class="stat-label">合格率</div>
                </div>
            </div>
        </div>
"""
        
        # 不合格孔位详情
        if (hasattr(report_data, 'unqualified_holes') and 
            template.include_unqualified_holes and
            report_data.unqualified_holes):
            html += f"""
        <div class="section">
            <h2 class="section-title">❌ 不合格孔位详情</h2>
            <div class="info-grid">
"""
            for i, hole in enumerate(report_data.unqualified_holes[:6], 1):
                hole_id = hole.get('hole_id', f'孔位{i}') if isinstance(hole, dict) else f'孔位{i}'
                qualification_rate = hole.get('qualification_rate', 0) if isinstance(hole, dict) else 0
                html += f"""
                <div class="info-item">
                    <div class="info-label">{hole_id}</div>
                    <div class="info-value">合格率: {qualification_rate:.1f}%</div>
                </div>
"""
            
            if len(report_data.unqualified_holes) > 6:
                html += f"""
                <div class="info-item" style="grid-column: 1 / -1; text-align: center; background-color: #fff3cd; border-left-color: #ffc107;">
                    <div class="info-value">... 还有 {len(report_data.unqualified_holes) - 6} 个不合格孔位</div>
                </div>
"""
            
            html += """
            </div>
        </div>
"""
        
        # 报告生成信息
        html += f"""
        <div class="footer">
            <p>📅 生成时间: {getattr(report_data, 'generated_at', '未知')}</p>
            <p>👤 生成者: {getattr(report_data, 'generated_by', '系统')} | 📄 版本: {getattr(report_data, 'report_version', '1.0')}</p>
            <p>🔍 这是预览版本，实际报告可能包含更多详细信息</p>
        </div>
    </div>
</body>
</html>
"""
        return html
    
    def _create_text_content(self, report_data, template) -> str:
        """创建文本格式的预览内容"""
        lines = []
        lines.append("=" * 60)
        lines.append("质量检测报告预览")
        lines.append("=" * 60)
        lines.append("")
        
        if template:
            lines.append(f"报告模板: {template.template_name}")
            lines.append(f"模板类型: {template.template_type.value}")
            lines.append(f"模板描述: {template.description}")
            lines.append("")
        
        if report_data:
            # 工件信息
            if hasattr(report_data, 'workpiece_info') and template and template.include_workpiece_info:
                workpiece = report_data.workpiece_info
                lines.append("1. 工件信息")
                lines.append("-" * 20)
                lines.append(f"工件ID: {getattr(workpiece, 'workpiece_id', '--')}")
                lines.append(f"工件名称: {getattr(workpiece, 'name', '--')}")
                lines.append(f"工件类型: {getattr(workpiece, 'type', '--')}")
                if hasattr(workpiece, 'material'):
                    lines.append(f"材质: {workpiece.material}")
                lines.append("")
            
            # 质量汇总
            if hasattr(report_data, 'quality_summary') and template and template.include_quality_summary:
                summary = report_data.quality_summary
                lines.append("2. 质量汇总")
                lines.append("-" * 20)
                lines.append(f"总孔位数: {getattr(summary, 'total_holes', '--')}")
                lines.append(f"合格孔位: {getattr(summary, 'qualified_holes', '--')}")
                lines.append(f"不合格孔位: {getattr(summary, 'unqualified_holes', '--')}")
                lines.append(f"合格率: {getattr(summary, 'qualification_rate', '--')}%")
                lines.append("")
        
        lines.append("=" * 60)
        lines.append("预览结束")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def cleanup_old_previews(self):
        """清理旧的预览文件"""
        try:
            if self.temp_dir.exists():
                for file in self.temp_dir.glob("preview_*"):
                    if file.is_file():
                        file.unlink()
        except Exception as e:
            print(f"⚠️ 清理预览文件失败: {e}")