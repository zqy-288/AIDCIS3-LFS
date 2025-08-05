"""
报告生成页面 - P4模块
基于assets/old/report_output_interface.py实现，但采用现代化的模块化架构
"""

import os
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, 
    QGroupBox, QLabel, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QProgressBar, QTabWidget,
    QCheckBox, QTextEdit, QMessageBox, QFileDialog, QDialog
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont

# 从assets/old目录导入现有的报告相关模块
try:
    from assets.old.report_models import (
        ReportType, ReportFormat, ReportInstance, ReportData
    )
    # 对于ReportConfiguration，我们需要特别处理
    from assets.old.report_models import ReportConfiguration as _OriginalReportConfiguration
    
    # 创建一个包装类来兼容不同的初始化方式
    class ReportConfiguration:
        """ReportConfiguration包装类，兼容dataclass和普通类"""
        def __init__(self, report_type=None, report_format=None, **kwargs):
            # 如果没有提供必需参数，使用默认值
            if report_type is None:
                report_type = ReportType.COMPREHENSIVE
            if report_format is None:
                report_format = ReportFormat.PDF
            
            # 创建原始配置实例
            try:
                # 只传递dataclass支持的参数
                valid_kwargs = {}
                for k, v in kwargs.items():
                    # 检查原始类是否有这个字段
                    if hasattr(_OriginalReportConfiguration, '__dataclass_fields__'):
                        if k in _OriginalReportConfiguration.__dataclass_fields__:
                            valid_kwargs[k] = v
                    else:
                        # 如果不是dataclass，尝试检查属性
                        if hasattr(_OriginalReportConfiguration, k):
                            valid_kwargs[k] = v
                
                self._config = _OriginalReportConfiguration(
                    report_type=report_type,
                    report_format=report_format,
                    **valid_kwargs
                )
                
                # 代理所有属性
                for attr in dir(self._config):
                    if not attr.startswith('_') and not callable(getattr(self._config, attr)):
                        setattr(self, attr, getattr(self._config, attr))
                        
            except Exception as e:
                # 如果包装失败，回退到基本属性设置
                self.report_type = report_type  
                self.report_format = report_format
                # 设置默认值
                self.include_workpiece_info = kwargs.get('include_workpiece_info', True)
                self.include_quality_summary = kwargs.get('include_quality_summary', True)
                self.include_qualified_holes = kwargs.get('include_qualified_holes', True)
                self.include_unqualified_holes = kwargs.get('include_unqualified_holes', True)
                self.include_defect_analysis = kwargs.get('include_defect_analysis', True)
                self.include_manual_reviews = kwargs.get('include_manual_reviews', True)
                self.include_charts = kwargs.get('include_charts', True)
                self.include_endoscope_images = kwargs.get('include_endoscope_images', True)
    
    from assets.old.report_history_manager import ReportHistoryManager
    MODELS_AVAILABLE = True
    print("✅ 使用真实的报告模型 (带兼容包装)")
except ImportError as e:
    print(f"警告: 无法导入报告模型: {e}")
    MODELS_AVAILABLE = False
    
    # 创建模拟的枚举和类
    from enum import Enum
    
    class ReportType(Enum):
        COMPREHENSIVE = "comprehensive"
        WORKPIECE_SUMMARY = "workpiece_summary"
        QUALITY_ANALYSIS = "quality_analysis"
        DEFECT_ANALYSIS = "defect_analysis"
    
    class ReportFormat(Enum):
        PDF = "pdf"
        HTML = "html"
        EXCEL = "excel"
        WORD = "word"
    
    class ReportConfiguration:
        """模拟报告配置类，兼容dataclass版本"""
        def __init__(self, report_type=None, report_format=None, **kwargs):
            # 提供默认值以兼容不同的初始化方式
            self.report_type = report_type if report_type is not None else kwargs.get('report_type', ReportType.COMPREHENSIVE)
            self.report_format = report_format if report_format is not None else kwargs.get('report_format', ReportFormat.PDF)
            
            # 内容包含选项
            self.include_workpiece_info = kwargs.get('include_workpiece_info', True)
            self.include_quality_summary = kwargs.get('include_quality_summary', True)
            self.include_qualified_holes = kwargs.get('include_qualified_holes', True)
            self.include_unqualified_holes = kwargs.get('include_unqualified_holes', True)
            self.include_defect_analysis = kwargs.get('include_defect_analysis', True)
            self.include_manual_reviews = kwargs.get('include_manual_reviews', True)
            self.include_charts = kwargs.get('include_charts', True)
            self.include_3d_models = kwargs.get('include_3d_models', False)
            self.include_endoscope_images = kwargs.get('include_endoscope_images', True)
            
            # 图表配置
            self.chart_dpi = kwargs.get('chart_dpi', 300)
            self.chart_format = kwargs.get('chart_format', 'png')
            
            # 页面配置
            self.page_size = kwargs.get('page_size', 'A4')
            self.page_orientation = kwargs.get('page_orientation', 'portrait')
            
            # 自定义配置
            self.custom_title = kwargs.get('custom_title', None)
            self.custom_logo_path = kwargs.get('custom_logo_path', None)
            self.company_info = kwargs.get('company_info', None)
    
    class ReportHistoryManager:
        def __init__(self):
            self.history_records = []
        
        def load_history(self):
            return []
        
        def get_history_records(self):
            return self.history_records
        
        def add_report_record(self, instance):
            pass
        
        def cleanup_missing_files(self):
            return 0
        
        def format_file_size(self, size):
            return f"{size} bytes"

