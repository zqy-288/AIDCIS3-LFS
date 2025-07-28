# Sector Types API 文档

## 模块概述
`sector_types.py` 提供了扇形相关的统一类型定义，是整个扇形管理系统的基础。

## 类型定义

### SectorQuadrant 枚举

扇形象限枚举，定义了四个标准扇形区域。

```python
from src.core_business.graphics.sector_types import SectorQuadrant

# 基本使用
sector = SectorQuadrant.SECTOR_1  # 右上扇形
print(sector.value)  # "sector_1"
print(sector.display_name)  # "扇形1 (右上)"
```

#### 枚举值
- `SECTOR_1`: 右上扇形 (0°-90°)
- `SECTOR_2`: 左上扇形 (90°-180°)
- `SECTOR_3`: 左下扇形 (180°-270°)
- `SECTOR_4`: 右下扇形 (270°-360°)

#### 属性方法

##### display_name
获取扇形的显示名称
```python
name = SectorQuadrant.SECTOR_1.display_name  # "扇形1 (右上)"
```

##### angle_range
获取扇形的角度范围
```python
start, end = SectorQuadrant.SECTOR_1.angle_range  # (0, 90)
```

#### 类方法

##### from_angle(angle: float) -> SectorQuadrant
根据角度获取对应的扇形
```python
sector = SectorQuadrant.from_angle(45)  # SECTOR_1
sector = SectorQuadrant.from_angle(135)  # SECTOR_2
```

##### from_position(x, y, center_x, center_y) -> SectorQuadrant
根据位置相对于中心点确定扇形
```python
# 点(100, 50)相对于中心(0, 0)
sector = SectorQuadrant.from_position(100, 50, 0, 0)  # SECTOR_4
```

### SectorProgress 数据类

扇形进度跟踪数据类，用于记录检测进度。

```python
from src.core_business.graphics.sector_types import SectorProgress
from PySide6.QtGui import QColor

progress = SectorProgress(
    sector=SectorQuadrant.SECTOR_1,
    total_holes=100,
    completed_holes=50,
    qualified_holes=45,
    defective_holes=5,
    progress_percentage=50.0,
    status_color=QColor(0, 255, 0)
)
```

#### 属性
- `sector`: SectorQuadrant - 所属扇形
- `total_holes`: int - 总孔位数
- `completed_holes`: int - 已完成数
- `qualified_holes`: int - 合格数
- `defective_holes`: int - 缺陷数
- `progress_percentage`: float - 进度百分比
- `status_color`: Optional[QColor] - 状态颜色

#### 计算属性

##### completion_rate
完成率（百分比）
```python
rate = progress.completion_rate  # 50.0
```

##### qualification_rate
合格率（百分比）
```python
rate = progress.qualification_rate  # 90.0
```

##### is_completed
是否已完成
```python
if progress.is_completed:
    print("扇形检测完成")
```

#### 兼容属性
为了向后兼容，提供了简化的属性名：
- `completed` -> `completed_holes`
- `total` -> `total_holes`
- `percentage` -> 计算的完成百分比

#### 方法

##### increment()
增加完成数
```python
progress.increment()  # completed_holes += 1
```

##### reset()
重置进度
```python
progress.reset()  # 清空所有进度数据
```

### SectorBounds 数据类

扇形边界数据类，用于管理扇形的几何边界。

```python
from src.core_business.graphics.sector_types import SectorBounds

bounds = SectorBounds(
    min_x=0,
    min_y=0,
    max_x=100,
    max_y=100
)
```

#### 属性
- `min_x`: float - 最小X坐标
- `min_y`: float - 最小Y坐标
- `max_x`: float - 最大X坐标
- `max_y`: float - 最大Y坐标

#### 计算属性

##### width
边界宽度
```python
w = bounds.width  # 100
```

##### height
边界高度
```python
h = bounds.height  # 100
```

##### center
中心点坐标
```python
cx, cy = bounds.center  # (50, 50)
```

#### 方法

##### contains_point(x, y) -> bool
检查点是否在边界内
```python
if bounds.contains_point(50, 50):
    print("点在边界内")
```

##### expand(margin)
扩展边界
```python
bounds.expand(10)  # 各方向扩展10个单位
```

##### to_tuple() -> Tuple[float, float, float, float]
转换为元组
```python
min_x, min_y, max_x, max_y = bounds.to_tuple()
```

## 使用示例

### 完整的扇形分配流程
```python
from src.core_business.graphics.sector_types import SectorQuadrant, SectorProgress

# 根据孔位位置分配扇形
holes = [
    {"id": "H1", "x": 50, "y": -50},   # 右上
    {"id": "H2", "x": -50, "y": -50},  # 左上
    {"id": "H3", "x": -50, "y": 50},   # 左下
    {"id": "H4", "x": 50, "y": 50},    # 右下
]

sector_assignments = {}
for hole in holes:
    sector = SectorQuadrant.from_position(
        hole["x"], hole["y"], 0, 0
    )
    sector_assignments[hole["id"]] = sector

# 统计每个扇形的孔位数
from collections import Counter
sector_counts = Counter(sector_assignments.values())

# 创建进度跟踪
progresses = {}
for sector, count in sector_counts.items():
    progresses[sector] = SectorProgress(
        sector=sector,
        total_holes=count,
        completed_holes=0
    )
```

### 进度更新示例
```python
# 更新检测进度
def update_hole_status(hole_id, status):
    sector = sector_assignments[hole_id]
    progress = progresses[sector]
    
    if status == "completed":
        progress.increment()
    elif status == "qualified":
        progress.qualified_holes += 1
    elif status == "defective":
        progress.defective_holes += 1
    
    # 检查是否完成
    if progress.is_completed:
        print(f"{sector.display_name} 检测完成！")
        print(f"合格率: {progress.qualification_rate:.1f}%")
```

## 最佳实践

1. **使用枚举而非字符串**
   ```python
   # 好
   if sector == SectorQuadrant.SECTOR_1:
       ...
   
   # 避免
   if sector == "sector_1":
       ...
   ```

2. **利用工厂方法**
   ```python
   # 根据角度自动分配
   angle = math.atan2(y, x)
   sector = SectorQuadrant.from_angle(math.degrees(angle))
   ```

3. **使用数据类的不可变性**
   ```python
   # SectorProgress 是可变的，适合跟踪进度
   progress.increment()
   
   # SectorBounds 可以创建新实例保持不可变性
   new_bounds = SectorBounds(
       bounds.min_x - 10,
       bounds.min_y - 10,
       bounds.max_x + 10,
       bounds.max_y + 10
   )
   ```