"""
样式覆盖检测器
检测和修复可能覆盖全局主题的组件样式
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import QObject, Signal


class StyleOverrideDetector(QObject):
    """样式覆盖检测器"""
    
    # 信号定义
    override_detected = Signal(str, str)  # 文件路径, 问题描述
    fix_applied = Signal(str, str)        # 文件路径, 修复描述
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 定义主题兼容的颜色
        self.theme_compatible_colors_list = [
            '#2C313C', '#313642', '#3A404E',  # 背景色
            '#D3D8E0', '#FFFFFF', '#AAAAAA',  # 文本色
            '#007ACC', '#4A90E2', '#0099FF', '#005C99',  # 强调色
            '#2ECC71', '#E67E22', '#E74C3C',  # 状态色
            '#404552', '#555555', '#1E222B',  # 边框和特殊背景
        ]
        
        self.problem_patterns = [
            # 白色背景
            (r'background-color:\s*white\b', "使用了白色背景"),
            (r'background-color:\s*#fff\b', "使用了白色背景"),
            (r'background-color:\s*#ffffff\b', "使用了白色背景"),
            
            # 硬编码浅色背景（排除主题兼容颜色）
            (r'background-color:\s*#f[0-9a-fA-F]{5}\b', "使用了浅色背景"),
            (r'background-color:\s*#e[0-9a-fA-F]{5}\b', "使用了浅色背景"),
            
            # 硬编码深色文本
            (r'color:\s*black\b', "使用了黑色文本"),
            (r'color:\s*#000\b', "使用了黑色文本"),
            (r'color:\s*#000000\b', "使用了黑色文本"),
            
            # 特定的不兼容颜色
            (r'background-color:\s*#4CAF50\b', "使用了硬编码绿色"),
            (r'background-color:\s*#f44336\b', "使用了硬编码红色"),
            (r'background-color:\s*#2196F3\b', "使用了硬编码蓝色"),
        ]
        
        self.theme_compatible_colors = {
            # 替换映射：不兼容颜色 -> 主题兼容颜色
            'white': 'var(--bg-secondary)',
            '#fff': 'var(--bg-secondary)',
            '#ffffff': 'var(--bg-secondary)',
            'black': 'var(--text-primary)',
            '#000': 'var(--text-primary)',
            '#000000': 'var(--text-primary)',
            '#4CAF50': 'var(--success)',
            '#f44336': 'var(--error)',
            '#2196F3': 'var(--accent-primary)',
        }
    
    def scan_directory(self, directory: Path) -> Dict[str, List[str]]:
        """扫描目录中的样式覆盖问题"""
        problems = {}
        
        for py_file in directory.rglob("*.py"):
            if py_file.name.startswith('.'):
                continue
                
            file_problems = self.scan_file(py_file)
            if file_problems:
                problems[str(py_file)] = file_problems
        
        return problems
    
    def scan_file(self, file_path: Path) -> List[str]:
        """扫描单个文件的样式覆盖问题"""
        problems = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否包含主题兼容颜色的setStyleSheet调用
            for pattern, description in self.problem_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    # 过滤掉包含主题兼容颜色的匹配
                    filtered_matches = []
                    for match in matches:
                        if not self._is_theme_compatible_usage(match, content):
                            filtered_matches.append(match)
                    
                    if filtered_matches:
                        problems.append(f"{description}: {filtered_matches}")
                        self.override_detected.emit(str(file_path), description)
        
        except Exception as e:
            self.logger.error(f"扫描文件失败 {file_path}: {e}")
        
        return problems
    
    def fix_style_overrides(self, file_path: Path, backup: bool = True) -> bool:
        """修复文件中的样式覆盖问题"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # 备份原文件
            if backup:
                backup_path = file_path.with_suffix('.py.style_backup')
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(original_content)
            
            # 应用修复
            content = self._apply_fixes(content)
            
            # 如果有变化，写回文件
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.fix_applied.emit(str(file_path), "样式覆盖问题已修复")
                self.logger.info(f"修复了样式覆盖问题: {file_path}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"修复文件失败 {file_path}: {e}")
            return False
    
    def _apply_fixes(self, content: str) -> str:
        """应用样式修复"""
        # 替换硬编码的颜色值
        for old_color, new_color in self.theme_compatible_colors.items():
            content = re.sub(
                rf'\b{re.escape(old_color)}\b',
                new_color,
                content,
                flags=re.IGNORECASE
            )
        
        # 修复setStyleSheet中的问题
        content = self._fix_setstylesheet_calls(content)
        
        return content
    
    def _fix_setstylesheet_calls(self, content: str) -> str:
        """修复setStyleSheet调用"""
        # 找到所有setStyleSheet调用
        pattern = r'(\w+\.setStyleSheet\([^)]+\))'
        matches = re.findall(pattern, content)
        
        for match in matches:
            # 检查是否包含不兼容的样式
            if self._contains_incompatible_styles(match):
                # 生成兼容的样式
                fixed_style = self._generate_compatible_style(match)
                if fixed_style:
                    content = content.replace(match, fixed_style)
        
        return content
    
    def _contains_incompatible_styles(self, stylesheet_call: str) -> bool:
        """检查样式表调用是否包含不兼容的样式"""
        for pattern, _ in self.problem_patterns:
            if re.search(pattern, stylesheet_call, re.IGNORECASE):
                return True
        return False
    
    def _is_theme_compatible_usage(self, match: str, content: str) -> bool:
        """检查颜色使用是否为主题兼容"""
        # 查找包含此匹配的完整setStyleSheet调用
        lines = content.split('\n')
        for line in lines:
            if match in line:
                # 检查是否包含主题兼容颜色
                for color in self.theme_compatible_colors_list:
                    if color in line:
                        return True
                # 检查是否使用了变量或主题管理器
                if any(keyword in line for keyword in ['theme_manager', 'COLORS', 'var(--', 'f"', 'f\'', '{', '}']):
                    return True
        return False
    
    def _generate_compatible_style(self, stylesheet_call: str) -> Optional[str]:
        """生成兼容的样式表调用"""
        # 这里可以实现更复杂的样式转换逻辑
        # 暂时返回None，表示需要手动处理
        return None
    
    def generate_report(self, problems: Dict[str, List[str]]) -> str:
        """生成问题报告"""
        report = "样式覆盖问题报告\n"
        report += "=" * 50 + "\n\n"
        
        total_files = len(problems)
        total_problems = sum(len(probs) for probs in problems.values())
        
        report += f"扫描结果: {total_files} 个文件存在 {total_problems} 个问题\n\n"
        
        for file_path, file_problems in problems.items():
            report += f"文件: {file_path}\n"
            for problem in file_problems:
                report += f"  - {problem}\n"
            report += "\n"
        
        return report
    
    def get_theme_compatible_suggestions(self) -> Dict[str, str]:
        """获取主题兼容的建议"""
        return {
            "使用ObjectName替代硬编码样式": "使用setObjectName()并在CSS中定义样式",
            "使用主题颜色变量": "使用theme_manager.COLORS中定义的颜色",
            "避免白色背景": "使用background_secondary或background_primary",
            "避免黑色文本": "使用text_primary或text_secondary",
            "使用主题兼容的按钮样式": "使用SuccessButton, ErrorButton等ObjectName",
        }


def create_theme_compatible_widget_mixin():
    """创建主题兼容的Widget混入类"""
    
    class ThemeCompatibleWidgetMixin:
        """主题兼容的Widget混入类"""
        
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._theme_manager = None
        
        def set_theme_manager(self, theme_manager):
            """设置主题管理器"""
            self._theme_manager = theme_manager
        
        def apply_theme_compatible_style(self, style_name: str = None):
            """应用主题兼容的样式"""
            if not self._theme_manager:
                try:
                    from .theme_manager_unified import get_unified_theme_manager
                    self._theme_manager = get_unified_theme_manager()
                except ImportError:
                    return
            
            if style_name:
                self.setObjectName(style_name)
            
            # 强制应用主题
            self._theme_manager.force_dark_theme(self)
        
        def set_theme_compatible_stylesheet(self, stylesheet: str):
            """设置主题兼容的样式表"""
            if not self._theme_manager:
                try:
                    from .theme_manager_unified import get_unified_theme_manager
                    self._theme_manager = get_unified_theme_manager()
                except ImportError:
                    self.setStyleSheet(stylesheet)
                    return
            
            # 替换样式表中的颜色变量
            colors = self._theme_manager.COLORS
            for key, value in colors.items():
                placeholder = f"var(--{key.replace('_', '-')})"
                stylesheet = stylesheet.replace(placeholder, value)
            
            self.setStyleSheet(stylesheet)
    
    return ThemeCompatibleWidgetMixin


# 全局检测器实例
_detector = None

def get_style_override_detector() -> StyleOverrideDetector:
    """获取样式覆盖检测器实例"""
    global _detector
    if _detector is None:
        _detector = StyleOverrideDetector()
    return _detector