try:
    from assets.old.report_generator import ReportGenerator
    GENERATOR_AVAILABLE = True
except ImportError as e:
    print(f"警告: 无法导入报告生成器: {e}")
    GENERATOR_AVAILABLE = False
    # 创建一个简化的报告生成器类
    class ReportGenerator:
        def collect_workpiece_data(self, workpiece_id):
            """收集工件数据 - 仅使用真实数据"""
            try:
                # 使用真实的数据收集逻辑
                real_data = self._collect_real_workpiece_data(workpiece_id)
                if real_data:
                    print(f"✅ 使用真实数据: 总孔位 {real_data.quality_summary.total_holes}")
                    return real_data
                else:
                    print("❌ 未找到有效的批次数据")
                    return None
            except Exception as e:
                print(f"❌ 数据收集失败: {e}")
                return None
        
        def _collect_real_workpiece_data(self, workpiece_id):
            """收集真实的工件数据 - 基于最新批次"""
            from datetime import datetime
            from pathlib import Path
            import csv
            import json
            
            # 优先从最新批次读取数据
            batch_data = self._get_latest_batch_data(workpiece_id)
            if batch_data:
                return batch_data
            
            # 回退：从原有孔位目录读取数据
            return self._collect_data_from_hole_directories(workpiece_id)
        
        def _get_latest_batch_data(self, workpiece_id):
            """从最新批次获取数据"""
            try:
                from pathlib import Path
                import json
                from datetime import datetime
                
                # 查找批次目录
                current_dir = Path(__file__).parent
                batches_dir = None
                for _ in range(10):
                    potential_dir = current_dir / "Data" / "Products" / workpiece_id / "InspectionBatches"
                    if potential_dir.exists():
                        batches_dir = potential_dir
                        break
                    current_dir = current_dir.parent
                
                if not batches_dir or not batches_dir.exists():
                    return None
                
                # 获取所有批次目录，按创建时间排序
                batch_dirs = [d for d in batches_dir.iterdir() if d.is_dir()]
                if not batch_dirs:
                    return None
                
                # 根据批次info中的创建时间排序，获取最新批次
                latest_batch = None
                latest_time = None
                
                for batch_dir in batch_dirs:
                    batch_info_file = batch_dir / "batch_info.json"
                    if batch_info_file.exists():
                        try:
                            with open(batch_info_file, 'r', encoding='utf-8') as f:
                                batch_info = json.load(f)
                            
                            created_at_str = batch_info.get('created_at')
                            if created_at_str:
                                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                                if latest_time is None or created_at > latest_time:
                                    latest_time = created_at
                                    latest_batch = batch_dir
                        except:
                            continue
                
                if not latest_batch:
                    return None
                
                # 从最新批次读取孔位数据
                hole_results_dir = latest_batch / "HoleResults"
                if not hole_results_dir.exists():
                    return None
                
                # 读取批次中的孔位结果
                hole_data_list = []
                result_files = list(hole_results_dir.glob("*.json"))
                
                if not result_files:
                    # 如果HoleResults为空，返回None
                    return None
                else:
                    for result_file in result_files:
                        try:
                            with open(result_file, 'r', encoding='utf-8') as f:
                                hole_result = json.load(f)
                            hole_data_list.append(self._convert_batch_result_to_hole_data(hole_result))
                        except:
                            continue
                
                if not hole_data_list:
                    return None
                
                # 计算批次统计
                return self._create_batch_based_report_data(workpiece_id, latest_batch.name, hole_data_list)
                
            except Exception as e:
                print(f"❌ 从批次获取数据失败: {e}")
                return None
        
        
        def _convert_batch_result_to_hole_data(self, batch_result):
            """将批次结果转换为孔位数据格式"""
            # 这里根据实际的批次结果JSON格式进行转换
            # 当前为占位实现，等实际看到结果格式后完善
            return {
                'hole_id': batch_result.get('hole_id', 'Unknown'),
                'batch_id': batch_result.get('batch_id', ''),
                'qualification_rate': batch_result.get('qualification_rate', 0),
                'is_qualified': batch_result.get('is_qualified', False),
                'total_count': batch_result.get('total_count', 0),
                'qualified_count': batch_result.get('qualified_count', 0),
                'measurement_timestamp': batch_result.get('timestamp'),
                'from_batch': True
            }
        
        def _create_batch_based_report_data(self, workpiece_id, batch_id, hole_data_list):
            """基于批次数据创建报告数据"""
            from datetime import datetime
            
            # 计算批次统计
            total_holes = len(hole_data_list)
            qualified_holes = sum(1 for hole in hole_data_list if hole.get('is_qualified', False))
            unqualified_holes = total_holes - qualified_holes
            qualification_rate = (qualified_holes / total_holes * 100) if total_holes > 0 else 0.0
            
            # 创建数据结构
            class BatchWorkpiece:
                def __init__(self):
                    self.workpiece_id = workpiece_id
                    self.name = f"工件-{workpiece_id}"
                    self.type = "核电站蒸汽发生器"
                    self.material = "母材材质：SA508.Gr3. C1.2；堆焊层材质：镍基堆焊层"
                    self.total_holes = total_holes
                    self.batch_id = batch_id
            
            class BatchSummary:
                def __init__(self):
                    self.total_holes = total_holes
                    self.qualified_holes = qualified_holes
                    self.unqualified_holes = unqualified_holes
                    self.qualification_rate = round(qualification_rate, 1)
                    self.holes_with_defects = unqualified_holes
                    self.manual_review_count = 0
                    self.batch_id = batch_id
            
            class BatchData:
                def __init__(self):
                    self.workpiece_info = BatchWorkpiece()
                    self.quality_summary = BatchSummary()
                    self.qualified_holes = [h for h in hole_data_list if h.get('is_qualified', False)]
                    self.unqualified_holes = [h for h in hole_data_list if not h.get('is_qualified', False)]
                    self.defect_data = []
                    self.manual_reviews = []
                    self.generated_at = datetime.now()
                    self.generated_by = "系统"
                    self.batch_id = batch_id
                    self.report_version = "1.0"
            
            return BatchData()
        
        def _collect_data_from_hole_directories(self, workpiece_id):
            """从孔位目录收集数据（回退方案）"""
            from datetime import datetime
            from pathlib import Path
            
            # 查找Data目录
            current_dir = Path(__file__).parent
            data_dir = None
            for _ in range(10):
                potential_data_dir = current_dir / "Data" / "CAP1000"
                if potential_data_dir.exists():
                    data_dir = potential_data_dir
                    break
                current_dir = current_dir.parent
            
            if not data_dir:
                return None
                
            # 收集所有孔位数据
            hole_data_list = []
            for hole_dir in data_dir.iterdir():
                if hole_dir.is_dir() and hole_dir.name.startswith(('AC', 'BC', 'C')):
                    hole_quality_data = self._collect_hole_quality_data(hole_dir.name, hole_dir)
                    if hole_quality_data:
                        hole_data_list.append(hole_quality_data)
            
            if not hole_data_list:
                return None
                
            # 计算统计数据
            total_holes = len(hole_data_list)
            qualified_holes = sum(1 for hole in hole_data_list if hole.get('is_qualified', False))
            unqualified_holes = total_holes - qualified_holes
            qualification_rate = (qualified_holes / total_holes * 100) if total_holes > 0 else 0.0
            
            # 创建数据结构
            class RealWorkpiece:
                def __init__(self):
                    self.workpiece_id = workpiece_id
                    self.name = f"工件-{workpiece_id}"
                    self.type = "核电站蒸汽发生器"
                    self.material = "母材材质：SA508.Gr3. C1.2；堆焊层材质：镍基堆焊层"
                    self.total_holes = total_holes
            
            class RealSummary:
                def __init__(self):
                    self.total_holes = total_holes
                    self.qualified_holes = qualified_holes
                    self.unqualified_holes = unqualified_holes
                    self.qualification_rate = round(qualification_rate, 1)
                    self.holes_with_defects = unqualified_holes
                    self.manual_review_count = 0
            
            class RealData:
                def __init__(self):
                    self.workpiece_info = RealWorkpiece()
                    self.quality_summary = RealSummary()
                    self.qualified_holes = [h for h in hole_data_list if h.get('is_qualified', False)]
                    self.unqualified_holes = [h for h in hole_data_list if not h.get('is_qualified', False)]
                    self.defect_data = []
                    self.manual_reviews = []
                    self.generated_at = datetime.now()
                    self.generated_by = "系统"
                    self.report_version = "1.0"
            
            return RealData()
        
        def _collect_hole_quality_data(self, hole_id, hole_dir):
            """收集单个孔位的质量数据"""
            try:
                import csv
                ccidm_dir = hole_dir / "CCIDM"
                if not ccidm_dir.exists():
                    return None
                    
                # 查找CSV文件
                csv_files = list(ccidm_dir.glob("*.csv"))
                if not csv_files:
                    return None
                    
                latest_csv = max(csv_files, key=lambda f: f.stat().st_mtime)
                measured_diameters = []
                
                # 读取CSV数据
                for encoding in ['utf-8-sig', 'gbk', 'utf-8']:
                    try:
                        with open(latest_csv, 'r', encoding=encoding) as f:
                            reader = csv.reader(f)
                            header = next(reader, None)
                            
                            # 查找直径列（通常是最后一列或包含"直径"的列）
                            diameter_col_index = -1
                            if header:
                                for i, col_name in enumerate(header):
                                    if '直径' in col_name or 'diameter' in col_name.lower():
                                        diameter_col_index = i
                                        break
                            
                            for row in reader:
                                try:
                                    if len(row) > abs(diameter_col_index):
                                        diameter = float(row[diameter_col_index])
                                        if diameter > 0:
                                            measured_diameters.append(diameter)
                                except (ValueError, TypeError, IndexError):
                                    continue
                        break
                    except (UnicodeDecodeError, FileNotFoundError):
                        continue
                
                if not measured_diameters:
                    return None
                
                # 质量标准
                standard_diameter = 17.6  # mm
                upper_tolerance = 0.05    # mm
                lower_tolerance = 0.07    # mm
                
                # 计算质量统计
                qualified_count = sum(
                    1 for d in measured_diameters
                    if standard_diameter - lower_tolerance <= d <= standard_diameter + upper_tolerance
                )
                total_count = len(measured_diameters)
                qualification_rate = (qualified_count / total_count * 100) if total_count > 0 else 0.0
                is_qualified = qualification_rate >= 95.0
                
                return {
                    'hole_id': hole_id,
                    'measured_diameters': measured_diameters,
                    'qualified_count': qualified_count,
                    'total_count': total_count,
                    'qualification_rate': qualification_rate,
                    'is_qualified': is_qualified,
                    'avg_diameter': sum(measured_diameters) / len(measured_diameters),
                    'measurement_timestamp': latest_csv.stat().st_mtime
                }
                
            except Exception as e:
                print(f"❌ 收集孔位 {hole_id} 数据失败: {e}")
                return None
        
        
        def generate_report_instance(self, workpiece_id, config):
            class MockInstance:
                def __init__(self):
                    self.output_path = f"reports/{workpiece_id}_report.txt"
            return MockInstance()

