# 蓝色状态不更新的根本原因分析

## 问题表现
- 检测时孔位变为蓝色（正常）
- 9.5秒后应该变为绿色/红色，但部分孔位仍保持蓝色
- 日志显示状态更新正确执行，但视觉上没有变化

## 根本原因

### 1. Qt图形项的绘制机制
QGraphicsEllipseItem 继承自 QAbstractGraphicsShapeItem，内部维护了画刷和画笔。当调用 `setBrush()` 时，Qt会：
- 更新内部画刷
- 调用 `update()` 标记需要重绘
- 等待事件循环处理绘制事件

### 2. 我们代码的问题

#### 问题1：过度优化导致的复杂性
```python
def update_appearance(self):
    # ... 设置颜色 ...
    self.setPen(pen)
    self.setBrush(brush)
    
    # 以下都是不必要的：
    self.prepareGeometryChange()  # 颜色改变不需要这个
    self.update()  # setBrush已经调用了update
    if self.scene():
        self.scene().update(self.sceneBoundingRect())  # 重复的更新
```

#### 问题2：paint()方法的LOD优化可能导致问题
```python
def paint(self, painter: QPainter, option, widget=None):
    # 不同缩放级别使用不同绘制方式
    # 但都依赖 self.brush() 返回正确的画刷
```

#### 问题3：多个地方调用update_appearance
- `set_color_override()` 调用
- `clear_color_override()` 调用  
- `update_status()` 调用
可能导致状态不一致

### 3. 为什么"强制刷新"似乎有效
- `repaint()` 立即重绘，绕过了事件队列
- `QApplication.processEvents()` 强制处理所有待处理事件
- 多次调用 `update()` 增加了被处理的概率

但这些都是症状治疗，不是根本解决。

## 真正的解决方案

### 1. 简化更新逻辑
```python
def update_appearance(self):
    """更新外观 - 简化版"""
    # 获取颜色
    if self._color_override:
        color = self._color_override
    else:
        color = self.STATUS_COLORS.get(self.hole_data.status, QColor(128, 128, 128))
    
    # 设置画笔和画刷
    # ... 设置 pen 和 brush ...
    
    # 只调用必要的更新
    self.setPen(pen)
    self.setBrush(brush)
    # 不需要额外的 update() 调用
```

### 2. 确保paint()方法正确
如果自定义了paint()，确保在所有情况下都使用最新的画刷。

### 3. 调试真正的问题
添加日志确认：
- `_color_override` 的值
- `self.brush().color()` 的实际颜色
- `paint()` 方法是否被调用

## 结论
问题不是Qt没有更新，而是我们的代码过于复杂，可能在某些情况下状态不一致。通过简化逻辑和正确使用Qt的API，应该可以解决问题，而不需要"强制刷新"。