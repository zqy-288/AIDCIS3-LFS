# 最终蓝色问题修复建议

## 当前状态
从截图可以看到大量蓝色孔位没有更新为最终颜色（绿色/红色）。

## 核心问题
尽管代码逻辑正确，颜色数据已更新，但Qt的绘制系统没有正确刷新显示。

## 推荐的修复方案

### 1. 修改视图更新模式
```python
# graphics_view.py
# 将 MinimalViewportUpdate 改为 FullViewportUpdate
self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
```

### 2. 禁用场景索引（临时）
```python
# 在加载孔位后
self.scene.setItemIndexMethod(QGraphicsScene.NoIndex)
```

### 3. 在 hole_item.py 中使用更激进的更新
```python
def clear_color_override(self):
    """清除颜色覆盖"""
    if self._color_override is not None:
        self._color_override = None
        self.update_appearance()
        # 更新提示框文本
        self.setToolTip(self._create_tooltip())
        
        # 强制场景失效并重绘
        if self.scene():
            self.scene().invalidate(self.sceneBoundingRect())
```

### 4. 批量更新优化
不要每个孔位单独更新，而是收集所有需要更新的孔位，然后一次性刷新：

```python
def _finalize_current_pair_status(self):
    # ... 更新所有孔位状态 ...
    
    # 一次性刷新整个场景
    if self.graphics_view and self.graphics_view.scene():
        self.graphics_view.scene().invalidate()
        self.graphics_view.viewport().repaint()
```

## 调试建议

1. **添加绘制计数器**：在 `paint()` 方法中添加计数器，确认每个蓝色孔位是否被重新绘制

2. **检查场景项数量**：确保没有重复的图形项

3. **测试不同的更新策略**：
   - `update()` vs `repaint()`
   - `scene.update()` vs `scene.invalidate()`
   - 部分更新 vs 全场景更新

## 根本解决方案

可能需要重新考虑颜色更新机制：
- 不使用 `_color_override`，直接修改状态
- 使用自定义绘制而不依赖 Qt 的缓存
- 考虑使用 QGraphicsEffect 来实现颜色效果