try:
    from assets.old.pdf_report_generator import PDFReportGenerator
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


class ReportGenerationWorker(QThread):
    """报告生成工作线程"""
    
    progress_updated = Signal(int)
    status_updated = Signal(str)
    report_completed = Signal(str)
    error_occurred = Signal(str)
    
    def __init__(self, workpiece_id: str, config: ReportConfiguration):
        super().__init__()
        self.workpiece_id = workpiece_id
        self.config = config
        self.generator = ReportGenerator()
    
    def run(self):
        """执行报告生成"""
        try:
            self.status_updated.emit("正在收集数据...")
            self.progress_updated.emit(10)
            
            # 收集报告数据
            report_data = self.generator.collect_workpiece_data(self.workpiece_id)
            self.progress_updated.emit(50)
            
            self.status_updated.emit("正在生成报告...")
            
            # 生成报告实例
            instance = self.generator.generate_report_instance(self.workpiece_id, self.config)
            self.progress_updated.emit(80)

            # 根据配置选择报告生成器
            if self.config.report_format == ReportFormat.PDF and PDF_AVAILABLE:
                self._generate_pdf_report(report_data, instance.output_path)
            else:
                # 回退到简单文本报告
                self._generate_simple_report(report_data, instance.output_path)
            
            self.progress_updated.emit(100)
            self.status_updated.emit("报告生成完成")
            self.report_completed.emit(instance.output_path)
            
        except Exception as e:
            self.error_occurred.emit(f"报告生成失败: {str(e)}")
    
    def _generate_simple_report(self, report_data: ReportData, output_path: str):
        """生成简单的文本报告"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("管孔检测系统 - 质量检测报告\n")
            f.write("=" * 60 + "\n\n")
            
            # 工件信息
            f.write("1. 工件信息\n")
            f.write("-" * 30 + "\n")
            f.write(f"工件ID: {report_data.workpiece_info.workpiece_id}\n")
            f.write(f"工件名称: {report_data.workpiece_info.name}\n")
            f.write(f"工件类型: {report_data.workpiece_info.type}\n")
            f.write(f"材料: {report_data.workpiece_info.material}\n")
            f.write(f"总孔位数: {report_data.workpiece_info.total_holes}\n\n")
            
            # 质量汇总
            f.write("2. 质量汇总\n")
            f.write("-" * 30 + "\n")
            summary = report_data.quality_summary
            f.write(f"总孔位数: {summary.total_holes}\n")
            f.write(f"合格孔位: {summary.qualified_holes}\n")
            f.write(f"不合格孔位: {summary.unqualified_holes}\n")
            f.write(f"合格率: {summary.qualification_rate:.2f}%\n")
            f.write(f"有缺陷孔位: {summary.holes_with_defects}\n")
            f.write(f"人工复检数: {summary.manual_review_count}\n\n")
            
            f.write(f"报告生成时间: {report_data.generated_at}\n")
            f.write(f"生成者: {report_data.generated_by}\n")

    def _generate_pdf_report(self, report_data: ReportData, output_path: str):
        """生成PDF报告"""
        try:
            pdf_generator = PDFReportGenerator()
            result_path = pdf_generator.generate_report(report_data, self.config, output_path)
            print(f"✅ PDF报告生成成功: {result_path}")
        except Exception as e:
            # 如果PDF生成失败，回退到文本报告
            print(f"❌ PDF生成失败，回退到文本报告: {e}")
            txt_path = output_path.replace('.pdf', '.txt')
            self._generate_simple_report(report_data, txt_path)
            # 抛出异常以便上层处理
            raise Exception(f"PDF生成失败，已生成文本报告: {txt_path}")


class ReportGenerationPage(QWidget):
    """报告生成页面"""
    
    # 状态更新信号，用于与主窗口通信
    status_updated = Signal(str)
    
    def __init__(self, shared_components=None, view_model=None, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.shared_components = shared_components
        self.view_model = view_model
        
        # 核心组件
        self.current_workpiece_id = None
        self.report_generator = ReportGenerator()
        self.history_manager = ReportHistoryManager()
        self.generation_worker = None
        
        # 导入并初始化模板管理器
        try:
            from src.pages.report_generation_p4.generators.report_template_manager import get_template_manager
            self.template_manager = get_template_manager()
            print("✅ 模板管理器初始化成功")
        except Exception as e:
            print(f"❌ 模板管理器初始化失败: {e}")
            self.template_manager = None
        
        # 初始化
        self._init_ui()
        self._init_connections()
        self._load_initial_data()
    
    def _init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # 完全移除边距
        layout.setSpacing(0)  # 移除组件间距
        
        # 简化的页面标题 - 极度紧凑
        title_label = QLabel("📋 报告生成 - 质量检测报告生成与管理")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setObjectName("MainTitle")
        title_label.setStyleSheet("margin: 0px; padding: 5px; font-size: 16px; background: #2b2b2b;")  # 极小边距
        title_label.setMaximumHeight(30)  # 限制标题高度
        layout.addWidget(title_label)
        
        # 主内容区域
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：配置面板
        self._create_config_panel(splitter)
        
        # 右侧：预览和管理面板
        self._create_preview_panel(splitter)
        
        # 设置分割器比例
        splitter.setSizes([400, 600])
        layout.addWidget(splitter)
    
    def _create_config_panel(self, parent):
        """创建配置面板"""
        config_widget = QWidget()
        config_layout = QVBoxLayout(config_widget)
        config_layout.setContentsMargins(5, 5, 5, 5)  # 极小面板边距
        config_layout.setSpacing(5)  # 极小组件间距
        
        # 工件选择
        workpiece_group = QGroupBox("1. 工件选择")
        workpiece_layout = QVBoxLayout(workpiece_group)
        workpiece_layout.setContentsMargins(5, 5, 5, 5)
        workpiece_layout.setSpacing(3)
        
        self.workpiece_combo = QComboBox()
        self.workpiece_combo.currentTextChanged.connect(self._on_workpiece_changed)
        self.workpiece_combo.setToolTip("选择要生成报告的工件")
        workpiece_layout.addWidget(QLabel("选择工件:"))
        workpiece_layout.addWidget(self.workpiece_combo)
        
        config_layout.addWidget(workpiece_group)
        
        # 报告类型配置
        type_group = QGroupBox("2. 报告类型")
        type_layout = QVBoxLayout(type_group)
        type_layout.setContentsMargins(5, 5, 5, 5)
        type_layout.setSpacing(3)
        
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems([
            "综合报告", "工件汇总报告", "质量分析报告", "缺陷分析报告"
        ])
        type_layout.addWidget(self.report_type_combo)
        
        config_layout.addWidget(type_group)
        
        # 报告格式配置
        format_group = QGroupBox("3. 输出格式")
        format_layout = QVBoxLayout(format_group)
        format_layout.setContentsMargins(5, 5, 5, 5)
        format_layout.setSpacing(3)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PDF", "HTML", "Excel", "Word"])
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        format_layout.addWidget(self.format_combo)
        
        # PDF状态提示
        self.pdf_status_label = QLabel()
        self.pdf_status_label.setWordWrap(True)
        self.pdf_status_label.setObjectName("StatusLabel")
        format_layout.addWidget(self.pdf_status_label)
        
        config_layout.addWidget(format_group)
        
        # 报告模板选择
        template_group = QGroupBox("4. 报告模板")
        template_layout = QVBoxLayout(template_group)
        template_layout.setContentsMargins(5, 5, 5, 5)
        template_layout.setSpacing(3)
        
        self.template_combo = QComboBox()
        self.template_combo.currentTextChanged.connect(self._on_template_changed)
        self.template_combo.setToolTip("选择报告模板类型")
        template_layout.addWidget(QLabel("选择模板:"))
        template_layout.addWidget(self.template_combo)
        
        # 模板描述
        self.template_desc_label = QLabel("请选择报告模板...")
        self.template_desc_label.setWordWrap(True)
        self.template_desc_label.setObjectName("TemplateDescLabel")
        self.template_desc_label.setStyleSheet("color: #666; font-size: 11px; margin: 5px;")
        template_layout.addWidget(self.template_desc_label)
        
        config_layout.addWidget(template_group)
        
        # 生成按钮
        button_layout = QHBoxLayout()
        
        self.preview_btn = QPushButton("预览报告")
        self.preview_btn.clicked.connect(self._preview_report)
        
        self.generate_btn = QPushButton("生成报告")
        self.generate_btn.clicked.connect(self._generate_report)
        
        button_layout.addWidget(self.preview_btn)
        button_layout.addWidget(self.generate_btn)
        
        config_layout.addLayout(button_layout)
        config_layout.addStretch()
        
        parent.addWidget(config_widget)
    
    def _create_preview_panel(self, parent):
        """创建预览面板"""
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        
        # 标签页
        tab_widget = QTabWidget()
        
        # 数据预览标签页
        self._create_data_preview_tab(tab_widget)
        
        # 报告管理标签页
        self._create_report_management_tab(tab_widget)
        
        preview_layout.addWidget(tab_widget)
        parent.addWidget(preview_widget)
    
    def _create_data_preview_tab(self, tab_widget):
        """创建数据预览标签页"""
        preview_tab = QWidget()
        preview_layout = QVBoxLayout(preview_tab)
        
        # 数据状态指示器
        self.data_status_label = QLabel("📊 数据状态: 未加载")
        self.data_status_label.setObjectName("DataStatusLabel")
        preview_layout.addWidget(self.data_status_label)
        
        # 数据汇总显示
        summary_group = QGroupBox("数据汇总")
        summary_layout = QVBoxLayout(summary_group)
        
        # 关键指标显示
        self.total_holes_label = QLabel("总孔位数: --")
        self.qualified_holes_label = QLabel("合格孔位: --")
        self.unqualified_holes_label = QLabel("不合格孔位: --")
        self.qualification_rate_label = QLabel("合格率: --%")
        
        summary_layout.addWidget(self.total_holes_label)
        summary_layout.addWidget(self.qualified_holes_label)
        summary_layout.addWidget(self.unqualified_holes_label)
        summary_layout.addWidget(self.qualification_rate_label)
        
        preview_layout.addWidget(summary_group)
        
        # 孔位数据表格
        table_group = QGroupBox("孔位数据")
        table_layout = QVBoxLayout(table_group)
        
        self.hole_data_table = QTableWidget()
        self.hole_data_table.setColumnCount(6)
        self.hole_data_table.setHorizontalHeaderLabels([
            "孔位ID", "位置(X,Y)", "合格率", "测量次数", "状态", "最后测量时间"
        ])
        
        table_layout.addWidget(self.hole_data_table)
        preview_layout.addWidget(table_group)
        
        tab_widget.addTab(preview_tab, "数据预览")
    
    def _create_report_management_tab(self, tab_widget):
        """创建报告管理标签页"""
        management_tab = QWidget()
        management_layout = QVBoxLayout(management_tab)
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        
        self.refresh_history_btn = QPushButton("刷新")
        self.refresh_history_btn.clicked.connect(self._refresh_history)
        toolbar_layout.addWidget(self.refresh_history_btn)
        
        self.cleanup_history_btn = QPushButton("清理失效记录")
        self.cleanup_history_btn.clicked.connect(self._cleanup_history)
        toolbar_layout.addWidget(self.cleanup_history_btn)
        
        toolbar_layout.addStretch()
        management_layout.addLayout(toolbar_layout)
        
        # 报告历史表格
        history_group = QGroupBox("报告历史")
        history_layout = QVBoxLayout(history_group)
        
        self.report_history_table = QTableWidget()
        self.report_history_table.setColumnCount(6)
        self.report_history_table.setHorizontalHeaderLabels([
            "序号", "生成时间", "工件ID", "状态", "文件大小", "格式"
        ])
        
        history_layout.addWidget(self.report_history_table)
        management_layout.addWidget(history_group)
        
        tab_widget.addTab(management_tab, "报告管理")
    
    def _init_connections(self):
        """初始化信号连接"""
        # 检查PDF依赖状态
        self._check_pdf_dependencies()
        
        # 设置默认格式状态
        self._on_format_changed(self.format_combo.currentText())
        
        # 加载历史记录
        self._refresh_history()
    
    def _load_initial_data(self):
        """加载初始数据"""
        # 加载工件列表
        self.workpiece_combo.addItem("CAP1000")
        
        # 加载报告模板
        self._load_templates()
        
        # 设置默认选择
        if self.workpiece_combo.count() > 0:
            self.workpiece_combo.setCurrentIndex(0)
            self._on_workpiece_changed("CAP1000")
    
    def _load_templates(self):
        """加载报告模板"""
        if not self.template_manager:
            self.template_combo.addItem("模板系统未初始化")
            return
        
        try:
            # 获取可用模板
            template_names = self.template_manager.get_template_names()
            
            self.template_combo.clear()
            if template_names:
                for template_id, template_name in template_names:
                    self.template_combo.addItem(template_name, template_id)
                
                # 默认选择第一个模板
                if self.template_combo.count() > 0:
                    self.template_combo.setCurrentIndex(0)
                    self._on_template_changed(self.template_combo.currentText())
            else:
                self.template_combo.addItem("无可用模板")
                
        except Exception as e:
            print(f"❌ 加载模板失败: {e}")
            self.template_combo.addItem("模板加载失败")
    
    def _on_template_changed(self, template_name: str):
        """模板选择改变"""
        if not self.template_manager or not template_name:
            return
        
        try:
            # 获取选中的模板ID
            template_id = self.template_combo.currentData()
            if not template_id:
                return
            
            # 获取模板对象
            template = self.template_manager.get_template(template_id)
            if template:
                # 更新模板描述
                self.template_desc_label.setText(template.description)
                
                # 存储当前选中的模板
                self.current_template = template
                print(f"✅ 选择模板: {template.template_name}")
            else:
                self.template_desc_label.setText("无法获取模板信息")
                self.current_template = None
                
        except Exception as e:
            print(f"❌ 处理模板选择失败: {e}")
            self.template_desc_label.setText(f"模板选择错误: {str(e)}")
            self.current_template = None
    
    def _on_workpiece_changed(self, workpiece_id: str):
        """工件选择改变"""
        if workpiece_id:
            self.current_workpiece_id = workpiece_id
            self._load_workpiece_data(workpiece_id)
    
    def _load_workpiece_data(self, workpiece_id: str):
        """加载工件数据预览"""
        try:
            # 更新状态
            self.data_status_label.setText("📊 数据状态: 正在加载...")
            
            # 收集工件数据
            report_data = self.report_generator.collect_workpiece_data(workpiece_id)
            
            # 更新汇总信息
            self._update_summary_display(report_data)
            
            # 更新孔位数据表格
            self._update_hole_data_table(report_data)
            
            # 更新状态
            total_holes = report_data.quality_summary.total_holes
            if total_holes > 0:
                self.data_status_label.setText(f"✅ 数据状态: 已加载 ({total_holes} 个孔位)")
            else:
                self.data_status_label.setText("⚠️ 数据状态: 无有效数据")
            
        except Exception as e:
            self.data_status_label.setText("❌ 数据状态: 加载失败")
            QMessageBox.warning(self, "错误", f"加载工件数据失败: {str(e)}")
    
    def _update_summary_display(self, report_data: ReportData):
        """更新汇总显示"""
        summary = report_data.quality_summary
        
        self.total_holes_label.setText(f"总孔位数: {summary.total_holes}")
        self.qualified_holes_label.setText(f"合格孔位: {summary.qualified_holes}")
        self.unqualified_holes_label.setText(f"不合格孔位: {summary.unqualified_holes}")
        self.qualification_rate_label.setText(f"合格率: {summary.qualification_rate:.1f}%")
    
    def _update_hole_data_table(self, report_data):
        """更新孔位数据表格"""
        all_holes = report_data.qualified_holes + report_data.unqualified_holes
        
        self.hole_data_table.setRowCount(len(all_holes))
        
        for row, hole in enumerate(all_holes):
            # hole 可能是对象或字典，需要兼容处理
            if isinstance(hole, dict):
                # 字典格式（我们的新格式）
                hole_id = hole.get('hole_id', 'Unknown')
                position_text = f"(估算位置)"  # 可以后续添加坐标估算逻辑
                rate_text = f"{hole.get('qualification_rate', 0):.1f}%"
                count_text = f"{hole.get('qualified_count', 0)}/{hole.get('total_count', 0)}"
                status_text = "合格" if hole.get('is_qualified', False) else "不合格"
                
                # 处理时间戳
                timestamp = hole.get('measurement_timestamp')
                if timestamp:
                    try:
                        from datetime import datetime
                        if isinstance(timestamp, (int, float)):
                            time_text = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
                        else:
                            time_text = str(timestamp)
                    except:
                        time_text = "未知"
                else:
                    time_text = "未知"
            else:
                # 对象格式（原有格式）
                hole_id = getattr(hole, 'hole_id', 'Unknown')
                position_x = getattr(hole, 'position_x', 0)
                position_y = getattr(hole, 'position_y', 0)
                position_text = f"({position_x:.1f}, {position_y:.1f})"
                rate_text = f"{getattr(hole, 'qualification_rate', 0):.1f}%"
                count_text = f"{getattr(hole, 'qualified_count', 0)}/{getattr(hole, 'total_count', 0)}"
                status_text = "合格" if getattr(hole, 'is_qualified', False) else "不合格"
                
                measurement_timestamp = getattr(hole, 'measurement_timestamp', None)
                if measurement_timestamp and hasattr(measurement_timestamp, 'strftime'):
                    time_text = measurement_timestamp.strftime("%Y-%m-%d %H:%M")
                else:
                    time_text = "未知"
            
            # 设置表格项
            self.hole_data_table.setItem(row, 0, QTableWidgetItem(hole_id))
            self.hole_data_table.setItem(row, 1, QTableWidgetItem(position_text))
            self.hole_data_table.setItem(row, 2, QTableWidgetItem(rate_text))
            self.hole_data_table.setItem(row, 3, QTableWidgetItem(count_text))
            self.hole_data_table.setItem(row, 4, QTableWidgetItem(status_text))
            self.hole_data_table.setItem(row, 5, QTableWidgetItem(time_text))
    
    def _preview_report(self):
        """预览报告"""
        if not self.current_workpiece_id:
            QMessageBox.warning(self, "警告", "请先选择工件")
            return
        
        if not hasattr(self, 'current_template') or not self.current_template:
            QMessageBox.warning(self, "警告", "请先选择报告模板")
            return
        
        try:
            # 收集报告数据
            report_data = self.report_generator.collect_workpiece_data(self.current_workpiece_id)
            
            # 使用新的预览窗口
            try:
                from src.pages.report_generation_p4.generators.report_preview_window import ReportPreviewWindow
                
                # 获取当前选择的输出格式
                output_format = self.format_combo.currentText()
                
                preview_window = ReportPreviewWindow(
                    report_data, 
                    self.current_template, 
                    self._create_report_configuration(),
                    output_format,  # 传递输出格式
                    self
                )
                if preview_window.exec() == QDialog.Accepted:
                    # 用户点击了"生成报告"按钮，触发实际生成
                    self._generate_report()
            except ImportError:
                # 回退到原始预览对话框
                preview_dialog = ReportPreviewDialog(report_data, self._create_report_configuration(), self)
                preview_dialog.exec()
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"生成预览失败: {str(e)}")
    
    def _generate_report(self):
        """生成报告"""
        if not self.current_workpiece_id:
            QMessageBox.warning(self, "警告", "请先选择工件")
            return
        
        if not hasattr(self, 'current_template') or not self.current_template:
            QMessageBox.warning(self, "警告", "请先选择报告模板")
            return
        
        # 创建报告配置
        config = self._create_report_configuration()
        
        # 创建报告实例并保存
        self.current_report_instance = self.report_generator.generate_report_instance(
            self.current_workpiece_id, config
        )
        
        # 启动报告生成工作线程
        self.generation_worker = ReportGenerationWorker(self.current_workpiece_id, config)
        self.generation_worker.status_updated.connect(self.status_updated.emit)
        self.generation_worker.report_completed.connect(self._on_report_completed)
        self.generation_worker.error_occurred.connect(self._on_generation_error)
        
        # 发射状态信号
        self.status_updated.emit("正在生成报告...")
        self.generate_btn.setEnabled(False)
        
        self.generation_worker.start()
    
    def _create_report_configuration(self) -> ReportConfiguration:
        """创建报告配置 - 基于选中的模板"""
        # 如果有选中的模板，使用模板配置
        if hasattr(self, 'current_template') and self.current_template:
            # 从模板生成配置
            template_config = self.current_template.to_report_configuration()
            
            # 覆盖输出格式（用户仍可选择格式）
            format_mapping = {
                "PDF": ReportFormat.PDF,
                "HTML": ReportFormat.HTML,
                "Excel": ReportFormat.EXCEL,
                "Word": ReportFormat.WORD
            }
            
            # 更新格式
            if hasattr(template_config, 'report_format'):
                template_config.report_format = format_mapping.get(self.format_combo.currentText(), template_config.report_format)
            
            print(f"✅ 使用模板配置: {self.current_template.template_name}")
            return template_config
        
        # 回退：如果没有模板，使用默认配置
        print("⚠️ 未选择模板，使用默认配置")
        format_mapping = {
            "PDF": ReportFormat.PDF,
            "HTML": ReportFormat.HTML,
            "Excel": ReportFormat.EXCEL,
            "Word": ReportFormat.WORD
        }
        
        return ReportConfiguration(
            report_type=ReportType.COMPREHENSIVE,
            report_format=format_mapping.get(self.format_combo.currentText(), ReportFormat.PDF),
            include_workpiece_info=True,
            include_quality_summary=True,
            include_qualified_holes=True,
            include_unqualified_holes=True,
            include_defect_analysis=True,
            include_manual_reviews=True,
            include_charts=True,
            include_endoscope_images=True
        )
    
    def _on_report_completed(self, output_path: str):
        """报告生成完成"""
        self.generate_btn.setEnabled(True)
        
        # 发射状态信号
        file_name = os.path.basename(output_path)
        self.status_updated.emit(f"报告生成成功: {file_name}")
        
        # 添加到历史记录
        if hasattr(self, 'current_report_instance'):
            self.current_report_instance.output_path = output_path
            self.history_manager.add_report_record(self.current_report_instance)
            self._refresh_history()
        
        reply = QMessageBox.question(
            self,
            "成功",
            f"报告生成完成!\n\n文件路径: {output_path}\n\n是否打开文件所在目录?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self._open_file_directory(output_path)
    
    def _on_generation_error(self, error_message: str):
        """报告生成错误"""
        self.generate_btn.setEnabled(True)
        
        # 发射状态信号
        self.status_updated.emit(f"错误: {error_message}")
        
        QMessageBox.critical(self, "错误", error_message)
    
    def _open_file_directory(self, file_path: str):
        """打开文件所在目录"""
        import platform
        import subprocess
        
        directory = os.path.dirname(file_path)
        try:
            if platform.system() == 'Windows':
                os.startfile(directory)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', directory])
            else:  # Linux
                subprocess.run(['xdg-open', directory])
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法打开目录: {str(e)}")
    
    def _check_pdf_dependencies(self):
        """检查PDF依赖"""
        if PDF_AVAILABLE:
            self.pdf_status_label.setText("✅ PDF支持已启用")
        else:
            self.pdf_status_label.setText("⚠️ PDF支持未安装，将使用文本格式")
    
    def _on_format_changed(self, format_text: str):
        """格式选择改变"""
        if format_text == "PDF" and not PDF_AVAILABLE:
            self.pdf_status_label.setText("⚠️ 选择PDF格式但未安装支持库，将回退到文本格式")
        elif format_text == "PDF" and PDF_AVAILABLE:
            self.pdf_status_label.setText("✅ PDF格式已就绪")
        else:
            self.pdf_status_label.setText(f"📄 将生成{format_text}格式报告")
    
    def _refresh_history(self):
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
                
        except Exception as e:
            QMessageBox.warning(self, "错误", f"刷新历史记录失败: {str(e)}")
    
    def _cleanup_history(self):
        """清理失效的历史记录"""
        removed_count = self.history_manager.cleanup_missing_files()
        if removed_count > 0:
            self._refresh_history()
            QMessageBox.information(self, "清理完成", f"已清理 {removed_count} 条失效记录")
        else:
            QMessageBox.information(self, "清理完成", "没有发现失效记录")
    
    def load_data_for_workpiece(self, workpiece_id: str):
        """为指定工件加载数据（从其他界面导航时调用）"""
        try:
            # 在工件下拉框中选择对应的工件
            index = self.workpiece_combo.findText(workpiece_id)
            if index >= 0:
                self.workpiece_combo.setCurrentIndex(index)
            else:
                # 如果工件不在列表中，添加它
                self.workpiece_combo.addItem(workpiece_id)
                self.workpiece_combo.setCurrentText(workpiece_id)
            
            # 加载数据
            if self.current_workpiece_id:
                self._load_workpiece_data(self.current_workpiece_id)
                
        except Exception as e:
            self.status_updated.emit(f"❌ 加载工件数据失败: {str(e)}")


class ReportPreviewDialog(QMessageBox):
    """简化的报告预览对话框"""
    
    def __init__(self, report_data: ReportData, config: ReportConfiguration, parent=None):
        super().__init__(parent)
        self.setWindowTitle("报告预览")
        self.setIcon(QMessageBox.Information)
        
        # 生成预览文本
        preview_text = self._generate_preview_text(report_data, config)
        self.setText("报告内容预览")
        self.setDetailedText(preview_text)
        
        self.setStandardButtons(QMessageBox.Ok)
    
    def _generate_preview_text(self, report_data: ReportData, config: ReportConfiguration) -> str:
        """生成预览文本"""
        lines = []
        
        lines.append("管孔检测系统 - 质量检测报告")
        lines.append("=" * 40)
        lines.append("")
        
        # 工件信息
        if config.include_workpiece_info:
            lines.append("1. 工件信息")
            workpiece = report_data.workpiece_info
            lines.append(f"工件ID: {workpiece.workpiece_id}")
            lines.append(f"工件名称: {workpiece.name}")
            lines.append(f"工件类型: {workpiece.type}")
            lines.append(f"总孔位数: {workpiece.total_holes}")
            lines.append("")
        
        # 质量汇总
        if config.include_quality_summary:
            lines.append("2. 质量汇总")
            summary = report_data.quality_summary
            lines.append(f"总孔位数: {summary.total_holes}")
            lines.append(f"合格孔位: {summary.qualified_holes}")
            lines.append(f"不合格孔位: {summary.unqualified_holes}")
            lines.append(f"合格率: {summary.qualification_rate:.2f}%")
            lines.append("")
        
        lines.append(f"报告生成时间: {report_data.generated_at}")
        
        return "\n".join(lines)