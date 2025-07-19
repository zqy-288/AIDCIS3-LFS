"""
报告历史管理器
管理已生成报告的历史记录、文件操作等
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import subprocess
import platform

from .report_models import ReportInstance


class ReportHistoryManager:
    """报告历史管理器"""
    
    def __init__(self, reports_dir: str = "reports"):
        self.reports_dir = Path(reports_dir)
        self.history_file = self.reports_dir / "report_history.json"
        self.reports_dir.mkdir(exist_ok=True)
        
        # 加载历史记录
        self.history_records = self.load_history()
    
    def load_history(self) -> List[Dict]:
        """加载报告历史记录"""
        if not self.history_file.exists():
            return []
        
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def save_history(self):
        """保存报告历史记录"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history_records, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存报告历史失败: {e}")
    
    def add_report_record(self, instance: ReportInstance):
        """添加报告记录"""
        # 检查文件是否存在并获取文件大小
        file_path = Path(instance.output_path)
        if file_path.exists():
            file_size = file_path.stat().st_size
            instance.file_size = file_size
            instance.completed_at = datetime.now()
            instance.status = "completed"
        else:
            instance.status = "failed"
            instance.error_message = "文件不存在"
        
        # 转换为字典并添加到历史记录
        record = instance.to_dict()
        
        # 添加额外信息
        record['file_exists'] = file_path.exists()
        record['file_extension'] = file_path.suffix
        record['relative_path'] = str(file_path.relative_to(self.reports_dir)) if file_path.exists() else instance.output_path
        
        # 插入到列表开头（最新的在前面）
        self.history_records.insert(0, record)
        
        # 限制历史记录数量（保留最近100条）
        if len(self.history_records) > 100:
            self.history_records = self.history_records[:100]
        
        # 保存到文件
        self.save_history()
    
    def get_history_records(self, workpiece_id: Optional[str] = None) -> List[Dict]:
        """获取历史记录"""
        if workpiece_id:
            return [record for record in self.history_records if record.get('workpiece_id') == workpiece_id]
        return self.history_records.copy()
    
    def delete_report(self, instance_id: str) -> bool:
        """删除报告"""
        try:
            # 查找记录
            record = None
            for r in self.history_records:
                if r.get('instance_id') == instance_id:
                    record = r
                    break
            
            if not record:
                return False
            
            # 删除文件
            file_path = Path(record['output_path'])
            if file_path.exists():
                file_path.unlink()
            
            # 从历史记录中移除
            self.history_records.remove(record)
            self.save_history()
            
            return True
            
        except Exception as e:
            print(f"删除报告失败: {e}")
            return False
    
    def open_report(self, instance_id: str) -> bool:
        """打开报告文件"""
        try:
            # 查找记录
            record = None
            for r in self.history_records:
                if r.get('instance_id') == instance_id:
                    record = r
                    break
            
            if not record:
                return False
            
            file_path = Path(record['output_path'])
            if not file_path.exists():
                return False
            
            # 根据操作系统打开文件
            if platform.system() == 'Windows':
                os.startfile(str(file_path))
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', str(file_path)])
            else:  # Linux
                subprocess.run(['xdg-open', str(file_path)])
            
            return True
            
        except Exception as e:
            print(f"打开报告失败: {e}")
            return False
    
    def open_report_directory(self, instance_id: str) -> bool:
        """打开报告所在目录"""
        try:
            # 查找记录
            record = None
            for r in self.history_records:
                if r.get('instance_id') == instance_id:
                    record = r
                    break
            
            if not record:
                return False
            
            file_path = Path(record['output_path'])
            directory = file_path.parent
            
            if not directory.exists():
                return False
            
            # 根据操作系统打开目录
            if platform.system() == 'Windows':
                os.startfile(str(directory))
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', str(directory)])
            else:  # Linux
                subprocess.run(['xdg-open', str(directory)])
            
            return True
            
        except Exception as e:
            print(f"打开目录失败: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        total_reports = len(self.history_records)
        completed_reports = sum(1 for r in self.history_records if r.get('status') == 'completed')
        failed_reports = sum(1 for r in self.history_records if r.get('status') == 'failed')
        
        # 按工件分组统计
        workpiece_stats = {}
        for record in self.history_records:
            workpiece_id = record.get('workpiece_id', 'unknown')
            if workpiece_id not in workpiece_stats:
                workpiece_stats[workpiece_id] = 0
            workpiece_stats[workpiece_id] += 1
        
        # 按格式分组统计
        format_stats = {}
        for record in self.history_records:
            file_ext = record.get('file_extension', 'unknown')
            if file_ext not in format_stats:
                format_stats[file_ext] = 0
            format_stats[file_ext] += 1
        
        # 计算总文件大小
        total_size = sum(record.get('file_size', 0) for record in self.history_records if record.get('file_size'))
        
        return {
            'total_reports': total_reports,
            'completed_reports': completed_reports,
            'failed_reports': failed_reports,
            'workpiece_stats': workpiece_stats,
            'format_stats': format_stats,
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024) if total_size > 0 else 0
        }
    
    def cleanup_missing_files(self) -> int:
        """清理不存在的文件记录"""
        removed_count = 0
        records_to_remove = []
        
        for record in self.history_records:
            file_path = Path(record['output_path'])
            if not file_path.exists():
                records_to_remove.append(record)
                removed_count += 1
        
        for record in records_to_remove:
            self.history_records.remove(record)
        
        if removed_count > 0:
            self.save_history()
        
        return removed_count
    
    def format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    
    def export_history_report(self, output_path: str) -> bool:
        """导出历史记录报告"""
        try:
            stats = self.get_statistics()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("报告历史记录汇总\n")
                f.write("=" * 50 + "\n\n")
                
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                f.write("统计信息:\n")
                f.write(f"  总报告数: {stats['total_reports']}\n")
                f.write(f"  成功生成: {stats['completed_reports']}\n")
                f.write(f"  生成失败: {stats['failed_reports']}\n")
                f.write(f"  总文件大小: {self.format_file_size(stats['total_size_bytes'])}\n\n")
                
                f.write("按工件统计:\n")
                for workpiece_id, count in stats['workpiece_stats'].items():
                    f.write(f"  {workpiece_id}: {count} 个报告\n")
                f.write("\n")
                
                f.write("按格式统计:\n")
                for format_type, count in stats['format_stats'].items():
                    f.write(f"  {format_type}: {count} 个文件\n")
                f.write("\n")
                
                f.write("详细记录:\n")
                f.write("-" * 50 + "\n")
                for i, record in enumerate(self.history_records, 1):
                    f.write(f"{i}. {record.get('workpiece_id', 'N/A')} - {record.get('created_at', 'N/A')}\n")
                    f.write(f"   文件: {record.get('relative_path', 'N/A')}\n")
                    f.write(f"   状态: {record.get('status', 'N/A')}\n")
                    if record.get('file_size'):
                        f.write(f"   大小: {self.format_file_size(record['file_size'])}\n")
                    f.write("\n")
            
            return True
            
        except Exception as e:
            print(f"导出历史记录失败: {e}")
            return False
