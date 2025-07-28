"""
检测批次领域模型
包含批次的业务逻辑和状态管理
"""

from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field


class BatchStatus(Enum):
    """批次状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    TERMINATED = "terminated"
    FAILED = "failed"


class DetectionType(Enum):
    """检测类型枚举"""
    REAL = "real"
    MOCK = "mock"


@dataclass
class DetectionProgress:
    """检测进度值对象"""
    current_index: int = 0
    total_holes: int = 0
    completed_holes: int = 0
    qualified_holes: int = 0
    defective_holes: int = 0
    
    @property
    def completion_rate(self) -> float:
        """完成率"""
        if self.total_holes == 0:
            return 0.0
        return (self.completed_holes / self.total_holes) * 100
    
    @property
    def qualification_rate(self) -> float:
        """合格率"""
        if self.completed_holes == 0:
            return 0.0
        return (self.qualified_holes / self.completed_holes) * 100


@dataclass
class DetectionState:
    """检测状态值对象"""
    pause_time: Optional[datetime] = None
    resume_count: int = 0
    detection_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    pending_holes: List[str] = field(default_factory=list)
    simulation_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DetectionBatch:
    """检测批次实体"""
    batch_id: str
    product_id: int
    detection_number: int
    detection_type: DetectionType
    status: BatchStatus = BatchStatus.PENDING
    
    # 基本信息
    operator: Optional[str] = None
    equipment_id: Optional[str] = None
    description: Optional[str] = None
    
    # 时间信息
    created_at: datetime = field(default_factory=datetime.now)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    # 进度信息
    progress: DetectionProgress = field(default_factory=DetectionProgress)
    
    # 状态信息
    state: DetectionState = field(default_factory=DetectionState)
    
    # 路径信息
    data_path: Optional[str] = None
    
    def __post_init__(self):
        """初始化后处理"""
        # 确保枚举类型
        if isinstance(self.detection_type, str):
            self.detection_type = DetectionType(self.detection_type)
        if isinstance(self.status, str):
            self.status = BatchStatus(self.status)
    
    @property
    def is_mock(self) -> bool:
        """是否为模拟批次"""
        return self.detection_type == DetectionType.MOCK
    
    @property
    def can_start(self) -> bool:
        """是否可以开始"""
        return self.status == BatchStatus.PENDING
    
    @property
    def can_pause(self) -> bool:
        """是否可以暂停"""
        return self.status == BatchStatus.RUNNING
    
    @property
    def can_resume(self) -> bool:
        """是否可以恢复"""
        return self.status == BatchStatus.PAUSED
    
    @property
    def can_terminate(self) -> bool:
        """是否可以终止"""
        return self.status in [BatchStatus.RUNNING, BatchStatus.PAUSED]
    
    @property
    def is_completed(self) -> bool:
        """是否已完成"""
        return self.status in [BatchStatus.COMPLETED, BatchStatus.TERMINATED, BatchStatus.FAILED]
    
    @property
    def duration(self) -> Optional[float]:
        """检测持续时间（秒）"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def start(self) -> None:
        """开始检测"""
        if not self.can_start:
            raise ValueError(f"Cannot start batch in {self.status.value} status")
        
        self.status = BatchStatus.RUNNING
        self.start_time = datetime.now()
    
    def pause(self) -> None:
        """暂停检测"""
        if not self.can_pause:
            raise ValueError(f"Cannot pause batch in {self.status.value} status")
        
        self.status = BatchStatus.PAUSED
        self.state.pause_time = datetime.now()
    
    def resume(self) -> None:
        """恢复检测"""
        if not self.can_resume:
            raise ValueError(f"Cannot resume batch in {self.status.value} status")
        
        self.status = BatchStatus.RUNNING
        self.state.resume_count += 1
    
    def terminate(self) -> None:
        """终止检测"""
        if not self.can_terminate:
            raise ValueError(f"Cannot terminate batch in {self.status.value} status")
        
        self.status = BatchStatus.TERMINATED
        self.end_time = datetime.now()
    
    def complete(self) -> None:
        """完成检测"""
        if self.status != BatchStatus.RUNNING:
            raise ValueError(f"Cannot complete batch in {self.status.value} status")
        
        self.status = BatchStatus.COMPLETED
        self.end_time = datetime.now()
    
    def fail(self, reason: str) -> None:
        """检测失败"""
        self.status = BatchStatus.FAILED
        self.end_time = datetime.now()
        self.description = f"{self.description or ''} Failed: {reason}".strip()
    
    def update_progress(self, current_index: int, completed: int = 0, 
                       qualified: int = 0, defective: int = 0) -> None:
        """更新进度"""
        self.progress.current_index = current_index
        if completed > 0:
            self.progress.completed_holes = completed
        if qualified > 0:
            self.progress.qualified_holes = qualified
        if defective > 0:
            self.progress.defective_holes = defective
    
    def add_detection_result(self, hole_id: str, result: Dict[str, Any]) -> None:
        """添加检测结果"""
        self.state.detection_results[hole_id] = result
        
        # 更新统计
        if result.get('status') == 'qualified':
            self.progress.qualified_holes += 1
        elif result.get('status') == 'defective':
            self.progress.defective_holes += 1
        
        self.progress.completed_holes += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'batch_id': self.batch_id,
            'product_id': self.product_id,
            'detection_number': self.detection_number,
            'detection_type': self.detection_type.value,
            'status': self.status.value,
            'operator': self.operator,
            'equipment_id': self.equipment_id,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'progress': {
                'current_index': self.progress.current_index,
                'total_holes': self.progress.total_holes,
                'completed_holes': self.progress.completed_holes,
                'qualified_holes': self.progress.qualified_holes,
                'defective_holes': self.progress.defective_holes,
                'completion_rate': self.progress.completion_rate,
                'qualification_rate': self.progress.qualification_rate
            },
            'state': {
                'pause_time': self.state.pause_time.isoformat() if self.state.pause_time else None,
                'resume_count': self.state.resume_count,
                'detection_results': self.state.detection_results,
                'pending_holes': self.state.pending_holes,
                'simulation_params': self.state.simulation_params
            },
            'data_path': self.data_path
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DetectionBatch':
        """从字典创建"""
        # 解析进度信息
        progress_data = data.get('progress', {})
        progress = DetectionProgress(
            current_index=progress_data.get('current_index', 0),
            total_holes=progress_data.get('total_holes', 0),
            completed_holes=progress_data.get('completed_holes', 0),
            qualified_holes=progress_data.get('qualified_holes', 0),
            defective_holes=progress_data.get('defective_holes', 0)
        )
        
        # 解析状态信息
        state_data = data.get('state', {})
        state = DetectionState(
            pause_time=datetime.fromisoformat(state_data['pause_time']) if state_data.get('pause_time') else None,
            resume_count=state_data.get('resume_count', 0),
            detection_results=state_data.get('detection_results', {}),
            pending_holes=state_data.get('pending_holes', []),
            simulation_params=state_data.get('simulation_params', {})
        )
        
        # 创建批次对象
        return cls(
            batch_id=data['batch_id'],
            product_id=data['product_id'],
            detection_number=data['detection_number'],
            detection_type=DetectionType(data['detection_type']),
            status=BatchStatus(data['status']),
            operator=data.get('operator'),
            equipment_id=data.get('equipment_id'),
            description=data.get('description'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            start_time=datetime.fromisoformat(data['start_time']) if data.get('start_time') else None,
            end_time=datetime.fromisoformat(data['end_time']) if data.get('end_time') else None,
            progress=progress,
            state=state,
            data_path=data.get('data_path')
        )