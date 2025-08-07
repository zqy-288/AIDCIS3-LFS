# Qt视图更新模式深度分析

## QGraphicsView 的更新模式

### 1. MinimalViewportUpdate (当前使用)
```python
self.setViewportUpdateMode(QGraphicsView.MinimalViewportUpdate)
```
- **特点**：只更新发生变化的最小矩形区域
- **优点**：性能最好，减少不必要的重绘
- **缺点**：可能导致某些更新被"优化"掉，特别是快速连续的更新
- **问题**：这就是为什么蓝色点没有更新的原因！

### 2. FullViewportUpdate
```python
self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
```
- **特点**：任何更新都会重绘整个视口
- **优点**：确保所有更新都能显示
- **缺点**：性能较差，特别是场景很大时

### 3. SmartViewportUpdate
```python
self.setViewportUpdateMode(QGraphicsView.SmartViewportUpdate)
```
- **特点**：Qt自动选择最优策略
- **优点**：平衡性能和正确性
- **缺点**：行为不可预测

### 4. BoundingRectViewportUpdate
```python
self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
```
- **特点**：更新所有变化区域的边界矩形
- **优点**：比Full快，比Minimal可靠
- **缺点**：多个分散的更新会导致大面积重绘

## 问题分析

### 为什么 MinimalViewportUpdate 导致蓝色不更新？

1. **更新合并**：Qt会合并相近的更新区域，如果一个孔位在短时间内多次更新（设置蓝色→清除蓝色），可能只执行最后一次

2. **脏区域计算**：如果图形项的边界没有变化（只是颜色变了），MinimalViewportUpdate 可能认为不需要更新

3. **场景缓存**：配合场景索引，可能使用了缓存的绘制结果

## 代码中的证据

从 `hole_item.py` 的修改可以看到，已经尝试了多种强制更新的方法：
```python
# 1. 基本的 update()
self.update()

# 2. 场景级别的更新
self.scene().update(self.sceneBoundingRect())

# 3. 视口级别的更新
for view in self.scene().views():
    view_rect = view.mapFromScene(rect).boundingRect()
    view.viewport().update(view_rect)
```

但是在 `MinimalViewportUpdate` 模式下，这些更新可能被优化掉了。

## 解决方案

### 方案1：改变更新模式（推荐）
```python
# graphics_view.py
def __init__(self):
    # ... 其他初始化 ...
    
    # 改为 SmartViewportUpdate 或 BoundingRectViewportUpdate
    self.setViewportUpdateMode(QGraphicsView.SmartViewportUpdate)
```

### 方案2：临时切换更新模式
```python
def update_hole_status(self, hole_id: str, status: HoleStatus, color_override=None):
    # 临时切换到 FullViewportUpdate
    old_mode = self.viewportUpdateMode()
    self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
    
    # 执行更新
    # ...
    
    # 恢复原模式
    self.setViewportUpdateMode(old_mode)
```

### 方案3：强制失效场景区域
```python
def clear_color_override(self):
    if self._color_override is not None:
        self._color_override = None
        self.update_appearance()
        
        # 强制使场景区域失效
        if self.scene():
            # invalidate 比 update 更强制
            self.scene().invalidate(self.sceneBoundingRect(), QGraphicsScene.ItemLayer)
```

## 性能考虑

1. **25000+ 孔位**的场景，FullViewportUpdate 可能很慢
2. **SmartViewportUpdate** 是个好的折中选择
3. 可以在**检测进行时**使用 SmartViewportUpdate，**检测结束后**恢复 MinimalViewportUpdate

## 建议实施步骤

1. 先改中间大图的更新模式，测试效果
2. 如果有效，再改其他视图
3. 考虑添加配置选项，让用户选择性能/质量平衡