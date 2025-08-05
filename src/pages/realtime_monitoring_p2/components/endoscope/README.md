# 内窥镜图像管理系统

## 概述

内窥镜管理器 (`EndoscopeManager`) 已升级为使用标准的数据路径结构，与项目的整体数据组织保持一致。

## 主要变更

### 1. 路径结构标准化

**之前**：
- 图像保存在项目根目录的 `endoscope_images/` 目录

**现在**：
- 图像保存在标准的批次目录结构中
- 路径格式：`/Data/Products/{product_id}/InspectionBatches/{batch_id}/...`

### 2. 保存位置逻辑

#### 针对特定孔位的检测：
```
/Data/Products/CAP1000/InspectionBatches/CAP1000_检测035_20250805_145238_MOCK/
└── HoleResults/
    └── AC097R001/
        └── BISDM/
            └── endoscope_images/
                ├── endoscope_20250805_143022_123_AC097R001_CAP1000_检测035_20250805_145238_MOCK.png
                └── endoscope_20250805_143023_456_AC097R001_CAP1000_检测035_20250805_145238_MOCK.png
```

#### 批次级别的图像（无特定孔位）：
```
/Data/Products/CAP1000/InspectionBatches/CAP1000_检测035_20250805_145238_MOCK/
└── endoscope_images/
    ├── endoscope_20250805_143022_123_CAP1000_检测035_20250805_145238_MOCK.png
    └── endoscope_20250805_143023_456_CAP1000_检测035_20250805_145238_MOCK.png
```

## 使用方法

### 1. 批次上下文设置（两种方式）

#### 方式1: 自动获取当前批次上下文（推荐）

```python
from src.pages.realtime_monitoring_p2.components.endoscope.endoscope_manager import EndoscopeManager

# 创建管理器
endoscope_manager = EndoscopeManager()

# 自动获取当前批次上下文
if endoscope_manager.refresh_batch_context():
    print("✅ 自动获取批次上下文成功")
else:
    print("⚠️ 需要手动设置批次上下文")

# 启用图像保存
endoscope_manager.set_save_images(True)
```

#### 方式2: 手动设置批次上下文（备用方案）

```python
# 手动设置批次上下文
product_id = "CAP1000"
batch_id = "CAP1000_检测035_20250805_145238_MOCK"
endoscope_manager.set_batch_context(product_id, batch_id)
```

### 批次上下文自动获取机制

系统会按以下顺序尝试获取当前批次信息：

1. **从 BusinessService 获取当前产品**
   - 检查 `business_service.current_product`
   - 获取产品的 `model_name` 或 `workpiece_id`

2. **从 DetectionService 获取当前批次ID**
   - 检查 `detection_service.current_batch_id`

3. **自动更新保存目录**
   - 根据获取的上下文信息动态设置保存路径

### 2. 设置当前检测孔位

```python
# 设置当前孔位（图像将保存到该孔位的BISDM目录）
hole_id = "AC097R001"
endoscope_manager.set_current_hole(hole_id)
```

### 3. 开始采集

```python
# 连接设备
endoscope_manager.connect_device()

# 开始采集
endoscope_manager.start_acquisition()
```

## API 变更

### 新方法

- `set_batch_context(product_id: str, batch_id: str)`: 手动设置批次上下文
- `refresh_batch_context()`: 自动获取并刷新当前批次上下文
- `_get_current_batch_context()`: 动态获取当前批次上下文信息
- `_update_save_directory()`: 根据当前上下文更新保存目录
- `_record_image_to_database(image_path: str)`: 记录图像到数据库（预留）

### 修改的方法

- `set_current_hole(hole_id, batch_id=None)`: 现在会自动更新保存目录
- `_save_image(pixmap)`: 增强的文件命名和路径管理

### 废弃的方法

- `set_save_directory()`: 已废弃，使用 `set_batch_context()` 代替

## 文件命名规范

图像文件命名格式：
```
endoscope_{timestamp}_{hole_id}_{batch_id}.png
```

示例：
```
endoscope_20250805_143022_123_AC097R001_CAP1000_检测035_20250805_145238_MOCK.png
```

## 数据库集成

系统预留了数据库记录功能，可以将图像元数据记录到 `EndoscopeImage` 表中，包括：
- 图像文件路径
- 孔位ID
- 深度信息
- 时间戳
- 图像类型

## 向后兼容性

- 保持了所有现有的公共API
- 自动处理路径迁移
- 优雅地处理缺失的上下文信息

## 故障排除

### 常见问题

1. **图像未保存**
   - 检查是否调用了 `set_batch_context()`
   - 确认 `save_images` 已启用
   - 检查目录权限

2. **路径错误**
   - 确保 `DataPathManager` 正确初始化
   - 检查产品ID和批次ID格式

3. **性能问题**
   - 大量图像保存时，考虑异步处理
   - 定期清理旧图像文件

## 测试

运行示例代码：
```bash
python src/pages/realtime_monitoring_p2/components/endoscope/endoscope_usage_example.py
```

这将演示完整的设置和使用流程。