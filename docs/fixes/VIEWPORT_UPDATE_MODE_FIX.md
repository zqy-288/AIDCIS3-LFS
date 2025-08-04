# 视口更新模式修复 - 解决蓝色不变绿色问题

## 问题根源
使用 `MinimalViewportUpdate` 模式导致快速的颜色变化被Qt的优化机制"吃掉"了。

## 实施的修复

### 1. 修改了中间大图的更新模式
文件：`src/core_business/graphics/graphics_view.py`
```python
# 原来：
self.setViewportUpdateMode(QGraphicsView.MinimalViewportUpdate)

# 改为：
self.setViewportUpdateMode(QGraphicsView.SmartViewportUpdate)
```

### 2. 修改了全景图的更新模式
文件：`src/pages/main_detection_p1/components/graphics/panorama_view/components/panorama_graphics_view.py`
```python
# 原来：
self.setViewportUpdateMode(QGraphicsView.MinimalViewportUpdate)

# 改为：
self.setViewportUpdateMode(QGraphicsView.SmartViewportUpdate)
```

## 为什么这能解决问题？

1. **MinimalViewportUpdate**：
   - 只更新"脏"区域的最小矩形
   - 会合并相近的更新请求
   - 如果颜色在短时间内变化（蓝色→绿色），可能只执行最后一次更新
   - 但如果最后一次更新被优化掉，就会保持中间状态（蓝色）

2. **SmartViewportUpdate**：
   - Qt自动决定最佳更新策略
   - 对于颜色变化这种情况，会确保更新被执行
   - 平衡了性能和正确性

## 性能影响

- 对于25000+孔位的场景，SmartViewportUpdate 可能稍慢
- 但确保了显示的正确性
- 如果性能问题严重，可以考虑：
  1. 在检测时使用 SmartViewportUpdate
  2. 检测结束后恢复 MinimalViewportUpdate

## 验证方法

1. 运行检测模拟
2. 观察蓝色孔位是否在9.5秒后正确变为绿色/红色
3. 检查是否有孔位"卡"在蓝色状态

## 后续优化建议

如果仍有问题，可以尝试：
1. 使用 `BoundingRectViewportUpdate`
2. 在关键时刻使用 `FullViewportUpdate`
3. 添加用户配置选项来选择更新模式