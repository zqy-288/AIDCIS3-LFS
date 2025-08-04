# 清理版修复方案 - 不依赖强制刷新

## 修复原则
1. 移除所有不必要的"强制刷新"
2. 简化更新逻辑
3. 正确使用Qt的绘制机制

## 具体修改

### 1. hole_item.py - 简化update_appearance
```python
def update_appearance(self):
    """更新外观"""
    # 获取状态颜色 - 优先使用颜色覆盖
    if self._color_override:
        color = self._color_override
    else:
        color = self.STATUS_COLORS.get(self.hole_data.status, QColor(128, 128, 128))
    
    # 设置画笔和画刷
    # ... 省略中间的画笔画刷设置逻辑 ...
    
    self.setPen(pen)
    self.setBrush(brush)
    # 移除所有额外的update调用
```

### 2. hole_item.py - 简化clear_color_override
```python
def clear_color_override(self):
    """清除颜色覆盖"""
    if self._color_override is not None:
        self._color_override = None
        self.update_appearance()
        # 更新提示框文本
        self.setToolTip(self._create_tooltip())
        # 移除所有强制刷新
```

### 3. hole_item.py - 简化set_color_override  
```python
def set_color_override(self, color_override):
    """设置颜色覆盖"""
    self._color_override = color_override
    self.update_appearance()
    # 移除所有强制刷新
```

### 4. 添加调试日志（临时）
```python
def update_appearance(self):
    """更新外观"""
    # 获取状态颜色
    if self._color_override:
        color = self._color_override
        print(f"[DEBUG] {self.hole_data.hole_id}: 使用覆盖颜色 RGB({color.red()}, {color.green()}, {color.blue()})")
    else:
        color = self.STATUS_COLORS.get(self.hole_data.status, QColor(128, 128, 128))
        print(f"[DEBUG] {self.hole_data.hole_id}: 使用状态颜色 {self.hole_data.status.value} RGB({color.red()}, {color.green()}, {color.blue()})")
    
    # ... 其余代码 ...
```

### 5. 确保paint()方法被调用
在paint()方法开始添加调试：
```python
def paint(self, painter: QPainter, option, widget=None):
    """自定义绘制"""
    # 调试日志
    current_color = self.brush().color()
    print(f"[DEBUG PAINT] {self.hole_data.hole_id}: 绘制颜色 RGB({current_color.red()}, {current_color.green()}, {current_color.blue()})")
    
    # ... 其余绘制代码 ...
```

## 预期结果
1. 简化后的代码应该正常工作
2. 调试日志会显示：
   - 设置蓝色时：使用覆盖颜色 RGB(33, 150, 243)
   - 清除蓝色时：使用状态颜色 qualified RGB(50, 200, 50)
   - paint时：绘制颜色应该与上面一致

## 如果还不工作
如果简化后还不工作，问题可能是：
1. Qt的事件循环被阻塞
2. 存在多个图形项实例
3. 场景的索引需要重建

这时才考虑添加最小的辅助：
- 在 simulation_controller 的 _finalize_current_pair_status 最后调用一次 `QApplication.processEvents(QEventLoop.ExcludeUserInputEvents)`