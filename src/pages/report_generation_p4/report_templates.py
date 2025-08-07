"""
报告模板系统
提供预定义的报告模板和自定义模板功能
"""

from typing import Dict, List
from .report_models import ReportConfiguration, ReportType, ReportFormat


class ReportTemplateManager:
    """报告模板管理器"""
    
    def __init__(self):
        self.templates = self._create_default_templates()
    
    def _create_default_templates(self) -> Dict[str, ReportConfiguration]:
        """创建默认模板"""
        templates = {}
        
        # 标准质量报告模板
        templates["standard_quality"] = ReportConfiguration(
            report_type=ReportType.COMPREHENSIVE,
            report_format=ReportFormat.PDF,
            include_workpiece_info=True,
            include_quality_summary=True,
            include_qualified_holes=True,
            include_unqualified_holes=True,
            include_defect_analysis=True,
            include_manual_reviews=True,
            include_charts=True,
            include_endoscope_images=True,
            custom_title="标准质量检测报告"
        )
        
        # 简化汇总报告模板
        templates["simple_summary"] = ReportConfiguration(
            report_type=ReportType.WORKPIECE_SUMMARY,
            report_format=ReportFormat.HTML,
            include_workpiece_info=True,
            include_quality_summary=True,
            include_qualified_holes=False,
            include_unqualified_holes=True,
            include_defect_analysis=False,
            include_manual_reviews=True,
            include_charts=True,
            include_endoscope_images=False,
            custom_title="工件质量汇总报告"
        )
        
        # 详细分析报告模板
        templates["detailed_analysis"] = ReportConfiguration(
            report_type=ReportType.QUALITY_ANALYSIS,
            report_format=ReportFormat.PDF,
            include_workpiece_info=True,
            include_quality_summary=True,
            include_qualified_holes=True,
            include_unqualified_holes=True,
            include_defect_analysis=True,
            include_manual_reviews=True,
            include_charts=True,
            include_endoscope_images=True,
            chart_dpi=300,
            custom_title="详细质量分析报告"
        )
        
        # 缺陷专项报告模板
        templates["defect_focus"] = ReportConfiguration(
            report_type=ReportType.DEFECT_ANALYSIS,
            report_format=ReportFormat.PDF,
            include_workpiece_info=True,
            include_quality_summary=False,
            include_qualified_holes=False,
            include_unqualified_holes=True,
            include_defect_analysis=True,
            include_manual_reviews=True,
            include_charts=True,
            include_endoscope_images=True,
            custom_title="缺陷分析专项报告"
        )
        
        # 快速检查报告模板
        templates["quick_check"] = ReportConfiguration(
            report_type=ReportType.WORKPIECE_SUMMARY,
            report_format=ReportFormat.HTML,
            include_workpiece_info=True,
            include_quality_summary=True,
            include_qualified_holes=False,
            include_unqualified_holes=False,
            include_defect_analysis=False,
            include_manual_reviews=False,
            include_charts=False,
            include_endoscope_images=False,
            custom_title="快速质量检查报告"
        )
        
        return templates
    
    def get_template_names(self) -> List[str]:
        """获取模板名称列表"""
        return list(self.templates.keys())
    
    def get_template_display_names(self) -> Dict[str, str]:
        """获取模板显示名称"""
        return {
            "standard_quality": "标准质量报告",
            "simple_summary": "简化汇总报告", 
            "detailed_analysis": "详细分析报告",
            "defect_focus": "缺陷专项报告",
            "quick_check": "快速检查报告"
        }
    
    def get_template(self, template_name: str) -> ReportConfiguration:
        """获取指定模板"""
        return self.templates.get(template_name, self.templates["standard_quality"])
    
    def get_template_description(self, template_name: str) -> str:
        """获取模板描述"""
        descriptions = {
            "standard_quality": "包含所有检测信息的标准质量报告，适用于正式的质量评估和存档",
            "simple_summary": "简化的汇总报告，重点关注整体质量状况和不合格项目",
            "detailed_analysis": "详细的质量分析报告，包含完整的统计数据和图表分析",
            "defect_focus": "专注于缺陷分析的报告，适用于缺陷调查和改进分析",
            "quick_check": "快速检查报告，仅包含基本的质量汇总信息"
        }
        return descriptions.get(template_name, "自定义报告模板")
    
    def apply_template_to_ui(self, template_name: str, ui_components: Dict):
        """将模板应用到UI组件"""
        template = self.get_template(template_name)
        
        # 更新UI组件状态
        if "report_type_combo" in ui_components:
            type_mapping = {
                ReportType.COMPREHENSIVE: "综合报告",
                ReportType.WORKPIECE_SUMMARY: "工件汇总报告",
                ReportType.QUALITY_ANALYSIS: "质量分析报告",
                ReportType.DEFECT_ANALYSIS: "缺陷分析报告"
            }
            ui_components["report_type_combo"].setCurrentText(type_mapping[template.report_type])
        
        if "format_combo" in ui_components:
            format_mapping = {
                ReportFormat.PDF: "PDF",
                ReportFormat.HTML: "HTML",
                ReportFormat.EXCEL: "Excel",
                ReportFormat.WORD: "Word"
            }
            ui_components["format_combo"].setCurrentText(format_mapping[template.report_format])
        
        # 更新复选框状态
        checkbox_mapping = {
            "include_workpiece_info": template.include_workpiece_info,
            "include_quality_summary": template.include_quality_summary,
            "include_qualified_holes": template.include_qualified_holes,
            "include_unqualified_holes": template.include_unqualified_holes,
            "include_defect_analysis": template.include_defect_analysis,
            "include_manual_reviews": template.include_manual_reviews,
            "include_charts": template.include_charts,
            "include_endoscope_images": template.include_endoscope_images
        }
        
        for checkbox_name, checked in checkbox_mapping.items():
            if checkbox_name in ui_components:
                ui_components[checkbox_name].setChecked(checked)
    
    def create_custom_template(self, name: str, config: ReportConfiguration) -> bool:
        """创建自定义模板"""
        try:
            self.templates[name] = config
            return True
        except Exception:
            return False
    
    def delete_template(self, template_name: str) -> bool:
        """删除模板（不能删除默认模板）"""
        default_templates = ["standard_quality", "simple_summary", "detailed_analysis", 
                           "defect_focus", "quick_check"]
        
        if template_name in default_templates:
            return False
        
        if template_name in self.templates:
            del self.templates[template_name]
            return True
        
        return False
    
    def export_template(self, template_name: str, file_path: str) -> bool:
        """导出模板到文件"""
        try:
            import json
            template = self.templates.get(template_name)
            if not template:
                return False
            
            # 将模板转换为可序列化的字典
            template_dict = {
                "name": template_name,
                "report_type": template.report_type.value,
                "report_format": template.report_format.value,
                "include_workpiece_info": template.include_workpiece_info,
                "include_quality_summary": template.include_quality_summary,
                "include_qualified_holes": template.include_qualified_holes,
                "include_unqualified_holes": template.include_unqualified_holes,
                "include_defect_analysis": template.include_defect_analysis,
                "include_manual_reviews": template.include_manual_reviews,
                "include_charts": template.include_charts,
                "include_endoscope_images": template.include_endoscope_images,
                "custom_title": template.custom_title,
                "chart_dpi": template.chart_dpi,
                "page_size": template.page_size,
                "page_orientation": template.page_orientation
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(template_dict, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception:
            return False
    
    def import_template(self, file_path: str) -> bool:
        """从文件导入模板"""
        try:
            import json
            
            with open(file_path, 'r', encoding='utf-8') as f:
                template_dict = json.load(f)
            
            # 重建ReportConfiguration对象
            config = ReportConfiguration(
                report_type=ReportType(template_dict["report_type"]),
                report_format=ReportFormat(template_dict["report_format"]),
                include_workpiece_info=template_dict.get("include_workpiece_info", True),
                include_quality_summary=template_dict.get("include_quality_summary", True),
                include_qualified_holes=template_dict.get("include_qualified_holes", True),
                include_unqualified_holes=template_dict.get("include_unqualified_holes", True),
                include_defect_analysis=template_dict.get("include_defect_analysis", True),
                include_manual_reviews=template_dict.get("include_manual_reviews", True),
                include_charts=template_dict.get("include_charts", True),
                include_endoscope_images=template_dict.get("include_endoscope_images", True),
                custom_title=template_dict.get("custom_title"),
                chart_dpi=template_dict.get("chart_dpi", 300),
                page_size=template_dict.get("page_size", "A4"),
                page_orientation=template_dict.get("page_orientation", "portrait")
            )
            
            template_name = template_dict["name"]
            self.templates[template_name] = config
            
            return True
            
        except Exception:
            return False