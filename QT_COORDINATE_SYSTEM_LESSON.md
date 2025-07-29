# Qt坐标系与数学坐标系差异导致的扇形映射问题

## 问题描述

在实现扇形分区功能时，遇到了一个典型的坐标系差异问题：点击左边扇形时，右边显示的内容与预期不符。具体表现为：
- 点击上方扇形，显示的是下方的内容
- 点击左侧扇形，显示的是右侧的内容

## 根本原因

### 1. 坐标系差异

**数学坐标系（DXF数据使用）**：
- 原点在左下角
- X轴向右为正
- **Y轴向上为正** ⬆️

**Qt屏幕坐标系（显示使用）**：
- 原点在左上角
- X轴向右为正
- **Y轴向下为正** ⬇️

### 2. 问题图示

```
数学坐标系:              Qt显示坐标系:
    ↑ Y                      (0,0) → X
    │                         │
 Q2 │ Q1                   Q2 │ Q1
────┼──── → X              ───┼───
 Q3 │ Q4                   Q3 │ Q4
    │                         ↓ Y
```

在数学坐标系中 `y > 0` 的点在"上方"，但在Qt显示时却出现在屏幕"下方"！

## 错误的实现

```python
# 原始错误的扇形分配逻辑
if dx >= 0 and dy >= 0:
    sector = SectorQuadrant.SECTOR_1  # 右上
elif dx < 0 and dy >= 0:
    sector = SectorQuadrant.SECTOR_2  # 左上
elif dx < 0 and dy < 0:
    sector = SectorQuadrant.SECTOR_3  # 左下
else:  # dx >= 0 and dy < 0
    sector = SectorQuadrant.SECTOR_4  # 右下
```

这个逻辑基于数学坐标系，但在Qt中显示时会出现错位。

## 正确的解决方案

### 方案1：修改扇形分配逻辑（推荐）

```python
# 考虑Qt坐标系Y轴向下的扇形分配
if dx >= 0 and dy <= 0:
    sector = SectorQuadrant.SECTOR_1  # Qt显示的右上（y<0在屏幕上方）
elif dx < 0 and dy <= 0:
    sector = SectorQuadrant.SECTOR_2  # Qt显示的左上（y<0在屏幕上方）
elif dx < 0 and dy > 0:
    sector = SectorQuadrant.SECTOR_3  # Qt显示的左下（y>0在屏幕下方）
else:  # dx >= 0 and dy > 0
    sector = SectorQuadrant.SECTOR_4  # Qt显示的右下（y>0在屏幕下方）
```

### 方案2：坐标转换（不推荐）

```python
# 将数学坐标转换为Qt坐标
qt_y = -math_y  # 翻转Y轴
```

不推荐这种方案，因为会影响整个系统的坐标计算。

## 调试技巧

### 1. 创建坐标系测试工具

```python
def test_coordinates():
    """可视化坐标系差异"""
    # 在数据的四个角添加标记
    # 观察它们在Qt中的实际显示位置
    
    # 右上角 (数据: x>0, y>0)
    text1 = scene.addText("数据右上\n(x>0,y>0)")
    text1.setPos(max_x, min_y)  # Qt中Y小的在上
    
    # 左下角 (数据: x<0, y<0)
    text3 = scene.addText("数据左下\n(x<0,y<0)")
    text3.setPos(min_x, max_y)  # Qt中Y大的在下
```

### 2. 打印调试信息

```python
print(f"数据坐标: ({x}, {y})")
print(f"  在数学坐标系中: {'上' if y > 0 else '下'}方")
print(f"  在Qt显示中: {'下' if y > 0 else '上'}方")
```

## 影响范围

这个问题会影响所有涉及方向判断的功能：
1. 扇形分区映射
2. 方向导航（上下左右）
3. 位置相关的高亮显示
4. 基于位置的数据筛选

## 最佳实践

1. **文档化坐标系**：在代码中明确注释使用的是哪种坐标系
2. **统一转换层**：在数据层和显示层之间建立明确的转换规则
3. **视觉验证**：实现新功能时，创建简单的视觉测试来验证坐标映射
4. **保持一致性**：整个项目中保持坐标系处理的一致性

## 修复清单

需要检查和修复的文件：
- [x] `/src/core_business/coordinate_system.py` - 扇形分配逻辑
- [ ] 其他使用方向判断的模块
- [ ] 坐标相关的工具函数

## 经验总结

1. **永远不要假设坐标系方向**：不同的系统可能使用不同的坐标系
2. **早期发现**：在开发初期就要注意坐标系差异
3. **可视化调试**：遇到位置相关问题时，优先使用可视化方式调试
4. **保持警觉**：特别是在处理图形、CAD数据时，坐标系差异是常见问题

## 参考资料

- Qt坐标系文档：https://doc.qt.io/qt-6/coordsys.html
- 数学坐标系 vs 屏幕坐标系：常见的图形编程陷阱