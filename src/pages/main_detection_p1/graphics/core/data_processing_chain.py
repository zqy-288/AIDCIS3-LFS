"""
数据处理责任链
实现清晰的单向数据流，避免重复处理
"""

from typing import Optional, Callable
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from src.shared.models.hole_data import HoleCollection
from src.pages.main_detection_p1.graphics.core.hole_data_adapter import HoleDataAdapter
from src.pages.main_detection_p1.graphics.core.sector_data_distributor import SectorDataDistributor
from src.pages.main_detection_p1.graphics.core.sector_controllers import UnifiedLogger


class DataProcessingChain(QObject):
    """
    数据处理责任链协调器
    
    确保数据按以下顺序单向流动：
    SharedDataManager → HoleDataAdapter → SectorDataDistributor → UI Components
    
    每个环节只处理一次，避免重复
    """
    
    # 链处理完成信号
    processing_complete = Signal(dict)  # 包含处理结果的字典
    processing_started = Signal()
    processing_error = Signal(str)
    
    def __init__(self, shared_data_manager, parent=None):
        super().__init__(parent)
        
        self.logger = UnifiedLogger("DataProcessingChain")
        self.shared_data_manager = shared_data_manager
        
        # 创建链中的处理器
        self.hole_data_adapter = HoleDataAdapter(shared_data_manager)
        self.sector_distributor = SectorDataDistributor(self.hole_data_adapter)
        
        # 禁用旧系统的自动信号连接，避免重复处理
        self._disable_old_system_signals()
        
        # 处理状态
        self._is_processing = False
        self._last_processed_hash = None
        
        # 初始化连接
        self._setup_connections()
        
    def _disable_old_system_signals(self):
        """禁用旧系统的自动信号连接"""
        try:
            # 断开SectorDataDistributor的自动连接
            self.hole_data_adapter.data_loaded.disconnect()
            self.logger.info("已禁用HoleDataAdapter的自动信号", "🔇")
        except:
            pass  # 如果没有连接则忽略
            
    def _setup_connections(self):
        """设置连接 - 只连接必要的信号"""
        # 监听SharedDataManager的数据变化
        self.shared_data_manager.data_changed.connect(self._on_shared_data_changed)
        
        # 不再连接adapter和distributor的自动信号
        # 改为手动控制处理流程
        
    def _on_shared_data_changed(self, change_type: str, data: any):
        """处理共享数据变化"""
        if change_type == "full_reload" and not self._is_processing:
            self.logger.info("检测到数据变化，启动处理链", "🔄")
            self.process_data()
            
    def process_data(self, force: bool = False) -> Optional[dict]:
        """
        执行完整的数据处理链
        
        Args:
            force: 是否强制处理（忽略缓存）
            
        Returns:
            处理结果字典，包含各阶段的输出
        """
        if self._is_processing:
            self.logger.warning("处理链正在运行中，跳过本次请求", "⚠️")
            return None
            
        try:
            self._is_processing = True
            self.processing_started.emit()
            
            result = {}
            
            # 步骤1：从adapter获取数据（带缓存检查）
            self.logger.info("步骤1：获取适配后的数据", "1️⃣")
            hole_collection = self.hole_data_adapter.get_hole_collection()
            
            if not hole_collection:
                self.logger.warning("没有可用的孔位数据", "❌")
                self.processing_error.emit("没有可用的孔位数据")
                return None
                
            # 检查是否需要处理（基于数据哈希）
            current_hash = self._calculate_data_hash(hole_collection)
            if not force and current_hash == self._last_processed_hash:
                self.logger.info("数据未变化，使用缓存结果", "✅")
                return self._last_result
                
            result['hole_collection'] = hole_collection
            result['hole_count'] = len(hole_collection)
            
            # 步骤2：分发到扇形（不触发自动信号）
            self.logger.info("步骤2：分发数据到扇形", "2️⃣")
            
            # 手动调用分发方法，不触发信号
            self.sector_distributor._clear_sector_data()
            self.sector_distributor._calculate_global_metrics(hole_collection)
            distribution_count = self.sector_distributor._distribute_holes_to_sectors(hole_collection)
            self.sector_distributor._update_sector_statistics()
            
            # 获取分发统计
            stats = self.sector_distributor._get_distribution_statistics()
            result['distribution_stats'] = stats
            
            self.logger.info(f"处理链完成: {result['hole_count']}个孔位已分发", "✅")
            
            # 更新缓存
            self._last_processed_hash = current_hash
            self._last_result = result
            
            # 发送完成信号
            self.processing_complete.emit(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"处理链出错: {e}", "❌")
            self.processing_error.emit(str(e))
            return None
            
        finally:
            self._is_processing = False
            
    def _calculate_data_hash(self, hole_collection: HoleCollection) -> str:
        """计算数据哈希，用于检测变化"""
        # 简单实现：使用孔位数量和第一个/最后一个孔的ID
        if not hole_collection or len(hole_collection) == 0:
            return "empty"
            
        hole_ids = list(hole_collection.holes.keys())
        return f"{len(hole_collection)}_{hole_ids[0]}_{hole_ids[-1]}"
        
    def get_hole_collection(self) -> Optional[HoleCollection]:
        """获取当前的孔位集合"""
        return self.hole_data_adapter.get_hole_collection()
        
    def get_sector_data(self, sector):
        """获取指定扇形的数据"""
        return self.sector_distributor.get_sector_data(sector)
        
    def get_all_sector_data(self):
        """获取所有扇形数据"""
        return self.sector_distributor.get_all_sector_data()
        
    def clear_all(self):
        """清除所有数据"""
        self.logger.info("清除所有数据", "🗑️")
        self.hole_data_adapter.clear_cache()
        self.sector_distributor.clear_all()
        self._last_processed_hash = None
        self._last_result = None