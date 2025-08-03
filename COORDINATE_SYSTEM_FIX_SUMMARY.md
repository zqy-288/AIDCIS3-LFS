# 坐标系统一修复总结

## 问题描述

左边的全景图和中间的扇形显示不一致：
- sector_1 在左边全景图显示为右上
- 但在中间扇形视图却显示为右下

## 问题原因

经过分析发现，系统中存在两种不同的坐标系使用：

1. **Qt坐标系（Y轴向下）**
   - `SectorQuadrant.from_position` 原本使用Qt坐标系
   - y < center_y 表示在上方

2. **数学坐标系（Y轴向上）**  
   - `SectorAssignmentManager` 使用数学坐标系
   - dy >= 0 表示在上方
   - DXF文件通常使用数学坐标系

这种不一致导致：
- 同一个孔位在不同组件中被分配到不同的扇形
- 左边全景图和中间扇形显示不一致

## 修复方案

统一使用数学坐标系，因为：
1. DXF文件使用数学坐标系
2. 扇形角度定义基于数学坐标系（0°在右，逆时针增加）
3. 大部分计算逻辑已经使用数学坐标系

## 修复内容

### 1. 修改 `SectorQuadrant.from_position` 方法
文件：`src/core_business/graphics/sector_types.py`

```python
@classmethod
def from_position(cls, x: float, y: float, center_x: float, center_y: float) -> 'SectorQuadrant':
    """根据位置相对于中心点确定扇形象限（数学坐标系）"""
    # 使用数学坐标系：Y轴向上
    if x >= center_x and y >= center_y:
        return cls.SECTOR_1  # 右上
    elif x < center_x and y >= center_y:
        return cls.SECTOR_2  # 左上
    elif x < center_x and y < center_y:
        return cls.SECTOR_3  # 左下
    else:  # x >= center_x and y < center_y
        return cls.SECTOR_4  # 右下
```

### 2. 修改全景图点击检测逻辑
文件：`src/core_business/graphics/complete_panorama_widget.py`

```python
# 计算角度（转换为0-360度）
# 使用数学坐标系：Y轴向上，角度从正X轴开始逆时针增加
angle_rad = math.atan2(dy, dx)  # 数学坐标系
angle_deg = math.degrees(angle_rad)
```

## 修复后的效果

1. **坐标系统一**
   - 所有组件使用相同的数学坐标系
   - 扇形分配逻辑保持一致

2. **扇形映射正确**
   - sector_1: 右上（第一象限）
   - sector_2: 左上（第二象限）
   - sector_3: 左下（第三象限）
   - sector_4: 右下（第四象限）

3. **显示一致性**
   - 左边全景图的扇形高亮与中间扇形视图显示的内容完全一致
   - 点击全景图的某个扇形，中间会显示相同的孔位集合

## 测试验证

运行 `test_coordinate_fix.py` 验证修复效果：

```bash
python3 test_coordinate_fix.py
```

测试结果显示：
- ✅ 所有坐标系转换方法返回一致的结果
- ✅ 扇形映射符合预期（数学坐标系）
- ✅ 左边全景图和中间扇形显示现在保持一致

## 注意事项

1. 如果系统中还有其他地方使用Qt坐标系进行扇形判断，也需要相应修改
2. 确保所有新增代码都使用数学坐标系
3. 在处理鼠标事件或屏幕坐标时，需要注意坐标系转换