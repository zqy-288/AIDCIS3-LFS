"""
文件操作增强模块
提供DXF文件拖放支持、批量文件导入、检测结果导出、报告生成等功能
支持多种文件格式和异步操作
"""

import logging
import os
import json
import csv
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict

from PySide6.QtCore import QObject, Signal, QThread, QMimeData, QUrl
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QLabel, QPushButton, QProgressBar, QTextEdit,
                               QFileDialog, QMessageBox, QGroupBox, QComboBox,
                               QCheckBox, QSpinBox, QListWidget, QListWidgetItem)
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtCore import Qt


class FileFormat(Enum):
    """文件格式枚举"""
    DXF = "dxf"
    JSON = "json"
    CSV = "csv"
    XLSX = "xlsx"
    PDF = "pdf"
    HTML = "html"
    XML = "xml"


class ExportType(Enum):
    """导出类型枚举"""
    DETECTION_RESULTS = "detection_results"
    STATISTICS_SUMMARY = "statistics_summary"
    HOLE_DETAILS = "hole_details"
    BATCH_REPORT = "batch_report"
    FULL_REPORT = "full_report"


@dataclass
class FileOperation:
    """文件操作数据类"""
    operation_type: str
    file_path: str
    timestamp: datetime
    status: str = "pending"
    progress: float = 0.0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class ExportConfig:
    """导出配置"""
    export_type: ExportType
    file_format: FileFormat
    output_path: str
    include_statistics: bool = True
    include_images: bool = False
    include_metadata: bool = True
    compress_output: bool = False
    custom_template: Optional[str] = None


