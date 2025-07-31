# 批次处理系统总结

## 1. 批次处理概述

系统通过 `BatchService` 和 `DataPathManager` 管理检测批次的完整生命周期。

## 2. 批次创建

### 创建方式
```python
# 创建批次服务
from src.domain.services.batch_service import BatchService
from src.infrastructure.repositories.batch_repository_impl import BatchRepositoryImpl

repository = BatchRepositoryImpl()
batch_service = BatchService(repository)

# 创建实际检测批次
real_batch = batch_service.create_batch(
    product_id=1,
    product_name="CAP1000",
    operator="张三",
    equipment_id="DEVICE-001",
    is_mock=False  # 实际检测
)

# 创建模拟测试批次
mock_batch = batch_service.create_batch(
    product_id=1,
    product_name="CAP1000", 
    operator="系统测试",
    equipment_id="SIMULATOR",
    is_mock=True  # 模拟测试
)
```

### 批次ID格式
- 实际检测：`CAP1000_检测001_20250729_120028`
- 模拟测试：`CAP1000_检测001_20250729_120028_MOCK`

## 3. 数据保存路径

### 主要路径结构
```
Data/Products/{产品名}/InspectionBatches/{批次ID}/
├── batch_info.json         # 批次基本信息
├── batch_summary.json      # 批次汇总（完成后生成）
├── detection_state.json    # 暂停状态保存
├── HoleResults/           # 孔位检测结果
│   ├── AC001R001/        # 单个孔位目录
│   │   ├── BISDM/        # 内窥镜数据
│   │   │   └── result/   # 检测图像
│   │   └── CCIDM/        # 孔径测量数据
│   │       └── measurement_data_*.csv
│   └── AC002R001/
└── data_batches/          # 批量数据文件
    ├── batch_0001.json
    └── batch_0002.json
```

### 路径获取方法
```python
from src.models.data_path_manager import DataPathManager

path_manager = DataPathManager()

# 批次根目录
batch_path = path_manager.get_inspection_batch_path("CAP1000", batch_id)
# 返回: Data/Products/CAP1000/InspectionBatches/{batch_id}

# 孔位结果目录
hole_results = path_manager.get_hole_results_dir("CAP1000", batch_id)
# 返回: Data/Products/CAP1000/InspectionBatches/{batch_id}/HoleResults

# 单个孔位路径
hole_path = path_manager.get_hole_path("CAP1000", batch_id, "AC001R001")
# 返回: Data/Products/CAP1000/InspectionBatches/{batch_id}/HoleResults/AC001R001
```

## 4. 模拟测试

### 模拟参数
```python
simulation_params = {
    'speed': 10,          # 检测速度
    'interval': 100,      # 100ms/孔位
    'success_rate': 0.995, # 99.5%合格率
    'defect_rate': 0.004,  # 0.4%缺陷率
    'blind_rate': 0.001    # 0.1%盲孔率
}
```

### 模拟流程
1. 创建带 `_MOCK` 后缀的批次
2. 使用 `DetectionService` 定时器驱动检测
3. 按概率生成检测结果
4. 保存结果到相同的目录结构

## 5. 批次状态管理

### 状态流转
```
PENDING → RUNNING → PAUSED ↔ RUNNING → COMPLETED
                 ↘        ↙
                  TERMINATED
```

### 暂停/恢复
- **暂停时**：保存当前状态到 `detection_state.json`
- **恢复时**：从文件加载状态继续检测

### 状态文件示例
```json
{
  "current_index": 5,
  "detection_results": {
    "AC001R001": "qualified",
    "AC002R001": "defective"
  },
  "pending_holes": ["AC003R001", "AC004R001"],
  "simulation_params": {
    "speed": 10,
    "success_rate": 0.95
  }
}
```

## 6. 数据存储

### 数据库存储
- 位置：`src/data/product_models.db`
- 表：`inspection_batches`
- 存储：批次元数据、状态、进度

### 文件系统存储
- 批次信息：`batch_info.json`
- 检测状态：`detection_state.json`
- 批次汇总：`batch_summary.json`
- 批量数据：`data_batches/*.json`
- 孔位结果：`HoleResults/{hole_id}/`

## 7. 实际使用示例

### 在主窗口控制器中
```python
# MainWindowController 中的批次处理
def start_detection(self, is_mock=False):
    # 创建批次
    batch = self.batch_service.create_batch(
        product_id=self.current_product_id,
        product_name=self.current_product.model_name,
        is_mock=is_mock
    )
    
    # 开始检测
    self.detection_service.start_detection(
        holes=self.hole_collection.holes,
        batch_id=batch.batch_id,
        is_mock=is_mock
    )
```

### 查看生成的数据
批次数据保存在：
- macOS/Linux: `/Users/username/Desktop/AIDCIS3-LFS/Data/Products/`
- Windows: `C:\Users\username\Desktop\AIDCIS3-LFS\Data\Products\`

每个批次都有完整的目录结构，包含所有检测数据和结果。