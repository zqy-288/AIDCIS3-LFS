# 模拟进行中蓝色不变绿色 - 真正的问题分析

## 问题重新定义
模拟**进行过程中**，某些孔位保持蓝色，没有在9.5秒后变成绿色。

## 可能的原因

### 1. Qt事件循环阻塞
虽然定时器设置正确，但Qt的事件循环可能被阻塞，导致：
- `update()` 调用没有触发实际的重绘
- 界面没有刷新显示新颜色

### 2. 视图更新不一致
从日志看到：
```
[DEBUG] BC098R164: 使用状态颜色 qualified RGB(50, 200, 50)
```
但是截图显示仍然是蓝色，说明：
- 数据模型已更新
- 图形项的颜色已改变
- 但**视觉显示没有更新**

### 3. 场景索引问题
Qt的场景可能使用了优化索引，导致某些项的更新被忽略。

### 4. 多线程问题
如果有其他线程在操作UI，可能导致更新不同步。

## 诊断方法

### 1. 检查 paint() 是否被调用
从之前的日志看，`paint()` 方法被大量调用，但可能没有绘制正确的颜色。

### 2. 检查场景更新机制
```python
# 在 hole_item.py 的 update_appearance() 中
self.setBrush(brush)
self.update()  # 这个可能不够

# 可能需要：
self.prepareGeometryChange()  # 通知场景几何变化
self.scene().update(self.sceneBoundingRect())  # 强制场景更新该区域
```

### 3. 检查是否有多个图形项实例
可能同一个孔位有多个图形项，导致显示的是旧的项。

## 真正的修复方案

### 方案1：强制场景更新（已经尝试过）
```python
def clear_color_override(self):
    if self._color_override is not None:
        self._color_override = None
        self.update_appearance()
        # 强制场景更新
        if self.scene():
            self.scene().update(self.sceneBoundingRect())
```

### 方案2：使用 repaint() 而不是 update()
```python
def update_appearance(self):
    # ... 设置颜色 ...
    self.setPen(pen)
    self.setBrush(brush)
    
    # 使用 repaint 立即重绘
    if self.scene() and self.scene().views():
        for view in self.scene().views():
            view.viewport().repaint(view.mapFromScene(self.sceneBoundingRect()).boundingRect())
```

### 方案3：重建场景索引
```python
# 在适当的时候
if self.scene():
    self.scene().setItemIndexMethod(QGraphicsScene.NoIndex)
    # 或者
    self.scene().invalidate()
```

## 最可能的原因

基于症状（数据正确但显示错误），最可能是：
1. **Qt的绘制优化导致某些更新被跳过**
2. **场景的索引缓存导致旧的绘制结果被使用**
3. **视口更新模式设置不当**

## 建议的调试步骤

1. 在 `paint()` 方法中添加计数器，确认是否被调用
2. 检查 `boundingRect()` 是否正确
3. 尝试禁用场景索引
4. 检查是否有其他地方在修改图形项