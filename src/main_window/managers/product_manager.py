"""产品管理器"""
import logging
from pathlib import Path
from typing import Optional, Any
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox, QFileDialog

from modules.product_selection import ProductSelectionDialog


class ProductManager(QObject):
    """
    产品管理器
    负责产品选择、加载和相关数据处理
    """
    
    # 信号定义
    product_selected = Signal(object)  # 产品对象
    product_loaded = Signal(str)  # 产品型号名
    dxf_loaded = Signal(str)  # DXF文件路径
    log_message = Signal(str)
    status_message = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 当前产品
        self.current_product = None
        
        # 外部组件引用
        self.main_window = None
        self.product_model_manager = None
        self.dxf_parser = None
        self.hole_collection = None
        
    def set_components(self, main_window, product_model_manager, dxf_parser):
        """设置外部组件引用"""
        self.main_window = main_window
        self.product_model_manager = product_model_manager
        self.dxf_parser = dxf_parser
        
    def select_product(self):
        """打开产品选择对话框"""
        try:
            dialog = ProductSelectionDialog(self.main_window)
            dialog.product_selected.connect(self._on_product_selected)
            dialog.exec()
        except Exception as e:
            error_msg = f"打开产品选择对话框失败: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.log_message.emit(f"❌ {error_msg}")
            QMessageBox.critical(self.main_window, "错误", error_msg)
            
    def _on_product_selected(self, product):
        """处理产品选择"""
        try:
            self.current_product = product
            self.status_message.emit(f"正在加载产品型号: {product.model_name}")
            self.log_message.emit(f"🎯 选择产品型号: {product.model_name}")
            
            # 发送产品选择信号
            self.product_selected.emit(product)
            
            # 配置扇形模式
            self._configure_sector_mode(product)
            
            # 处理DXF文件
            if hasattr(product, 'dxf_file_path') and product.dxf_file_path:
                self.log_message.emit(f"📁 产品关联DXF文件: {product.dxf_file_path}")
                self.load_dxf_from_product(product.dxf_file_path)
            else:
                self.log_message.emit("⚠️ 产品没有关联DXF文件")
                self._prompt_for_dxf_file(product)
                
            self.product_loaded.emit(product.model_name)
            self.status_message.emit(f"产品型号已选择: {product.model_name}")
            self.log_message.emit(f"✅ 成功选择产品型号: {product.model_name}")
            
        except Exception as e:
            error_msg = f"处理产品选择失败: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.log_message.emit(f"❌ {error_msg}")
            QMessageBox.critical(self.main_window, "错误", error_msg)
            
    def _configure_sector_mode(self, product):
        """配置扇形模式"""
        if hasattr(product, 'sector_count') and product.sector_count:
            sector_count = product.sector_count
            dynamic_mode = sector_count != 4
            
            # 这里需要通过信号通知主窗口更新扇形管理器
            # 或者直接访问扇形管理器（如果有引用）
            self.log_message.emit(f"🔧 配置扇形模式: {sector_count} 扇形, 动态模式: {dynamic_mode}")
            
    def load_dxf_from_product(self, dxf_file_path: str):
        """从产品关联的DXF文件加载数据"""
        if not dxf_file_path or not Path(dxf_file_path).exists():
            self.log_message.emit(f"警告: DXF文件不存在 - {dxf_file_path}")
            return False
            
        try:
            self.log_message.emit(f"加载产品关联的DXF文件: {dxf_file_path}")
            
            # 使用DXF解析器加载文件
            if self.dxf_parser:
                hole_collection = self.dxf_parser.parse_file(dxf_file_path)
                
                if not hole_collection or len(hole_collection) == 0:
                    error_msg = "DXF文件中未找到符合条件的孔位"
                    self.log_message.emit(f"警告: {error_msg}")
                    QMessageBox.warning(self.main_window, "警告", error_msg)
                    return False
                    
                self.hole_collection = hole_collection
                self.log_message.emit(f"DXF解析成功，找到 {len(hole_collection)} 个孔位")
                
                # 发送DXF加载成功信号
                self.dxf_loaded.emit(dxf_file_path)
                
                return True
                
        except Exception as e:
            error_msg = f"加载DXF文件失败: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.log_message.emit(f"❌ {error_msg}")
            QMessageBox.critical(self.main_window, "错误", error_msg)
            return False
            
    def _prompt_for_dxf_file(self, product):
        """提示用户选择DXF文件"""
        reply = QMessageBox.question(
            self.main_window, "需要加载DXF文件",
            f"产品型号 '{product.model_name}' 没有关联的DXF文件。\n是否现在选择一个DXF文件？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            file_path, _ = QFileDialog.getOpenFileName(
                self.main_window, "选择DXF文件", "", "DXF文件 (*.dxf);;所有文件 (*)"
            )
            
            if file_path:
                # 保存DXF文件路径到产品
                try:
                    if self.product_model_manager:
                        self.product_model_manager.update_product(
                            product.id, dxf_file_path=file_path
                        )
                    self.load_dxf_from_product(file_path)
                except Exception as e:
                    self.log_message.emit(f"保存DXF文件路径失败: {str(e)}")
            else:
                self.log_message.emit("🚫 用户取消选择DXF文件")
        else:
            self.log_message.emit("🚫 用户选择不加载DXF文件")
            
    def get_current_product(self):
        """获取当前产品"""
        return self.current_product
        
    def get_hole_collection(self):
        """获取当前孔位集合"""
        return self.hole_collection