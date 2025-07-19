"""
DXF视图控制器
专门处理DXF文件解析和显示的控制器
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from PySide6.QtCore import QObject, Signal, QTimer, QThread, pyqtSignal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QProgressBar, QLabel, QPushButton, QFileDialog, QMessageBox

# 导入现有组件
from src.core_business.dxf_parser import DXFParser
from src.core_business.models.hole_data import HoleCollection, HoleData
from src.core.dependency_injection import injectable, ServiceLifetime

# 事件类型常量
class EventTypes:
    DXF_FILE_LOADED = "dxf_file_loaded"
    PARSING_PROGRESS = "parsing_progress"
    PARSING_ERROR = "parsing_error"


class DXFParsingWorker(QThread):
    """DXF解析工作线程 - 避免阻塞UI"""
    
    progress_updated = Signal(int, str)  # 进度值，状态信息
    parsing_completed = Signal(str, object)  # 文件路径，孔位集合
    parsing_failed = Signal(str, str)  # 文件路径，错误信息
    
    def __init__(self, file_path: str, dxf_parser: DXFParser):
        super().__init__()
        self.file_path = file_path
        self.dxf_parser = dxf_parser
        self.logger = logging.getLogger(__name__)
    
    def run(self):
        """执行DXF解析任务"""
        try:
            self.progress_updated.emit(10, "开始解析DXF文件...")
            
            # 验证文件存在
            if not os.path.exists(self.file_path):
                self.parsing_failed.emit(self.file_path, "文件不存在")
                return
            
            self.progress_updated.emit(30, "读取DXF文件结构...")
            
            # 执行解析
            hole_collection = self.dxf_parser.parse_file(self.file_path)
            
            self.progress_updated.emit(80, "处理孔位数据...")
            
            # 验证解析结果
            if not hole_collection or len(hole_collection) == 0:
                self.parsing_failed.emit(self.file_path, "未找到有效的孔位数据")
                return
            
            self.progress_updated.emit(100, f"解析完成，共找到 {len(hole_collection)} 个孔位")
            self.parsing_completed.emit(self.file_path, hole_collection)
            
        except Exception as e:
            self.logger.error(f"DXF解析失败: {e}")
            self.parsing_failed.emit(self.file_path, str(e))


@injectable(ServiceLifetime.TRANSIENT)
class DXFViewController(QObject):
    """DXF视图控制器 - 专门处理DXF文件解析和显示"""
    
    # 局部信号 - 不依赖MainWindow
    dxf_loaded = Signal(str, object)  # 文件路径，孔位集合
    parsing_progress = Signal(int, str)  # 进度值，状态信息
    parsing_error = Signal(str, str)  # 文件路径，错误信息
    
    # 状态信号
    loading_started = Signal()
    loading_finished = Signal()
    
    def __init__(self, parent: QWidget, model, event_bus):
        super().__init__()
        self.parent = parent
        self.model = model
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)
        
        # 初始化DXF解析器
        try:
            self.dxf_parser = DXFParser()
        except Exception as e:
            self.logger.error(f"DXF解析器初始化失败: {e}")
            self.dxf_parser = None
        
        # 工作线程
        self.parsing_worker = None
        
        # 当前状态
        self.current_file_path = None
        self.is_loading = False
        
        # 连接模型信号
        if hasattr(self.model, 'workpiece_loaded'):
            self.model.workpiece_loaded.connect(self.on_workpiece_loaded)
        
        # 设置UI
        self.setup_ui()
        
        # 连接信号
        self.setup_signal_connections()
        
        self.logger.info("DXF视图控制器初始化完成")
    
    def setup_ui(self):
        """设置DXF相关UI组件"""
        try:
            # 创建主容器
            self.ui_container = QWidget()
            layout = QVBoxLayout(self.ui_container)
            
            # 文件加载工具栏
            toolbar_layout = QHBoxLayout()
            
            # 加载按钮
            self.load_button = QPushButton("加载DXF文件")
            self.load_button.clicked.connect(self.show_file_dialog)
            toolbar_layout.addWidget(self.load_button)
            
            # 文件路径显示
            self.file_path_label = QLabel("未选择文件")
            self.file_path_label.setStyleSheet("color: #666; font-size: 12px;")
            toolbar_layout.addWidget(self.file_path_label)
            
            toolbar_layout.addStretch()
            layout.addLayout(toolbar_layout)
            
            # 进度显示区域
            progress_layout = QHBoxLayout()
            
            # 进度条
            self.progress_bar = QProgressBar()
            self.progress_bar.setVisible(False)
            progress_layout.addWidget(self.progress_bar)
            
            # 状态标签
            self.status_label = QLabel("就绪")
            self.status_label.setStyleSheet("color: #007ACC; font-weight: bold;")
            progress_layout.addWidget(self.status_label)
            
            layout.addLayout(progress_layout)
            
            # 文件信息显示
            self.info_label = QLabel("文件信息将在这里显示")
            self.info_label.setStyleSheet("color: #888; font-size: 11px;")
            layout.addWidget(self.info_label)
            
            # 应用主题
            self.apply_theme()
            
        except Exception as e:
            self.logger.error(f"DXF UI设置失败: {e}")
    
    def setup_signal_connections(self):
        """设置信号连接"""
        # 连接内部信号
        self.dxf_loaded.connect(self.on_dxf_loaded_internal)
        self.parsing_progress.connect(self.on_parsing_progress_internal)
        self.parsing_error.connect(self.on_parsing_error_internal)
    
    def show_file_dialog(self):
        """显示文件选择对话框"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self.parent,
                "选择DXF文件",
                "",
                "DXF files (*.dxf);;All files (*.*)"
            )
            
            if file_path:
                self.load_dxf_file(file_path)
                
        except Exception as e:
            self.logger.error(f"文件对话框显示失败: {e}")
            self.show_error_message("文件选择失败", str(e))
    
    def load_dxf_file(self, file_path: str):
        """加载DXF文件"""
        try:
            # 验证输入
            if not file_path or not isinstance(file_path, str):
                raise ValueError("无效的文件路径")
            
            # 验证文件存在
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            # 验证文件扩展名
            if not file_path.lower().endswith('.dxf'):
                raise ValueError("文件格式不支持，请选择DXF文件")
            
            # 检查是否正在加载
            if self.is_loading:
                self.logger.warning("正在加载其他文件，请稍后再试")
                return
            
            # 检查解析器
            if not self.dxf_parser:
                raise RuntimeError("DXF解析器未初始化")
            
            # 更新状态
            self.is_loading = True
            self.current_file_path = file_path
            self.loading_started.emit()
            
            # 更新UI
            self.update_ui_for_loading_state(True)
            
            # 创建并启动解析工作线程
            self.parsing_worker = DXFParsingWorker(file_path, self.dxf_parser)
            
            # 连接工作线程信号
            self.parsing_worker.progress_updated.connect(self.on_worker_progress)
            self.parsing_worker.parsing_completed.connect(self.on_worker_completed)
            self.parsing_worker.parsing_failed.connect(self.on_worker_failed)
            self.parsing_worker.finished.connect(self.on_worker_finished)
            
            # 启动解析
            self.parsing_worker.start()
            
            self.logger.info(f"开始加载DXF文件: {file_path}")
            
        except Exception as e:
            self.logger.error(f"DXF文件加载失败: {e}")
            self.is_loading = False
            self.update_ui_for_loading_state(False)
            self.parsing_error.emit(file_path, str(e))
    
    def on_worker_progress(self, progress: int, message: str):
        """处理工作线程进度更新"""
        self.parsing_progress.emit(progress, message)
    
    def on_worker_completed(self, file_path: str, hole_collection: HoleCollection):
        """处理工作线程完成"""
        try:
            # 更新模型
            if hasattr(self.model, 'hole_collection'):
                self.model.hole_collection = hole_collection
            
            if hasattr(self.model, 'current_workpiece'):
                self.model.current_workpiece = self.extract_workpiece_id(file_path)
            
            # 发布事件
            self.event_bus.publish(EventTypes.DXF_FILE_LOADED, {
                'file_path': file_path,
                'hole_collection': hole_collection,
                'hole_count': len(hole_collection)
            })
            
            # 发出局部信号
            self.dxf_loaded.emit(file_path, hole_collection)
            
            self.logger.info(f"DXF文件加载成功: {file_path}, 孔位数量: {len(hole_collection)}")
            
        except Exception as e:
            self.logger.error(f"处理解析结果失败: {e}")
            self.parsing_error.emit(file_path, str(e))
    
    def on_worker_failed(self, file_path: str, error_message: str):
        """处理工作线程失败"""
        self.parsing_error.emit(file_path, error_message)
    
    def on_worker_finished(self):
        """处理工作线程结束"""
        self.is_loading = False
        self.update_ui_for_loading_state(False)
        self.loading_finished.emit()
        
        # 清理工作线程
        if self.parsing_worker:
            self.parsing_worker.deleteLater()
            self.parsing_worker = None
    
    def update_ui_for_loading_state(self, loading: bool):
        """更新UI加载状态"""
        try:
            if loading:
                self.progress_bar.setVisible(True)
                self.progress_bar.setValue(0)
                self.load_button.setEnabled(False)
                self.status_label.setText("加载中...")
                self.status_label.setStyleSheet("color: #E67E22; font-weight: bold;")
            else:
                self.progress_bar.setVisible(False)
                self.load_button.setEnabled(True)
                self.status_label.setText("就绪")
                self.status_label.setStyleSheet("color: #007ACC; font-weight: bold;")
                
        except Exception as e:
            self.logger.error(f"UI状态更新失败: {e}")
    
    def on_dxf_loaded_internal(self, file_path: str, hole_collection: HoleCollection):
        """内部DXF加载完成处理"""
        try:
            # 更新文件路径显示
            filename = os.path.basename(file_path)
            self.file_path_label.setText(f"当前文件: {filename}")
            self.file_path_label.setStyleSheet("color: #2ECC71; font-weight: bold;")
            
            # 更新文件信息
            file_size = os.path.getsize(file_path)
            file_size_mb = file_size / (1024 * 1024)
            hole_count = len(hole_collection)
            
            info_text = f"文件大小: {file_size_mb:.2f}MB | 孔位数量: {hole_count}"
            self.info_label.setText(info_text)
            self.info_label.setStyleSheet("color: #007ACC; font-weight: bold;")
            
        except Exception as e:
            self.logger.error(f"内部DXF加载处理失败: {e}")
    
    def on_parsing_progress_internal(self, progress: int, message: str):
        """内部解析进度处理"""
        try:
            self.progress_bar.setValue(progress)
            self.status_label.setText(message)
            
        except Exception as e:
            self.logger.error(f"解析进度处理失败: {e}")
    
    def on_parsing_error_internal(self, file_path: str, error_message: str):
        """内部解析错误处理"""
        try:
            self.status_label.setText("解析失败")
            self.status_label.setStyleSheet("color: #E74C3C; font-weight: bold;")
            
            # 显示错误信息
            self.show_error_message("DXF解析失败", error_message)
            
        except Exception as e:
            self.logger.error(f"解析错误处理失败: {e}")
    
    def on_workpiece_loaded(self, workpiece_id: str):
        """处理工件加载事件"""
        try:
            self.logger.info(f"工件已加载: {workpiece_id}")
            
        except Exception as e:
            self.logger.error(f"工件加载处理失败: {e}")
    
    def extract_workpiece_id(self, file_path: str) -> str:
        """从文件路径提取工件ID"""
        try:
            # 从文件名提取工件ID
            filename = os.path.basename(file_path)
            workpiece_id = os.path.splitext(filename)[0]
            
            # 简单的ID清理
            workpiece_id = workpiece_id.replace(" ", "_")
            workpiece_id = workpiece_id.replace("-", "_")
            
            return workpiece_id
            
        except Exception as e:
            self.logger.error(f"工件ID提取失败: {e}")
            return "unknown_workpiece"
    
    def show_error_message(self, title: str, message: str):
        """显示错误消息"""
        try:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            msg_box.exec()
            
        except Exception as e:
            self.logger.error(f"错误消息显示失败: {e}")
    
    def apply_theme(self):
        """应用主题样式"""
        try:
            # 应用深色主题
            self.ui_container.setStyleSheet("""
                QWidget {
                    background-color: #2C313C;
                    color: #D3D8E0;
                }
                QPushButton {
                    background-color: #007ACC;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #0099FF;
                }
                QPushButton:pressed {
                    background-color: #005C99;
                }
                QPushButton:disabled {
                    background-color: #555555;
                    color: #AAAAAA;
                }
                QProgressBar {
                    border: 1px solid #404552;
                    border-radius: 4px;
                    background-color: #313642;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #007ACC;
                    border-radius: 3px;
                }
            """)
            
        except Exception as e:
            self.logger.error(f"主题应用失败: {e}")
    
    def get_current_file_path(self) -> Optional[str]:
        """获取当前文件路径"""
        return self.current_file_path
    
    def is_file_loaded(self) -> bool:
        """检查是否有文件已加载"""
        return self.current_file_path is not None
    
    def get_ui_container(self) -> QWidget:
        """获取UI容器"""
        return self.ui_container
    
    def cleanup(self):
        """清理资源"""
        try:
            # 停止工作线程
            if self.parsing_worker and self.parsing_worker.isRunning():
                self.parsing_worker.quit()
                self.parsing_worker.wait(3000)  # 等待3秒
                
            # 清理引用
            self.parsing_worker = None
            self.dxf_parser = None
            
            self.logger.info("DXF视图控制器资源清理完成")
            
        except Exception as e:
            self.logger.error(f"资源清理失败: {e}")