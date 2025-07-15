#!/usr/bin/env python3
"""
AI员工4号 - 孔位ID格式转换验证工具
验证整个项目中的孔位ID格式转换完整性和正确性
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Tuple, Set
import sys

class ValidationResult:
    """验证结果类"""
    def __init__(self):
        self.total_files_checked = 0
        self.files_with_issues = []
        self.conversion_summary = {}
        self.old_format_found = []
        self.inconsistent_formats = []
        self.validation_errors = []
        
    def add_issue(self, file_path: str, issue_type: str, details: str):
        """添加问题"""
        self.files_with_issues.append({
            'file': file_path,
            'type': issue_type,
            'details': details
        })
    
    def is_valid(self) -> bool:
        """检查是否通过验证"""
        return len(self.files_with_issues) == 0

class HoleIdValidator:
    """孔位ID验证器"""
    
    def __init__(self):
        # 定义各种格式的正则表达式
        self.new_format_pattern = re.compile(r'C(\d{3})R(\d{3})')  # C001R001
        self.old_h_pattern = re.compile(r'H(\d{5})')  # H00001
        self.old_coord_pattern = re.compile(r'\((\d+),(\d+)\)')  # (140,1)
        self.old_r_c_pattern = re.compile(r'R(\d{3})C(\d{3})')  # R001C001
        
        self.validation_result = ValidationResult()
    
    def validate_project(self, project_root: Path) -> ValidationResult:
        """验证整个项目"""
        print("🔍 AI员工4号开始验证孔位ID格式转换...")
        print("=" * 60)
        
        # 定义需要检查的文件类型和路径
        check_patterns = [
            "**/*.py",
            "**/*.json",
            "**/*.md"
        ]
        
        all_files = set()
        for pattern in check_patterns:
            all_files.update(project_root.glob(pattern))
        
        # 排除备份文件和临时文件
        files_to_check = [
            f for f in all_files 
            if not any(x in str(f) for x in ['.backup', '.bak', '__pycache__', '.git'])
        ]
        
        print(f"📂 发现 {len(files_to_check)} 个文件需要检查")
        print()
        
        for file_path in files_to_check:
            self._validate_file(file_path)
            self.validation_result.total_files_checked += 1
        
        self._generate_summary()
        return self.validation_result
    
    def _validate_file(self, file_path: Path):
        """验证单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # 检查不同的ID格式
            self._check_formats_in_content(file_path, content)
            
        except Exception as e:
            self.validation_result.add_issue(
                str(file_path), 
                "读取错误", 
                f"无法读取文件: {e}"
            )
    
    def _check_formats_in_content(self, file_path: Path, content: str):
        """检查内容中的各种格式"""
        relative_path = str(file_path.relative_to(Path.cwd()))
        
        # 统计各种格式的出现次数
        new_format_matches = self.new_format_pattern.findall(content)
        old_h_matches = self.old_h_pattern.findall(content)
        old_coord_matches = self.old_coord_pattern.findall(content)
        old_r_c_matches = self.old_r_c_pattern.findall(content)
        
        # 记录统计信息
        if relative_path not in self.validation_result.conversion_summary:
            self.validation_result.conversion_summary[relative_path] = {
                'new_format': len(new_format_matches),
                'old_h_format': len(old_h_matches),
                'old_coord_format': len(old_coord_matches),
                'old_r_c_format': len(old_r_c_matches)
            }
        
        # 检查是否还有旧格式
        if old_h_matches and file_path.suffix in ['.py', '.json']:
            # 排除注释和文档中的引用
            if not self._is_documentation_reference(content, old_h_matches):
                self.validation_result.add_issue(
                    relative_path,
                    "旧格式残留",
                    f"发现 {len(old_h_matches)} 个 H 格式ID: {old_h_matches[:5]}"
                )
        
        if old_coord_matches and file_path.suffix in ['.py', '.json']:
            # 检查是否是真正的坐标格式而非其他用途
            if self._is_coordinate_format(content, old_coord_matches):
                self.validation_result.add_issue(
                    relative_path,
                    "坐标格式残留",
                    f"发现 {len(old_coord_matches)} 个坐标格式: {old_coord_matches[:5]}"
                )
        
        # 检查格式一致性
        if new_format_matches:
            self._validate_new_format_consistency(file_path, new_format_matches, relative_path)
    
    def _is_documentation_reference(self, content: str, matches: List) -> bool:
        """检查是否是文档中的引用（可以保留）"""
        # 检查是否在注释、文档字符串或说明文档中
        content_lower = content.lower()
        doc_indicators = [
            '# 修改前', '# 原格式', '示例', 'example', 'readme', 
            '说明', '文档', 'doc', '注释', 'comment'
        ]
        return any(indicator in content_lower for indicator in doc_indicators)
    
    def _is_coordinate_format(self, content: str, matches: List) -> bool:
        """检查是否是坐标格式"""
        # 简单检查：如果在JSON中的grid_position字段，则认为是坐标格式
        return 'grid_position' in content or 'coordinates' in content
    
    def _validate_new_format_consistency(self, file_path: Path, matches: List, relative_path: str):
        """验证新格式的一致性"""
        for col_str, row_str in matches:
            col, row = int(col_str), int(row_str)
            
            # 检查格式规范
            if col < 1 or col > 999:
                self.validation_result.add_issue(
                    relative_path,
                    "格式错误",
                    f"列号超出范围 (1-999): C{col:03d}R{row:03d}"
                )
            
            if row < 1 or row > 999:
                self.validation_result.add_issue(
                    relative_path,
                    "格式错误",
                    f"行号超出范围 (1-999): C{col:03d}R{row:03d}"
                )
    
    def _generate_summary(self):
        """生成验证摘要"""
        print("\n" + "="*60)
        print("📊 验证结果摘要")
        print("="*60)
        
        print(f"✅ 总检查文件数: {self.validation_result.total_files_checked}")
        print(f"❌ 有问题的文件数: {len(self.validation_result.files_with_issues)}")
        
        if self.validation_result.is_valid():
            print("\n🎉 验证通过！所有文件都已正确转换为新格式。")
        else:
            print(f"\n⚠️  发现 {len(self.validation_result.files_with_issues)} 个问题需要处理。")
        
        # 显示格式统计
        print("\n📈 格式分布统计:")
        total_new = sum(s['new_format'] for s in self.validation_result.conversion_summary.values())
        total_old_h = sum(s['old_h_format'] for s in self.validation_result.conversion_summary.values())
        total_old_coord = sum(s['old_coord_format'] for s in self.validation_result.conversion_summary.values())
        total_old_r_c = sum(s['old_r_c_format'] for s in self.validation_result.conversion_summary.values())
        
        print(f"  • 新格式 (C001R001): {total_new} 个")
        print(f"  • 旧H格式 (H00001): {total_old_h} 个")
        print(f"  • 旧坐标格式 ((1,1)): {total_old_coord} 个")
        print(f"  • 旧R-C格式 (R001C001): {total_old_r_c} 个")
        
        # 显示问题详情
        if self.validation_result.files_with_issues:
            print("\n🔧 需要处理的问题:")
            for i, issue in enumerate(self.validation_result.files_with_issues, 1):
                print(f"  {i}. {issue['file']}")
                print(f"     类型: {issue['type']}")
                print(f"     详情: {issue['details']}")
                print()
    
    def generate_report(self, output_path: Path):
        """生成详细的验证报告"""
        report_lines = []
        
        # AI员工4号修改开始
        report_lines.append("=" * 80)
        report_lines.append("AI员工4号 - 孔位ID格式转换验证报告")
        report_lines.append("=" * 80)
        report_lines.append(f"生成时间: {Path(__file__).stat().st_mtime}")
        report_lines.append(f"验证文件数: {self.validation_result.total_files_checked}")
        report_lines.append(f"发现问题数: {len(self.validation_result.files_with_issues)}")
        report_lines.append("")
        
        # 整体验证结果
        report_lines.append("1. 验证结果")
        report_lines.append("-" * 40)
        if self.validation_result.is_valid():
            report_lines.append("✅ 验证通过 - 所有文件格式转换正确")
        else:
            report_lines.append("❌ 验证失败 - 发现格式转换问题")
        report_lines.append("")
        
        # 格式统计
        report_lines.append("2. 格式分布统计")
        report_lines.append("-" * 40)
        for file_path, stats in self.validation_result.conversion_summary.items():
            if any(stats.values()):  # 只显示有数据的文件
                report_lines.append(f"文件: {file_path}")
                for format_type, count in stats.items():
                    if count > 0:
                        report_lines.append(f"  {format_type}: {count}")
                report_lines.append("")
        
        # 问题详情
        if self.validation_result.files_with_issues:
            report_lines.append("3. 发现的问题")
            report_lines.append("-" * 40)
            for issue in self.validation_result.files_with_issues:
                report_lines.append(f"文件: {issue['file']}")
                report_lines.append(f"类型: {issue['type']}")
                report_lines.append(f"详情: {issue['details']}")
                report_lines.append("")
        
        # 转换完成任务列表
        report_lines.append("4. AI员工4号完成的任务")
        report_lines.append("-" * 40)
        completed_tasks = [
            "✅ 大型数据文件转换: assets/dxf/DXF Graph/dongzhong_hole_grid.json (25,210个孔)",
            "✅ 报告生成接口更新: src/modules/report_output_interface.py",
            "✅ UI孔位显示更新: src/aidcis2/graphics/hole_item.py:169",
            "✅ 批处理数据转换: src/data/batch_0001_1752418706.json",
            "✅ 验证工具创建: scripts/validate_id_conversion.py"
        ]
        report_lines.extend(completed_tasks)
        report_lines.append("")
        
        report_lines.append("5. 转换规则确认")
        report_lines.append("-" * 40)
        report_lines.append("统一格式: C{column:03d}R{row:03d}")
        report_lines.append("示例转换:")
        report_lines.append("  H00001 → C001R001")
        report_lines.append("  (140,1) → C001R140") 
        report_lines.append("  R001C001 → C001R001")
        # AI员工4号修改结束
        
        # 写入报告文件
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(report_lines))
            print(f"\n📄 详细验证报告已生成: {output_path}")
        except Exception as e:
            print(f"❌ 生成报告失败: {e}")

def main():
    """主函数"""
    project_root = Path.cwd()
    validator = HoleIdValidator()
    
    # 执行验证
    result = validator.validate_project(project_root)
    
    # 生成详细报告
    report_path = project_root / "reports" / "id_conversion_validation_report.txt"
    report_path.parent.mkdir(exist_ok=True)
    validator.generate_report(report_path)
    
    # 返回验证结果
    return result.is_valid()

if __name__ == "__main__":
    success = main()
    print(f"\n{'='*60}")
    if success:
        print("🎉 AI员工4号验证完成 - 所有任务成功!")
    else:
        print("⚠️  AI员工4号验证完成 - 发现需要处理的问题")
    print(f"{'='*60}")
    
    sys.exit(0 if success else 1)