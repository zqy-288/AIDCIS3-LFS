# 废弃文件清单

本文档列出了在批次检测系统重构过程中被标记为废弃的文件。这些文件已被新的DDD架构替代，但仍保留用于向后兼容。

## 废弃文件列表

### 1. 模型层文件 (已废弃)
- **`/src/models/inspection_batch_model.py`** - 原批次数据模型
  - **替代文件**: 
    - `/src/domain/models/detection_batch.py` - 领域模型
    - `/src/domain/repositories/batch_repository.py` - 仓储接口
    - `/src/infrastructure/repositories/batch_repository_impl.py` - 仓储实现

### 2. 控制器文件 (已废弃)
- **`/src/controllers/main_window_controller.py`** - 原主窗口控制器
  - **替代文件**: 
    - `/src/controllers/main_window_controller_refactored.py` - 重构后控制器
    - `/src/application/use_cases/batch_detection_use_case.py` - 用例层

### 3. 服务层文件 (已废弃)
- **`/src/controllers/services/detection_service.py`** - 原检测服务
  - **替代文件**: 
    - `/src/domain/services/batch_service.py` - 领域服务
    - `/src/application/use_cases/batch_detection_use_case.py` - 用例层

### 4. 测试文件 (已废弃)
- **`/tests/test_batch_management.py`** - 原批次管理测试
  - **替代文件**: 
    - `/tests/test_decoupling_architecture.py` - 架构解耦测试
    - `/tests/test_refactored_integration.py` - 功能集成测试

## 重构架构对比

### 重构前 (已废弃)
```
src/
├── models/
│   └── inspection_batch_model.py           [DEPRECATED]
├── controllers/
│   ├── main_window_controller.py           [DEPRECATED]
│   └── services/
│       └── detection_service.py            [DEPRECATED]
└── tests/
    └── test_batch_management.py             [DEPRECATED]
```

### 重构后 (新架构)
```
src/
├── domain/                    # 领域层
│   ├── models/               
│   │   └── detection_batch.py              [NEW]
│   ├── repositories/         
│   │   └── batch_repository.py             [NEW]
│   └── services/             
│       └── batch_service.py                [NEW]
├── application/              # 应用层
│   └── use_cases/           
│       └── batch_detection_use_case.py     [NEW]
├── infrastructure/           # 基础设施层
│   ├── repositories/        
│   │   └── batch_repository_impl.py        [NEW]
│   └── event_bus.py                        [NEW]
├── controllers/             # 控制器层
│   └── main_window_controller_refactored.py [NEW]
└── tests/
    ├── test_decoupling_architecture.py     [NEW]
    └── test_refactored_integration.py      [NEW]
```

## 废弃原因

### 1. 高耦合问题
- 原有代码层级间高度耦合
- 业务逻辑散布在各个层级
- 难以进行单元测试

### 2. 低内聚问题
- 单个类承担过多职责
- 缺乏清晰的领域模型
- 没有明确的服务边界

### 3. 架构改进
- 采用领域驱动设计(DDD)
- 实现分层架构
- 使用依赖注入和事件驱动

## 迁移指南

如果您需要从废弃的文件迁移到新架构：

### 1. 批次操作迁移
```python
# 旧方式 (已废弃)
from src.models.inspection_batch_model import InspectionBatchManager
batch_manager = InspectionBatchManager()
batch = batch_manager.create_batch(...)

# 新方式
from src.application.use_cases.batch_detection_use_case import BatchDetectionUseCase
from src.domain.services.batch_service import BatchService
from src.infrastructure.repositories.batch_repository_impl import BatchRepositoryImpl

repository = BatchRepositoryImpl()
service = BatchService(repository)
use_case = BatchDetectionUseCase(service)
response = use_case.start_detection(request)
```

### 2. 控制器迁移
```python
# 旧方式 (已废弃)
from src.controllers.main_window_controller import MainWindowController

# 新方式
from src.controllers.main_window_controller_refactored import MainWindowControllerRefactored
```

## 注意事项

1. **向后兼容**: 废弃文件仍然保留，确保现有代码继续工作
2. **逐步迁移**: 建议逐步将代码迁移到新架构
3. **测试验证**: 新架构已通过完整的测试验证
4. **文档更新**: 请参考 `/REFACTORING_SUMMARY.md` 了解详细的重构说明

## 清理计划

在确认所有代码都已迁移到新架构后，可以考虑：
1. 将废弃文件移动到 `/deprecated` 目录
2. 最终删除不再使用的废弃文件
3. 更新相关的导入和引用

---
**最后更新**: 2025-01-26  
**重构版本**: v2.0.0