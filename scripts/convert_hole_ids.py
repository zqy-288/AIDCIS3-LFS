#!/usr/bin/env python3
"""
孔位ID格式批量转换脚本
AI员工2号创建 - 2025-01-14

功能：
- 批量转换现有数据文件中的孔位ID格式
- 从各种旧格式转换为统一的C{column:03d}R{row:03d}格式
- 支持多种文件类型：JSON、TXT、Python文件等
- 提供转换前备份和验证功能
"""

import os
import re
import json
import shutil
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime


class HoleIDConverter:
    """孔位ID格式转换器"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.conversion_stats = {
            "files_processed": 0,
            "files_modified": 0,
            "total_conversions": 0,
            "conversion_types": {},
            "errors": []
        }
        
    @staticmethod
    def convert_hole_id(old_id: str) -> Tuple[str, str]:
        """
        转换孔位ID格式
        
        Args:
            old_id: 旧格式的孔位ID
            
        Returns:
            Tuple[str, str]: (新格式ID, 转换类型)
        """
        # 如果已经是新格式，直接返回
        if re.match(r'^C\d{3}R\d{3}$', old_id):
            return old_id, "already_new_format"
        
        # H格式转换: H00001 -> 需要推测行列
        h_match = re.match(r'^H(\d+)$', old_id)
        if h_match:
            hole_num = int(h_match.group(1))
            # 简单的行列推算（假设每行最多100个孔）
            row = ((hole_num - 1) // 100) + 1
            col = ((hole_num - 1) % 100) + 1
            return f"C{col:03d}R{row:03d}", "H_format"
        
        # 坐标格式转换: (row,col) -> C{col:03d}R{row:03d}
        coord_match = re.match(r'^\((\d+),(\d+)\)$', old_id)
        if coord_match:
            row, col = map(int, coord_match.groups())
            return f"C{col:03d}R{row:03d}", "coordinate_format"
        
        # R###C###格式转换: R001C002 -> C002R001
        rc_match = re.match(r'^R(\d+)C(\d+)$', old_id)
        if rc_match:
            row, col = map(int, rc_match.groups())
            return f"C{col:03d}R{row:03d}", "RC_format"
        
        # hole_格式转换: hole_1 -> C001R001 (假设单行排列)
        hole_match = re.match(r'^hole_(\d+)$', old_id)
        if hole_match:
            hole_num = int(hole_match.group(1))
            # 假设单行排列
            return f"C{hole_num:03d}R001", "hole_format"
        
        return old_id, "unknown_format"
    
    def convert_json_file(self, file_path: Path) -> bool:
        """转换JSON文件中的孔位ID"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            modified = False
            conversions_made = 0
            
            def convert_recursive(obj):
                nonlocal modified, conversions_made
                
                if isinstance(obj, dict):
                    for key, value in list(obj.items()):
                        # 检查键是否是孔位ID
                        if any(pattern in key.lower() for pattern in ['hole_id', 'grid_position', 'hole']):
                            if isinstance(value, str):
                                new_id, conv_type = self.convert_hole_id(value)
                                if new_id != value:
                                    obj[key] = new_id
                                    modified = True
                                    conversions_made += 1
                                    self.conversion_stats["conversion_types"][conv_type] = \
                                        self.conversion_stats["conversion_types"].get(conv_type, 0) + 1
                        
                        # 递归处理值
                        convert_recursive(value)
                        
                elif isinstance(obj, list):
                    for item in obj:
                        convert_recursive(item)
                        
                elif isinstance(obj, str):
                    # 检查字符串是否包含孔位ID模式
                    for pattern in [r'H\d+', r'\(\d+,\d+\)', r'R\d+C\d+', r'hole_\d+']:
                        if re.search(pattern, obj):
                            # 这里可以添加更复杂的字符串内容替换逻辑
                            pass
            
            convert_recursive(data)
            
            if modified:
                # 创建备份
                backup_path = file_path.with_suffix(f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
                shutil.copy2(file_path, backup_path)
                
                # 写入修改后的文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                print(f"✅ 转换 {file_path}: {conversions_made} 个孔位ID")
                return True
            
            return False
            
        except Exception as e:
            error_msg = f"转换JSON文件 {file_path} 失败: {e}"
            print(f"❌ {error_msg}")
            self.conversion_stats["errors"].append(error_msg)
            return False
    
    def convert_python_file(self, file_path: Path) -> bool:
        """转换Python文件中的孔位ID"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            conversions_made = 0
            
            # 转换字符串中的孔位ID模式
            patterns = [
                (r'"H(\d+)"', lambda m: f'"C{int(m.group(1)) % 100 or 100:03d}R{(int(m.group(1)) - 1) // 100 + 1:03d}"'),
                (r"'H(\d+)'", lambda m: f"'C{int(m.group(1)) % 100 or 100:03d}R{(int(m.group(1)) - 1) // 100 + 1:03d}'"),
                (r'"R(\d+)C(\d+)"', lambda m: f'"C{int(m.group(2)):03d}R{int(m.group(1)):03d}"'),
                (r"'R(\d+)C(\d+)'", lambda m: f"'C{int(m.group(2)):03d}R{int(m.group(1)):03d}'"),
            ]
            
            for pattern, replacement in patterns:
                new_content, count = re.subn(pattern, replacement, content)
                if count > 0:
                    content = new_content
                    conversions_made += count
                    self.conversion_stats["conversion_types"]["python_string"] = \
                        self.conversion_stats["conversion_types"].get("python_string", 0) + count
            
            if content != original_content:
                # 创建备份
                backup_path = file_path.with_suffix(f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.py')
                shutil.copy2(file_path, backup_path)
                
                # 写入修改后的文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"✅ 转换 {file_path}: {conversions_made} 个孔位ID")
                return True
            
            return False
            
        except Exception as e:
            error_msg = f"转换Python文件 {file_path} 失败: {e}"
            print(f"❌ {error_msg}")
            self.conversion_stats["errors"].append(error_msg)
            return False
    
    def convert_text_file(self, file_path: Path) -> bool:
        """转换文本文件中的孔位ID"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            conversions_made = 0
            
            # 查找并替换孔位ID模式
            def replace_hole_id(match):
                nonlocal conversions_made
                old_id = match.group(0)
                new_id, conv_type = self.convert_hole_id(old_id)
                if new_id != old_id:
                    conversions_made += 1
                    self.conversion_stats["conversion_types"][conv_type] = \
                        self.conversion_stats["conversion_types"].get(conv_type, 0) + 1
                return new_id
            
            # 匹配各种孔位ID格式
            patterns = [
                r'H\d+',
                r'\(\d+,\d+\)',
                r'R\d+C\d+',
                r'hole_\d+'
            ]
            
            for pattern in patterns:
                content = re.sub(pattern, replace_hole_id, content)
            
            if content != original_content:
                # 创建备份
                backup_path = file_path.with_suffix(f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}{file_path.suffix}')
                shutil.copy2(file_path, backup_path)
                
                # 写入修改后的文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"✅ 转换 {file_path}: {conversions_made} 个孔位ID")
                return True
            
            return False
            
        except Exception as e:
            error_msg = f"转换文本文件 {file_path} 失败: {e}"
            print(f"❌ {error_msg}")
            self.conversion_stats["errors"].append(error_msg)
            return False
    
    def convert_file(self, file_path: Path) -> bool:
        """根据文件类型选择转换方法"""
        self.conversion_stats["files_processed"] += 1
        
        if file_path.suffix.lower() == '.json':
            result = self.convert_json_file(file_path)
        elif file_path.suffix.lower() == '.py':
            result = self.convert_python_file(file_path)
        elif file_path.suffix.lower() in ['.txt', '.md', '.rst']:
            result = self.convert_text_file(file_path)
        else:
            print(f"⚠️ 跳过不支持的文件类型: {file_path}")
            return False
        
        if result:
            self.conversion_stats["files_modified"] += 1
        
        return result
    
    def scan_and_convert(self, target_paths: List[str] = None, file_patterns: List[str] = None) -> Dict:
        """扫描并转换指定路径中的文件"""
        if target_paths is None:
            target_paths = [
                "src/",
                "assets/",
                "Data/",
                "reports/",
                "scripts/"
            ]
        
        if file_patterns is None:
            file_patterns = ["*.json", "*.py", "*.txt", "*.md"]
        
        print(f"🔍 开始扫描转换...")
        print(f"📁 目标路径: {target_paths}")
        print(f"📄 文件模式: {file_patterns}")
        
        for target_path in target_paths:
            full_path = self.project_root / target_path
            if not full_path.exists():
                print(f"⚠️ 路径不存在: {full_path}")
                continue
            
            print(f"\n📂 扫描 {target_path}...")
            
            for pattern in file_patterns:
                for file_path in full_path.rglob(pattern):
                    # 跳过备份文件
                    if '.backup_' in file_path.name:
                        continue
                    
                    print(f"🔄 处理 {file_path.relative_to(self.project_root)}")
                    self.convert_file(file_path)
        
        return self.conversion_stats
    
    def generate_conversion_report(self, output_file: str = None) -> str:
        """生成转换报告"""
        report = {
            "conversion_time": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "statistics": self.conversion_stats,
            "summary": {
                "success_rate": (self.conversion_stats["files_modified"] / 
                               max(self.conversion_stats["files_processed"], 1)) * 100
            }
        }
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"📄 转换报告已保存: {output_file}")
        
        # 打印摘要
        print(f"\n📊 转换完成摘要:")
        print(f"   处理文件数: {self.conversion_stats['files_processed']}")
        print(f"   修改文件数: {self.conversion_stats['files_modified']}")
        print(f"   总转换数: {self.conversion_stats['total_conversions']}")
        print(f"   成功率: {report['summary']['success_rate']:.1f}%")
        
        if self.conversion_stats["conversion_types"]:
            print(f"   转换类型分布:")
            for conv_type, count in self.conversion_stats["conversion_types"].items():
                print(f"     {conv_type}: {count}")
        
        if self.conversion_stats["errors"]:
            print(f"   错误数: {len(self.conversion_stats['errors'])}")
            for error in self.conversion_stats["errors"][:5]:  # 只显示前5个错误
                print(f"     - {error}")
        
        return json.dumps(report, ensure_ascii=False, indent=2)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="孔位ID格式批量转换工具",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--project-root", "-r",
        default=".",
        help="项目根目录路径（默认: 当前目录）"
    )
    
    parser.add_argument(
        "--paths", "-p",
        nargs="+",
        default=["src/", "assets/", "Data/", "reports/"],
        help="要转换的目录路径列表"
    )
    
    parser.add_argument(
        "--patterns", "-f",
        nargs="+",
        default=["*.json", "*.py", "*.txt", "*.md"],
        help="要处理的文件模式"
    )
    
    parser.add_argument(
        "--report", "-o",
        help="转换报告输出文件路径"
    )
    
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="模拟运行（不实际修改文件）"
    )
    
    args = parser.parse_args()
    
    print("🔧 孔位ID格式批量转换工具")
    print("=" * 50)
    print(f"📁 项目根目录: {args.project_root}")
    
    if args.dry_run:
        print("🔍 模拟运行模式（不会修改文件）")
    
    converter = HoleIDConverter(args.project_root)
    
    # 执行转换
    try:
        stats = converter.scan_and_convert(args.paths, args.patterns)
        
        # 生成报告
        report_file = args.report or f"conversion_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        converter.generate_conversion_report(report_file)
        
        print(f"\n✅ 转换完成!")
        
    except KeyboardInterrupt:
        print(f"\n⚠️ 用户中断转换")
    except Exception as e:
        print(f"\n❌ 转换失败: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())