class FileOperationWorker(QThread):
    """文件操作工作线程"""
    
    operation_progress = Signal(str, float)  # operation_id, progress
    operation_completed = Signal(str, bool, str)  # operation_id, success, result_path
    operation_error = Signal(str, str)  # operation_id, error_message
    
    def __init__(self, operation_id: str, operation_type: str, **kwargs):
        super().__init__()
        self.operation_id = operation_id
        self.operation_type = operation_type
        self.kwargs = kwargs
        self.logger = logging.getLogger(__name__)
        self.is_cancelled = False
    
    def run(self):
        """执行文件操作"""
        try:
            if self.operation_type == "import_dxf":
                self._import_dxf_files()
            elif self.operation_type == "export_data":
                self._export_detection_data()
            elif self.operation_type == "generate_report":
                self._generate_report()
            elif self.operation_type == "batch_import":
                self._batch_import_files()
            else:
                raise ValueError(f"不支持的操作类型: {self.operation_type}")
                
        except Exception as e:
            self.logger.error(f"文件操作失败: {e}")
            self.operation_error.emit(self.operation_id, str(e))
    
    def _import_dxf_files(self):
        """导入DXF文件"""
        file_paths = self.kwargs.get('file_paths', [])
        
        for i, file_path in enumerate(file_paths):
            if self.is_cancelled:
                break
                
            try:
                progress = (i / len(file_paths)) * 100
                self.operation_progress.emit(self.operation_id, progress)
                
                # 模拟DXF文件解析
                self.msleep(100)  # 模拟处理时间
                
                # 这里应该调用实际的DXF解析逻辑
                self.logger.info(f"导入DXF文件: {file_path}")
                
            except Exception as e:
                self.logger.error(f"导入DXF文件失败 {file_path}: {e}")
        
        self.operation_completed.emit(self.operation_id, True, "DXF导入完成")
    
    def _export_detection_data(self):
        """导出检测数据"""
        export_config = self.kwargs.get('export_config')
        detection_data = self.kwargs.get('detection_data', {})
        
        try:
            output_path = export_config.output_path
            file_format = export_config.file_format
            
            # 根据格式导出数据
            if file_format == FileFormat.JSON:
                self._export_to_json(detection_data, output_path)
            elif file_format == FileFormat.CSV:
                self._export_to_csv(detection_data, output_path)
            elif file_format == FileFormat.XLSX:
                self._export_to_excel(detection_data, output_path)
            else:
                raise ValueError(f"不支持的导出格式: {file_format}")
            
            self.operation_completed.emit(self.operation_id, True, output_path)
            
        except Exception as e:
            self.operation_error.emit(self.operation_id, f"导出失败: {e}")
    
    def _generate_report(self):
        """生成报告"""
        report_config = self.kwargs.get('report_config')
        report_data = self.kwargs.get('report_data', {})
        
        try:
            # 模拟报告生成过程
            for progress in range(0, 101, 10):
                if self.is_cancelled:
                    break
                self.operation_progress.emit(self.operation_id, progress)
                self.msleep(50)
            
            output_path = report_config.get('output_path', 'report.pdf')
            
            # 这里应该实现实际的报告生成逻辑
            self._create_sample_report(output_path, report_data)
            
            self.operation_completed.emit(self.operation_id, True, output_path)
            
        except Exception as e:
            self.operation_error.emit(self.operation_id, f"报告生成失败: {e}")
    
    def _batch_import_files(self):
        """批量导入文件"""
        file_paths = self.kwargs.get('file_paths', [])
        import_type = self.kwargs.get('import_type', 'dxf')
        
        successful_imports = 0
        
        for i, file_path in enumerate(file_paths):
            if self.is_cancelled:
                break
                
            try:
                progress = (i / len(file_paths)) * 100
                self.operation_progress.emit(self.operation_id, progress)
                
                # 根据类型处理文件
                if import_type == 'dxf':
                    self._process_dxf_file(file_path)
                elif import_type == 'config':
                    self._process_config_file(file_path)
                
                successful_imports += 1
                self.msleep(50)
                
            except Exception as e:
                self.logger.error(f"处理文件失败 {file_path}: {e}")
        
        result_msg = f"批量导入完成: {successful_imports}/{len(file_paths)} 个文件成功"
        self.operation_completed.emit(self.operation_id, True, result_msg)
    
    def _export_to_json(self, data: Dict, output_path: str):
        """导出为JSON格式"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        self.logger.info(f"JSON导出完成: {output_path}")
    
    def _export_to_csv(self, data: Dict, output_path: str):
        """导出为CSV格式"""
        # 假设data包含孔位检测结果
        holes_data = data.get('holes', [])
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            if holes_data:
                writer = csv.DictWriter(f, fieldnames=holes_data[0].keys())
                writer.writeheader()
                writer.writerows(holes_data)
        
        self.logger.info(f"CSV导出完成: {output_path}")
    
    def _export_to_excel(self, data: Dict, output_path: str):
        """导出为Excel格式"""
        try:
            import pandas as pd
            
            # 创建Excel工作簿
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # 导出孔位数据
                if 'holes' in data:
                    holes_df = pd.DataFrame(data['holes'])
                    holes_df.to_excel(writer, sheet_name='孔位数据', index=False)
                
                # 导出统计数据
                if 'statistics' in data:
                    stats_df = pd.DataFrame([data['statistics']])
                    stats_df.to_excel(writer, sheet_name='统计信息', index=False)
            
            self.logger.info(f"Excel导出完成: {output_path}")
            
        except ImportError:
            # 如果pandas不可用，使用基础方法
            self._export_to_csv(data, output_path.replace('.xlsx', '.csv'))
    
    def _create_sample_report(self, output_path: str, data: Dict):
        """创建示例报告"""
        # 这里是一个简化的报告生成示例
        # 实际实现应该使用专业的报告生成库
        
        report_content = f"""
检测报告
==================

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

检测统计:
- 总孔数: {data.get('total_holes', 0)}
- 合格数: {data.get('qualified_holes', 0)}
- 不合格数: {data.get('unqualified_holes', 0)}
- 合格率: {data.get('qualification_rate', 0):.2f}%

