"""
批次服务层
封装批次相关的业务逻辑
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

from src.domain.models.detection_batch import (
    DetectionBatch, BatchStatus, DetectionType
)
from src.domain.repositories.batch_repository import IBatchRepository
from src.models.data_path_manager import DataPathManager


class BatchService:
    """批次服务"""
    
    def __init__(self, repository: IBatchRepository, path_manager: DataPathManager = None):
        """初始化服务"""
        self.repository = repository
        self.path_manager = path_manager or DataPathManager()
    
    def create_batch(self, product_id: int, product_name: str, 
                    operator: str = None, equipment_id: str = None,
                    description: str = None, is_mock: bool = False) -> DetectionBatch:
        """创建新批次"""
        # 防御性编程：确保product_id是整数
        if hasattr(product_id, 'id'):
            print(f"警告：create_batch接收到ProductModel对象而不是ID，自动转换")
            product_id = product_id.id
        
        # 获取检测序号
        detection_number = self.repository.get_next_detection_number(product_id)
        
        # 生成批次ID
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        detection_type = DetectionType.MOCK if is_mock else DetectionType.REAL
        mock_suffix = '_MOCK' if is_mock else ''
        batch_id = f"{product_name}_检测{detection_number:03d}_{timestamp}{mock_suffix}"
        
        # 创建目录结构
        self.path_manager.create_inspection_structure(product_name, batch_id)
        data_path = self.path_manager.get_inspection_batch_path(product_name, batch_id)
        
        # 创建批次实体
        batch = DetectionBatch(
            batch_id=batch_id,
            product_id=product_id,
            detection_number=detection_number,
            detection_type=detection_type,
            operator=operator,
            equipment_id=equipment_id,
            description=description,
            data_path=data_path
        )
        
        # 保存到仓储
        self.repository.save(batch)
        
        # 创建批次信息文件
        self._create_batch_info_file(batch, product_name)
        
        return batch
    
    def start_batch(self, batch_id: str) -> bool:
        """开始批次"""
        batch = self.repository.find_by_id(batch_id)
        if not batch:
            return False
        
        try:
            batch.start()
            self.repository.save(batch)
            self._update_batch_info_file(batch)
            return True
        except ValueError:
            return False
    
    def pause_batch(self, batch_id: str, detection_state: Dict[str, Any]) -> bool:
        """暂停批次"""
        batch = self.repository.find_by_id(batch_id)
        if not batch:
            return False
        
        try:
            batch.pause()
            
            # 保存状态到批次对象
            if 'current_index' in detection_state:
                batch.progress.current_index = detection_state['current_index']
            if 'detection_results' in detection_state:
                batch.state.detection_results = detection_state['detection_results']
            if 'pending_holes' in detection_state:
                batch.state.pending_holes = detection_state['pending_holes']
            if 'simulation_params' in detection_state:
                batch.state.simulation_params = detection_state['simulation_params']
            
            # 保存到仓储
            self.repository.save(batch)
            self.repository.save_state(batch_id, detection_state)
            self._update_batch_info_file(batch)
            
            return True
        except ValueError:
            return False
    
    def resume_batch(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """恢复批次"""
        batch = self.repository.find_by_id(batch_id)
        if not batch:
            return None
        
        try:
            batch.resume()
            self.repository.save(batch)
            
            # 加载保存的状态
            state = self.repository.load_state(batch_id)
            if state:
                return state
            
            # 如果没有文件状态，从批次对象构建
            return {
                'current_index': batch.progress.current_index,
                'detection_results': batch.state.detection_results,
                'pending_holes': batch.state.pending_holes,
                'simulation_params': batch.state.simulation_params
            }
            
        except ValueError:
            return None
    
    def terminate_batch(self, batch_id: str) -> bool:
        """终止批次"""
        batch = self.repository.find_by_id(batch_id)
        if not batch:
            return False
        
        try:
            batch.terminate()
            self.repository.save(batch)
            self._update_batch_info_file(batch)
            self._create_summary_file(batch)
            return True
        except ValueError:
            return False
    
    def complete_batch(self, batch_id: str) -> bool:
        """完成批次"""
        batch = self.repository.find_by_id(batch_id)
        if not batch:
            return False
        
        try:
            batch.complete()
            self.repository.save(batch)
            self._update_batch_info_file(batch)
            self._create_summary_file(batch)
            return True
        except ValueError:
            return False
    
    def update_progress(self, batch_id: str, 
                       current_index: int = None,
                       total_holes: int = None,
                       completed_holes: int = None,
                       qualified_holes: int = None,
                       defective_holes: int = None) -> bool:
        """更新进度"""
        batch = self.repository.find_by_id(batch_id)
        if not batch:
            return False
        
        # 更新进度
        if current_index is not None:
            batch.progress.current_index = current_index
        if total_holes is not None:
            batch.progress.total_holes = total_holes
        if completed_holes is not None:
            batch.progress.completed_holes = completed_holes
        if qualified_holes is not None:
            batch.progress.qualified_holes = qualified_holes
        if defective_holes is not None:
            batch.progress.defective_holes = defective_holes
        
        # 保存
        self.repository.save(batch)
        self._update_summary_file(batch)
        
        return True
    
    def add_detection_result(self, batch_id: str, hole_id: str, result: Dict[str, Any]) -> bool:
        """添加检测结果"""
        batch = self.repository.find_by_id(batch_id)
        if not batch:
            return False
        
        batch.add_detection_result(hole_id, result)
        self.repository.save(batch)
        
        return True
    
    def get_batch(self, batch_id: str) -> Optional[DetectionBatch]:
        """获取批次"""
        return self.repository.find_by_id(batch_id)
    
    def get_product_batches(self, product_id: int, detection_type: str = None) -> List[DetectionBatch]:
        """获取产品的批次列表"""
        return self.repository.find_by_product(product_id, detection_type)
    
    def get_resumable_batch(self, product_id: int, is_mock: bool = False) -> Optional[DetectionBatch]:
        """获取可恢复的批次"""
        detection_type = 'mock' if is_mock else 'real'
        return self.repository.find_resumable(product_id, detection_type)
    
    def _create_batch_info_file(self, batch: DetectionBatch, product_name: str):
        """创建批次信息文件"""
        info_path = self.path_manager.get_batch_info_path(product_name, batch.batch_id)
        info_data = {
            'batch_id': batch.batch_id,
            'product_id': product_name,
            'product_name': product_name,
            'detection_number': batch.detection_number,
            'detection_type': batch.detection_type.value,
            'is_mock': batch.is_mock,
            'operator': batch.operator,
            'equipment_id': batch.equipment_id,
            'description': batch.description,
            'status': batch.status.value,
            'created_at': batch.created_at.isoformat()
        }
        
        try:
            import json
            with open(info_path, 'w', encoding='utf-8') as f:
                json.dump(info_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"创建批次信息文件失败: {e}")
    
    def _update_batch_info_file(self, batch: DetectionBatch):
        """更新批次信息文件"""
        # 需要获取产品名称
        # 这里简化处理，从batch_id中提取
        product_name = batch.batch_id.split('_')[0]
        
        info_path = self.path_manager.get_batch_info_path(product_name, batch.batch_id)
        info_data = batch.to_dict()
        
        try:
            import json
            with open(info_path, 'w', encoding='utf-8') as f:
                json.dump(info_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"更新批次信息文件失败: {e}")
    
    def _create_summary_file(self, batch: DetectionBatch):
        """创建汇总文件"""
        self._update_summary_file(batch)
    
    def _update_summary_file(self, batch: DetectionBatch):
        """更新汇总文件"""
        product_name = batch.batch_id.split('_')[0]
        summary_path = self.path_manager.get_batch_summary_path(product_name, batch.batch_id)
        
        summary_data = {
            'batch_id': batch.batch_id,
            'detection_number': batch.detection_number,
            'status': batch.status.value,
            'total_holes': batch.progress.total_holes,
            'completed_holes': batch.progress.completed_holes,
            'qualified_holes': batch.progress.qualified_holes,
            'defective_holes': batch.progress.defective_holes,
            'completion_rate': batch.progress.completion_rate,
            'qualification_rate': batch.progress.qualification_rate,
            'duration': batch.duration,
            'updated_at': datetime.now().isoformat()
        }
        
        try:
            import json
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"更新汇总文件失败: {e}")