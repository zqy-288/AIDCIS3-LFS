"""
批次检测用例
协调UI层与领域层的交互
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass

from src.domain.services.batch_service import BatchService
from src.domain.models.detection_batch import DetectionBatch


@dataclass
class StartDetectionRequest:
    """开始检测请求"""
    product_id: int
    product_name: str
    operator: Optional[str] = None
    equipment_id: Optional[str] = None
    description: Optional[str] = None
    is_mock: bool = False


@dataclass
class StartDetectionResponse:
    """开始检测响应"""
    success: bool
    batch_id: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class PauseDetectionRequest:
    """暂停检测请求"""
    batch_id: str
    current_index: int
    detection_results: Dict[str, Any]
    pending_holes: list
    simulation_params: Dict[str, Any]


@dataclass
class ContinueDetectionRequest:
    """继续检测请求"""
    batch_id: str


@dataclass
class ContinueDetectionResponse:
    """继续检测响应"""
    success: bool
    detection_state: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


@dataclass
class CheckResumableResponse:
    """检查可恢复批次响应"""
    has_resumable: bool
    batch_id: Optional[str] = None
    detection_number: Optional[int] = None
    pause_time: Optional[str] = None
    progress: Optional[Dict[str, Any]] = None


class BatchDetectionUseCase:
    """批次检测用例"""
    
    def __init__(self, batch_service: BatchService):
        """初始化用例"""
        self.batch_service = batch_service
    
    def start_detection(self, request: StartDetectionRequest) -> StartDetectionResponse:
        """开始检测"""
        try:
            # 创建批次
            batch = self.batch_service.create_batch(
                product_id=request.product_id,
                product_name=request.product_name,
                operator=request.operator,
                equipment_id=request.equipment_id,
                description=request.description,
                is_mock=request.is_mock
            )
            
            # 开始检测
            if self.batch_service.start_batch(batch.batch_id):
                return StartDetectionResponse(
                    success=True,
                    batch_id=batch.batch_id
                )
            else:
                return StartDetectionResponse(
                    success=False,
                    error_message="无法开始检测"
                )
                
        except Exception as e:
            return StartDetectionResponse(
                success=False,
                error_message=str(e)
            )
    
    def pause_detection(self, request: PauseDetectionRequest) -> bool:
        """暂停检测"""
        detection_state = {
            'current_index': request.current_index,
            'detection_results': request.detection_results,
            'pending_holes': request.pending_holes,
            'simulation_params': request.simulation_params
        }
        
        return self.batch_service.pause_batch(request.batch_id, detection_state)
    
    def continue_detection(self, request: ContinueDetectionRequest) -> ContinueDetectionResponse:
        """继续检测"""
        try:
            detection_state = self.batch_service.resume_batch(request.batch_id)
            
            if detection_state:
                return ContinueDetectionResponse(
                    success=True,
                    detection_state=detection_state
                )
            else:
                return ContinueDetectionResponse(
                    success=False,
                    error_message="无法恢复检测"
                )
                
        except Exception as e:
            return ContinueDetectionResponse(
                success=False,
                error_message=str(e)
            )
    
    def terminate_detection(self, batch_id: str) -> bool:
        """终止检测"""
        return self.batch_service.terminate_batch(batch_id)
    
    def check_resumable_batch(self, product_id: int, is_mock: bool = False) -> CheckResumableResponse:
        """检查可恢复的批次"""
        batch = self.batch_service.get_resumable_batch(product_id, is_mock)
        
        if batch:
            return CheckResumableResponse(
                has_resumable=True,
                batch_id=batch.batch_id,
                detection_number=batch.detection_number,
                pause_time=batch.state.pause_time.isoformat() if batch.state.pause_time else None,
                progress={
                    'completed_holes': batch.progress.completed_holes,
                    'total_holes': batch.progress.total_holes,
                    'completion_rate': batch.progress.completion_rate,
                    'qualification_rate': batch.progress.qualification_rate
                }
            )
        else:
            return CheckResumableResponse(has_resumable=False)
    
    def update_detection_progress(self, batch_id: str, 
                                 total_holes: int = None,
                                 current_index: int = None) -> bool:
        """更新检测进度"""
        return self.batch_service.update_progress(
            batch_id=batch_id,
            total_holes=total_holes,
            current_index=current_index
        )
    
    def add_hole_result(self, batch_id: str, hole_id: str, 
                       is_qualified: bool, defect_info: Dict[str, Any] = None) -> bool:
        """添加孔位检测结果"""
        result = {
            'status': 'qualified' if is_qualified else 'defective',
            'defect_info': defect_info
        }
        
        return self.batch_service.add_detection_result(batch_id, hole_id, result)
    
    def get_batch_info(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """获取批次信息"""
        batch = self.batch_service.get_batch(batch_id)
        if batch:
            return batch.to_dict()
        return None