详细信息:
{json.dumps(data, ensure_ascii=False, indent=2)}
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
    
    def _process_dxf_file(self, file_path: str):
        """处理DXF文件"""
        # 这里应该调用实际的DXF处理逻辑
        self.logger.debug(f"处理DXF文件: {file_path}")
    
    def _process_config_file(self, file_path: str):
        """处理配置文件"""
        # 这里应该调用实际的配置文件处理逻辑
        self.logger.debug(f"处理配置文件: {file_path}")
    
    def cancel_operation(self):
        """取消操作"""
        self.is_cancelled = True


class FileOperationsManager(QObject):
    """文件操作管理器"""
    
    # 信号定义
    operation_started = Signal(str)  # operation_id
    operation_progress = Signal(str, float)  # operation_id, progress
    operation_completed = Signal(str, bool, str)  # operation_id, success, result
    operation_error = Signal(str, str)  # operation_id, error
    files_dropped = Signal(list)  # file_paths
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 操作管理
        self.active_operations: Dict[str, FileOperationWorker] = {}
        self.operation_history: List[FileOperation] = []
        
        # 配置
        self.supported_dxf_extensions = ['.dxf', '.dwg']
        self.supported_export_formats = list(FileFormat)
        
        self.logger.info("📁 文件操作管理器初始化完成")
    
    def import_dxf_files(self, file_paths: List[str]) -> str:
        """导入DXF文件"""
        operation_id = self._generate_operation_id("import_dxf")
        
        try:
            # 验证文件
            valid_files = self._validate_dxf_files(file_paths)
            if not valid_files:
                raise ValueError("没有有效的DXF文件")
            
            # 创建工作线程
            worker = FileOperationWorker(
                operation_id, "import_dxf",
                file_paths=valid_files
            )
            
            self._start_operation(operation_id, worker)
            
            return operation_id
            
        except Exception as e:
            self.logger.error(f"启动DXF导入失败: {e}")
            self.operation_error.emit(operation_id, str(e))
            return operation_id
    
    def export_detection_data(self, data: Dict[str, Any], export_config: ExportConfig) -> str:
        """导出检测数据"""
        operation_id = self._generate_operation_id("export_data")
        
        try:
            # 验证导出配置
            self._validate_export_config(export_config)
            
            # 创建工作线程
            worker = FileOperationWorker(
                operation_id, "export_data",
                detection_data=data,
                export_config=export_config
            )
            
            self._start_operation(operation_id, worker)
            
            return operation_id
            
        except Exception as e:
            self.logger.error(f"启动数据导出失败: {e}")
            self.operation_error.emit(operation_id, str(e))
            return operation_id
    
    def generate_report(self, data: Dict[str, Any], report_config: Dict[str, Any]) -> str:
        """生成报告"""
        operation_id = self._generate_operation_id("generate_report")
        
        try:
            # 创建工作线程
            worker = FileOperationWorker(
                operation_id, "generate_report",
                report_data=data,
                report_config=report_config
            )
            
            self._start_operation(operation_id, worker)
            
            return operation_id
            
        except Exception as e:
            self.logger.error(f"启动报告生成失败: {e}")
            self.operation_error.emit(operation_id, str(e))
            return operation_id
    
    def batch_import_files(self, file_paths: List[str], import_type: str = "dxf") -> str:
        """批量导入文件"""
        operation_id = self._generate_operation_id("batch_import")
        
        try:
            if not file_paths:
                raise ValueError("文件列表为空")
            
            # 创建工作线程
            worker = FileOperationWorker(
                operation_id, "batch_import",
                file_paths=file_paths,
                import_type=import_type
            )
            
            self._start_operation(operation_id, worker)
            
            return operation_id
            
        except Exception as e:
            self.logger.error(f"启动批量导入失败: {e}")
            self.operation_error.emit(operation_id, str(e))
            return operation_id
    
    def cancel_operation(self, operation_id: str) -> bool:
        """取消操作"""
        try:
            if operation_id in self.active_operations:
                worker = self.active_operations[operation_id]
                worker.cancel_operation()
                worker.wait(3000)  # 等待3秒
                
                del self.active_operations[operation_id]
                self.logger.info(f"操作已取消: {operation_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"取消操作失败: {e}")
            return False
    
    def get_operation_status(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """获取操作状态"""
        try:
            for operation in self.operation_history:
                if operation_id in str(operation.operation_type):
                    return asdict(operation)
            return None
            
        except Exception as e:
            self.logger.error(f"获取操作状态失败: {e}")
            return None
    
    def get_active_operations(self) -> List[str]:
        """获取活动操作列表"""
        return list(self.active_operations.keys())
    
    def _generate_operation_id(self, operation_type: str) -> str:
        """生成操作ID"""
        import uuid
        return f"{operation_type}_{uuid.uuid4().hex[:8]}"
    
    def _start_operation(self, operation_id: str, worker: FileOperationWorker):
        """启动操作"""
        # 连接信号
        worker.operation_progress.connect(self.operation_progress.emit)
        worker.operation_completed.connect(self._on_operation_completed)
        worker.operation_error.connect(self.operation_error.emit)
        
        # 启动线程
        self.active_operations[operation_id] = worker
        worker.start()
        
        self.operation_started.emit(operation_id)
        self.logger.info(f"操作已启动: {operation_id}")
    
    def _on_operation_completed(self, operation_id: str, success: bool, result: str):
        """处理操作完成"""
        # 清理活动操作
        if operation_id in self.active_operations:
            del self.active_operations[operation_id]
        
        # 记录到历史
        operation = FileOperation(
            operation_type=operation_id.split('_')[0],
            file_path=result,
            timestamp=datetime.now(),
            status="completed" if success else "failed"
        )
        self.operation_history.append(operation)
        
        self.operation_completed.emit(operation_id, success, result)
        self.logger.info(f"操作完成: {operation_id} -> {result}")
    
    def _validate_dxf_files(self, file_paths: List[str]) -> List[str]:
        """验证DXF文件"""
        valid_files = []
        
        for file_path in file_paths:
            if Path(file_path).suffix.lower() in self.supported_dxf_extensions:
                if Path(file_path).exists():
                    valid_files.append(file_path)
                else:
                    self.logger.warning(f"文件不存在: {file_path}")
            else:
                self.logger.warning(f"不支持的文件格式: {file_path}")
        
        return valid_files
    
    def _validate_export_config(self, config: ExportConfig):
        """验证导出配置"""
        if not config.output_path:
            raise ValueError("输出路径不能为空")
        
        # 创建输出目录
        output_dir = Path(config.output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)


class DragDropFileWidget(QWidget):
    """支持拖放的文件组件"""
    
    files_dropped = Signal(list)  # file_paths
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        self.drop_label = QLabel("拖放DXF文件到此处\n或点击选择文件")
        self.drop_label.setAlignment(Qt.AlignCenter)
        self.drop_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 10px;
                background-color: #f9f9f9;
                color: #666;
                font-size: 14px;
                padding: 40px;
                margin: 10px;
            }
            QLabel:hover {
                border-color: #007acc;
                background-color: #f0f8ff;
            }
        """)
        
        layout.addWidget(self.drop_label)
        
        # 选择文件按钮
        self.select_btn = QPushButton("选择文件...")
        self.select_btn.clicked.connect(self._select_files)
        layout.addWidget(self.select_btn)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """放下事件"""
        urls = event.mimeData().urls()
        file_paths = [url.toLocalFile() for url in urls]
        
        # 过滤有效文件
        valid_files = [f for f in file_paths if Path(f).suffix.lower() in ['.dxf', '.dwg']]
        
        if valid_files:
            self.files_dropped.emit(valid_files)
        
        event.acceptProposedAction()
    
    def _select_files(self):
        """选择文件"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择DXF文件", "",
            "DXF文件 (*.dxf *.dwg);;所有文件 (*)"
        )
        
        if file_paths:
            self.files_dropped.emit(file_paths)


