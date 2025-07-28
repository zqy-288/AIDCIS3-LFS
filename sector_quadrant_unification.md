# SectorQuadrant 统一化说明

## 当前情况

项目中存在两个 `SectorQuadrant` 定义：

1. **`src/core_business/coordinate_system.py`**
   - 基础定义，被 SharedDataManager 等核心模块使用
   - 简单的枚举定义

2. **`src/core_business/graphics/sector_types.py`**
   - 功能增强版本，包含额外的方法和属性
   - 为图形组件提供更丰富的功能

## 为什么保留两个版本

1. **避免循环依赖**
   - `coordinate_system.py` 是底层模块
   - `sector_types.py` 依赖于图形模块
   - 如果统一会造成循环依赖

2. **功能分层**
   - 核心功能使用简单定义
   - 图形功能使用增强定义

## 使用建议

### 核心模块（数据处理、坐标管理）
```python
from src.core_business.coordinate_system import SectorQuadrant
```

### 图形模块（UI组件、显示逻辑）
```python
from src.core_business.graphics.sector_types import SectorQuadrant
```

## 确保一致性

两个定义的枚举值必须保持一致：
- `SECTOR_1 = "sector_1"`  # 右上 (0°-90°)
- `SECTOR_2 = "sector_2"`  # 左上 (90°-180°)
- `SECTOR_3 = "sector_3"`  # 左下 (180°-270°)
- `SECTOR_4 = "sector_4"`  # 右下 (270°-360°)

## 未来改进方向

1. **创建基础类型模块**
   ```
   src/core_business/base_types.py  # 放置所有基础类型定义
   ```

2. **使用类型别名**
   ```python
   # 在需要增强功能的地方
   from src.core_business.base_types import SectorQuadrant as BaseSectorQuadrant
   
   class SectorQuadrant(BaseSectorQuadrant):
       # 添加额外方法
       pass
   ```

3. **使用协议（Protocol）**
   - 定义接口而不是具体实现
   - 允许不同模块有自己的实现

## 注意事项

1. 修改枚举值时，必须同时修改两个文件
2. 新增枚举项时，需要在两处添加
3. 使用时注意导入来源，避免混淆