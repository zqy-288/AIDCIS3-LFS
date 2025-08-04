"""
报告历史管理面板组件
提供报告历史记录的查看、管理和操作功能
"""

from datetime import datetime
from typing import List, Dict, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QMenu
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction

# 从assets/old目录导入历史管理器
from assets.old.report_history_manager import ReportHistoryManager


class ReportHistoryPanel(QWidget):
    """报告历史管理面板"""
    
    # 信号
    history_refreshed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.history_manager = ReportHistoryManager()
        self._init_ui()
        self._init_connections()
    
    def _init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        
        self.refresh_history_btn = QPushButton("刷新")
        self.cleanup_history_btn = QPushButton("清理失效记录")
        self.export_history_btn = QPushButton("导出历史记录")
        
        toolbar_layout.addWidget(self.refresh_history_btn)
        toolbar_layout.addWidget(self.cleanup_history_btn)
        toolbar_layout.addWidget(self.export_history_btn)
        toolbar_layout.addStretch()
        
        layout.addLayout(toolbar_layout)
        
        # 报告历史表格
        history_group = QGroupBox("报告历史")
        history_layout = QVBoxLayout(history_group)
        
        self.report_history_table = QTableWidget()
        self.report_history_table.setColumnCount(6)
        self.report_history_table.setHorizontalHeaderLabels([
            "序号", "生成时间", "工件ID", "状态", "文件大小", "格式"
        ])
        
        # 启用右键菜单
        self.report_history_table.setContextMenuPolicy(Qt.CustomContextMenu)
        
        history_layout.addWidget(self.report_history_table)
        layout.addWidget(history_group)
    
    def _init_connections(self):
        """初始化信号连接"""
        self.refresh_history_btn.clicked.connect(self.refresh_history)
        self.cleanup_history_btn.clicked.connect(self.cleanup_history)
        self.export_history_btn.clicked.connect(self.export_history)
        self.report_history_table.customContextMenuRequested.connect(self._show_context_menu)
    
    def refresh_history(self):
        """刷新历史记录"""
        try:
            # 重新加载历史记录
            self.history_manager.history_records = self.history_manager.load_history()
            
            # 更新表格
            records = self.history_manager.get_history_records()
            self.report_history_table.setRowCount(len(records))
            
            for row, record in enumerate(records):
                # 序号列
                seq_item = QTableWidgetItem(str(row + 1))
                seq_item.setTextAlignment(Qt.AlignCenter)
                self.report_history_table.setItem(row, 0, seq_item)
                
                # 生成时间
                created_at = record.get('created_at', '')
                if created_at:
                    try:
                        dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        time_str = dt.strftime('%m-%d %H:%M')
                    except:
                        time_str = created_at[:16]
                else:
                    time_str = '未知'
                self.report_history_table.setItem(row, 1, QTableWidgetItem(time_str))
                
                # 工件ID
                workpiece_id = record.get('workpiece_id', '未知')
                self.report_history_table.setItem(row, 2, QTableWidgetItem(workpiece_id))
                
                # 状态
                status = record.get('status', '未知')
                self.report_history_table.setItem(row, 3, QTableWidgetItem(status))
                
                # 文件大小
                file_size = record.get('file_size', 0)
                if file_size:
                    size_str = self.history_manager.format_file_size(file_size)
                else:
                    size_str = '-'
                self.report_history_table.setItem(row, 4, QTableWidgetItem(size_str))
                
                # 格式
                file_ext = record.get('file_extension', '').upper()
                if file_ext.startswith('.'):
                    file_ext = file_ext[1:]
                self.report_history_table.setItem(row, 5, QTableWidgetItem(file_ext))
            
            self.history_refreshed.emit()
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"刷新历史记录失败: {str(e)}")
    
    def cleanup_history(self):
        """清理失效的历史记录"""
        removed_count = self.history_manager.cleanup_missing_files()
        if removed_count > 0:
            self.refresh_history()
            QMessageBox.information(self, "清理完成", f"已清理 {removed_count} 条失效记录")
        else:
            QMessageBox.information(self, "清理完成", "没有发现失效记录")
    
    def export_history(self):
        """导出历史记录"""
        from PySide6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出历史记录",
            f"report_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "文本文件 (*.txt);;所有文件 (*)"
        )
        
        if file_path:
            if self.history_manager.export_history_report(file_path):
                QMessageBox.information(self, "导出成功", f"历史记录已导出到:\n{file_path}")
            else:
                QMessageBox.warning(self, "导出失败", "导出历史记录失败")
    
    def _show_context_menu(self, position):
        """显示右键上下文菜单"""
        item = self.report_history_table.itemAt(position)
        if not item:
            return
        
        row = item.row()
        
        # 从历史记录中获取该行的数据
        try:
            record = self.history_manager.get_history_records()[row]
            instance_id = record.get('instance_id')
            file_exists = record.get('file_exists', False)
        except IndexError:
            return
        
        # 创建菜单
        menu = QMenu()
        
        # 创建操作
        open_action = QAction("打开文件", self)
        open_action.setEnabled(file_exists)
        open_action.triggered.connect(lambda: self._open_report_file(instance_id))
        
        dir_action = QAction("打开所在目录", self)
        dir_action.setEnabled(file_exists)
        dir_action.triggered.connect(lambda: self._open_report_directory(instance_id))
        
        delete_action = QAction("删除记录", self)
        delete_action.triggered.connect(lambda: self._delete_report_file(instance_id))
        
        # 将操作添加到菜单
        menu.addAction(open_action)
        menu.addAction(dir_action)
        menu.addSeparator()
        menu.addAction(delete_action)
        
        # 在鼠标光标位置显示菜单
        menu.exec(self.report_history_table.viewport().mapToGlobal(position))
    
    def _open_report_file(self, instance_id: str):
        """打开报告文件"""
        if self.history_manager.open_report(instance_id):
            # 可以发射成功信号
            pass
        else:
            QMessageBox.warning(self, "错误", "无法打开报告文件")
    
    def _open_report_directory(self, instance_id: str):
        """打开报告目录"""
        if self.history_manager.open_report_directory(instance_id):
            # 可以发射成功信号
            pass
        else:
            QMessageBox.warning(self, "错误", "无法打开报告目录")
    
    def _delete_report_file(self, instance_id: str):
        """删除报告文件"""
        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除这个报告文件吗？\n\n此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.history_manager.delete_report(instance_id):
                self.refresh_history()
            else:
                QMessageBox.warning(self, "错误", "删除报告失败")
    
    def add_report_record(self, report_instance):
        """添加报告记录到历史"""
        self.history_manager.add_report_record(report_instance)
        self.refresh_history()
    
    def get_history_count(self) -> int:
        """获取历史记录数量"""
        return len(self.history_manager.get_history_records())