class FileOperationsWidget(QWidget):
    """文件操作界面组件"""
    
    # 信号定义
    import_requested = Signal(list)  # file_paths
    export_requested = Signal(dict, dict)  # data, config
    report_requested = Signal(dict, dict)  # data, config
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.file_manager = FileOperationsManager(self)
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        # 文件拖放区域
        self.create_drag_drop_section(layout)
        
        # 导出配置区域
        self.create_export_section(layout)
        
        # 操作进度区域
        self.create_progress_section(layout)
        
        layout.addStretch()
    
    def create_drag_drop_section(self, layout):
        """创建拖放区域"""
        drag_group = QGroupBox("文件导入")
        drag_layout = QVBoxLayout(drag_group)
        
        self.drag_drop_widget = DragDropFileWidget()
        drag_layout.addWidget(self.drag_drop_widget)
        
        layout.addWidget(drag_group)
    
    def create_export_section(self, layout):
        """创建导出区域"""
        export_group = QGroupBox("数据导出")
        export_layout = QGridLayout(export_group)
        
        # 导出格式选择
        export_layout.addWidget(QLabel("导出格式:"), 0, 0)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["JSON", "CSV", "Excel", "PDF"])
        export_layout.addWidget(self.format_combo, 0, 1)
        
        # 导出类型选择
        export_layout.addWidget(QLabel("导出类型:"), 1, 0)
        self.type_combo = QComboBox()
        self.type_combo.addItems(["检测结果", "统计摘要", "孔位详情", "批次报告", "完整报告"])
        export_layout.addWidget(self.type_combo, 1, 1)
        
        # 导出选项
        self.include_stats_cb = QCheckBox("包含统计信息")
        self.include_stats_cb.setChecked(True)
        export_layout.addWidget(self.include_stats_cb, 2, 0, 1, 2)
        
        self.include_images_cb = QCheckBox("包含图像")
        export_layout.addWidget(self.include_images_cb, 3, 0, 1, 2)
        
        # 导出按钮
        self.export_btn = QPushButton("导出数据")
        self.export_btn.setFixedHeight(35)
        export_layout.addWidget(self.export_btn, 4, 0, 1, 2)
        
        # 生成报告按钮
        self.report_btn = QPushButton("生成报告")
        self.report_btn.setFixedHeight(35)
        export_layout.addWidget(self.report_btn, 5, 0, 1, 2)
        
        layout.addWidget(export_group)
    
    def create_progress_section(self, layout):
        """创建进度区域"""
        progress_group = QGroupBox("操作进度")
        progress_layout = QVBoxLayout(progress_group)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        progress_layout.addWidget(self.status_label)
        
        # 操作日志
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        progress_layout.addWidget(self.log_text)
        
        layout.addWidget(progress_group)
    
    def setup_connections(self):
        """设置信号连接"""
        # 拖放文件
        self.drag_drop_widget.files_dropped.connect(self._on_files_dropped)
        
        # 按钮点击
        self.export_btn.clicked.connect(self._on_export_clicked)
        self.report_btn.clicked.connect(self._on_report_clicked)
        
        # 文件管理器信号
        self.file_manager.operation_started.connect(self._on_operation_started)
        self.file_manager.operation_progress.connect(self._on_operation_progress)
        self.file_manager.operation_completed.connect(self._on_operation_completed)
        self.file_manager.operation_error.connect(self._on_operation_error)
    
    def _on_files_dropped(self, file_paths: List[str]):
        """处理文件拖放"""
        self.log_text.append(f"接收到 {len(file_paths)} 个文件")
        operation_id = self.file_manager.import_dxf_files(file_paths)
        self.log_text.append(f"开始导入操作: {operation_id}")
    
    def _on_export_clicked(self):
        """处理导出按钮点击"""
        try:
            # 获取导出配置
            export_config = self._get_export_config()
            
            # 准备示例数据
            sample_data = self._get_sample_detection_data()
            
            # 开始导出
            operation_id = self.file_manager.export_detection_data(sample_data, export_config)
            self.log_text.append(f"开始导出操作: {operation_id}")
            
        except Exception as e:
            self.log_text.append(f"导出失败: {e}")
    
    def _on_report_clicked(self):
        """处理报告按钮点击"""
        try:
            # 准备报告配置
            report_config = {
                'output_path': 'detection_report.pdf',
                'template': 'default',
                'include_charts': True
            }
            
            # 准备示例数据
            sample_data = self._get_sample_detection_data()
            
            # 开始生成报告
            operation_id = self.file_manager.generate_report(sample_data, report_config)
            self.log_text.append(f"开始生成报告: {operation_id}")
            
        except Exception as e:
            self.log_text.append(f"生成报告失败: {e}")
    
    def _get_export_config(self) -> ExportConfig:
        """获取导出配置"""
        format_map = {
            "JSON": FileFormat.JSON,
            "CSV": FileFormat.CSV,
            "Excel": FileFormat.XLSX,
            "PDF": FileFormat.PDF
        }
        
        type_map = {
            "检测结果": ExportType.DETECTION_RESULTS,
            "统计摘要": ExportType.STATISTICS_SUMMARY,
            "孔位详情": ExportType.HOLE_DETAILS,
            "批次报告": ExportType.BATCH_REPORT,
            "完整报告": ExportType.FULL_REPORT
        }
        
        file_format = format_map[self.format_combo.currentText()]
        export_type = type_map[self.type_combo.currentText()]
        
        # 选择输出路径
        output_path, _ = QFileDialog.getSaveFileName(
            self, "保存导出文件", 
            f"export.{file_format.value}",
            f"{file_format.value.upper()}文件 (*.{file_format.value})"
        )
        
        if not output_path:
            raise ValueError("未选择输出路径")
        
        return ExportConfig(
            export_type=export_type,
            file_format=file_format,
            output_path=output_path,
            include_statistics=self.include_stats_cb.isChecked(),
            include_images=self.include_images_cb.isChecked()
        )
    
    def _get_sample_detection_data(self) -> Dict[str, Any]:
        """获取示例检测数据"""
        return {
            'holes': [
                {'id': 'H001', 'x': 100, 'y': 200, 'status': 'qualified', 'diameter': 6.2},
                {'id': 'H002', 'x': 150, 'y': 200, 'status': 'unqualified', 'diameter': 5.8},
                {'id': 'H003', 'x': 200, 'y': 200, 'status': 'qualified', 'diameter': 6.1},
            ],
            'statistics': {
                'total_holes': 3,
                'qualified_holes': 2,
                'unqualified_holes': 1,
                'qualification_rate': 66.67
            },
            'metadata': {
                'detection_time': datetime.now().isoformat(),
                'operator': 'System',
                'workpiece_id': 'WP001'
            }
        }
    
    def _on_operation_started(self, operation_id: str):
        """处理操作开始"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText(f"操作进行中: {operation_id}")
    
    def _on_operation_progress(self, operation_id: str, progress: float):
        """处理操作进度"""
        self.progress_bar.setValue(int(progress))
        self.status_label.setText(f"操作进度: {progress:.1f}%")
    
    def _on_operation_completed(self, operation_id: str, success: bool, result: str):
        """处理操作完成"""
        self.progress_bar.setVisible(False)
        
        if success:
            self.status_label.setText("操作完成")
            self.log_text.append(f"✅ 操作成功: {result}")
        else:
            self.status_label.setText("操作失败")
            self.log_text.append(f"❌ 操作失败: {result}")
    
    def _on_operation_error(self, operation_id: str, error_msg: str):
        """处理操作错误"""
        self.progress_bar.setVisible(False)
        self.status_label.setText("操作错误")
        self.log_text.append(f"❌ 错误: {error_msg}")


# 导出的公共接口
__all__ = [
    'FileOperationsManager',
    'FileOperationsWidget',
    'DragDropFileWidget',
    'ExportConfig',
    'FileFormat',
    'ExportType'
]