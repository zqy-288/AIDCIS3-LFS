"""DXF文件管理器"""
import logging
from pathlib import Path
from typing import Optional
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox, QFileDialog

from aidcis2.models.hole_data import HoleCollection
from aidcis2.dxf_parser import DXFParser


class DXFManager(QObject):
    """
    DXF文件管理器
    负责DXF文件的加载、解析和验证
    """
    
    # 信号定义
    dxf_loaded = Signal(str, object)  # 文件路径, HoleCollection
    log_message = Signal(str)
    status_message = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # DXF解析器
        self.dxf_parser = DXFParser()
        
        # 当前加载的数据
        self.current_file_path: Optional[str] = None
        self.current_hole_collection: Optional[HoleCollection] = None
        
    def load_dxf_file(self, file_path: str = None) -> bool:
        """加载DXF文件"""
        # 如果没有提供文件路径，打开文件选择对话框
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(
                None, "选择DXF文件", "", "DXF文件 (*.dxf);;所有文件 (*)"
            )
            if not file_path:
                return False
                
        # 验证文件存在
        if not Path(file_path).exists():
            self.log_message.emit(f"❌ 文件不存在: {file_path}")
            QMessageBox.warning(None, "警告", f"文件不存在: {file_path}")
            return False
            
        try:
            self.status_message.emit("正在加载DXF文件...")
            self.log_message.emit(f"📂 加载DXF文件: {file_path}")
            
            # 解析文件
            hole_collection = self.dxf_parser.parse_file(file_path)
            
            if not hole_collection or len(hole_collection) == 0:
                error_msg = "DXF文件中未找到符合条件的孔位"
                self.log_message.emit(f"⚠️ {error_msg}")
                QMessageBox.warning(None, "警告", error_msg)
                return False
                
            # 保存数据
            self.current_file_path = file_path
            self.current_hole_collection = hole_collection
            
            # 发送成功信号
            self.log_message.emit(f"✅ DXF解析成功，找到 {len(hole_collection)} 个孔位")
            self.status_message.emit(f"已加载 {len(hole_collection)} 个孔位")
            self.dxf_loaded.emit(file_path, hole_collection)
            
            return True
            
        except Exception as e:
            error_msg = f"加载DXF文件失败: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.log_message.emit(f"❌ {error_msg}")
            QMessageBox.critical(None, "错误", error_msg)
            return False
            
    def reload_current_file(self) -> bool:
        """重新加载当前文件"""
        if self.current_file_path:
            return self.load_dxf_file(self.current_file_path)
        return False
        
    def get_hole_collection(self) -> Optional[HoleCollection]:
        """获取当前孔位集合"""
        return self.current_hole_collection
        
    def get_file_info(self) -> dict:
        """获取文件信息"""
        if not self.current_file_path:
            return {
                'file_path': '',
                'file_name': '',
                'hole_count': 0,
                'file_size': 0
            }
            
        path = Path(self.current_file_path)
        return {
            'file_path': str(path),
            'file_name': path.name,
            'hole_count': len(self.current_hole_collection) if self.current_hole_collection else 0,
            'file_size': path.stat().st_size if path.exists() else 0
        }
        
    def clear(self):
        """清空当前数据"""
        self.current_file_path = None
        self.current_hole_collection = None
        self.log_message.emit("🗑️ 已清空DXF数据")