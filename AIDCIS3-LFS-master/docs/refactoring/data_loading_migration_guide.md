# 数据加载逻辑拆分迁移指南

## 概述

本文档描述了如何将 `DynamicSectorDisplayWidget` 的数据加载逻辑拆分到独立的服务层，实现数据管理与UI的分离。

## 架构变化

### 之前的架构
```
SharedDataManager → DynamicSectorDisplayWidget (2896行，包含所有逻辑)
```

### 新的架构
```
SharedDataManager 
    ↓
HoleDataAdapter (数据适配层)
    ↓
SectorDataDistributor (扇形数据分发)
    ↓
DynamicSectorDisplayRefactored (纯UI组件)
```

## 新增组件

### 1. HoleDataAdapter (`hole_data_adapter.py`)
- **职责**：从SharedDataManager获取数据并适配为视图可用格式
- **主要功能**：
  - 从SharedDataManager提取孔位数据
  - 转换数据格式为HoleCollection
  - 提供数据变化通知机制
  - 管理数据缓存

### 2. SectorDataDistributor (`sector_data_distributor.py`)
- **职责**：管理孔位数据到扇形的分配
- **主要功能**：
  - 从HoleDataAdapter获取数据
  - 根据位置将孔分配到4个扇形
  - 管理每个扇形的数据缓存
  - 提供扇形数据访问接口

### 3. DynamicSectorDisplayRefactored (`dynamic_sector_display_refactored.py`)
- **职责**：纯UI组件，专注于显示逻辑
- **主要功能**：
  - 使用数据服务获取数据
  - 管理视图切换
  - 处理用户交互
  - 更新显示状态

## 迁移步骤

### 第一步：在主窗口中替换组件

```python
# 旧代码
from src.core_business.graphics.dynamic_sector_view import DynamicSectorDisplayWidget

self.sector_widget = DynamicSectorDisplayWidget()
self.sector_widget.set_hole_collection(hole_collection, sector_manager)

# 新代码
from src.core_business.graphics.dynamic_sector_display_refactored import DynamicSectorDisplayRefactored

self.sector_widget = DynamicSectorDisplayRefactored(self.shared_data_manager)
# 数据会自动从SharedDataManager加载，无需手动设置
```

### 第二步：更新数据流

旧的数据流：
```python
# 手动设置数据
hole_collection = parser.parse_dxf(file_path)
sector_widget.set_hole_collection(hole_collection, sector_manager)
```

新的数据流：
```python
# 数据通过SharedDataManager自动流入
shared_data_manager.set_hole_collection(hole_collection)
# DynamicSectorDisplayRefactored会自动获取并显示
```

### 第三步：处理信号连接

```python
# 信号保持兼容
sector_widget.sector_changed.connect(self.on_sector_changed)
sector_widget.detection_progress.connect(self.on_progress_updated)
```

## 优势

1. **解耦**：UI组件不再直接依赖数据源
2. **可测试性**：数据服务可以独立测试
3. **可维护性**：每个组件职责单一，易于维护
4. **性能**：数据缓存和增量更新支持
5. **扩展性**：容易添加新的数据处理逻辑

## 注意事项

1. **数据同步**：确保SharedDataManager是数据的唯一真实来源
2. **信号连接**：检查所有信号连接是否正确迁移
3. **兼容性**：保留了 `set_hole_collection` 方法以兼容旧代码
4. **初始化顺序**：确保SharedDataManager在组件创建前初始化

## 后续优化

1. 实现增量数据更新
2. 添加数据预加载机制
3. 优化扇形切换性能
4. 实现数据压缩和懒加载