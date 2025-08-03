# 蓝色到绿色/红色渲染延迟问题修复

## 问题描述
在模拟检测过程中，孔位在检测完成后（9.5秒）应该从蓝色变为绿色（合格）或红色（不合格），但实际显示时颜色更新有延迟，即使下一个孔位已经开始检测，上一个孔位仍然显示为蓝色。

## 问题原因
1. **Qt事件循环延迟**：Qt使用异步更新机制，`update()` 调用不会立即重绘
2. **视图缓冲**：图形视图可能使用了缓冲机制，导致颜色变化不立即可见
3. **事件优先级**：颜色更新事件可能被其他事件延迟处理

## 解决方案

### 1. 强制立即视图更新
在 `_finalize_current_pair_status` 方法中添加了 `_force_immediate_visual_update` 方法：
- 使用 `repaint()` 而不是 `update()` 强制立即重绘
- 对图形视图和全景图都进行强制刷新
- 使用 `QApplication.processEvents()` 确保所有更新被处理

### 2. 颜色清除后的快速刷新
在 `_update_hole_status` 方法中检测颜色覆盖清除：
- 当 `color_override=None` 且状态不是 PENDING 时，触发快速刷新
- 使用 10ms 延迟的 `QTimer.singleShot` 确保更新在下一个事件循环中执行

### 3. 局部区域刷新优化
添加了 `_quick_refresh_view` 方法：
- 只刷新特定孔位的边界区域，而不是整个场景
- 减少刷新开销，提高响应速度

## 关键代码改动

```python
# 1. 强制立即更新
def _force_immediate_visual_update(self):
    """强制立即更新所有视图"""
    if self.graphics_view:
        self.graphics_view.viewport().repaint()  # repaint 而不是 update
    if self.panorama_widget:
        self.panorama_widget.repaint()
    QApplication.processEvents(QEventLoop.AllEvents, 50)

# 2. 颜色清除检测
if color_override is None and status != HoleStatus.PENDING:
    QTimer.singleShot(10, lambda: self._quick_refresh_view(hole_id))

# 3. 局部刷新
def _quick_refresh_view(self, hole_id):
    """快速刷新特定孔位"""
    # 只更新孔位的边界区域
    scene.update(item.sceneBoundingRect())
```

## 效果
- 孔位颜色在9.5秒后立即从蓝色变为最终状态颜色
- 不会出现上一个孔位还是蓝色而下一个已经开始检测的情况
- 渲染更新更加流畅和及时

## 进一步优化建议
1. 如果问题仍然存在，可以考虑：
   - 增加检测间隔（如从10秒增加到11秒）
   - 在状态更新之间添加更多的事件处理时间
   - 使用 `QGraphicsView.FullViewportUpdate` 模式

2. 性能优化：
   - 批量更新多个孔位时，先收集所有更新，然后一次性刷新
   - 使用脏区域（dirty region）机制减少不必要的重绘