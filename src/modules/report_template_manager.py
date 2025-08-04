"""
报告模板管理器
负责管理报告模板的定义、加载和权限控制
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum


class PermissionLevel(Enum):
    """权限级别"""
    PUBLIC = "public"          # 公开，所有用户可用
    OPERATOR = "operator"      # 操作员级别
    ADMIN = "admin"           # 管理员级别


class TemplateType(Enum):
    """模板类型"""
    STANDARD = "standard"      # 标准检测报告 
    SIMPLIFIED = "simplified"  # 简化报告
    DETAILED = "detailed"      # 详细报告
    SUMMARY = "summary"        # 汇总报告


@dataclass
class ReportTemplate:
    """报告模板定义"""
    template_id: str
    template_name: str
    template_type: TemplateType
    description: str
    permission_level: PermissionLevel
    
    # 内容配置 - 对应原来的ReportConfiguration
    include_workpiece_info: bool = True
    include_quality_summary: bool = True
    include_qualified_holes: bool = True
    include_unqualified_holes: bool = True
    include_defect_analysis: bool = True
    include_manual_reviews: bool = True
    include_charts: bool = True
    include_endoscope_images: bool = True
    
    # 格式配置
    page_size: str = "A4"
    page_orientation: str = "portrait"
    chart_dpi: int = 300
    
    # 模板文件路径（可选，用于基于文件的模板）
    template_file_path: Optional[str] = None
    
    def to_report_configuration(self):
        """转换为ReportConfiguration对象"""
        # 动态导入避免循环依赖
        try:
            from assets.old.report_models import ReportConfiguration, ReportType, ReportFormat
            return ReportConfiguration(
                report_type=ReportType.COMPREHENSIVE,  # 默认类型
                report_format=ReportFormat.PDF,        # 默认格式
                include_workpiece_info=self.include_workpiece_info,
                include_quality_summary=self.include_quality_summary,
                include_qualified_holes=self.include_qualified_holes,
                include_unqualified_holes=self.include_unqualified_holes,
                include_defect_analysis=self.include_defect_analysis,
                include_manual_reviews=self.include_manual_reviews,
                include_charts=self.include_charts,
                include_endoscope_images=self.include_endoscope_images,
                page_size=self.page_size,
                page_orientation=self.page_orientation,
                chart_dpi=self.chart_dpi
            )
        except ImportError:
            # 如果无法导入，返回兼容的配置对象
            class ConfigCompat:
                def __init__(self, **kwargs):
                    for k, v in kwargs.items():
                        setattr(self, k, v)
            
            return ConfigCompat(
                report_type="comprehensive",  # 兼容性默认值
                report_format="pdf",          # 兼容性默认值
                include_workpiece_info=self.include_workpiece_info,
                include_quality_summary=self.include_quality_summary,
                include_qualified_holes=self.include_qualified_holes,
                include_unqualified_holes=self.include_unqualified_holes,
                include_defect_analysis=self.include_defect_analysis,
                include_manual_reviews=self.include_manual_reviews,
                include_charts=self.include_charts,
                include_endoscope_images=self.include_endoscope_images,
                page_size=self.page_size,
                page_orientation=self.page_orientation,
                chart_dpi=self.chart_dpi
            )


class ReportTemplateManager:
    """报告模板管理器"""
    
    def __init__(self, templates_dir: Optional[str] = None):
        # 设置模板配置目录
        if templates_dir:
            self.templates_dir = Path(templates_dir)
        else:
            # 默认在项目根目录的templates文件夹
            current_dir = Path(__file__).parent
            project_root = current_dir.parent.parent  # 向上两级到项目根目录
            self.templates_dir = project_root / "templates" / "reports"
        
        # 确保目录存在
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置文件路径
        self.config_file = self.templates_dir / "templates.json"
        
        # 加载或初始化模板
        self.templates: Dict[str, ReportTemplate] = {}
        self._load_templates()
        
        # 当前用户权限级别（默认为操作员）
        self.current_user_permission = PermissionLevel.OPERATOR
    
    def _load_templates(self):
        """加载模板配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for template_data in data.get('templates', []):
                    # 转换枚举类型
                    template_data['template_type'] = TemplateType(template_data['template_type'])
                    template_data['permission_level'] = PermissionLevel(template_data['permission_level'])
                    
                    template = ReportTemplate(**template_data)
                    self.templates[template.template_id] = template
                    
                print(f"✅ 加载了 {len(self.templates)} 个报告模板")
                
            except Exception as e:
                print(f"❌ 加载模板配置失败: {e}")
                self._create_default_templates()
        else:
            self._create_default_templates()
    
    def _create_default_templates(self):
        """创建默认模板"""
        default_templates = [
            ReportTemplate(
                template_id="standard_report",
                template_name="标准检测报告",
                template_type=TemplateType.STANDARD,
                description="包含完整检测信息的标准报告，适用于正式提交",
                permission_level=PermissionLevel.PUBLIC,
                include_workpiece_info=True,
                include_quality_summary=True,
                include_qualified_holes=True,
                include_unqualified_holes=True,
                include_defect_analysis=True,
                include_manual_reviews=True,
                include_charts=True,
                include_endoscope_images=True
            ),
            ReportTemplate(
                template_id="simplified_report", 
                template_name="简化报告",
                template_type=TemplateType.SIMPLIFIED,
                description="包含基本质量信息的简化报告，适用于日常检查",
                permission_level=PermissionLevel.PUBLIC,
                include_workpiece_info=True,
                include_quality_summary=True,
                include_qualified_holes=False,
                include_unqualified_holes=True,
                include_defect_analysis=False,
                include_manual_reviews=False,
                include_charts=True,
                include_endoscope_images=False
            ),
            ReportTemplate(
                template_id="summary_report",
                template_name="汇总报告", 
                template_type=TemplateType.SUMMARY,
                description="仅包含质量汇总数据的报告，适用于管理层查看",
                permission_level=PermissionLevel.OPERATOR,
                include_workpiece_info=True,
                include_quality_summary=True,
                include_qualified_holes=False,
                include_unqualified_holes=False,
                include_defect_analysis=False,
                include_manual_reviews=False,
                include_charts=True,
                include_endoscope_images=False
            ),
            ReportTemplate(
                template_id="detailed_report",
                template_name="详细分析报告",
                template_type=TemplateType.DETAILED,
                description="包含详细分析数据的完整报告，需要管理员权限",
                permission_level=PermissionLevel.ADMIN,
                include_workpiece_info=True,
                include_quality_summary=True,
                include_qualified_holes=True,
                include_unqualified_holes=True,
                include_defect_analysis=True,
                include_manual_reviews=True,
                include_charts=True,
                include_endoscope_images=True
            )
        ]
        
        for template in default_templates:
            self.templates[template.template_id] = template
        
        self._save_templates()
        print(f"✅ 创建了 {len(default_templates)} 个默认模板")
    
    def _save_templates(self):
        """保存模板配置"""
        try:
            # 转换为可序列化的格式
            templates_data = []
            for template in self.templates.values():
                template_dict = asdict(template)
                # 转换枚举为字符串
                template_dict['template_type'] = template.template_type.value
                template_dict['permission_level'] = template.permission_level.value
                templates_data.append(template_dict)
            
            data = {
                'version': '1.0',
                'templates': templates_data
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"❌ 保存模板配置失败: {e}")
    
    def get_available_templates(self) -> List[ReportTemplate]:
        """获取当前用户可用的模板列表"""
        available = []
        for template in self.templates.values():
            if self._check_permission(template.permission_level):
                available.append(template)
        
        # 按权限级别和名称排序
        available.sort(key=lambda t: (t.permission_level.value, t.template_name))
        return available
    
    def get_template(self, template_id: str) -> Optional[ReportTemplate]:
        """获取指定模板"""
        template = self.templates.get(template_id)
        if template and self._check_permission(template.permission_level):
            return template
        return None
    
    def get_template_names(self) -> List[tuple]:
        """获取可用模板的ID和名称列表"""
        available = self.get_available_templates()
        return [(t.template_id, t.template_name) for t in available]
    
    def _check_permission(self, required_level: PermissionLevel) -> bool:
        """检查权限"""
        permission_order = {
            PermissionLevel.PUBLIC: 0,
            PermissionLevel.OPERATOR: 1, 
            PermissionLevel.ADMIN: 2
        }
        
        return permission_order[self.current_user_permission] >= permission_order[required_level]
    
    def set_user_permission(self, permission: PermissionLevel):
        """设置当前用户权限"""
        self.current_user_permission = permission
        print(f"🔑 用户权限设置为: {permission.value}")
    
    def add_template(self, template: ReportTemplate) -> bool:
        """添加新模板（需要管理员权限）"""
        if not self._check_permission(PermissionLevel.ADMIN):
            print("❌ 添加模板需要管理员权限")
            return False
        
        self.templates[template.template_id] = template
        self._save_templates()
        print(f"✅ 添加模板: {template.template_name}")
        return True
    
    def update_template(self, template_id: str, template: ReportTemplate) -> bool:
        """更新模板（需要管理员权限）"""
        if not self._check_permission(PermissionLevel.ADMIN):
            print("❌ 更新模板需要管理员权限")
            return False
        
        if template_id in self.templates:
            self.templates[template_id] = template
            self._save_templates()
            print(f"✅ 更新模板: {template.template_name}")
            return True
        else:
            print(f"❌ 模板不存在: {template_id}")
            return False
    
    def delete_template(self, template_id: str) -> bool:
        """删除模板（需要管理员权限）"""
        if not self._check_permission(PermissionLevel.ADMIN):
            print("❌ 删除模板需要管理员权限")
            return False
        
        if template_id in self.templates:
            template = self.templates.pop(template_id)
            self._save_templates()
            print(f"✅ 删除模板: {template.template_name}")
            return True
        else:
            print(f"❌ 模板不存在: {template_id}")
            return False


# 全局单例
_template_manager = None

def get_template_manager() -> ReportTemplateManager:
    """获取模板管理器单例"""
    global _template_manager
    if _template_manager is None:
        _template_manager = ReportTemplateManager()
    return _template_manager