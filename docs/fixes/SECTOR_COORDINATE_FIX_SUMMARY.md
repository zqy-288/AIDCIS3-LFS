# 扇形坐标系修复总结

## 问题描述
用户反馈 sector_1 应该显示右上角的内容，但实际显示的是右下角的内容。

## 问题根源
经过分析发现，项目中存在坐标系混用的问题：
- **数学坐标系**（Y轴向上）：sector_types.py 和 sector_assignment_manager.py
- **Qt坐标系**（Y轴向下）：sector_controllers.py 和 sector_data_distributor.py

这导致了扇形分配和显示的不一致。

## 坐标系差异

### 数学坐标系（Y轴向上）
```
        SECTOR_2 (左上)  |  SECTOR_1 (右上)
                         |
        -----------------+-------------------> X
                         |
        SECTOR_3 (左下)  |  SECTOR_4 (右下)
                         |
                         v Y
```

### Qt坐标系（Y轴向下）
```
                         ^ Y (向上是负值)
                         |
        SECTOR_2 (左上)  |  SECTOR_1 (右上)
                         |
        -----------------+-------------------> X
                         |
        SECTOR_3 (左下)  |  SECTOR_4 (右下)
                         |
                         v Y (向下是正值)
```

## 修复方案
统一使用 **Qt坐标系**，因为：
1. Qt的绘图系统本身使用Qt坐标系
2. 鼠标事件和场景坐标都是Qt坐标系
3. 保持与实际显示一致

## 修改内容

### 1. `/src/core_business/graphics/sector_types.py`
修改 `from_position` 方法，从数学坐标系改为Qt坐标系：

```python
# 修改前（数学坐标系）
if x >= center_x and y >= center_y:
    return cls.SECTOR_1  # 右上

# 修改后（Qt坐标系）
if x >= center_x and y < center_y:
    return cls.SECTOR_1  # 右上
```

### 2. `/src/pages/main_detection_p1/components/sector_assignment_manager.py`
- 更新象限定义注释
- 修改 `_perform_sector_assignment` 方法的判断逻辑

```python
# 修改前（数学坐标系）
if x_sign >= 0 and dy >= 0:
    sector = SectorQuadrant.SECTOR_1  # 右上

# 修改后（Qt坐标系）
if x_sign >= 0 and dy < 0:
    sector = SectorQuadrant.SECTOR_1  # 右上
```

## 验证结果
修复后的扇形分配：
- **SECTOR_1 (右上)**: x >= center_x, y < center_y ✓
- **SECTOR_2 (左上)**: x < center_x, y < center_y ✓
- **SECTOR_3 (左下)**: x < center_x, y >= center_y ✓
- **SECTOR_4 (右下)**: x >= center_x, y >= center_y ✓

## 影响范围
此修复仅影响扇形的分配逻辑，不影响：
- 孔位数据本身
- 检测逻辑
- 渲染显示
- 其他功能模块

## 建议
1. 在代码中明确标注使用的坐标系类型
2. 统一项目中所有坐标系的使用
3. 添加单元测试确保扇形分配的正确性